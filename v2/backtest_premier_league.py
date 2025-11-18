"""
Premier League Multi-Period Backtesting
Tests predictor across different lookback periods to validate robustness.
"""

import pandas as pd
from datetime import datetime, timedelta
from simple_premier_league_predictor import SimplePremierLeaguePredictor
from data.premier_league_adapter import load_premier_league_data


def backtest_period(predictor, start_date, end_date, period_name):
    """Backtest a specific date range."""
    test_df = predictor.df[
        (predictor.df['date'] >= start_date) & 
        (predictor.df['date'] <= end_date)
    ].copy()
    
    total_predictions = 0
    correct_predictions = 0
    total_profit = 0.0
    
    print(f"\nBacktesting {period_name}: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
    print(f"Test matches: {len(test_df)}")
    
    for _, match in test_df.iterrows():
        predictions = predictor.predict_match(
            match['home_team'],
            match['away_team'],
            match['date'],
            verbose=False
        )
        
        # Test each prediction
        for pred in predictions:
            pattern_func = predictor.filtered_patterns[pred['pattern']]['func']
            actual_result = pattern_func(match)
            
            total_predictions += 1
            if actual_result:
                correct_predictions += 1
                total_profit += 1.0  # Assuming 2.0 odds (profit = 1.0)
            else:
                total_profit -= 1.0  # Lost stake
    
    win_rate = (correct_predictions / total_predictions * 100) if total_predictions > 0 else 0
    
    print(f"Results: {correct_predictions}/{total_predictions} correct ({win_rate:.1f}% win rate)")
    print(f"Profit: {total_profit:+.1f} units")
    
    return {
        'period': period_name,
        'start_date': start_date,
        'end_date': end_date,
        'total_predictions': total_predictions,
        'correct_predictions': correct_predictions,
        'win_rate': win_rate,
        'profit': total_profit
    }


def main():
    """Run multi-period backtesting on Premier League."""
    print("="*80)
    print("PREMIER LEAGUE MULTI-PERIOD BACKTESTING")
    print("="*80)
    
    df = load_premier_league_data()
    latest_date = df['date'].max()
    
    # Test periods: 7, 10, 14, 30, 45, 60, 90, 120, 160 days lookback
    test_configs = [
        (7, 'Recent-7d'),
        (10, 'Recent-10d'),
        (14, 'Recent-14d'),
        (30, 'Recent-30d'),
        (45, 'Recent-45d'),
        (60, 'Recent-60d'),
        (90, 'Recent-90d'),
        (120, 'Recent-120d'),
        (160, 'Recent-160d'),
    ]
    
    results = []
    
    for lookback_days, period_name in test_configs:
        # Create predictor with specific lookback
        predictor = SimplePremierLeaguePredictor(lookback_days=lookback_days)
        
        # Test on last 30 days of data
        end_date = latest_date
        start_date = end_date - timedelta(days=30)
        
        # Make sure we have enough historical data
        min_date_required = start_date - timedelta(days=lookback_days)
        if min_date_required < df['date'].min():
            print(f"\nSkipping {period_name}: insufficient historical data")
            continue
        
        result = backtest_period(predictor, start_date, end_date, period_name)
        results.append(result)
    
    # Summary
    print("\n" + "="*80)
    print("SUMMARY - ALL PERIODS")
    print("="*80)
    print(f"{'Period':<15} {'Predictions':<15} {'Win Rate':<15} {'Profit':<15}")
    print("-"*80)
    
    for result in results:
        print(f"{result['period']:<15} {result['total_predictions']:<15} "
              f"{result['win_rate']:.1f}%{'':<11} {result['profit']:+.1f} units{'':<4}")
    
    # Overall stats
    if results:
        avg_win_rate = sum(r['win_rate'] for r in results) / len(results)
        total_profit = sum(r['profit'] for r in results)
        profitable_periods = sum(1 for r in results if r['profit'] > 0)
        
        print("-"*80)
        print(f"{'AVERAGE':<15} {'':<15} {avg_win_rate:.1f}%{'':<11} {total_profit:+.1f} units total")
        print(f"\nProfitable periods: {profitable_periods}/{len(results)} ({profitable_periods/len(results)*100:.0f}%)")
        print("="*80)


if __name__ == "__main__":
    main()
