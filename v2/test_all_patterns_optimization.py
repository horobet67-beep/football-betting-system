"""
Test all patterns across historical periods to find optimal weight configurations.
Tests each pattern individually across multiple timeframes to determine best settings per league.
WITH PARALLEL PROCESSING for faster results.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
from collections import defaultdict
from multiprocessing import Pool, cpu_count
from functools import partial
import warnings
import json
import time

warnings.filterwarnings('ignore')

from data.premier_league_adapter import load_premier_league_data
from data.bundesliga_adapter import load_bundesliga_data
from data.la_liga_adapter import load_la_liga_data
from data.serie_a_adapter import load_serie_a_data
from data.romanian_adapter import load_romanian_data

from patterns.registry import get_pattern_registry, clear_patterns
from patterns.premier_league_patterns import register_premier_league_patterns
from patterns.bundesliga_patterns import register_bundesliga_patterns
from patterns.la_liga_patterns import register_la_liga_patterns
from patterns.serie_a_patterns import register_serie_a_patterns
from patterns.romanian_patterns import register_romanian_patterns

from utils.confidence import calculate_multi_timeframe_confidence


# Test different weight configurations
WEIGHT_CONFIGURATIONS = {
    'extreme_recent': {
        7: 0.40, 14: 0.30, 30: 0.15, 90: 0.10, 365: 0.05
    },
    'recent_heavy': {
        7: 0.35, 14: 0.25, 30: 0.20, 90: 0.15, 365: 0.05
    },
    'balanced': {
        7: 0.25, 14: 0.25, 30: 0.25, 90: 0.15, 365: 0.10
    },
    'season_focused': {
        7: 0.20, 14: 0.20, 30: 0.25, 90: 0.25, 365: 0.10
    },
    'long_term': {
        7: 0.15, 14: 0.15, 30: 0.20, 90: 0.25, 365: 0.25
    }
}


class PatternBacktester:
    """Backtest individual patterns to find optimal configurations"""
    
    def __init__(self, league_name: str, df: pd.DataFrame, register_func):
        self.league_name = league_name
        self.df = df
        
        # Ensure Date column exists
        if 'Date' not in self.df.columns:
            if 'date' in self.df.columns:
                self.df['Date'] = pd.to_datetime(self.df['date'])
            else:
                raise ValueError("No Date column found in dataframe")
        
        # Register patterns
        clear_patterns()
        register_func()
        
        registry = get_pattern_registry()
        all_patterns = registry.get_all_patterns()
        self.patterns = {p.name: p for p in all_patterns}
        
        print(f"\n{'='*80}")
        print(f"Initialized {league_name} Backtester")
        print(f"Patterns: {len(self.patterns)}, Matches: {len(self.df)}")
        print(f"Date Range: {self.df['Date'].min()} to {self.df['Date'].max()}")
        print(f"{'='*80}")
    
    def test_single_config_period(self, args):
        """Test a single configuration on a single period (for parallel processing)"""
        pattern_name, pattern_func, weight_config, config_name, period_start, period_end, min_confidence = args
        
        # Get matches in test period
        test_matches = self.df[
            (self.df['Date'] >= period_start) & 
            (self.df['Date'] <= period_end)
        ].copy()
        
        if len(test_matches) == 0:
            return None
        
        predictions = []
        results = []
        
        for _, match in test_matches.iterrows():
            match_date = pd.Timestamp(match['Date'])
            
            # Calculate confidence using this weight config
            try:
                success_rate, debug_info = calculate_multi_timeframe_confidence(
                    self.df,
                    match_date,
                    pattern_func,
                    min_matches_7d=2,
                    min_matches_30d=8,
                    custom_timeframes=weight_config,
                    use_all_history=False
                )
                
                # Check if we would bet on this
                if success_rate >= min_confidence:
                    predictions.append({
                        'date': match_date,
                        'confidence': success_rate,
                    })
                    
                    # Check actual result
                    actual_result = pattern_func(match)
                    results.append(1 if actual_result else 0)
            except:
                continue
        
        if len(predictions) == 0:
            return None
        
        win_rate = np.mean(results) if results else 0.0
        
        return {
            'config_name': config_name,
            'predictions': len(predictions),
            'wins': sum(results),
            'win_rate': win_rate,
            'avg_confidence': np.mean([p['confidence'] for p in predictions])
        }
    
    def test_pattern_all_configs_parallel(
        self,
        pattern_name: str,
        test_periods: List[Tuple[datetime, datetime]],
        min_confidence: float = 0.60
    ) -> Dict:
        """Test a pattern across all weight configurations and time periods using parallel processing"""
        
        pattern = self.patterns.get(pattern_name)
        if not pattern:
            return None
        
        # Create all tasks for parallel processing
        tasks = []
        for period_start, period_end in test_periods:
            for config_name, weight_config in WEIGHT_CONFIGURATIONS.items():
                tasks.append((
                    pattern_name,
                    pattern.label_fn,
                    weight_config,
                    config_name,
                    period_start,
                    period_end,
                    min_confidence
                ))
        
        # Process in parallel
        results_by_config = defaultdict(list)
        
        # Use fewer workers to avoid overwhelming the system
        num_workers = min(cpu_count() - 1, 4)
        
        with Pool(num_workers) as pool:
            results = pool.map(self.test_single_config_period, tasks)
        
        # Organize results by config
        for result in results:
            if result:
                results_by_config[result['config_name']].append(result)
        
        # Aggregate results per configuration
        aggregated = {}
        for config_name, results in results_by_config.items():
            if results:
                total_preds = sum(r['predictions'] for r in results)
                total_wins = sum(r['wins'] for r in results)
                
                aggregated[config_name] = {
                    'total_predictions': total_preds,
                    'total_wins': total_wins,
                    'overall_win_rate': total_wins / total_preds if total_preds > 0 else 0.0,
                    'avg_confidence': np.mean([r['avg_confidence'] for r in results]),
                    'periods_tested': len(results)
                }
        
        return aggregated
    
    def find_best_configuration(
        self,
        pattern_name: str,
        test_periods: List[Tuple[datetime, datetime]],
        min_predictions: int = 10
    ) -> Tuple[str, Dict]:
        """Find the best weight configuration for a pattern"""
        
        results = self.test_pattern_all_configs_parallel(pattern_name, test_periods)
        
        if not results:
            return None, None
        
        # Filter configs with enough predictions
        valid_configs = {
            name: stats for name, stats in results.items()
            if stats['total_predictions'] >= min_predictions
        }
        
        if not valid_configs:
            return None, None
        
        # Find best by win rate
        best_config = max(valid_configs.items(), key=lambda x: x[1]['overall_win_rate'])
        
        return best_config[0], best_config[1]


def generate_test_periods(df: pd.DataFrame, period_length_days: int = 30) -> List[Tuple[datetime, datetime]]:
    """Generate non-overlapping test periods from historical data"""
    
    min_date = df['Date'].min()
    max_date = df['Date'].max()
    
    periods = []
    current_start = min_date
    
    while current_start < max_date:
        current_end = current_start + timedelta(days=period_length_days)
        if current_end > max_date:
            current_end = max_date
        
        periods.append((current_start, current_end))
        current_start = current_end + timedelta(days=1)
    
    return periods


def main():
    """Run pattern optimization for all leagues"""
    
    print(f"\n🚀 Using {min(cpu_count() - 1, 4)} CPU cores for parallel processing\n")
    
    start_time = time.time()
    
    leagues = {
        'Premier League': (load_premier_league_data(), register_premier_league_patterns),
        'Bundesliga': (load_bundesliga_data(), register_bundesliga_patterns),
        'La Liga': (load_la_liga_data(), register_la_liga_patterns),
        'Serie A': (load_serie_a_data(), register_serie_a_patterns),
        'Romanian Liga 1': (load_romanian_data(), register_romanian_patterns)
    }
    
    # Store best configurations per league
    league_best_configs = {}
    all_detailed_results = {}
    
    print("\n" + "="*80)
    print("PATTERN WEIGHT OPTIMIZATION - Testing ALL Patterns Across Time Periods")
    print("="*80)
    
    for league_name, (df, register_func) in leagues.items():
        print(f"\n{'='*80}")
        print(f"Testing {league_name}")
        print(f"{'='*80}")
        
        backtester = PatternBacktester(league_name, df, register_func)
        
        # Generate test periods (30-day windows)
        test_periods = generate_test_periods(df, period_length_days=30)
        print(f"Generated {len(test_periods)} test periods")
        
        # Test ALL patterns (with parallel processing this is feasible)
        # Filter out disabled patterns (threshold >= 0.99)
        test_patterns = [
            name for name, pattern in backtester.patterns.items()
            if pattern.default_threshold < 0.99  # Skip disabled patterns
        ]
        
        print(f"\nTesting ALL {len(test_patterns)} active patterns with parallel processing...")
        print(f"Sample patterns: {', '.join(list(test_patterns)[:5])}...")
        print(f"Skipped {len([p for p in backtester.patterns.values() if p.default_threshold >= 0.99])} disabled patterns (threshold >= 0.99)")
        
        pattern_results = {}
        
        league_start_time = time.time()
        
        for i, pattern_name in enumerate(test_patterns, 1):
            print(f"  [{i:3d}/{len(test_patterns)}] Testing {pattern_name:45s}...", end=' ', flush=True)
            
            pattern_start = time.time()
            
            best_config_name, best_stats = backtester.find_best_configuration(
                pattern_name,
                test_periods,
                min_predictions=10
            )
            
            elapsed = time.time() - pattern_start
            
            if best_config_name:
                pattern_results[pattern_name] = {
                    'best_config': best_config_name,
                    'stats': best_stats
                }
                
                print(f"✓ {best_config_name:20s} WR: {best_stats['overall_win_rate']:.1%} ({best_stats['total_wins']}/{best_stats['total_predictions']}) [{elapsed:.1f}s]")
            else:
                print(f"✗ Insufficient data [{elapsed:.1f}s]")
        
        league_elapsed = time.time() - league_start_time
        print(f"\n⏱️  League processing time: {league_elapsed:.1f}s ({league_elapsed/60:.1f} minutes)")
        
        # Store detailed results
        all_detailed_results[league_name] = pattern_results
        
        # Aggregate best configuration for league
        config_counts = defaultdict(int)
        config_avg_wr = defaultdict(list)
        
        for pattern_name, result in pattern_results.items():
            config_name = result['best_config']
            config_counts[config_name] += 1
            config_avg_wr[config_name].append(result['stats']['overall_win_rate'])
        
        if config_counts:
            best_league_config = max(config_counts.items(), key=lambda x: (x[1], np.mean(config_avg_wr[x[0]])))
            
            league_best_configs[league_name] = {
                'config': best_league_config[0],
                'pattern_count': best_league_config[1],
                'avg_win_rate': np.mean(config_avg_wr[best_league_config[0]]),
                'all_configs': dict(config_counts),
                'patterns_tested': len(pattern_results)
            }
            
            print(f"\n{'='*80}")
            print(f"{league_name} - RECOMMENDED CONFIGURATION")
            print(f"{'='*80}")
            print(f"Config: {best_league_config[0]}")
            print(f"Patterns using this config: {best_league_config[1]}/{len(pattern_results)}")
            print(f"Average Win Rate: {np.mean(config_avg_wr[best_league_config[0]]):.1%}")
            print(f"\nWeights: {WEIGHT_CONFIGURATIONS[best_league_config[0]]}")
            print(f"\nAll config usage:")
            for config_name, count in sorted(config_counts.items(), key=lambda x: -x[1]):
                print(f"  {config_name:20s}: {count:2d} patterns, Avg WR: {np.mean(config_avg_wr[config_name]):.1%}")
    
    # Final summary
    print("\n" + "="*80)
    print("FINAL RECOMMENDATIONS - Best Weight Configuration Per League")
    print("="*80)
    
    for league_name, config_info in league_best_configs.items():
        print(f"\n{league_name}:")
        print(f"  Recommended: {config_info['config']}")
        print(f"  Win Rate: {config_info['avg_win_rate']:.1%}")
        print(f"  Patterns Tested: {config_info['patterns_tested']}")
        print(f"  Weights: {WEIGHT_CONFIGURATIONS[config_info['config']]}")
    
    total_elapsed = time.time() - start_time
    print(f"\n⏱️  Total execution time: {total_elapsed:.1f}s ({total_elapsed/60:.1f} minutes)")
    
    # Save detailed results to JSON file
    output_file = f"pattern_weight_optimization_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    
    # Convert results to serializable format
    serializable_results = {}
    for league, patterns in all_detailed_results.items():
        serializable_results[league] = {}
        for pattern_name, result in patterns.items():
            serializable_results[league][pattern_name] = {
                'best_config': result['best_config'],
                'total_predictions': result['stats']['total_predictions'],
                'total_wins': result['stats']['total_wins'],
                'overall_win_rate': result['stats']['overall_win_rate'],
                'avg_confidence': result['stats']['avg_confidence'],
                'periods_tested': result['stats']['periods_tested']
            }
    
    with open(output_file, 'w') as f:
        json.dump({
            'timestamp': datetime.now().isoformat(),
            'execution_time_seconds': total_elapsed,
            'weight_configurations': WEIGHT_CONFIGURATIONS,
            'league_recommendations': league_best_configs,
            'detailed_results': serializable_results
        }, f, indent=2)
    
    print(f"\n💾 Detailed results saved to: {output_file}")
    
    print("\n" + "="*80)


if __name__ == "__main__":
    main()
