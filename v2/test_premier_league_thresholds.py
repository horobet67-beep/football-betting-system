"""
Premier League Threshold Optimization Testing
Test different threshold configurations to maximize profitability.
Based on successful Bundesliga optimization approach.
"""

import pandas as pd
from datetime import datetime, timedelta
from simple_premier_league_predictor import SimplePremierLeaguePredictor
from data.premier_league_adapter import load_premier_league_data


def test_threshold_config(config_name: str, threshold_overrides: dict, lookback_days: int = 90):
    """
    Test a specific threshold configuration.
    
    Args:
        config_name: Name of the configuration
        threshold_overrides: Dict of pattern_name -> threshold overrides
        lookback_days: Lookback period for predictions
    """
    print(f"\n{'='*80}")
    print(f"Testing Configuration: {config_name}")
    print(f"{'='*80}")
    
    # Load data
    df = load_premier_league_data()
    
    # Test on recent period (last 30 days before current incomplete season)
    test_end = pd.to_datetime('2025-10-10')
    test_start = test_end - timedelta(days=30)
    
    print(f"Test period: {test_start.strftime('%Y-%m-%d')} to {test_end.strftime('%Y-%m-%d')}")
    
    # Get test matches
    test_matches = df[(df['date'] >= test_start) & (df['date'] < test_end)].copy()
    print(f"Test matches: {len(test_matches)}")
    
    if len(test_matches) == 0:
        print("No test matches in period")
        return None
    
    # Prepare test data
    test_matches['FTR'] = test_matches.apply(
        lambda row: 'H' if row['home_goals'] > row['away_goals'] 
                    else ('A' if row['away_goals'] > row['home_goals'] else 'D'),
        axis=1
    )
    test_matches = test_matches.rename(columns={
        'home_goals': 'FTHG',
        'away_goals': 'FTAG',
        'home_corners': 'HC',
        'away_corners': 'AC',
        'home_yellows': 'HY',
        'away_yellows': 'AY',
        'home_reds': 'HR',
        'away_reds': 'AR'
    })
    
    # Create predictor
    predictor = SimplePremierLeaguePredictor(lookback_days=lookback_days)
    
    # Track results by pattern
    pattern_results = {}
    total_correct = 0
    total_predictions = 0
    total_profit = 0.0
    
    for _, match in test_matches.iterrows():
        predictions = predictor.predict_match(
            match['home_team'],
            match['away_team'],
            match['date'],
            verbose=False
        )
        
        for pred in predictions:
            pattern_name = pred['pattern']
            base_threshold = pred['base_threshold']
            
            # Apply threshold override if specified
            if pattern_name in threshold_overrides:
                override_threshold = threshold_overrides[pattern_name]
                # Re-check if prediction would still be made
                if pred['confidence'] < override_threshold:
                    continue  # Skip this prediction with new threshold
            
            # Test prediction
            pattern_func = predictor.filtered_patterns[pattern_name]['func']
            actual_result = pattern_func(match)
            
            # Track pattern stats
            if pattern_name not in pattern_results:
                pattern_results[pattern_name] = {
                    'total': 0,
                    'correct': 0,
                    'profit': 0.0
                }
            
            pattern_results[pattern_name]['total'] += 1
            total_predictions += 1
            
            if actual_result:
                pattern_results[pattern_name]['correct'] += 1
                total_correct += 1
                total_profit += 1.0
                pattern_results[pattern_name]['profit'] += 1.0
            else:
                total_profit -= 1.0
                pattern_results[pattern_name]['profit'] -= 1.0
    
    # Calculate overall stats
    win_rate = (total_correct / total_predictions * 100) if total_predictions > 0 else 0
    
    print(f"\nOVERALL RESULTS:")
    print(f"  Predictions: {total_predictions}")
    print(f"  Correct: {total_correct}")
    print(f"  Win Rate: {win_rate:.1f}%")
    print(f"  Profit: {total_profit:+.1f} units")
    
    # Show top 15 patterns
    print(f"\nTOP 15 PATTERNS BY PROFIT:")
    sorted_patterns = sorted(pattern_results.items(), 
                            key=lambda x: x[1]['profit'], 
                            reverse=True)
    
    for pattern_name, stats in sorted_patterns[:15]:
        pattern_wr = (stats['correct'] / stats['total'] * 100) if stats['total'] > 0 else 0
        override_marker = " ⭐" if pattern_name in threshold_overrides else ""
        print(f"  {pattern_name:30s} | {stats['correct']:3d}/{stats['total']:3d} ({pattern_wr:5.1f}%) | {stats['profit']:+7.1f} units{override_marker}")
    
    return {
        'config_name': config_name,
        'total_predictions': total_predictions,
        'correct': total_correct,
        'win_rate': win_rate,
        'profit': total_profit,
        'pattern_results': pattern_results
    }


def main():
    """Test different threshold configurations."""
    print("="*80)
    print("PREMIER LEAGUE THRESHOLD OPTIMIZATION")
    print("Testing different threshold configurations for maximum profitability")
    print("="*80)
    
    # Configuration 1: Baseline (current thresholds)
    baseline = test_threshold_config(
        "BASELINE (Current)",
        {},
        lookback_days=90
    )
    
    # Configuration 2: Aggressive Corner Thresholds (like optimized Bundesliga)
    # Based on Premier League having even MORE corners than Bundesliga (10.42 vs 7.6)
    aggressive_corners = test_threshold_config(
        "AGGRESSIVE CORNERS",
        {
            'total_over_8_5_corners': 0.55,  # From 0.60 - very aggressive
            'total_over_9_5_corners': 0.58,  # From 0.62 - aggressive
            'total_over_7_5_corners': 0.58,  # From 0.63 - aggressive
            'home_over_2_5_corners': 0.55,   # From 0.60 - aggressive
            'away_over_2_5_corners': 0.57,   # From 0.62 - aggressive
            'home_over_3_5_corners': 0.58,   # From 0.62 - aggressive
            'total_over_10_5_corners': 0.62, # From 0.65 - moderate
        },
        lookback_days=90
    )
    
    # Configuration 3: Super Aggressive (push limits even more)
    super_aggressive = test_threshold_config(
        "SUPER AGGRESSIVE",
        {
            'total_over_8_5_corners': 0.52,  # Very aggressive
            'total_over_9_5_corners': 0.55,  # Very aggressive
            'total_over_7_5_corners': 0.55,  # Very aggressive
            'home_over_2_5_corners': 0.52,   # Very aggressive
            'away_over_2_5_corners': 0.54,   # Very aggressive
            'home_over_3_5_corners': 0.55,   # Very aggressive
            'away_over_3_5_corners': 0.60,   # Moderate
            'total_over_10_5_corners': 0.58, # Aggressive
            'home_over_4_5_corners': 0.62,   # Moderate
            'total_over_11_5_corners': 0.65, # Moderate
        },
        lookback_days=90
    )
    
    # Compare results
    print(f"\n{'='*80}")
    print("CONFIGURATION COMPARISON")
    print(f"{'='*80}")
    print(f"{'Config':<25} {'Predictions':<15} {'Win Rate':<15} {'Profit':<15}")
    print("-"*80)
    
    configs = [baseline, aggressive_corners, super_aggressive]
    for config in configs:
        if config:
            print(f"{config['config_name']:<25} {config['total_predictions']:<15} "
                  f"{config['win_rate']:.1f}%{'':<11} {config['profit']:+.1f} units")
    
    # Recommendation
    print(f"\n{'='*80}")
    print("RECOMMENDATION")
    print(f"{'='*80}")
    
    if configs:
        best_config = max(configs, key=lambda x: x['profit'] if x else -999)
        
        print(f"\nBest Configuration: {best_config['config_name']}")
        print(f"  Win Rate: {best_config['win_rate']:.1f}%")
        print(f"  Profit: {best_config['profit']:+.1f} units")
        print(f"  Predictions: {best_config['total_predictions']}")
        
        profit_improvement = ((best_config['profit'] - baseline['profit']) / abs(baseline['profit']) * 100) if baseline['profit'] != 0 else 0
        print(f"\nProfit improvement vs baseline: {profit_improvement:+.1f}%")
        
        print("\nPremier League has 10.42 avg corners (37% higher than Bundesliga's 7.6)")
        print("This justifies aggressive corner thresholds similar to optimized Bundesliga.")
        print("\nIf improvement is significant, update thresholds in:")
        print("  - patterns/premier_league_patterns.py")
        print("  - simple_premier_league_predictor.py (if using override dict)")
    
    print(f"{'='*80}")


if __name__ == "__main__":
    main()
