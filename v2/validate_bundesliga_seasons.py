#!/usr/bin/env python3
"""
Season-by-Season Validation for Bundesliga
Tests if system works consistently across different seasons
"""

import pandas as pd
import numpy as np
from datetime import datetime
import sys

sys.path.append('.')

from simple_bundesliga_predictor import SimpleBundesligaPredictor
from data.bundesliga_adapter import load_bundesliga_data
from patterns.bundesliga_patterns import register_bundesliga_patterns
from patterns.registry import clear_patterns, get_pattern_registry


def backtest_season(all_data: pd.DataFrame, season_start: datetime, season_end: datetime, 
                    season_label: str, lookback_matches: int = 100):
    """Backtest a specific season"""
    
    predictor = SimpleBundesligaPredictor()
    
    # Get test data for this season
    test_data = all_data[
        (all_data['Date'] >= season_start) & 
        (all_data['Date'] <= season_end)
    ]
    
    results = {
        'season': season_label,
        'total_matches': 0,
        'total_bets': 0,
        'wins': 0,
        'losses': 0,
        'units': 0.0,
        'pattern_stats': {}
    }
    
    for _, match in test_data.iterrows():
        # Get historical data before this match
        historical = all_data[all_data['Date'] < match['Date']].tail(lookback_matches)
        
        if len(historical) < 30:
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
    print("="*80)
    print("BUNDESLIGA SEASON-BY-SEASON VALIDATION")
    print("Testing system consistency across different years")
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
    
    # Define seasons (Bundesliga typically runs Aug-May)
    seasons = [
        {
            'label': '2022-23',
            'start': datetime(2022, 8, 1),
            'end': datetime(2023, 5, 31)
        },
        {
            'label': '2023-24',
            'start': datetime(2023, 8, 1),
            'end': datetime(2024, 5, 31)
        },
        {
            'label': '2024-25',
            'start': datetime(2024, 8, 1),
            'end': datetime(2025, 5, 31)
        }
    ]
    
    all_season_results = []
    
    print("Testing each season...\n")
    
    for season in seasons:
        print(f"Testing {season['label']} season...")
        results = backtest_season(
            all_data, 
            season['start'], 
            season['end'],
            season['label']
        )
        all_season_results.append(results)
        
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
        print()
    
    # Summary table
    print("="*80)
    print("SEASON-BY-SEASON SUMMARY")
    print("="*80)
    print(f"{'Season':>10} {'Matches':>8} {'Bets':>8} {'Wins':>6} {'Win%':>7} {'Units':>8} {'ROI%':>7}")
    print("-"*80)
    
    total_bets = 0
    total_wins = 0
    total_units = 0.0
    profitable_seasons = 0
    
    for results in all_season_results:
        if results['total_bets'] > 0:
            win_rate = results['wins'] / results['total_bets'] * 100
            roi = (results['units'] / results['total_bets']) * 100
            
            print(f"{results['season']:>10} {results['total_matches']:>8} {results['total_bets']:>8} "
                  f"{results['wins']:>6} {win_rate:>6.1f}% {results['units']:>+8.1f} {roi:>+6.1f}%")
            
            total_bets += results['total_bets']
            total_wins += results['wins']
            total_units += results['units']
            
            if results['units'] > 0:
                profitable_seasons += 1
    
    print("-"*80)
    if total_bets > 0:
        avg_win_rate = total_wins / total_bets * 100
        avg_roi = (total_units / total_bets) * 100
        print(f"{'AVERAGE':>10} {'-':>8} {total_bets:>8} {total_wins:>6} "
              f"{avg_win_rate:>6.1f}% {total_units:>+8.1f} {avg_roi:>+6.1f}%")
    
    # Analysis
    print()
    print("="*80)
    print("VALIDATION ANALYSIS")
    print("="*80)
    print()
    
    if len(all_season_results) > 0:
        print(f"Total Seasons Tested: {len(all_season_results)}")
        print(f"Profitable Seasons: {profitable_seasons}/{len(all_season_results)} "
              f"({profitable_seasons/len(all_season_results)*100:.0f}%)")
        print()
        
        # Calculate consistency metrics
        win_rates = []
        for results in all_season_results:
            if results['total_bets'] > 0:
                win_rates.append(results['wins'] / results['total_bets'] * 100)
        
        if len(win_rates) > 1:
            avg_wr = np.mean(win_rates)
            std_wr = np.std(win_rates)
            min_wr = min(win_rates)
            max_wr = max(win_rates)
            
            print(f"Win Rate Consistency:")
            print(f"  Average: {avg_wr:.1f}%")
            print(f"  Std Dev: {std_wr:.1f}%")
            print(f"  Range: {min_wr:.1f}% - {max_wr:.1f}%")
            print()
            
            # Verdict
            print("="*80)
            print("VERDICT")
            print("="*80)
            print()
            
            if profitable_seasons == len(all_season_results) and avg_wr >= 70:
                print("✅ SYSTEM VALIDATED ACROSS ALL SEASONS")
                print("   → 100% of seasons profitable")
                print(f"   → Average win rate: {avg_wr:.1f}%")
                print(f"   → Total profit: {total_units:+.1f} units")
                print()
                print("   READY FOR PRODUCTION DEPLOYMENT")
            elif profitable_seasons >= len(all_season_results) * 0.67:
                print("⚠️  SYSTEM MOSTLY VALIDATED")
                print(f"   → {profitable_seasons}/{len(all_season_results)} seasons profitable")
                print(f"   → Average win rate: {avg_wr:.1f}%")
                print()
                print("   PROCEED WITH CAUTION - Monitor closely")
            else:
                print("❌ VALIDATION CONCERNS")
                print(f"   → Only {profitable_seasons}/{len(all_season_results)} seasons profitable")
                print(f"   → Average win rate: {avg_wr:.1f}%")
                print()
                print("   NEEDS IMPROVEMENT before production")
            
            print("="*80)
    
    # Top patterns across all seasons
    print()
    print("="*80)
    print("TOP PATTERNS (All Seasons Combined)")
    print("="*80)
    
    combined_patterns = {}
    for results in all_season_results:
        for pattern_name, stats in results['pattern_stats'].items():
            if pattern_name not in combined_patterns:
                combined_patterns[pattern_name] = {'bets': 0, 'wins': 0, 'units': 0.0}
            combined_patterns[pattern_name]['bets'] += stats['bets']
            combined_patterns[pattern_name]['wins'] += stats['wins']
            combined_patterns[pattern_name]['units'] += stats['units']
    
    sorted_patterns = sorted(
        combined_patterns.items(),
        key=lambda x: x[1]['units'],
        reverse=True
    )
    
    print(f"{'Pattern':40} {'Bets':>6} {'Win%':>7} {'Units':>8}")
    print("-"*80)
    
    for pattern_name, stats in sorted_patterns[:15]:
        if stats['bets'] >= 5:
            win_rate = stats['wins'] / stats['bets'] * 100
            print(f"{pattern_name:40} {stats['bets']:>6} {win_rate:>6.1f}% {stats['units']:>+8.1f}")
    
    print("="*80)


if __name__ == '__main__':
    main()
