#!/usr/bin/env python3
"""Complete backtest for ALL 4 leagues with detailed results"""

import pandas as pd
from datetime import timedelta, datetime
import sys
import os

# Configure backtest period (days)
BACKTEST_DAYS = 30  # Change this to adjust backtest period

sys.path.append('.')

# Create backtesting_runs directory if it doesn't exist
BACKTEST_DIR = 'backtesting_runs'
os.makedirs(BACKTEST_DIR, exist_ok=True)

from data.premier_league_adapter import load_premier_league_data
from data.bundesliga_adapter import load_bundesliga_data
from data.la_liga_adapter import load_la_liga_data
from data.romanian_adapter import load_romanian_data

from simple_premier_league_predictor import SimplePremierLeaguePredictor
from simple_bundesliga_predictor import SimpleBundesligaPredictor
from simple_la_liga_predictor import SimpleLaLigaPredictor
from simple_romanian_predictor import SimpleRomanianPredictor

from patterns.premier_league_patterns import register_premier_league_patterns
from patterns.bundesliga_patterns import register_bundesliga_patterns
from patterns.la_liga_patterns import register_la_liga_patterns
from patterns.romanian_patterns import register_romanian_patterns
from patterns.registry import clear_patterns, get_pattern_registry


def show_premier_league_details():
    """Show Premier League detailed results"""
    print("="*100)
    print(f"PREMIER LEAGUE - Last {BACKTEST_DAYS} Days (Detailed)")
    print("="*100)
    
    # Setup - predictor loads its own data
    clear_patterns()
    register_premier_league_patterns()
    predictor = SimplePremierLeaguePredictor()
    
    # Get test period from predictor's data
    data = predictor.df
    end_date = data['date'].max()
    start_date = end_date - timedelta(days=BACKTEST_DAYS)
    test_data = data[(data['date'] >= start_date) & (data['date'] <= end_date)]
    
    print(f"Period: {start_date.date()} to {end_date.date()}")
    print(f"Total matches: {len(test_data)}\n")
    
    results = []
    for idx, row in test_data.iterrows():
        try:
            # Premier League predictor returns a single dict (best bet), not a list
            best_bet = predictor.predict(row['home_team'], row['away_team'], row['date'])
            
            if best_bet and isinstance(best_bet, dict):
                pattern = get_pattern_registry().get_pattern(best_bet['pattern'])
                outcome = pattern.label_fn(row) if pattern else False
                
                # Premier League uses FTHG/FTAG after column renaming in predictor.__init__
                results.append({
                    'date': row['date'].strftime('%Y-%m-%d'),
                    'home': row['home_team'][:18],
                    'away': row['away_team'][:18],
                    'pattern': best_bet['pattern'][:28],
                    'confidence': best_bet.get('risk_adjusted_confidence', best_bet.get('confidence')),
                    'result': '✅' if outcome else '❌',
                    'score': f"{int(row['FTHG'])}-{int(row['FTAG'])}"
                })
        except Exception as e:
            # Skip matches with errors
            continue
    
    # Display
    if results:
        print(f"{'Date':<12} {'Match':<38} {'Pattern':<30} {'Conf':<6} {'Res':<4} {'Score':<5}")
        print("-"*100)
        for r in results:
            match_str = f"{r['home']} vs {r['away']}"
            print(f"{r['date']:<12} {match_str:<38} {r['pattern']:<30} {r['confidence']*100:>5.1f}% {r['result']:<4} {r['score']:<5}")
        
        wins = sum(1 for r in results if r['result'] == '✅')
        print(f"\nBets: {len(results)}, Wins: {wins}, Win Rate: {wins/len(results)*100:.1f}%")
    else:
        print("No predictions generated.")
    
    print()
    return results


def show_bundesliga_details():
    """Show Bundesliga detailed results"""
    print("="*100)
    print(f"BUNDESLIGA - Last {BACKTEST_DAYS} Days (Detailed)")
    print("="*100)
    
    # Load
    data = load_bundesliga_data()
    data = data[(data['HC'] >= 0) & (data['AC'] >= 0)]
    
    # Setup
    clear_patterns()
    register_bundesliga_patterns()
    predictor = SimpleBundesligaPredictor()
    
    # Period
    end_date = data['Date'].max()
    start_date = end_date - timedelta(days=BACKTEST_DAYS)
    test_data = data[(data['Date'] >= start_date) & (data['Date'] <= end_date)]
    
    print(f"Period: {start_date.date()} to {end_date.date()}")
    print(f"Total matches: {len(test_data)}\n")
    
    results = []
    for idx, row in test_data.iterrows():
        hist = data[data['Date'] < row['Date']].tail(200)
        if len(hist) < 30:
            continue
        
        # Get prediction - pass historical data only
        best_bet = predictor.predict_match(row['HomeTeam'], row['AwayTeam'], hist, row['Date'])
        
        if best_bet:
            pattern = get_pattern_registry().get_pattern(best_bet.pattern_name)
            outcome = pattern.label_fn(row) if pattern else False
            
            results.append({
                'date': row['Date'].strftime('%Y-%m-%d'),
                'home': row['HomeTeam'][:18],
                'away': row['AwayTeam'][:18],
                'pattern': best_bet.pattern_name[:28],
                'confidence': best_bet.risk_adjusted_confidence,
                'result': '✅' if outcome else '❌',
                'score': f"{int(row['FTHG'])}-{int(row['FTAG'])}"
            })
    
    # Display
    if results:
        print(f"{'Date':<12} {'Match':<38} {'Pattern':<30} {'Conf':<6} {'Res':<4} {'Score':<5}")
        print("-"*100)
        for r in results:
            match_str = f"{r['home']} vs {r['away']}"
            print(f"{r['date']:<12} {match_str:<38} {r['pattern']:<30} {r['confidence']*100:>5.1f}% {r['result']:<4} {r['score']:<5}")
        
        wins = sum(1 for r in results if r['result'] == '✅')
        print(f"\nBets: {len(results)}, Wins: {wins}, Win Rate: {wins/len(results)*100:.1f}%")
    else:
        print("No predictions generated.")
    
    print()
    return results


def show_laliga_details():
    """Show La Liga detailed results"""
    print("="*100)
    print(f"LA LIGA - Last {BACKTEST_DAYS} Days (Detailed)")
    print("="*100)
    
    # Load
    data = load_la_liga_data()
    data = data[(data['HC'] >= 0) & (data['AC'] >= 0)]
    
    # Setup
    clear_patterns()
    register_la_liga_patterns()
    predictor = SimpleLaLigaPredictor()
    
    # Period
    end_date = data['Date'].max()
    start_date = end_date - timedelta(days=BACKTEST_DAYS)
    test_data = data[(data['Date'] >= start_date) & (data['Date'] <= end_date)]
    
    print(f"Period: {start_date.date()} to {end_date.date()}")
    print(f"Total matches: {len(test_data)}\n")
    
    results = []
    for idx, row in test_data.iterrows():
        hist = data[data['Date'] < row['Date']].tail(200)
        if len(hist) < 30:
            continue
        
        best_bet = predictor.predict_match(row['HomeTeam'], row['AwayTeam'], hist, row['Date'])
        
        if best_bet:
            pname = best_bet.get('pattern_name', best_bet.get('pattern'))
            pattern = get_pattern_registry().get_pattern(pname)
            outcome = pattern.label_fn(row) if pattern else False
            
            results.append({
                'date': row['Date'].strftime('%Y-%m-%d'),
                'home': row['HomeTeam'][:18],
                'away': row['AwayTeam'][:18],
                'pattern': pname[:28],
                'confidence': best_bet.get('risk_adjusted_confidence', best_bet.get('confidence')),
                'result': '✅' if outcome else '❌',
                'score': f"{int(row['FTHG'])}-{int(row['FTAG'])}"
            })
    
    # Display
    if results:
        print(f"{'Date':<12} {'Match':<38} {'Pattern':<30} {'Conf':<6} {'Res':<4} {'Score':<5}")
        print("-"*100)
        for r in results:
            match_str = f"{r['home']} vs {r['away']}"
            print(f"{r['date']:<12} {match_str:<38} {r['pattern']:<30} {r['confidence']*100:>5.1f}% {r['result']:<4} {r['score']:<5}")
        
        wins = sum(1 for r in results if r['result'] == '✅')
        print(f"\nBets: {len(results)}, Wins: {wins}, Win Rate: {wins/len(results)*100:.1f}%")
    else:
        print("No predictions generated.")
    
    print()
    return results


def show_romania_details():
    """Show Romania detailed results"""
    print("="*100)
    print(f"ROMANIA LIGA I - Last {BACKTEST_DAYS} Days (Detailed)")
    print("="*100)
    
    # Load
    data = load_romanian_data()
    # Filter completed matches only (exclude 0-0 fixtures)
    data = data[~((data['FTHG'] == 0) & (data['FTAG'] == 0))]
    data = data[(data['HC'] >= 0) & (data['AC'] >= 0)]
    
    # Setup
    clear_patterns()
    register_romanian_patterns()
    predictor = SimpleRomanianPredictor()
    
    # Period
    end_date = data['Date'].max()
    start_date = end_date - timedelta(days=BACKTEST_DAYS)
    test_data = data[(data['Date'] >= start_date) & (data['Date'] <= end_date)]
    
    print(f"Period: {start_date.date()} to {end_date.date()}")
    print(f"Total matches: {len(test_data)}\n")
    
    results = []
    for idx, row in test_data.iterrows():
        hist = data[data['Date'] < row['Date']].tail(200)
        if len(hist) < 30:
            continue
        
        # Get prediction using simple predictor
        best_bet = predictor.predict_match(row['HomeTeam'], row['AwayTeam'], hist, row['Date'])
        
        if best_bet:
            pattern = get_pattern_registry().get_pattern(best_bet.pattern_name)
            outcome = pattern.label_fn(row) if pattern else False
            
            results.append({
                'date': row['Date'].strftime('%Y-%m-%d'),
                'home': row['HomeTeam'][:18],
                'away': row['AwayTeam'][:18],
                'pattern': best_bet.pattern_name[:28],
                'confidence': best_bet.risk_adjusted_confidence,
                'result': '✅' if outcome else '❌',
                'score': f"{int(row['FTHG'])}-{int(row['FTAG'])}"
            })
    
    # Display
    if results:
        print(f"{'Date':<12} {'Match':<38} {'Pattern':<30} {'Conf':<6} {'Res':<4} {'Score':<5}")
        print("-"*100)
        for r in results:
            match_str = f"{r['home']} vs {r['away']}"
            print(f"{r['date']:<12} {match_str:<38} {r['pattern']:<30} {r['confidence']*100:>5.1f}% {r['result']:<4} {r['score']:<5}")
        
        wins = sum(1 for r in results if r['result'] == '✅')
        print(f"\nBets: {len(results)}, Wins: {wins}, Win Rate: {wins/len(results)*100:.1f}%")
    else:
        print("⚠️  No high-confidence predictions found in this period.")
        print("    All patterns had confidence below their thresholds.")
    
    print()
    return results


if __name__ == '__main__':
    # Generate filename with timestamp
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_file = os.path.join(BACKTEST_DIR, f'all_leagues_{BACKTEST_DAYS}days_{timestamp}.txt')
    
    # Open file for writing
    with open(output_file, 'w') as f:
        # Redirect print to file and console
        original_print = print
        def dual_print(*args, **kwargs):
            # Remove 'file' from kwargs if present to avoid conflict
            kwargs_copy = {k: v for k, v in kwargs.items() if k != 'file'}
            original_print(*args, **kwargs_copy)  # Print to console
            original_print(*args, **kwargs_copy, file=f)  # Print to file
        
        # Replace print temporarily
        import builtins
        builtins.print = dual_print
        
        print("\n" + "="*100)
        print(" "*20 + f"🏆 COMPLETE {BACKTEST_DAYS}-DAY BACKTEST - ALL LEAGUES 🏆")
        print("="*100 + "\n")
        
        # Run all leagues
        pl_results = show_premier_league_details()
        bundesliga_results = show_bundesliga_details()
        laliga_results = show_laliga_details()
        romania_results = show_romania_details()
        
        # Overall summary
        print("="*100)
        print(" "*35 + "📊 OVERALL SUMMARY")
        print("="*100)
        
        all_results = {
            'Premier League': pl_results,
            'Bundesliga': bundesliga_results,
            'La Liga': laliga_results,
            'Romania Liga I': romania_results
        }
        
        total_bets = 0
        total_wins = 0
        
        print(f"\n{'League':<20} {'Bets':<8} {'Wins':<8} {'Losses':<8} {'Win Rate':<12} {'Performance':<15}")
        print("-"*100)
        
        for league, results in all_results.items():
            if results:
                bets = len(results)
                wins = sum(1 for r in results if r['result'] == '✅')
                losses = bets - wins
                win_rate = wins / bets * 100 if bets > 0 else 0
                
                # Performance indicator
                if win_rate >= 80:
                    perf = "🔥 Excellent"
                elif win_rate >= 75:
                    perf = "✅ Very Good"
                elif win_rate >= 70:
                    perf = "👍 Good"
                elif win_rate >= 60:
                    perf = "⚠️  Fair"
                else:
                    perf = "❌ Poor"
                
                print(f"{league:<20} {bets:<8} {wins:<8} {losses:<8} {win_rate:>6.1f}%      {perf:<15}")
                total_bets += bets
                total_wins += wins
            else:
                print(f"{league:<20} {'0':<8} {'0':<8} {'0':<8} {'N/A':<12} {'⏳ No bets':<15}")
        
        print("-"*100)
        
        if total_bets > 0:
            overall_wr = total_wins / total_bets * 100
            print(f"{'TOTAL':<20} {total_bets:<8} {total_wins:<8} {total_bets - total_wins:<8} {overall_wr:>6.1f}%")
            print("\n" + "="*100)
            print(f"✅ System Performance: {overall_wr:.1f}% Win Rate across {total_bets} bets")
            
            if overall_wr >= 75:
                print(f"🎯 EXCELLENT: System is performing very well! Ready for production.")
            elif overall_wr >= 70:
                print(f"👍 GOOD: System is performing well. Consider production deployment.")
            else:
                print(f"⚠️  CAUTION: System needs optimization before production use.")
        else:
            print("⚠️  No bets generated across all leagues.")
        
        print("="*100 + "\n")
        
        # Add metadata footer
        print("\n" + "="*100)
        print("BACKTEST METADATA")
        print("="*100)
        print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Backtest Period: {BACKTEST_DAYS} days")
        print(f"Total Leagues: 4 (Premier League, Bundesliga, La Liga, Romania Liga I)")
        print(f"Output File: {output_file}")
        print("="*100)
        
        # Restore original print
        builtins.print = original_print
    
    print(f"\n✅ Results saved to: {output_file}")
    print(f"📊 Total bets analyzed: {total_bets}")
    print(f"🎯 Overall win rate: {overall_wr:.1f}%\n")
