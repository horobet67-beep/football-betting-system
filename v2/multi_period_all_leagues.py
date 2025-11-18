#!/usr/bin/env python3
"""
Multi-Period Backtest for ALL Leagues
Tests recent performance across different time periods: 7, 14, 30, 50, 90, 120, 160 days
Shows current state and momentum for each league
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sys

sys.path.append('.')

from simple_bundesliga_predictor import SimpleBundesligaPredictor
from simple_premier_league_predictor import SimplePremierLeaguePredictor
from simple_la_liga_predictor import SimpleLaLigaPredictor
from predictor.romanian_predictor import RomanianMatchPredictor

from data.bundesliga_adapter import load_bundesliga_data
from data.premier_league_adapter import load_premier_league_data
from data.la_liga_adapter import load_la_liga_data
from data.romanian_adapter import load_romanian_data

from patterns.bundesliga_patterns import register_bundesliga_patterns
from patterns.premier_league_patterns import register_premier_league_patterns
from patterns.la_liga_patterns import register_la_liga_patterns
from patterns.romanian_patterns import register_romanian_patterns
from patterns.registry import clear_patterns, get_pattern_registry


def backtest_period(predictor, all_data: pd.DataFrame, days_back: int, 
                   league_name: str, lookback_matches: int = 100):
    """Backtest a specific time period"""
    
    # Handle different date column names
    date_col = 'date' if 'date' in all_data.columns else 'Date'
    
    end_date = all_data[date_col].max()
    start_date = end_date - timedelta(days=days_back)
    
    test_data = all_data[
        (all_data[date_col] >= start_date) & 
        (all_data[date_col] <= end_date)
    ]
    
    results = {
        'league': league_name,
        'period': f'{days_back}d',
        'matches': 0,
        'bets': 0,
        'wins': 0,
        'losses': 0,
        'units': 0.0
    }
    
    for _, match in test_data.iterrows():
        historical = all_data[all_data[date_col] < match[date_col]].tail(lookback_matches)
        
        if len(historical) < 30:
            continue
        
        results['matches'] += 1
        
        # Get prediction based on league (now returns single best_bet or None)
        if league_name == 'Premier League':
            best_bet = predictor.predict_match(
                match['home_team'],
                match['away_team'],
                historical,
                match.get('date')
            )
        elif league_name == 'Romanian Liga I':
            # Romanian predictor returns prediction object with best_bet
            prediction = predictor.predict_match(match, historical)
            best_bet = prediction.best_bet
        else:
            # Bundesliga and La Liga
            best_bet = predictor.predict_match(
                match['HomeTeam'],
                match['AwayTeam'],
                historical,
                match.get('Date', match.get('date'))
            )
        
        # Check if there's a bet
        if best_bet is None:
            continue
            
        # Extract pattern name
        if isinstance(best_bet, dict):
            pattern_name = best_bet['pattern']
        elif hasattr(best_bet, 'pattern_name'):
            pattern_name = best_bet.pattern_name
        else:
            continue
        
        # Get pattern from registry
        pattern = get_pattern_registry().get(pattern_name)
        if pattern is None:
            continue
        
        outcome = pattern.label_fn(match)
        results['bets'] += 1
        
        if outcome:
            results['wins'] += 1
            # Use predictor's odds estimation
            if league_name == 'Premier League':
                estimated_odds = predictor._estimate_odds(pattern_name)
            else:
                estimated_odds = predictor._estimate_odds(pattern_name)
            profit = estimated_odds - 1
            results['units'] += profit
        else:
            results['losses'] += 1
            results['units'] -= 1.0
    
    return results


def test_league(league_name: str, predictor_class, data_loader, pattern_registrar):
    """Test all periods for a single league"""
    
    print(f"\n{'='*80}")
    print(f"{league_name.upper()} - MULTI-PERIOD BACKTEST")
    print(f"{'='*80}\n")
    
    # Load data
    print(f"Loading {league_name} data...")
    all_data = data_loader()
    
    # Filter valid data
    if 'HC' in all_data.columns and 'AC' in all_data.columns:
        all_data = all_data[(all_data['HC'] >= 0) & (all_data['AC'] >= 0)]
    elif 'home_corners' in all_data.columns and 'away_corners' in all_data.columns:
        all_data = all_data[(all_data['home_corners'] >= 0) & (all_data['away_corners'] >= 0)]
    
    # Get date column
    date_col = 'date' if 'date' in all_data.columns else 'Date'
    
    print(f"Loaded {len(all_data)} matches")
    print(f"Date range: {all_data[date_col].min().date()} to {all_data[date_col].max().date()}")
    
    # Register patterns
    clear_patterns()
    pattern_registrar()
    
    # Initialize predictor
    predictor = predictor_class()
    
    # Test periods
    periods = [7, 14, 30, 50, 90, 120, 160]
    all_results = []
    
    print(f"\nTesting periods: {periods}\n")
    
    for days_back in periods:
        print(f"Testing last {days_back} days...")
        results = backtest_period(predictor, all_data, days_back, league_name)
        all_results.append(results)
        
        if results['bets'] > 0:
            win_rate = results['wins'] / results['bets'] * 100
            roi = (results['units'] / results['bets']) * 100
            print(f"  Matches: {results['matches']}, Bets: {results['bets']}, "
                  f"WR: {win_rate:.1f}%, Units: {results['units']:+.1f}, ROI: {roi:+.1f}%")
        else:
            print(f"  No bets in this period")
    
    return all_results


def main():
    print("="*80)
    print("MULTI-PERIOD BACKTEST - ALL LEAGUES")
    print("Testing: 7, 14, 30, 50, 90, 120, 160 days")
    print("="*80)
    
    all_league_results = {}
    
    # Test each league
    leagues = [
        ('Premier League', SimplePremierLeaguePredictor, load_premier_league_data, register_premier_league_patterns),
        ('Bundesliga', SimpleBundesligaPredictor, load_bundesliga_data, register_bundesliga_patterns),
        ('La Liga', SimpleLaLigaPredictor, load_la_liga_data, register_la_liga_patterns),
        ('Romanian Liga I', RomanianMatchPredictor, load_romanian_data, register_romanian_patterns),
    ]
    
    for league_name, predictor_class, data_loader, pattern_registrar in leagues:
        try:
            results = test_league(league_name, predictor_class, data_loader, pattern_registrar)
            all_league_results[league_name] = results
        except Exception as e:
            print(f"\n❌ Error testing {league_name}: {e}")
            continue
    
    # Summary comparison table
    print("\n" + "="*80)
    print("SUMMARY - ALL LEAGUES COMPARISON")
    print("="*80)
    
    periods = [7, 14, 30, 50, 90, 120, 160]
    
    for period in periods:
        print(f"\n{period}-DAY PERIOD:")
        print("-"*80)
        print(f"{'League':20} {'Matches':>8} {'Bets':>8} {'Wins':>6} {'Win%':>7} {'Units':>8} {'ROI%':>7}")
        print("-"*80)
        
        for league_name, results_list in all_league_results.items():
            # Find results for this period
            period_result = next((r for r in results_list if r['period'] == f'{period}d'), None)
            
            if period_result and period_result['bets'] > 0:
                win_rate = period_result['wins'] / period_result['bets'] * 100
                roi = (period_result['units'] / period_result['bets']) * 100
                
                print(f"{league_name:20} {period_result['matches']:>8} {period_result['bets']:>8} "
                      f"{period_result['wins']:>6} {win_rate:>6.1f}% {period_result['units']:>+8.1f} {roi:>+6.1f}%")
            else:
                print(f"{league_name:20} {'N/A':>8} {'N/A':>8} {'N/A':>6} {'N/A':>7} {'N/A':>8} {'N/A':>7}")
    
    # Trend analysis
    print("\n" + "="*80)
    print("TREND ANALYSIS")
    print("="*80)
    
    for league_name, results_list in all_league_results.items():
        print(f"\n{league_name}:")
        
        # Calculate trend from 7d to 160d
        win_rates = []
        for result in results_list:
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
                
                if trend > 2:
                    print(f"  📈 IMPROVING: Short-term WR ({avg_short:.1f}%) > Long-term ({avg_long:.1f}%) [+{trend:.1f}%]")
                elif trend < -2:
                    print(f"  📉 DECLINING: Short-term WR ({avg_short:.1f}%) < Long-term ({avg_long:.1f}%) [{trend:.1f}%]")
                else:
                    print(f"  ➡️  STABLE: Short-term WR ({avg_short:.1f}%) ≈ Long-term ({avg_long:.1f}%) [{trend:+.1f}%]")
        
        # Recent 7-day performance
        recent = next((r for r in results_list if r['period'] == '7d'), None)
        if recent and recent['bets'] > 0:
            recent_wr = recent['wins'] / recent['bets'] * 100
            if recent_wr >= 75:
                print(f"  ✅ Last 7 days: {recent_wr:.1f}% WR ({recent['wins']}/{recent['bets']}) - STRONG")
            elif recent_wr >= 65:
                print(f"  ⚠️  Last 7 days: {recent_wr:.1f}% WR ({recent['wins']}/{recent['bets']}) - ACCEPTABLE")
            else:
                print(f"  ❌ Last 7 days: {recent_wr:.1f}% WR ({recent['wins']}/{recent['bets']}) - WEAK")
    
    # Best performing league per period
    print("\n" + "="*80)
    print("BEST LEAGUE PER PERIOD")
    print("="*80)
    
    for period in periods:
        best_league = None
        best_wr = 0
        
        for league_name, results_list in all_league_results.items():
            period_result = next((r for r in results_list if r['period'] == f'{period}d'), None)
            
            if period_result and period_result['bets'] >= 10:  # Minimum 10 bets
                wr = period_result['wins'] / period_result['bets'] * 100
                if wr > best_wr:
                    best_wr = wr
                    best_league = league_name
        
        if best_league:
            print(f"{period:>3}d: {best_league:20} ({best_wr:.1f}% WR)")
    
    print("\n" + "="*80)


if __name__ == '__main__':
    main()
