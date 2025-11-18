#!/usr/bin/env python3
"""
Multi-Period Backtest for Bundesliga
Tests across multiple lookback periods to find optimal settings
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sys
from typing import Dict, List

sys.path.append('.')

from simple_bundesliga_predictor import SimpleBundesligaPredictor
from data.bundesliga_adapter import load_bundesliga_data
from patterns.bundesliga_patterns import register_bundesliga_patterns
from patterns.registry import clear_patterns, get_pattern_registry


def backtest_period(all_data: pd.DataFrame, lookback_days: int) -> Dict:
    """Backtest a specific lookback period"""
    
    predictor = SimpleBundesligaPredictor()
    
    # Use most recent data for testing
    cutoff_date = all_data['Date'].max() - timedelta(days=lookback_days)
    test_data = all_data[all_data['Date'] > cutoff_date]
    
    results = {
        'total_matches': 0,
        'total_bets': 0,
        'wins': 0,
        'losses': 0,
        'units': 0.0,
        'pattern_stats': {}
    }
    
    for _, match in test_data.iterrows():
        # Get historical data before this match
        historical = all_data[all_data['Date'] < match['Date']].tail(500)
        
        if len(historical) < 50:
            continue
        
        results['total_matches'] += 1
        
        # Get predictions
        recommendations = predictor.predict_match(
            match['HomeTeam'],
            match['AwayTeam'],
            historical,
            match['Date']
        )
        
        # Check each bet
        for rec in recommendations:
            if rec.recommendation != "BET":
                continue
            
            # Verify pattern outcome
            pattern = get_pattern_registry().get_pattern(rec.pattern_name)
            if not pattern:
                continue
            
            outcome = pattern.label_fn(match)
            
            # Track pattern stats
            if rec.pattern_name not in results['pattern_stats']:
                results['pattern_stats'][rec.pattern_name] = {
                    'bets': 0, 'wins': 0, 'losses': 0, 'units': 0.0
                }
            
            results['total_bets'] += 1
            results['pattern_stats'][rec.pattern_name]['bets'] += 1
            
            if outcome:
                results['wins'] += 1
                results['pattern_stats'][rec.pattern_name]['wins'] += 1
                # Estimate profit (using estimated odds - 1)
                estimated_odds = predictor._estimate_odds(rec.pattern_name)
                profit = estimated_odds - 1
                results['units'] += profit
                results['pattern_stats'][rec.pattern_name]['units'] += profit
            else:
                results['losses'] += 1
                results['pattern_stats'][rec.pattern_name]['losses'] += 1
                results['units'] -= 1.0
                results['pattern_stats'][rec.pattern_name]['units'] -= 1.0
    
    return results


def main():
    """Run multi-period backtest"""
    
    print("="*80)
    print("BUNDESLIGA MULTI-PERIOD BACKTEST")
    print("Testing improvements 1-4 across multiple lookback periods")
    print("="*80)
    print()
    
    # Load data
    print("Loading Bundesliga data...")
    all_data = load_bundesliga_data()
    all_data = all_data[(all_data['HC'] >= 0) & (all_data['AC'] >= 0)]
    print(f"Loaded {len(all_data)} matches")
    print(f"Date range: {all_data['Date'].min().date()} to {all_data['Date'].max().date()}")
    print()
    
    # Register patterns
    clear_patterns()
    register_bundesliga_patterns()
    
    # Test periods (requested by user)
    test_periods = [7, 10, 14, 30, 45, 60, 90, 120, 160]
    
    all_results = {}
    
    for days in test_periods:
        print(f"\nTesting {days}-day lookback period...")
        results = backtest_period(all_data, days)
        all_results[days] = results
        
        if results['total_bets'] > 0:
            win_rate = results['wins'] / results['total_bets'] * 100
            roi = (results['units'] / results['total_bets']) * 100
            
            print(f"  Matches: {results['total_matches']}")
            print(f"  Bets: {results['total_bets']}")
            print(f"  Win Rate: {win_rate:.1f}% ({results['wins']}/{results['total_bets']})")
            print(f"  Units: {results['units']:+.1f}")
            print(f"  ROI: {roi:+.1f}%")
        else:
            print(f"  No bets generated")
    
    # Summary table
    print("\n" + "="*80)
    print("SUMMARY - All Periods")
    print("="*80)
    print(f"{'Period':>8} {'Matches':>8} {'Bets':>8} {'Wins':>6} {'Win%':>7} {'Units':>8} {'ROI%':>7}")
    print("-"*80)
    
    total_bets = 0
    total_wins = 0
    total_units = 0.0
    
    for days in test_periods:
        results = all_results[days]
        if results['total_bets'] > 0:
            win_rate = results['wins'] / results['total_bets'] * 100
            roi = (results['units'] / results['total_bets']) * 100
            
            print(f"{days:>8} {results['total_matches']:>8} {results['total_bets']:>8} "
                  f"{results['wins']:>6} {win_rate:>6.1f}% {results['units']:>+8.1f} {roi:>+6.1f}%")
            
            total_bets += results['total_bets']
            total_wins += results['wins']
            total_units += results['units']
    
    print("-"*80)
    if total_bets > 0:
        avg_win_rate = total_wins / total_bets * 100
        avg_roi = (total_units / total_bets) * 100
        print(f"{'AVERAGE':>8} {'-':>8} {total_bets:>8} {total_wins:>6} "
              f"{avg_win_rate:>6.1f}% {total_units:>+8.1f} {avg_roi:>+6.1f}%")
    
    # Top patterns analysis
    print("\n" + "="*80)
    print("TOP PATTERNS (90-day period)")
    print("="*80)
    
    if 90 in all_results and all_results[90]['pattern_stats']:
        pattern_stats = all_results[90]['pattern_stats']
        
        # Sort by units
        sorted_patterns = sorted(
            pattern_stats.items(),
            key=lambda x: x[1]['units'],
            reverse=True
        )
        
        print(f"{'Pattern':40} {'Bets':>6} {'Win%':>7} {'Units':>8}")
        print("-"*80)
        
        for pattern_name, stats in sorted_patterns[:15]:
            if stats['bets'] >= 3:
                win_rate = stats['wins'] / stats['bets'] * 100
                print(f"{pattern_name:40} {stats['bets']:>6} {win_rate:>6.1f}% {stats['units']:>+8.1f}")
    
    print("\n" + "="*80)
    print("BUNDESLIGA BACKTEST COMPLETE")
    print("="*80)


if __name__ == '__main__':
    main()
