#!/usr/bin/env python3
"""
Premier League Multi-Period Backtest
Tests recent performance across different time periods: 7, 14, 30, 50, 90, 120, 160 days
Shows current state and momentum
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sys

sys.path.append('.')

from simple_premier_league_predictor import SimplePremierLeaguePredictor
from data.premier_league_adapter import load_premier_league_data
from patterns.premier_league_patterns import register_premier_league_patterns
from patterns.registry import clear_patterns, get_pattern_registry


def backtest_period(predictor, all_data: pd.DataFrame, days_back: int):
    """Backtest a specific time period"""
    
    # Use predictor's internal df which has raw column names
    end_date = predictor.df['date'].max()
    start_date = end_date - timedelta(days=days_back)
    
    test_data = predictor.df[
        (predictor.df['date'] >= start_date) & 
        (predictor.df['date'] <= end_date)
    ]
    
    results = {
        'period': f'{days_back}d',
        'matches': 0,
        'bets': 0,
        'wins': 0,
        'losses': 0,
        'units': 0.0
    }
    
    for _, match in test_data.iterrows():
        results['matches'] += 1
        
        # Get best bet prediction (now returns single bet or None)
        best_bet = predictor.predict_match(
            match['home_team'],
            match['away_team'],
            match['date'],
            verbose=False
        )
        
        # Check if there's a bet recommendation
        if best_bet and best_bet.get('recommendation') == "BET":
            pattern_name = best_bet['pattern']
            
            if pattern_name in predictor.filtered_patterns:
                pattern_func = predictor.filtered_patterns[pattern_name]['func']
                outcome = pattern_func(match)
                results['bets'] += 1
                
                if outcome:
                    results['wins'] += 1
                    results['units'] += 1.0  # Assuming 2.0 odds (profit = 1.0)
                else:
                    results['losses'] += 1
                    results['units'] -= 1.0  # Lost stake
    
    return results


def main():
    print("="*80)
    print("PREMIER LEAGUE - MULTI-PERIOD BACKTEST")
    print("="*80)
    print()
    
    # Load data
    print("Loading Premier League data...")
    all_data = load_premier_league_data()
    
    # Filter valid data
    all_data = all_data[(all_data['home_corners'] >= 0) & (all_data['away_corners'] >= 0)]
    
    print(f"Loaded {len(all_data)} matches")
    print(f"Date range: {all_data['date'].min().date()} to {all_data['date'].max().date()}")
    
    # Register patterns
    clear_patterns()
    register_premier_league_patterns()
    
    # Initialize predictor
    predictor = SimplePremierLeaguePredictor()
    
    # Test periods
    periods = [7, 14, 30, 50, 90, 120, 160]
    all_results = []
    
    print(f"\nTesting periods: {periods}\n")
    
    for days_back in periods:
        print(f"Testing last {days_back} days...")
        results = backtest_period(predictor, all_data, days_back)
        all_results.append(results)
        
        if results['bets'] > 0:
            win_rate = results['wins'] / results['bets'] * 100
            roi = (results['units'] / results['bets']) * 100
            print(f"  Matches: {results['matches']}, Bets: {results['bets']}, "
                  f"WR: {win_rate:.1f}%, Units: {results['units']:+.1f}, ROI: {roi:+.1f}%")
        else:
            print(f"  No bets in this period")
    
    # Summary table
    print("\n" + "="*80)
    print("PREMIER LEAGUE MULTI-PERIOD SUMMARY")
    print("="*80)
    
    print(f"\n{'Period':>10} {'Matches':>8} {'Bets':>8} {'Wins':>6} {'Win%':>7} {'Units':>8} {'ROI%':>7}")
    print("-"*80)
    
    for result in all_results:
        if result['bets'] > 0:
            win_rate = result['wins'] / result['bets'] * 100
            roi = (result['units'] / result['bets']) * 100
            
            print(f"{result['period']:>10} {result['matches']:>8} {result['bets']:>8} "
                  f"{result['wins']:>6} {win_rate:>6.1f}% {result['units']:>+8.1f} {roi:>+6.1f}%")
        else:
            print(f"{result['period']:>10} {result['matches']:>8} {'N/A':>8} {'N/A':>6} {'N/A':>7} {'N/A':>8} {'N/A':>7}")
    
    # Trend analysis
    print("\n" + "="*80)
    print("TREND ANALYSIS")
    print("="*80)
    
    win_rates = []
    for result in all_results:
        if result['bets'] > 0:
            wr = result['wins'] / result['bets'] * 100
            win_rates.append((result['period'], wr))
    
    if len(win_rates) >= 3:
        short_term = [wr for period, wr in win_rates if period in ['7d', '14d', '30d']]
        long_term = [wr for period, wr in win_rates if period in ['90d', '120d', '160d']]
        
        if short_term and long_term:
            avg_short = np.mean(short_term)
            avg_long = np.mean(long_term)
            trend = avg_short - avg_long
            
            print()
            if trend > 2:
                print(f"📈 IMPROVING: Short-term WR ({avg_short:.1f}%) > Long-term ({avg_long:.1f}%) [+{trend:.1f}%]")
            elif trend < -2:
                print(f"📉 DECLINING: Short-term WR ({avg_short:.1f}%) < Long-term ({avg_long:.1f}%) [{trend:.1f}%]")
            else:
                print(f"➡️  STABLE: Short-term WR ({avg_short:.1f}%) ≈ Long-term ({avg_long:.1f}%) [{trend:+.1f}%]")
    
    # Recent 7-day performance
    recent = next((r for r in all_results if r['period'] == '7d'), None)
    if recent and recent['bets'] > 0:
        recent_wr = recent['wins'] / recent['bets'] * 100
        print()
        if recent_wr >= 75:
            print(f"✅ Last 7 days: {recent_wr:.1f}% WR ({recent['wins']}/{recent['bets']}) - STRONG")
        elif recent_wr >= 65:
            print(f"⚠️  Last 7 days: {recent_wr:.1f}% WR ({recent['wins']}/{recent['bets']}) - ACCEPTABLE")
        else:
            print(f"❌ Last 7 days: {recent_wr:.1f}% WR ({recent['wins']}/{recent['bets']}) - WEAK")
    
    # Best period
    print("\n" + "="*80)
    print("BEST PERFORMING PERIOD")
    print("="*80)
    
    best_result = max([r for r in all_results if r['bets'] >= 10], 
                     key=lambda x: x['wins'] / x['bets'] if x['bets'] > 0 else 0,
                     default=None)
    
    if best_result:
        best_wr = best_result['wins'] / best_result['bets'] * 100
        print(f"\n{best_result['period']:>10}: {best_wr:.1f}% WR, {best_result['units']:+.1f} units")
    
    print("\n" + "="*80)


if __name__ == '__main__':
    main()
