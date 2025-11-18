"""
Premier League Pattern Analysis
Deep dive into pattern performance to identify improvement opportunities.
"""

import pandas as pd
from datetime import datetime
from simple_premier_league_predictor import SimplePremierLeaguePredictor
from data.premier_league_adapter import load_premier_league_data


def analyze_pattern_performance(lookback_days: int = 60):
    """Analyze individual pattern performance across full season."""
    
    print("="*80)
    print("PREMIER LEAGUE PATTERN PERFORMANCE ANALYSIS")
    print("="*80)
    
    # Load full dataset
    df = load_premier_league_data()
    
    # Test on 2024-25 season (complete or near-complete)
    season_df = df[df['season'] == '2024-2025'].copy()
    
    print(f"\nAnalyzing Season: 2024-2025")
    print(f"Matches: {len(season_df)}")
    print(f"Date range: {season_df['date'].min().strftime('%Y-%m-%d')} to {season_df['date'].max().strftime('%Y-%m-%d')}")
    print(f"Lookback: {lookback_days} days")
    
    # Prepare data
    season_df['FTR'] = season_df.apply(
        lambda row: 'H' if row['home_goals'] > row['away_goals'] 
                    else ('A' if row['away_goals'] > row['home_goals'] else 'D'),
        axis=1
    )
    season_df = season_df.rename(columns={
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
    
    # Track detailed pattern stats
    pattern_stats = {}
    
    for _, match in season_df.iterrows():
        predictions = predictor.predict_match(
            match['home_team'],
            match['away_team'],
            match['date'],
            verbose=False
        )
        
        for pred in predictions:
            pattern_name = pred['pattern']
            pattern_func = predictor.filtered_patterns[pattern_name]['func']
            actual_result = pattern_func(match)
            
            if pattern_name not in pattern_stats:
                pattern_stats[pattern_name] = {
                    'total': 0,
                    'correct': 0,
                    'profit': 0.0,
                    'confidences': [],
                    'threshold': pred['base_threshold']
                }
            
            pattern_stats[pattern_name]['total'] += 1
            pattern_stats[pattern_name]['confidences'].append(pred['confidence'])
            
            if actual_result:
                pattern_stats[pattern_name]['correct'] += 1
                pattern_stats[pattern_name]['profit'] += 1.0
            else:
                pattern_stats[pattern_name]['profit'] -= 1.0
    
    # Calculate statistics
    for pattern_name, stats in pattern_stats.items():
        stats['win_rate'] = (stats['correct'] / stats['total'] * 100) if stats['total'] > 0 else 0
        stats['avg_confidence'] = sum(stats['confidences']) / len(stats['confidences']) if stats['confidences'] else 0
        stats['min_confidence'] = min(stats['confidences']) if stats['confidences'] else 0
        stats['max_confidence'] = max(stats['confidences']) if stats['confidences'] else 0
    
    # Report by category
    print(f"\n{'='*80}")
    print("CORNER PATTERNS (sorted by win rate)")
    print(f"{'='*80}")
    print(f"{'Pattern':<30} {'Count':<8} {'WR':<8} {'Profit':<10} {'Threshold':<10} {'Avg Conf':<10}")
    print("-"*80)
    
    corner_patterns = [(name, stats) for name, stats in pattern_stats.items() 
                      if 'corner' in name.lower()]
    corner_patterns.sort(key=lambda x: x[1]['win_rate'], reverse=True)
    
    for pattern_name, stats in corner_patterns:
        print(f"{pattern_name:<30} {stats['total']:<8} {stats['win_rate']:>6.1f}% "
              f"{stats['profit']:>+8.1f} {stats['threshold']:>8.2f} {stats['avg_confidence']:>8.1%}")
    
    print(f"\n{'='*80}")
    print("GOAL PATTERNS (sorted by win rate)")
    print(f"{'='*80}")
    print(f"{'Pattern':<30} {'Count':<8} {'WR':<8} {'Profit':<10} {'Threshold':<10} {'Avg Conf':<10}")
    print("-"*80)
    
    goal_patterns = [(name, stats) for name, stats in pattern_stats.items() 
                    if 'goal' in name.lower() or 'win' in name.lower() or 'draw' in name.lower()]
    goal_patterns.sort(key=lambda x: x[1]['win_rate'], reverse=True)
    
    for pattern_name, stats in goal_patterns:
        print(f"{pattern_name:<30} {stats['total']:<8} {stats['win_rate']:>6.1f}% "
              f"{stats['profit']:>+8.1f} {stats['threshold']:>8.2f} {stats['avg_confidence']:>8.1%}")
    
    print(f"\n{'='*80}")
    print("CARD PATTERNS (sorted by win rate)")
    print(f"{'='*80}")
    print(f"{'Pattern':<30} {'Count':<8} {'WR':<8} {'Profit':<10} {'Threshold':<10} {'Avg Conf':<10}")
    print("-"*80)
    
    card_patterns = [(name, stats) for name, stats in pattern_stats.items() 
                    if 'card' in name.lower()]
    card_patterns.sort(key=lambda x: x[1]['win_rate'], reverse=True)
    
    for pattern_name, stats in card_patterns:
        print(f"{pattern_name:<30} {stats['total']:<8} {stats['win_rate']:>6.1f}% "
              f"{stats['profit']:>+8.1f} {stats['threshold']:>8.2f} {stats['avg_confidence']:>8.1%}")
    
    # Identify optimization opportunities
    print(f"\n{'='*80}")
    print("OPTIMIZATION OPPORTUNITIES")
    print(f"{'='*80}")
    
    # Patterns with high WR but conservative thresholds
    print("\n1. HIGH WIN RATE PATTERNS (consider lowering threshold):")
    print("   Pattern has high WR, threshold could be more aggressive")
    print("-"*80)
    
    high_wr_patterns = [(name, stats) for name, stats in pattern_stats.items() 
                       if stats['win_rate'] > 80 and stats['total'] >= 10]
    high_wr_patterns.sort(key=lambda x: x[1]['win_rate'], reverse=True)
    
    for pattern_name, stats in high_wr_patterns[:10]:
        margin = stats['avg_confidence'] - stats['threshold']
        print(f"  {pattern_name:<30} | WR: {stats['win_rate']:>5.1f}% | "
              f"Threshold: {stats['threshold']:.2f} | Avg Conf: {stats['avg_confidence']:.2%} | "
              f"Margin: +{margin:.2%}")
    
    # Patterns with low volume but high WR
    print("\n2. LOW VOLUME HIGH WIN RATE (could trigger more often):")
    print("   Reliable patterns with too few predictions")
    print("-"*80)
    
    low_vol_patterns = [(name, stats) for name, stats in pattern_stats.items() 
                       if stats['win_rate'] > 75 and stats['total'] < 50 and stats['total'] >= 5]
    low_vol_patterns.sort(key=lambda x: x[1]['win_rate'], reverse=True)
    
    for pattern_name, stats in low_vol_patterns[:10]:
        suggested_threshold = max(0.50, stats['threshold'] - 0.05)
        print(f"  {pattern_name:<30} | {stats['total']:<3} predictions | WR: {stats['win_rate']:>5.1f}% | "
              f"Current: {stats['threshold']:.2f} → Suggested: {suggested_threshold:.2f}")
    
    # Underperforming patterns
    print("\n3. UNDERPERFORMING PATTERNS (consider raising threshold or disabling):")
    print("   Patterns below 65% WR")
    print("-"*80)
    
    underperformers = [(name, stats) for name, stats in pattern_stats.items() 
                      if stats['win_rate'] < 65 and stats['total'] >= 5]
    underperformers.sort(key=lambda x: x[1]['win_rate'])
    
    for pattern_name, stats in underperformers[:10]:
        print(f"  {pattern_name:<30} | {stats['total']:<3} predictions | WR: {stats['win_rate']:>5.1f}% | "
              f"Profit: {stats['profit']:>+7.1f} | Threshold: {stats['threshold']:.2f}")
    
    # Overall summary
    total_predictions = sum(s['total'] for s in pattern_stats.values())
    total_correct = sum(s['correct'] for s in pattern_stats.values())
    total_profit = sum(s['profit'] for s in pattern_stats.values())
    overall_wr = (total_correct / total_predictions * 100) if total_predictions > 0 else 0
    
    print(f"\n{'='*80}")
    print("OVERALL SUMMARY")
    print(f"{'='*80}")
    print(f"Total Predictions: {total_predictions}")
    print(f"Win Rate: {overall_wr:.1f}%")
    print(f"Profit: {total_profit:+.1f} units")
    print(f"Active Patterns: {len(pattern_stats)}")


if __name__ == "__main__":
    # Test different lookback periods
    for lookback in [30, 60, 90]:
        analyze_pattern_performance(lookback)
        print("\n" * 2)
