#!/usr/bin/env python3
"""
Production Bet Recommendations - All 4 Leagues
Generate real betting recommendations for matches in a date range.

Usage:
    python predict_date_range_all_leagues.py --start-date 2025-11-09 --end-date 2025-11-16
    python predict_date_range_all_leagues.py --start-date 2025-11-09 --end-date 2025-11-16 --min-confidence 0.75
"""

import argparse
import pandas as pd
from datetime import datetime, timedelta
import sys

sys.path.append('.')

from simple_premier_league_predictor import SimplePremierLeaguePredictor
from simple_la_liga_predictor import SimpleLaLigaPredictor
from simple_bundesliga_predictor import SimpleBundesligaPredictor
from predictor.romanian_predictor import RomanianMatchPredictor

from data.premier_league_adapter import load_premier_league_data
from data.la_liga_adapter import load_la_liga_data
from data.bundesliga_adapter import load_bundesliga_data
from data.romanian_adapter import load_romanian_data

from patterns.premier_league_patterns import register_premier_league_patterns
from patterns.la_liga_patterns import register_la_liga_patterns
from patterns.bundesliga_patterns import register_bundesliga_patterns
from patterns.romanian_patterns import register_romanian_patterns
from patterns.registry import clear_patterns


def predict_premier_league(start_date, end_date, min_confidence=0.70):
    """Get Premier League recommendations"""
    print("\n" + "="*80)
    print("🏴󠁧󠁢󠁥󠁮󠁧󠁿  PREMIER LEAGUE PREDICTIONS")
    print("="*80)
    
    data = load_premier_league_data()
    clear_patterns()
    register_premier_league_patterns()
    
    predictor = SimplePremierLeaguePredictor()
    
    # Filter matches in date range
    matches = data[
        (data['date'] >= start_date) & 
        (data['date'] <= end_date)
    ].sort_values('date')
    
    recommendations = []
    
    for _, match in matches.iterrows():
        best_bet = predictor.predict_match(
            match['home_team'],
            match['away_team'],
            match['date']
        )
        
        if best_bet and best_bet.get('risk_adjusted_confidence', 0) >= min_confidence:
            recommendations.append({
                'league': 'Premier League',
                'date': match['date'],
                'home': match['home_team'],
                'away': match['away_team'],
                'pattern': best_bet['pattern'],
                'confidence': best_bet.get('risk_adjusted_confidence', best_bet['confidence']),
                'raw_confidence': best_bet['confidence'],
                'threshold': best_bet.get('adjusted_threshold', 0.65)
            })
    
    return recommendations


def predict_la_liga(start_date, end_date, min_confidence=0.70):
    """Get La Liga recommendations"""
    print("\n" + "="*80)
    print("🇪🇸  LA LIGA PREDICTIONS")
    print("="*80)
    
    data = load_la_liga_data()
    clear_patterns()
    register_la_liga_patterns()
    
    predictor = SimpleLaLigaPredictor()
    
    # Filter matches in date range
    matches = data[
        (data['Date'] >= start_date) & 
        (data['Date'] <= end_date)
    ].sort_values('Date')
    
    recommendations = []
    
    for _, match in matches.iterrows():
        historical = data[data['Date'] < match['Date']].tail(200)
        
        if len(historical) < 50:
            continue
        
        best_bet = predictor.predict_match(
            match['HomeTeam'],
            match['AwayTeam'],
            historical,
            match['Date']
        )
        
        if best_bet and best_bet.get('risk_adjusted_confidence', 0) >= min_confidence:
            recommendations.append({
                'league': 'La Liga',
                'date': match['Date'],
                'home': match['HomeTeam'],
                'away': match['AwayTeam'],
                'pattern': best_bet['pattern_name'],
                'confidence': best_bet.get('risk_adjusted_confidence', best_bet['confidence']),
                'raw_confidence': best_bet['confidence'],
                'threshold': best_bet['threshold']
            })
    
    return recommendations


def predict_bundesliga(start_date, end_date, min_confidence=0.70):
    """Get Bundesliga recommendations"""
    print("\n" + "="*80)
    print("🇩🇪  BUNDESLIGA PREDICTIONS")
    print("="*80)
    
    data = load_bundesliga_data()
    clear_patterns()
    register_bundesliga_patterns()
    
    predictor = SimpleBundesligaPredictor()
    
    # Filter matches in date range
    matches = data[
        (data['Date'] >= start_date) & 
        (data['Date'] <= end_date)
    ].sort_values('Date')
    
    recommendations = []
    
    for _, match in matches.iterrows():
        historical = data[data['Date'] < match['Date']].tail(200)
        
        if len(historical) < 50:
            continue
        
        best_bet = predictor.predict_match(
            match['HomeTeam'],
            match['AwayTeam'],
            historical,
            match['Date']
        )
        
        if best_bet and hasattr(best_bet, 'risk_adjusted_confidence') and best_bet.risk_adjusted_confidence >= min_confidence:
            recommendations.append({
                'league': 'Bundesliga',
                'date': match['Date'],
                'home': match['HomeTeam'],
                'away': match['AwayTeam'],
                'pattern': best_bet.pattern_name,
                'confidence': best_bet.risk_adjusted_confidence,
                'raw_confidence': best_bet.confidence,
                'threshold': best_bet.threshold
            })
    
    return recommendations


def predict_romanian(start_date, end_date, min_confidence=0.70):
    """Get Romanian Liga I recommendations"""
    print("\n" + "="*80)
    print("🇷🇴  ROMANIAN LIGA I PREDICTIONS")
    print("="*80)
    
    try:
        data = load_romanian_data()
    except Exception as e:
        print(f"⚠️  Skipping Romanian Liga I: {e}")
        return []
    
    clear_patterns()
    register_romanian_patterns()
    
    predictor = RomanianMatchPredictor()
    
    # Filter matches in date range
    matches = data[
        (data['Date'] >= start_date) & 
        (data['Date'] <= end_date)
    ].sort_values('Date')
    
    recommendations = []
    
    for _, match in matches.iterrows():
        historical = data[data['Date'] < match['Date']].tail(200)
        
        if len(historical) < 50:
            continue
        
        match_data = pd.Series({
            'HomeTeam': match['HomeTeam'],
            'AwayTeam': match['AwayTeam'],
            'Date': match['Date']
        })
        
        prediction = predictor.predict_match(match_data, historical)
        
        if prediction.best_bet and hasattr(prediction.best_bet, 'risk_adjusted_confidence') and prediction.best_bet.risk_adjusted_confidence >= min_confidence:
            recommendations.append({
                'league': 'Romanian Liga I',
                'date': match['Date'],
                'home': match['HomeTeam'],
                'away': match['AwayTeam'],
                'pattern': prediction.best_bet.pattern_name,
                'confidence': prediction.best_bet.risk_adjusted_confidence,
                'raw_confidence': prediction.best_bet.confidence,
                'threshold': prediction.best_bet.threshold
            })
    
    return recommendations


def main():
    parser = argparse.ArgumentParser(
        description='Generate betting recommendations across all 4 leagues',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Next week's matches
    python predict_date_range_all_leagues.py --start-date 2025-11-09 --end-date 2025-11-16
    
    # Only high confidence bets (75%+)
    python predict_date_range_all_leagues.py --start-date 2025-11-09 --end-date 2025-11-16 --min-confidence 0.75
    
    # Ultra conservative (80%+)
    python predict_date_range_all_leagues.py --start-date 2025-11-09 --end-date 2025-11-16 --min-confidence 0.80
        """
    )
    
    parser.add_argument('--start-date', type=str, required=True,
                       help='Start date (YYYY-MM-DD)')
    parser.add_argument('--end-date', type=str, required=True,
                       help='End date (YYYY-MM-DD)')
    parser.add_argument('--min-confidence', type=float, default=0.70,
                       help='Minimum risk-adjusted confidence (default: 0.70)')
    parser.add_argument('--league', type=str, choices=['premier', 'laliga', 'bundesliga', 'romania', 'all'], 
                       default='all', help='Specific league or all (default: all)')
    
    args = parser.parse_args()
    
    start_date = pd.to_datetime(args.start_date)
    end_date = pd.to_datetime(args.end_date)
    
    print("="*80)
    print("💰 PRODUCTION BET RECOMMENDATIONS - REAL MONEY")
    print("="*80)
    print(f"\nDate Range: {args.start_date} to {args.end_date}")
    print(f"Minimum Confidence: {args.min_confidence:.0%} (risk-adjusted)")
    print(f"\n⚠️  IMPORTANT: These are REAL betting recommendations")
    print("   • Based on historical win rates (not dummy odds)")
    print("   • Risk-adjusted to favor consistent patterns")
    print("   • Only bet what you can afford to lose")
    
    # Collect recommendations from all leagues
    all_recommendations = []
    
    if args.league in ['premier', 'all']:
        all_recommendations.extend(predict_premier_league(start_date, end_date, args.min_confidence))
    
    if args.league in ['laliga', 'all']:
        all_recommendations.extend(predict_la_liga(start_date, end_date, args.min_confidence))
    
    if args.league in ['bundesliga', 'all']:
        all_recommendations.extend(predict_bundesliga(start_date, end_date, args.min_confidence))
    
    if args.league in ['romania', 'all']:
        all_recommendations.extend(predict_romanian(start_date, end_date, args.min_confidence))
    
    # Sort by date, then confidence
    all_recommendations.sort(key=lambda x: (x['date'], -x['confidence']))
    
    # Display recommendations
    print("\n" + "="*80)
    print("📋 BETTING SLIP - RECOMMENDED BETS")
    print("="*80)
    
    if not all_recommendations:
        print("\n❌ No betting opportunities found in this date range")
        print(f"   Try lowering --min-confidence (current: {args.min_confidence:.0%})")
        return
    
    print(f"\n{'Date':<12} {'League':<18} {'Match':<40} {'Pattern':<25} {'Conf':<8}")
    print("-"*120)
    
    for i, rec in enumerate(all_recommendations, 1):
        match_str = f"{rec['home']} vs {rec['away']}"
        print(f"{rec['date'].strftime('%Y-%m-%d'):<12} {rec['league']:<18} {match_str:<40} {rec['pattern']:<25} {rec['confidence']:.1%}")
    
    # Summary statistics
    print("\n" + "="*80)
    print("📊 SUMMARY")
    print("="*80)
    
    total_bets = len(all_recommendations)
    avg_confidence = sum(r['confidence'] for r in all_recommendations) / total_bets if total_bets > 0 else 0
    
    by_league = {}
    for rec in all_recommendations:
        league = rec['league']
        by_league[league] = by_league.get(league, 0) + 1
    
    print(f"\nTotal Bets: {total_bets}")
    print(f"Average Confidence: {avg_confidence:.1%}")
    print(f"\nBy League:")
    for league, count in sorted(by_league.items(), key=lambda x: -x[1]):
        print(f"  {league:<20} {count:>3} bets")
    
    # Pattern distribution
    by_pattern = {}
    for rec in all_recommendations:
        pattern_type = 'corners' if 'corner' in rec['pattern'].lower() else \
                       'cards' if 'card' in rec['pattern'].lower() else \
                       'goals' if 'goal' in rec['pattern'].lower() else 'other'
        by_pattern[pattern_type] = by_pattern.get(pattern_type, 0) + 1
    
    print(f"\nBy Pattern Type:")
    for pattern_type, count in sorted(by_pattern.items(), key=lambda x: -x[1]):
        print(f"  {pattern_type.capitalize():<20} {count:>3} bets")
    
    print("\n" + "="*80)
    print("💡 BETTING TIPS")
    print("="*80)
    print("""
1. BANKROLL MANAGEMENT:
   ✅ Bet 1-2% of your bankroll per bet
   ✅ Never bet more than you can afford to lose
   ✅ Track all bets in a spreadsheet

2. RISK-ADJUSTED CONFIDENCE:
   ✅ Higher confidence = more reliable
   ✅ Corners generally more consistent than goals
   ✅ 70-75% = good, 75-80% = very good, 80%+ = excellent

3. VERIFY BEFORE BETTING:
   ✅ Check team news (injuries, suspensions)
   ✅ Verify match is actually happening
   ✅ Shop around for best odds

4. REALISTIC EXPECTATIONS:
   ✅ No system is perfect
   ✅ Variance is normal (winning/losing streaks happen)
   ✅ Long-term consistency matters most
    """)
    
    print("="*80)
    print("🎯 Good luck! Bet responsibly.")
    print("="*80)


if __name__ == '__main__':
    main()
