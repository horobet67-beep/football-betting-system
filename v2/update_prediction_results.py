"""
Update Prediction Results from Database

Automatically checks completed matches in database and updates prediction files
with WIN/LOSS results. Leaves future matches as PENDING.

Usage:
    python3 update_prediction_results.py predictions_20251101_20251109_backtest.txt
    python3 update_prediction_results.py --help
"""

import json
import sys
import argparse
import pandas as pd
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, List

# Import data adapters
from data.serie_a_adapter import load_serie_a_data
from data.bundesliga_adapter import load_bundesliga_data
from data.la_liga_adapter import load_la_liga_data
from data.premier_league_adapter import load_premier_league_data
from data.romanian_adapter import load_romanian_data


# Pattern checking functions
def check_pattern_result(pattern_name: str, match_data: dict) -> Optional[bool]:
    """
    Check if a pattern was successful based on match data.
    
    Args:
        pattern_name: Name of the betting pattern
        match_data: Dictionary with match statistics
        
    Returns:
        True if pattern succeeded, False if failed, None if cannot determine
    """
    # Cards patterns (using HY/HR/AY/AR column names)
    if pattern_name == 'away_over_0_5_cards':
        away_yellow = match_data.get('AY', match_data.get('away_yellow_cards', 0))
        away_red = match_data.get('AR', match_data.get('away_red_cards', 0))
        if pd.isna(away_yellow) or pd.isna(away_red):
            return None
        return (away_yellow + away_red) >= 1
    
    if pattern_name == 'home_over_0_5_cards':
        home_yellow = match_data.get('HY', match_data.get('home_yellow_cards', 0))
        home_red = match_data.get('HR', match_data.get('home_red_cards', 0))
        if pd.isna(home_yellow) or pd.isna(home_red):
            return None
        return (home_yellow + home_red) >= 1
    
    # Corners patterns (using HC/AC column names)
    if pattern_name == 'home_over_2_5_corners':
        corners = match_data.get('HC', match_data.get('home_corners', 0))
        if pd.isna(corners):
            return None
        return corners >= 3
    
    if pattern_name == 'home_over_3_5_corners':
        corners = match_data.get('HC', match_data.get('home_corners', 0))
        if pd.isna(corners):
            return None
        return corners >= 4
    
    if pattern_name == 'away_over_2_5_corners':
        corners = match_data.get('AC', match_data.get('away_corners', 0))
        if pd.isna(corners):
            return None
        return corners >= 3
    
    if pattern_name == 'total_over_7_5_corners':
        home_c = match_data.get('HC', match_data.get('home_corners', 0))
        away_c = match_data.get('AC', match_data.get('away_corners', 0))
        if pd.isna(home_c) or pd.isna(away_c):
            return None
        return (home_c + away_c) >= 8
    
    # Goals patterns (using FTHG/FTAG column names)
    if pattern_name == 'total_over_1_5_goals':
        home_goals = match_data.get('FTHG', match_data.get('full_time_home_goals', 0))
        away_goals = match_data.get('FTAG', match_data.get('full_time_away_goals', 0))
        if pd.isna(home_goals) or pd.isna(away_goals):
            return None
        return (home_goals + away_goals) >= 2
    
    if pattern_name == 'total_under_2_5_goals':
        home_goals = match_data.get('FTHG', match_data.get('full_time_home_goals', 0))
        away_goals = match_data.get('FTAG', match_data.get('full_time_away_goals', 0))
        if pd.isna(home_goals) or pd.isna(away_goals):
            return None
        return (home_goals + away_goals) <= 2
    
    if pattern_name == 'home_over_0_5_goals':
        goals = match_data.get('FTHG', match_data.get('full_time_home_goals', 0))
        if pd.isna(goals):
            return None
        return goals >= 1
    
    # Result patterns (using FTR column)
    if pattern_name == 'home_win_or_draw':
        result = match_data.get('FTR', match_data.get('full_time_result', ''))
        if not result or pd.isna(result):
            return None
        return result in ['H', 'D']
    
    if pattern_name == 'away_win_or_draw':
        result = match_data.get('FTR', match_data.get('full_time_result', ''))
        if not result or pd.isna(result):
            return None
        return result in ['A', 'D']
    
    # Pattern not implemented
    print(f"  ⚠️  Pattern '{pattern_name}' check not implemented")
    return None


def load_league_data(league_name: str) -> Optional[dict]:
    """Load all match data for a league."""
    try:
        if league_name == 'Serie A':
            df = load_serie_a_data(include_future=False)
        elif league_name == 'Bundesliga':
            df = load_bundesliga_data(include_future=False)
        elif league_name == 'La Liga':
            df = load_la_liga_data(include_future=False)
        elif league_name == 'Premier League':
            df = load_premier_league_data(include_future=False)
        elif league_name == 'Romania Liga 1':
            df = load_romanian_data(include_future=False)
        else:
            print(f"  ⚠️  Unknown league: {league_name}")
            return None
        
        # Convert to dictionary keyed by (date, home, away)
        matches = {}
        for idx, row in df.iterrows():
            key = (
                row['Date'].strftime('%Y-%m-%d %H:%M'),
                row['HomeTeam'],
                row['AwayTeam']
            )
            matches[key] = row.to_dict()
        
        return matches
    
    except Exception as e:
        print(f"  ❌ Error loading {league_name} data: {e}")
        return None


def update_prediction_file(input_file: str, output_file: Optional[str] = None):
    """
    Update prediction file with actual results from database.
    
    Args:
        input_file: Path to prediction file
        output_file: Path to save updated file (defaults to overwriting input)
    """
    if output_file is None:
        output_file = input_file
    
    input_path = Path(input_file)
    if not input_path.exists():
        print(f"❌ File not found: {input_file}")
        return
    
    # Read prediction file
    print(f"📖 Reading {input_file}...")
    txt = input_path.read_text(encoding='utf-8')
    
    # Extract JSON data
    idx = txt.find('📦 JSON')
    if idx == -1:
        print("❌ No JSON data found in file")
        return
    
    json_start = txt[idx:].find('{')
    json_data = txt[idx + json_start:]
    data = json.loads(json_data)
    
    predictions = data['predictions']
    print(f"Found {len(predictions)} predictions\n")
    
    # Load data for each league
    print("📊 Loading league data...")
    league_data = {}
    leagues_needed = set(p['league'] for p in predictions)
    
    for league in leagues_needed:
        print(f"  Loading {league}...", end=' ')
        matches = load_league_data(league)
        if matches:
            league_data[league] = matches
            print(f"✅ {len(matches)} matches")
        else:
            print("❌ Failed")
    
    print()
    
    # Update predictions
    print("🔄 Checking prediction results...")
    now = datetime.now()
    updated_count = 0
    won_count = 0
    lost_count = 0
    pending_count = 0
    cannot_check = 0
    
    for pred in predictions:
        # Parse prediction date
        try:
            pred_date = datetime.strptime(pred['date'], '%Y-%m-%d %H:%M')
        except:
            print(f"  ⚠️  Could not parse date: {pred['date']}")
            continue
        
        # Skip future matches
        if pred_date > now:
            pred['result'] = 'PENDING'
            pred['won'] = ''
            pending_count += 1
            continue
        
        # Look up match in database
        league = pred['league']
        if league not in league_data:
            cannot_check += 1
            continue
        
        key = (pred['date'], pred['home'], pred['away'])
        match_data = league_data[league].get(key)
        
        if not match_data:
            # Try without exact time match
            date_only = pred['date'].split()[0]
            match_data = None
            for (mdate, mhome, maway), mdata in league_data[league].items():
                if mdate.startswith(date_only) and mhome == pred['home'] and maway == pred['away']:
                    match_data = mdata
                    break
        
        if not match_data:
            print(f"  ⚠️  Match not found: {pred['home']} vs {pred['away']} on {pred['date']}")
            cannot_check += 1
            continue
        
        # Check pattern result
        pattern_won = check_pattern_result(pred['pattern'], match_data)
        
        if pattern_won is None:
            cannot_check += 1
            continue
        
        # Update prediction
        pred['result'] = 'COMPLETE'
        pred['won'] = 'YES' if pattern_won else 'NO'
        
        # Build outcome description
        if 'cards' in pred['pattern']:
            home_cards = match_data.get('HY', 0) + match_data.get('HR', 0)
            away_cards = match_data.get('AY', 0) + match_data.get('AR', 0)
            pred['actual_outcome'] = f"Cards: Home {home_cards}, Away {away_cards}"
        elif 'corners' in pred['pattern']:
            home_corners = match_data.get('HC', 0)
            away_corners = match_data.get('AC', 0)
            pred['actual_outcome'] = f"Corners: Home {home_corners}, Away {away_corners}"
        elif 'goals' in pred['pattern'] or 'under' in pred['pattern'] or 'over' in pred['pattern']:
            home_goals = match_data.get('FTHG', 0)
            away_goals = match_data.get('FTAG', 0)
            pred['actual_outcome'] = f"Score: {home_goals}-{away_goals}"
        else:
            result = match_data.get('FTR', 'N/A')
            pred['actual_outcome'] = f"Result: {result}"
        
        updated_count += 1
        if pattern_won:
            won_count += 1
        else:
            lost_count += 1
    
    # Update JSON in file
    data['predictions'] = predictions
    new_json = json.dumps(data, indent=2, ensure_ascii=False)
    
    # Replace JSON section in file
    txt_before_json = txt[:idx + json_start]
    new_txt = txt_before_json + new_json + "\n"
    
    # Write updated file
    Path(output_file).write_text(new_txt, encoding='utf-8')
    
    # Print summary
    print()
    print("="*80)
    print("📊 UPDATE SUMMARY")
    print("="*80)
    print(f"Total predictions:     {len(predictions)}")
    print(f"Updated with results:  {updated_count}")
    print(f"  ✅ Won:               {won_count} ({won_count/updated_count*100:.1f}%)" if updated_count > 0 else "  ✅ Won:               0")
    print(f"  ❌ Lost:              {lost_count} ({lost_count/updated_count*100:.1f}%)" if updated_count > 0 else "  ❌ Lost:              0")
    print(f"Pending (future):      {pending_count}")
    print(f"Could not check:       {cannot_check}")
    print("="*80)
    print(f"✅ Updated file saved: {output_file}")
    
    if updated_count > 0:
        win_rate = won_count / updated_count * 100
        print(f"\n🎯 Win Rate: {win_rate:.1f}%")
        
        if win_rate >= 70:
            print("   ✅ EXCELLENT - Matches backtest expectations!")
        elif win_rate >= 60:
            print("   ⚠️  ACCEPTABLE - Slightly below target")
        else:
            print("   ❌ BELOW TARGET - Review predictions carefully")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Update prediction file with actual results from database'
    )
    parser.add_argument('input_file', help='Prediction file to update')
    parser.add_argument('--output', '-o', help='Output file (default: overwrite input)')
    
    args = parser.parse_args()
    
    update_prediction_file(args.input_file, args.output)


if __name__ == '__main__':
    main()
