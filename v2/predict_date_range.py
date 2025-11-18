#!/usr/bin/env python3
"""
Romanian Liga I Date Range Match Predictor

Predict betting opportunities for matches within a specific time window.
Usage: python predict_date_range.py --start "2025-11-15" --end "2025-12-01"
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import argparse
import sys
import glob
from typing import List, Dict, Tuple
import logging

# Add v2 to path
sys.path.append('.')

from predictor.romanian_predictor import RomanianMatchPredictor
from patterns.registry import get_pattern_registry, clear_patterns
from patterns.romanian_patterns import register_romanian_patterns

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)


def parse_date(date_str: str) -> datetime:
    """Parse date string in various formats"""
    formats = [
        "%Y-%m-%d",
        "%Y/%m/%d", 
        "%d-%m-%Y",
        "%d/%m/%Y",
        "%m-%d-%Y",
        "%m/%d/%Y"
    ]
    
    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
    
    raise ValueError(f"Unable to parse date: {date_str}. Use format YYYY-MM-DD")


def load_romanian_data() -> pd.DataFrame:
    """Load and process Romanian Liga I data"""
    print("📂 Loading Romanian Liga I data...")
    
    csv_files = glob.glob('data/liga1-romania/*.csv')
    if not csv_files:
        raise FileNotFoundError("No Romanian Liga I data files found in data/liga1-romania/")
    
    data_frames = []
    for file in csv_files:
        df = pd.read_csv(file)
        
        # Map Romanian column names to standard format
        df_mapped = pd.DataFrame({
            'HomeTeam': df['home_team_name'],
            'AwayTeam': df['away_team_name'],
            'FTHG': df['home_team_goal_count'],
            'FTAG': df['away_team_goal_count'],
            'HC': df['home_team_corner_count'],
            'AC': df['away_team_corner_count'],
            'HY': df['home_team_yellow_cards'],
            'AY': df['away_team_yellow_cards'],
            'HR': df['home_team_red_cards'],
            'AR': df['away_team_red_cards'],
            'HS': df['home_team_shots'],
            'AS': df['away_team_shots'],
            'Date': df['date_GMT'],
            'Status': df['status'],
            'Timestamp': df['timestamp']
        })
        
        # Add result column for completed matches
        def get_result(row):
            if pd.isna(row['FTHG']) or pd.isna(row['FTAG']):
                return None
            if row['FTHG'] > row['FTAG']:
                return 'H'
            elif row['FTAG'] > row['FTHG']:
                return 'A'
            else:
                return 'D'
        
        df_mapped['FTR'] = df_mapped.apply(get_result, axis=1)
        data_frames.append(df_mapped)
    
    combined_data = pd.concat(data_frames, ignore_index=True)
    
    # Remove rows with missing team names
    combined_data = combined_data.dropna(subset=['HomeTeam', 'AwayTeam'])
    
    print(f"✅ Loaded {len(combined_data)} total matches")
    return combined_data


def filter_matches_by_date_range(data: pd.DataFrame, start_date: datetime, end_date: datetime) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Filter matches by date range and separate historical vs future matches"""
    
    # Convert timestamps to datetime for filtering
    data['DateTime'] = pd.to_datetime(data['Timestamp'], unit='s')
    
    # Filter by date range
    mask = (data['DateTime'] >= start_date) & (data['DateTime'] <= end_date)
    matches_in_range = data[mask].copy()
    
    # Separate completed (historical) and incomplete (future) matches
    completed_matches = data[data['Status'] == 'complete'].copy()
    future_matches = matches_in_range[matches_in_range['Status'] == 'incomplete'].copy()
    
    return completed_matches, future_matches


def predict_date_range_matches(start_date: str, end_date: str, min_confidence: float = 0.60) -> None:
    """Predict matches in the specified date range"""
    
    # Parse dates
    try:
        start_dt = parse_date(start_date)
        end_dt = parse_date(end_date)
    except ValueError as e:
        print(f"❌ Error: {e}")
        return
    
    if start_dt > end_dt:
        print("❌ Error: Start date must be before end date")
        return
    
    print(f"\n🎯 ROMANIAN LIGA I PREDICTIONS")
    print(f"📅 Date Range: {start_dt.strftime('%Y-%m-%d')} to {end_dt.strftime('%Y-%m-%d')}")
    print("=" * 60)
    
    # Load data
    try:
        all_data = load_romanian_data()
    except Exception as e:
        print(f"❌ Error loading data: {e}")
        return
    
    # Filter matches by date range
    historical_data, future_matches = filter_matches_by_date_range(all_data, start_dt, end_dt)
    
    if len(future_matches) == 0:
        print(f"\n⚠️  No future matches found in the specified date range.")
        print(f"💡 Try a date range that includes upcoming matches (status: incomplete)")
        return
    
    print(f"\n📊 Analysis Summary:")
    print(f"   • Historical matches: {len(historical_data)}")
    print(f"   • Future matches to predict: {len(future_matches)}")
    print()
    
    # Initialize predictor with enhanced features
    clear_patterns()
    register_romanian_patterns()
    predictor = RomanianMatchPredictor()
    
    # Process each future match
    bet_recommendations = []
    monitor_opportunities = []
    no_bet_matches = []
    
    for idx, match in future_matches.iterrows():
        try:
            prediction = predictor.predict_match(match, historical_data)
            
            match_info = {
                'date': match['Date'],
                'home': match['HomeTeam'],
                'away': match['AwayTeam'],
                'prediction': prediction
            }
            
            if prediction.best_bet:
                bet_recommendations.append(match_info)
            elif any(r.recommendation == "MONITOR" for r in prediction.recommendations):
                monitor_opportunities.append(match_info)
            else:
                no_bet_matches.append(match_info)
                
        except Exception as e:
            print(f"⚠️  Error predicting {match['HomeTeam']} vs {match['AwayTeam']}: {e}")
    
    # Display results
    print("🏆 BETTING RECOMMENDATIONS")
    print("=" * 40)
    
    if bet_recommendations:
        for i, match in enumerate(bet_recommendations, 1):
            pred = match['prediction']
            print(f"\n{i}. 🟢 {match['date']}")
            print(f"   🏟️  {match['home']} vs {match['away']}")
            print(f"   ✅ BET: {pred.best_bet.bet_type}")
            print(f"   📊 Confidence: {pred.best_bet.confidence:.1%}")
            print(f"   🎯 Threshold: {pred.best_bet.threshold:.1%} (adaptive)")
            print(f"   💰 Expected Value: {pred.best_bet.expected_value:+.2%}")
            print(f"   💡 Reasoning: {pred.best_bet.reasoning}")
    else:
        print("❌ No high-confidence betting opportunities found")
    
    if monitor_opportunities:
        print(f"\n👁️  MONITOR OPPORTUNITIES ({len(monitor_opportunities)} matches)")
        print("-" * 35)
        for match in monitor_opportunities:
            pred = match['prediction']
            monitor_bets = [r for r in pred.recommendations if r.recommendation == "MONITOR"]
            best_monitor = max(monitor_bets, key=lambda x: x.confidence)
            print(f"📅 {match['date']} - {match['home']} vs {match['away']}")
            print(f"   👁️  {best_monitor.bet_type} ({best_monitor.confidence:.1%})")
    
    if no_bet_matches:
        print(f"\n🚫 NO BET RECOMMENDATIONS ({len(no_bet_matches)} matches)")
        print("-" * 35)
        for match in no_bet_matches[:5]:  # Show first 5
            print(f"📅 {match['date']} - {match['home']} vs {match['away']}")
        if len(no_bet_matches) > 5:
            print(f"   ... and {len(no_bet_matches) - 5} more matches")
    
    # Summary statistics
    total_matches = len(bet_recommendations) + len(monitor_opportunities) + len(no_bet_matches)
    
    print(f"\n📈 PREDICTION SUMMARY")
    print("=" * 25)
    print(f"🎯 Total matches analyzed: {total_matches}")
    print(f"✅ BET recommendations: {len(bet_recommendations)} ({len(bet_recommendations)/total_matches*100:.1f}%)")
    print(f"👁️ MONITOR opportunities: {len(monitor_opportunities)} ({len(monitor_opportunities)/total_matches*100:.1f}%)")
    print(f"🚫 NO BET: {len(no_bet_matches)} ({len(no_bet_matches)/total_matches*100:.1f}%)")
    
    if bet_recommendations:
        avg_confidence = np.mean([m['prediction'].best_bet.confidence for m in bet_recommendations])
        avg_ev = np.mean([m['prediction'].best_bet.expected_value for m in bet_recommendations])
        print(f"\n💎 Average confidence: {avg_confidence:.1%}")
        print(f"💰 Average expected value: {avg_ev:+.2%}")
    
    print(f"\n🚀 Enhanced with recent form weighting & adaptive thresholds!")


def main():
    parser = argparse.ArgumentParser(description='Predict Romanian Liga I matches in a date range')
    parser.add_argument('--start', required=True, help='Start date (YYYY-MM-DD)')
    parser.add_argument('--end', required=True, help='End date (YYYY-MM-DD)')
    parser.add_argument('--min-confidence', type=float, default=0.60, 
                       help='Minimum confidence threshold (default: 0.60)')
    
    args = parser.parse_args()
    
    predict_date_range_matches(args.start, args.end, args.min_confidence)


if __name__ == "__main__":
    main()