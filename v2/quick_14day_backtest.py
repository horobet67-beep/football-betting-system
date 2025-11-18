#!/usr/bin/env python3
"""Quick 14-day backtest for all 4 leagues"""

import pandas as pd
from datetime import datetime, timedelta
import sys

sys.path.append('.')

from data.premier_league_adapter import load_premier_league_data
from data.bundesliga_adapter import load_bundesliga_data
from data.la_liga_adapter import load_la_liga_data
from data.romanian_adapter import load_romanian_data

from simple_premier_league_predictor import SimplePremierLeaguePredictor
from simple_bundesliga_predictor import SimpleBundesligaPredictor
from simple_la_liga_predictor import SimpleLaLigaPredictor
from predictor.romanian_predictor import RomanianMatchPredictor

from patterns.premier_league_patterns import register_premier_league_patterns
from patterns.bundesliga_patterns import register_bundesliga_patterns
from patterns.la_liga_patterns import register_la_liga_patterns
from patterns.romanian_patterns import register_romanian_patterns
from patterns.registry import clear_patterns, get_pattern_registry


def test_league_14days(name, data_loader, register_fn, predictor_class, date_col='Date', home_col='HomeTeam', away_col='AwayTeam'):
    """Test a league for last 14 days"""
    
    print('='*80)
    print(f'{name} - Last 14 Days')
    print('='*80)
    
    # Load data
    data = data_loader()
    
    # Filter valid data (has corner data)
    if 'HC' in data.columns and 'AC' in data.columns:
        data = data[(data['HC'] >= 0) & (data['AC'] >= 0)]
    elif 'home_corners' in data.columns and 'away_corners' in data.columns:
        data = data[(data['home_corners'] >= 0) & (data['away_corners'] >= 0)]
    
    # Get test period
    end_date = data[date_col].max()
    start_date = end_date - timedelta(days=14)
    test_data = data[(data[date_col] >= start_date) & (data[date_col] <= end_date)]
    
    print(f'Test period: {start_date.date()} to {end_date.date()}')
    print(f'Matches in period: {len(test_data)}')
    
    # Register patterns
    clear_patterns()
    register_fn()
    
    # Initialize predictor
    predictor = predictor_class()
    
    # Backtest
    bets, wins, losses = 0, 0, 0
    units = 0.0
    
    for _, match in test_data.iterrows():
        # Get historical data
        hist = data[data[date_col] < match[date_col]].tail(200)
        if len(hist) < 30:
            continue
        
        # Get prediction
        if name == 'Romanian Liga I':
            pred = predictor.predict_match(match, hist)
            best_bet = pred.best_bet
        else:
            # Pass date value directly (it's already Timestamp)
            date_value = match[date_col]
            best_bet = predictor.predict_match(match[home_col], match[away_col], hist, date_value)
        
        # Check bet
        if best_bet:
            bets += 1
            
            # Get pattern name
            if isinstance(best_bet, dict):
                pname = best_bet['pattern']
            elif hasattr(best_bet, 'pattern_name'):
                pname = best_bet.pattern_name
            else:
                continue
            
            # Get pattern and check outcome
            pattern = get_pattern_registry().get_pattern(pname)
            if pattern:
                outcome = pattern.label_fn(match)
                if outcome:
                    wins += 1
                    units += 0.8  # Estimated profit
                else:
                    losses += 1
                    units -= 1.0
    
    # Calculate stats
    wr = (wins/bets*100) if bets > 0 else 0
    roi = (units/bets*100) if bets > 0 else 0
    
    print(f'Bets: {bets}')
    print(f'Wins: {wins}')
    print(f'Losses: {losses}')
    print(f'Win Rate: {wr:.1f}%')
    print(f'Units: {units:+.1f}')
    print(f'ROI: {roi:+.1f}%')
    print()
    
    return {'league': name, 'bets': bets, 'wins': wins, 'losses': losses, 'wr': wr, 'units': units, 'roi': roi}


def main():
    print("="*80)
    print("14-DAY BACKTEST - ALL LEAGUES")
    print("="*80)
    print()
    
    results = []
    
    # Test each league
    results.append(test_league_14days(
        'Premier League',
        load_premier_league_data,
        register_premier_league_patterns,
        SimplePremierLeaguePredictor,
        date_col='date',
        home_col='home_team',
        away_col='away_team'
    ))
    
    results.append(test_league_14days(
        'Bundesliga',
        load_bundesliga_data,
        register_bundesliga_patterns,
        SimpleBundesligaPredictor
    ))
    
    results.append(test_league_14days(
        'La Liga',
        load_la_liga_data,
        register_la_liga_patterns,
        SimpleLaLigaPredictor
    ))
    
    results.append(test_league_14days(
        'Romanian Liga I',
        load_romanian_data,
        register_romanian_patterns,
        RomanianMatchPredictor
    ))
    
    # Summary
    print("="*80)
    print("SUMMARY - Last 14 Days (Oct 28 - Nov 11, 2025)")
    print("="*80)
    print()
    print(f"{'League':<20} {'Bets':>6} {'Wins':>6} {'WR':>8} {'Units':>8} {'ROI':>8}")
    print("-"*80)
    
    for r in results:
        print(f"{r['league']:<20} {r['bets']:>6} {r['wins']:>6} {r['wr']:>7.1f}% {r['units']:>+7.1f} {r['roi']:>+7.1f}%")
    
    # Best league
    print()
    best_wr = max(results, key=lambda x: x['wr'] if x['bets'] > 0 else 0)
    best_roi = max(results, key=lambda x: x['roi'] if x['bets'] > 0 else 0)
    
    print(f"🏆 Highest Win Rate: {best_wr['league']} ({best_wr['wr']:.1f}%)")
    print(f"💰 Best ROI: {best_roi['league']} ({best_roi['roi']:+.1f}%)")


if __name__ == '__main__':
    main()
