"""
Save future betting predictions to a file for tracking.
Generates a comprehensive report of all predictions across all leagues.
"""

from datetime import datetime, timedelta
from typing import List, Dict, Optional
import sys
import json
import pandas as pd
import os

# Import all predictors
from simple_serie_a_predictor import SimpleSerieAPredictor
from simple_bundesliga_predictor import SimpleBundesligaPredictor
from simple_la_liga_predictor import SimpleLaLigaPredictor
from simple_premier_league_predictor import SimplePremierLeaguePredictor
from simple_romanian_predictor import SimpleRomanianPredictor

# Import adapters
from data.serie_a_adapter import load_serie_a_data
from data.bundesliga_adapter import load_bundesliga_data
from data.la_liga_adapter import load_la_liga_data
from data.premier_league_adapter import load_premier_league_data
from data.romanian_adapter import load_romanian_data


# ============================================================================
# UPGRADE #3: Dynamic Pattern-Specific Thresholds
# Based on comprehensive backtesting results showing different patterns
# have different reliability levels. Optimized thresholds maximize win rate.
# ============================================================================
PATTERN_RISK_ADJUSTED_THRESHOLDS = {
    # ULTRA-RELIABLE PATTERNS (83-84% threshold - proven high WR even at lower confidence)
    'away_over_0_5_cards': 83,        # Premier: 89.4% WR, Serie A: 94%+ WR
    'home_over_0_5_cards': 83,        # Premier: 85.7% WR, Bundesliga: 88%+ WR
    'total_under_5_5_goals': 84,      # Premier: 92.7% WR, consistent across leagues
    
    # HIGHLY-RELIABLE PATTERNS (85% threshold - standard excellent performers)
    'total_over_1_5_cards': 85,       # Premier: 89.7% WR, universal card pattern
    'total_under_2_5_cards': 85,      # Bundesliga: 96.0% WR
    'total_under_7_5_corners': 85,    # Bundesliga: 98.1% WR
    'defensive_match': 85,            # Bundesliga: 100% WR (210/210)
    'draw_and_under_2_5': 85,         # Bundesliga: 100% WR (197/197)
    
    # RELIABLE PATTERNS (87% threshold - good but need higher confidence)
    'total_under_2_5_goals': 87,      # Bundesliga: 98.1% WR
    'home_over_2_5_corners': 87,      # Premier: 84.6% WR
    'away_over_2_5_corners': 87,      # Context-dependent
    
    # CONTEXT-DEPENDENT PATTERNS (88% threshold - require specific conditions)
    'total_over_8_5_corners': 88,     # Volatile, needs high confidence
    'home_over_3_5_corners': 88,      # Team-specific
    'away_over_3_5_corners': 88,      # Team-specific
    
    # CONSERVATIVE PATTERNS (90% threshold - only bet when very confident)
    'total_over_2_5_goals': 90,       # Higher variance
    'btts': 90,                       # Both teams to score - unpredictable
    
    # DEFAULT for unlisted patterns
    'default': 85
}

def get_pattern_threshold(pattern_name: str) -> float:
    """
    Get the optimized risk-adjusted threshold for a specific pattern.
    Returns the threshold as a percentage (0-100).
    """
    # Direct match
    if pattern_name in PATTERN_RISK_ADJUSTED_THRESHOLDS:
        return PATTERN_RISK_ADJUSTED_THRESHOLDS[pattern_name]
    
    # Partial pattern matching for variations
    for key_pattern, threshold in PATTERN_RISK_ADJUSTED_THRESHOLDS.items():
        if key_pattern in pattern_name:
            return threshold
    
    # Default threshold
    return PATTERN_RISK_ADJUSTED_THRESHOLDS['default']


def check_pattern_result(pattern_name: str, match_data: Dict) -> Optional[bool]:
    """
    Check if a betting pattern was successful for a completed match.
    
    Args:
        pattern_name: Name of the betting pattern
        match_data: Dictionary with match results (HY, AY, HC, AC, FTHG, FTAG, FTR, etc.)
    
    Returns:
        True if pattern won, False if lost, None if can't determine
    """



    """
    Check if a betting pattern was successful for a completed match.
    
    Args:
        pattern_name: Name of the betting pattern
        match_data: Dictionary with match results (HY, AY, HC, AC, FTHG, FTAG, FTR, etc.)
    
    Returns:
        True if pattern won, False if lost, None if can't determine
    """
    try:
        # Cards patterns - expanded thresholds
        if 'cards' in pattern_name:
            # Total cards patterns
            if 'total' in pattern_name:
                home_cards = match_data.get('HY', 0) + match_data.get('HR', 0) * 2  # Red = 2 cards value
                away_cards = match_data.get('AY', 0) + match_data.get('AR', 0) * 2
                if pd.isna(home_cards) or pd.isna(away_cards):
                    return None
                
                total_cards = home_cards + away_cards
                
                # Over thresholds
                if 'over_5_5' in pattern_name or 'over_5.5' in pattern_name:
                    return total_cards >= 6
                elif 'over_4_5' in pattern_name or 'over_4.5' in pattern_name:
                    return total_cards >= 5
                elif 'over_3_5' in pattern_name or 'over_3.5' in pattern_name:
                    return total_cards >= 4
                elif 'over_2_5' in pattern_name or 'over_2.5' in pattern_name:
                    return total_cards >= 3
                elif 'over_1_5' in pattern_name or 'over_1.5' in pattern_name:
                    return total_cards >= 2
                elif 'over_0_5' in pattern_name or 'over_0.5' in pattern_name:
                    return total_cards >= 1
                # Under thresholds - NEW
                elif 'under_2_5' in pattern_name or 'under_2.5' in pattern_name:
                    return total_cards <= 2
                elif 'under_1_5' in pattern_name or 'under_1.5' in pattern_name:
                    return total_cards <= 1
            
            # Individual team cards patterns
            elif 'home' in pattern_name:
                cards = match_data.get('HY', 0) + match_data.get('HR', 0) * 2
                if pd.isna(cards):
                    return None
                
                if 'over_4_5' in pattern_name or 'over_4.5' in pattern_name:
                    return cards >= 5
                elif 'over_3_5' in pattern_name or 'over_3.5' in pattern_name:
                    return cards >= 4
                elif 'over_2_5' in pattern_name or 'over_2.5' in pattern_name:
                    return cards >= 3
                elif 'over_1_5' in pattern_name or 'over_1.5' in pattern_name:
                    return cards >= 2
                elif 'over_0_5' in pattern_name or 'over_0.5' in pattern_name:
                    return cards >= 1
            
            elif 'away' in pattern_name:
                cards = match_data.get('AY', 0) + match_data.get('AR', 0) * 2
                if pd.isna(cards):
                    return None
                
                if 'over_4_5' in pattern_name or 'over_4.5' in pattern_name:
                    return cards >= 5
                elif 'over_3_5' in pattern_name or 'over_3.5' in pattern_name:
                    return cards >= 4
                elif 'over_2_5' in pattern_name or 'over_2.5' in pattern_name:
                    return cards >= 3
                elif 'over_1_5' in pattern_name or 'over_1.5' in pattern_name:
                    return cards >= 2
                elif 'over_0_5' in pattern_name or 'over_0.5' in pattern_name:
                    return cards >= 1
        
        # Corners patterns
        if 'corners' in pattern_name:
            if 'total' in pattern_name:
                # Total corners (home + away)
                home_corners = match_data.get('HC', 0)
                away_corners = match_data.get('AC', 0)
                if pd.isna(home_corners) or pd.isna(away_corners):
                    return None
                
                total_corners = home_corners + away_corners
                
                if 'over_8_5' in pattern_name or 'over_8.5' in pattern_name:
                    return total_corners >= 9
                elif 'over_7_5' in pattern_name or 'over_7.5' in pattern_name:
                    return total_corners >= 8
                elif 'over_6_5' in pattern_name or 'over_6.5' in pattern_name:
                    return total_corners >= 7
                elif 'over_5_5' in pattern_name or 'over_5.5' in pattern_name:
                    return total_corners >= 6
                elif 'over_4_5' in pattern_name or 'over_4.5' in pattern_name:
                    return total_corners >= 5
                elif 'over_3_5' in pattern_name or 'over_3.5' in pattern_name:
                    return total_corners >= 4
                elif 'over_2_5' in pattern_name or 'over_2.5' in pattern_name:
                    return total_corners >= 3
            
            elif 'home' in pattern_name:
                corners = match_data.get('HC', 0)
                if pd.isna(corners):
                    return None
                
                if 'over_8_5' in pattern_name or 'over_8.5' in pattern_name:
                    return corners >= 9
                elif 'over_7_5' in pattern_name or 'over_7.5' in pattern_name:
                    return corners >= 8
                elif 'over_6_5' in pattern_name or 'over_6.5' in pattern_name:
                    return corners >= 7
                elif 'over_5_5' in pattern_name or 'over_5.5' in pattern_name:
                    return corners >= 6
                elif 'over_4_5' in pattern_name or 'over_4.5' in pattern_name:
                    return corners >= 5
                elif 'over_3_5' in pattern_name or 'over_3.5' in pattern_name:
                    return corners >= 4
                elif 'over_2_5' in pattern_name or 'over_2.5' in pattern_name:
                    return corners >= 3
                # Under thresholds - NEW
                elif 'under_8_5' in pattern_name or 'under_8.5' in pattern_name:
                    return corners <= 8
            
            elif 'away' in pattern_name:
                corners = match_data.get('AC', 0)
                if pd.isna(corners):
                    return None
                
                if 'over_8_5' in pattern_name or 'over_8.5' in pattern_name:
                    return corners >= 9
                elif 'over_7_5' in pattern_name or 'over_7.5' in pattern_name:
                    return corners >= 8
                elif 'over_6_5' in pattern_name or 'over_6.5' in pattern_name:
                    return corners >= 7
                elif 'over_5_5' in pattern_name or 'over_5.5' in pattern_name:
                    return corners >= 6
                elif 'over_4_5' in pattern_name or 'over_4.5' in pattern_name:
                    return corners >= 5
                elif 'over_3_5' in pattern_name or 'over_3.5' in pattern_name:
                    return corners >= 4
                elif 'over_2_5' in pattern_name or 'over_2.5' in pattern_name:
                    return corners >= 3
                # Under thresholds - NEW
                elif 'under_8_5' in pattern_name or 'under_8.5' in pattern_name:
                    return corners <= 8
        
        # Goals patterns
        if 'goals' in pattern_name:
            home_goals = match_data.get('FTHG', 0)
            away_goals = match_data.get('FTAG', 0)
            
            if pd.isna(home_goals) or pd.isna(away_goals):
                return None
            
            total_goals = home_goals + away_goals
            
            # Over thresholds
            if 'total_over_5_5' in pattern_name or 'total_over_5.5' in pattern_name:
                return total_goals >= 6
            elif 'total_over_4_5' in pattern_name or 'total_over_4.5' in pattern_name:
                return total_goals >= 5
            elif 'total_over_3_5' in pattern_name or 'total_over_3.5' in pattern_name:
                return total_goals >= 4
            elif 'total_over_2_5' in pattern_name or 'total_over_2.5' in pattern_name:
                return total_goals >= 3
            elif 'total_over_1_5' in pattern_name or 'total_over_1.5' in pattern_name:
                return total_goals >= 2
            # Under thresholds - NEW
            elif 'total_under_5_5' in pattern_name or 'total_under_5.5' in pattern_name:
                return total_goals <= 5
            elif 'total_under_4_5' in pattern_name or 'total_under_4.5' in pattern_name:
                return total_goals <= 4
            elif 'total_under_2_5' in pattern_name or 'total_under_2.5' in pattern_name:
                return total_goals <= 2
            # Individual team goals
            elif 'home_over_0_5' in pattern_name or 'home_over_0.5' in pattern_name:
                return home_goals >= 1
            elif 'away_over_0_5' in pattern_name or 'away_over_0.5' in pattern_name:
                return away_goals >= 1
        
        # Result patterns
        if 'win_or_draw' in pattern_name:
            result = match_data.get('FTR', '')
            if not result or pd.isna(result):
                return None
            
            if 'home' in pattern_name:
                return result in ['H', 'D']
            elif 'away' in pattern_name:
                return result in ['A', 'D']
        
        return None
    
    except Exception as e:
        print(f"Error checking pattern {pattern_name}: {e}")
        return None


def load_league_data(league_name: str) -> Dict:
    """
    Load match data for a league and return as dictionary keyed by (date, home, away).
    
    Args:
        league_name: Name of the league
    
    Returns:
        Dictionary with match results
    """
    loader_map = {
        'Serie A': load_serie_a_data,
        'Bundesliga': load_bundesliga_data,
        'La Liga': load_la_liga_data,
        'Premier League': load_premier_league_data,
        'Romania Liga 1': load_romanian_data
    }
    
    if league_name not in loader_map:
        return {}
    
    df = loader_map[league_name]()
    
    # Create dictionary keyed by (date, home, away)
    match_dict = {}
    for _, row in df.iterrows():
        date_str = row['Date'].strftime('%Y-%m-%d')
        key = (date_str, row['HomeTeam'], row['AwayTeam'])
        match_dict[key] = row.to_dict()
    
    return match_dict


def save_predictions_to_file(start_date: datetime, end_date: datetime, output_file: str):
    """
    Generate predictions and save to file.
    
    Args:
        start_date: Start of prediction window
        end_date: End of prediction window (inclusive)
        output_file: Path to output file
    """
    all_predictions = []
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    
    # Load all league data once for result checking
    print("📥 Loading league data for result checking...")
    league_data_cache = {
        'Serie A': load_league_data('Serie A'),
        'Bundesliga': load_league_data('Bundesliga'),
        'La Liga': load_league_data('La Liga'),
        'Premier League': load_league_data('Premier League'),
        'Romania Liga 1': load_league_data('Romania Liga 1')
    }
    
    # League configurations - Updated with optimized weights from comprehensive testing
    leagues = [
        {
            'name': 'Serie A',
            'emoji': '🇮🇹',
            'predictor_class': SimpleSerieAPredictor,
            'adapter_func': load_serie_a_data,
            'weights': 'Long Term (15/15/20/25/25)',
            'backtest_wr': 64.2,
            'patterns_tested': 32
        },
        {
            'name': 'Bundesliga',
            'emoji': '🇩🇪',
            'predictor_class': SimpleBundesligaPredictor,
            'adapter_func': load_bundesliga_data,
            'weights': 'Extreme Recent (40/30/15/10/5)',
            'backtest_wr': 52.6,
            'patterns_tested': 38
        },
        {
            'name': 'La Liga',
            'emoji': '🇪🇸',
            'predictor_class': SimpleLaLigaPredictor,
            'adapter_func': load_la_liga_data,
            'weights': 'Extreme Recent (40/30/15/10/5)',
            'backtest_wr': 88.4,
            'patterns_tested': 19
        },
        {
            'name': 'Premier League',
            'emoji': '🏴󠁧󠁢󠁥󠁮󠁧󠁿',
            'predictor_class': SimplePremierLeaguePredictor,
            'adapter_func': load_premier_league_data,
            'weights': 'Extreme Recent (40/30/15/10/5)',
            'backtest_wr': 72.1,
            'patterns_tested': 28
        },
        {
            'name': 'Romania Liga 1',
            'emoji': '🇷🇴',
            'predictor_class': SimpleRomanianPredictor,
            'adapter_func': load_romanian_data,
            'weights': 'Long Term (15/15/20/25/25)',
            'backtest_wr': 75.9,
            'patterns_tested': 37
        }
    ]
    
    print(f"🔮 Generating predictions for {start_date.date()} to {end_date.date()}...")
    
    # Process each league
    for league_config in leagues:
        print(f"  Processing {league_config['emoji']} {league_config['name']}...", end='', flush=True)
        
        try:
            # Initialize predictor
            predictor = league_config['predictor_class']()
            latest_historical = predictor.data['Date'].max()
            
            # Load future matches
            all_data = league_config['adapter_func'](include_future=True)
            
            # Filter by date range
            upcoming = all_data[
                (all_data['Date'] >= start_date) & 
                (all_data['Date'] <= end_date)
            ].sort_values('Date')
            
            # Generate predictions
            league_bets = 0
            for idx, match in upcoming.iterrows():
                try:
                    # Try different predictor interfaces
                    prediction = None
                    
                    # Use the actual upcoming match date as the prediction cutoff.
                    # Previously this used `latest_historical` which can produce
                    # incorrect confidence estimates for future matches.
                    match_dt = match['Date']

                    if hasattr(predictor, 'predict_match') and 'historical_data' not in predictor.predict_match.__code__.co_varnames:
                        prediction = predictor.predict_match(
                            home_team=match['HomeTeam'],
                            away_team=match['AwayTeam'],
                            match_date=match_dt
                        )
                    elif hasattr(predictor, 'predict_match_simple'):
                        prediction = predictor.predict_match_simple(
                            home_team=match['HomeTeam'],
                            away_team=match['AwayTeam'],
                            match_date=match_dt
                        )
                    elif hasattr(predictor, 'predict_match'):
                        # predictors that expect historical_data/have different signatures
                        prediction = predictor.predict_match(
                            home_team=match['HomeTeam'],
                            away_team=match['AwayTeam'],
                            historical_data=predictor.data,
                            match_date=match_dt
                        )
                    
                    # Handle different prediction return types
                    if prediction:
                        risk_adj = getattr(prediction, 'risk_adjusted_confidence', None)
                        confidence = getattr(prediction, 'confidence', None)
                        threshold = getattr(prediction, 'threshold', None)
                        pattern_name = getattr(prediction, 'pattern_name', None)
                        
                        # For dict returns (La Liga)
                        if isinstance(prediction, dict):
                            risk_adj = prediction.get('risk_adjusted_confidence')
                            confidence = prediction.get('confidence')
                            threshold = prediction.get('threshold')
                            pattern_name = prediction.get('pattern_name')

                        # Allow zero/low numeric values (don't rely on truthiness)
                        if (risk_adj is not None and confidence is not None and threshold is not None
                                and pattern_name and (risk_adj >= threshold)):
                            
                            # Check if match is in the past and has results
                            match_date = match['Date'].replace(hour=0, minute=0, second=0, microsecond=0)
                            result_status = 'PENDING'
                            won_status = ''
                            
                            if match_date < today:
                                # Try to get match result
                                date_str = match['Date'].strftime('%Y-%m-%d')
                                match_key = (date_str, match['HomeTeam'], match['AwayTeam'])
                                
                                league_matches = league_data_cache.get(league_config['name'], {})
                                if match_key in league_matches:
                                    match_result = league_matches[match_key]
                                    pattern_won = check_pattern_result(pattern_name, match_result)
                                    
                                    if pattern_won is not None:
                                        result_status = 'COMPLETE'
                                        won_status = 'WIN' if pattern_won else 'LOSS'
                            
                            match_data = {
                                'league': league_config['name'],
                                'league_emoji': league_config['emoji'],
                                'date': match['Date'].strftime('%Y-%m-%d %H:%M'),
                                'day_of_week': match['Date'].strftime('%A'),
                                'home': match['HomeTeam'],
                                'away': match['AwayTeam'],
                                'pattern': pattern_name,
                                'confidence': f"{confidence:.1%}",
                                'risk_adjusted': f"{risk_adj:.1%}",
                                'threshold': f"{threshold:.1%}",
                                'margin': f"+{(risk_adj - threshold)*100:.1f}%",
                                'backtest_wr': f"{league_config['backtest_wr']:.1f}%",
                                'weights': league_config['weights'],
                                'result': result_status,
                                'actual_outcome': '',  # To be filled in manually if needed
                                'won': won_status
                            }
                            all_predictions.append(match_data)
                            league_bets += 1
                        
                except Exception as e:
                    continue
            
            print(f" ✅ {league_bets} bets")
            
        except Exception as e:
            print(f" ❌ Error: {e}")
            continue
    
    # Sort by date
    all_predictions.sort(key=lambda x: x['date'])
    
    # Calculate statistics
    total_predictions = len(all_predictions)
    completed = sum(1 for p in all_predictions if p['result'] == 'COMPLETE')
    pending = sum(1 for p in all_predictions if p['result'] == 'PENDING')
    won = sum(1 for p in all_predictions if p['won'] == 'WIN')
    lost = sum(1 for p in all_predictions if p['won'] == 'LOSS')
    win_rate = (won / completed * 100) if completed > 0 else 0
    
    # Write to file
    with open(output_file, 'w', encoding='utf-8') as f:
        # Header
        f.write("="*120 + "\n")
        f.write("🎯 FOOTBALL BETTING PREDICTIONS - MULTI-LEAGUE SYSTEM\n")
        f.write("="*120 + "\n")
        f.write(f"📅 Date Range: {start_date.date()} → {end_date.date()}\n")
        f.write(f"📊 Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"✅ Total Predictions: {total_predictions} bets across 5 leagues\n")
        f.write(f"📈 Completed: {completed} | Pending: {pending}\n")
        if completed > 0:
            f.write(f"🎯 Results: {won} WIN ({win_rate:.1f}%) | {lost} LOSS ({100-win_rate:.1f}%)\n")
        f.write("="*120 + "\n\n")
        
        # League summary
        f.write("📊 LEAGUE SUMMARY\n")
        f.write("-"*120 + "\n")
        from collections import defaultdict
        by_league = defaultdict(list)
        for pred in all_predictions:
            by_league[pred['league']].append(pred)
        
        for league in sorted(by_league.keys()):
            preds = by_league[league]
            avg_conf = sum(float(p['risk_adjusted'].strip('%'))/100 for p in preds) / len(preds)
            f.write(f"{preds[0]['league_emoji']} {league:20} {len(preds):3} bets   Avg Confidence: {avg_conf:.1%}\n")
        
        # Pattern summary
        f.write("\n🎯 PATTERN SUMMARY\n")
        f.write("-"*120 + "\n")
        by_pattern = defaultdict(int)
        for pred in all_predictions:
            by_pattern[pred['pattern']] += 1
        
        for pattern, count in sorted(by_pattern.items(), key=lambda x: -x[1]):
            f.write(f"  {pattern:40} {count:3} bets\n")
        
        # UPGRADE #3: Filter with dynamic pattern-specific thresholds
        # Each pattern has an optimized threshold based on backtesting performance
        high_confidence_bets = []
        for p in all_predictions:
            pattern_threshold = get_pattern_threshold(p['pattern'])
            if float(p['risk_adjusted'].strip('%')) >= pattern_threshold:
                high_confidence_bets.append(p)
        
        # Calculate min/max thresholds used for display
        if high_confidence_bets:
            thresholds_used = [get_pattern_threshold(p['pattern']) for p in high_confidence_bets]
            min_threshold = min(thresholds_used)
            max_threshold = max(thresholds_used)
            threshold_display = f"{min_threshold}%" if min_threshold == max_threshold else f"{min_threshold}-{max_threshold}%"
        else:
            threshold_display = "85%"  # Default display
        
        # HIGH-CONFIDENCE TABLE (Dynamic Thresholds)
        if high_confidence_bets:
            f.write("\n" + "="*180 + "\n")
            f.write(f"🌟 HIGH-CONFIDENCE PREDICTIONS (R-Adj ≥ {threshold_display}) - FILTERED TABLE\n")
            f.write("="*180 + "\n")
            
            # Calculate filtered stats
            filtered_total = len(high_confidence_bets)
            filtered_completed = sum(1 for p in high_confidence_bets if p['result'] == 'COMPLETE')
            filtered_pending = sum(1 for p in high_confidence_bets if p['result'] == 'PENDING')
            filtered_won = sum(1 for p in high_confidence_bets if p['won'] == 'WIN')
            filtered_lost = sum(1 for p in high_confidence_bets if p['won'] == 'LOSS')
            filtered_win_rate = (filtered_won / filtered_completed * 100) if filtered_completed > 0 else 0
            
            f.write(f"📊 Filtered Bets: {filtered_total} of {total_predictions} total ({100*filtered_total/total_predictions:.1f}%)\n")
            f.write(f"📈 Completed: {filtered_completed} | Pending: {filtered_pending}\n")
            if filtered_completed > 0:
                f.write(f"🎯 Results: {filtered_won} WIN ({filtered_win_rate:.1f}%) | {filtered_lost} LOSS ({100-filtered_win_rate:.1f}%)\n")
            f.write("\n")
            
            # Table header
            f.write(f"{'#':<4} {'Date':<12} {'Time':<6} {'League':<18} {'Home Team':<25} {'Away Team':<25} {'Pattern':<25} {'Conf':<7} {'R-Adj':<7} {'Status':<10} {'Result':<7}\n")
            f.write("-"*180 + "\n")
            
            by_date_filtered = defaultdict(list)
            for pred in high_confidence_bets:
                date_key = pred['date'].split()[0]
                by_date_filtered[date_key].append(pred)
            
            bet_number = 1
            for date_key in sorted(by_date_filtered.keys()):
                matches = by_date_filtered[date_key]
                
                for pred in matches:
                    date_part = pred['date'].split()[0]
                    time_part = pred['date'].split()[1]
                    league_short = pred['league_emoji'] + ' ' + pred['league'][:15]
                    
                    # Truncate team names if too long
                    home = pred['home'][:24]
                    away = pred['away'][:24]
                    pattern = pred['pattern'][:24]
                    
                    # Format result column
                    result_display = pred['won'] if pred['won'] else pred['result']
                    
                    f.write(f"{bet_number:<4} {date_part:<12} {time_part:<6} {league_short:<18} {home:<25} {away:<25} {pattern:<25} {pred['confidence']:<7} {pred['risk_adjusted']:<7} {pred['result']:<10} {result_display:<7}\n")
                    bet_number += 1
            
            f.write("-"*180 + "\n")
            f.write(f"\nFiltered Total: {filtered_total} bets (≥85% confidence)\n")
            f.write("="*180 + "\n\n")
        
        # ALL PREDICTIONS TABLE
        f.write("\n" + "="*180 + "\n")
        f.write("📅 ALL PREDICTIONS TABLE - COMPLETE TRACKING SHEET\n")
        f.write("="*180 + "\n\n")
        
        # Table header
        f.write(f"{'#':<4} {'Date':<12} {'Time':<6} {'League':<18} {'Home Team':<25} {'Away Team':<25} {'Pattern':<25} {'Conf':<7} {'R-Adj':<7} {'Status':<10} {'Result':<7}\n")
        f.write("-"*180 + "\n")
        
        by_date = defaultdict(list)
        for pred in all_predictions:
            date_key = pred['date'].split()[0]
            by_date[date_key].append(pred)
        
        bet_number = 1
        for date_key in sorted(by_date.keys()):
            matches = by_date[date_key]
            
            for pred in matches:
                date_part = pred['date'].split()[0]
                time_part = pred['date'].split()[1]
                league_short = pred['league_emoji'] + ' ' + pred['league'][:15]
                
                # Truncate team names if too long
                home = pred['home'][:24]
                away = pred['away'][:24]
                pattern = pred['pattern'][:24]
                
                # Format result column
                result_display = pred['won'] if pred['won'] else pred['result']
                
                f.write(f"{bet_number:<4} {date_part:<12} {time_part:<6} {league_short:<18} {home:<25} {away:<25} {pattern:<25} {pred['confidence']:<7} {pred['risk_adjusted']:<7} {pred['result']:<10} {result_display:<7}\n")
                bet_number += 1
        
        f.write("-"*180 + "\n")
        f.write(f"\nTotal: {len(all_predictions)} bets\n")
        f.write("="*180 + "\n\n")
        
        # Detailed breakdown by date
        f.write("\n" + "="*180 + "\n")
        f.write("📊 DETAILED PREDICTIONS BY DATE\n")
        f.write("="*180 + "\n\n")
        
        bet_number = 1
        for date_key in sorted(by_date.keys()):
            matches = by_date[date_key]
            day_name = matches[0]['day_of_week']
            
            f.write(f"📅 {day_name}, {date_key} ({len(matches)} bets)\n")
            f.write("-"*180 + "\n\n")
            
            for pred in matches:
                f.write(f"{bet_number}. {pred['league_emoji']} {pred['league']:20} | {pred['date'].split()[1]:5} | {pred['home']} vs {pred['away']}\n")
                f.write(f"   🎯 Pattern: {pred['pattern']}\n")
                f.write(f"   📊 Confidence: {pred['confidence']} → Risk-Adj: {pred['risk_adjusted']}\n")
                f.write(f"   🚧 Threshold: {pred['threshold']} | Margin: {pred['margin']}\n")
                f.write(f"   📈 League Backtest: {pred['backtest_wr']} WR | Weights: {pred['weights']}\n")
                
                # Show result with appropriate emoji
                if pred['won'] == 'WIN':
                    f.write(f"   ✅ Result: {pred['result']} | Outcome: {pred['won']}\n")
                elif pred['won'] == 'LOSS':
                    f.write(f"   ❌ Result: {pred['result']} | Outcome: {pred['won']}\n")
                else:
                    f.write(f"   ⏳ Result: {pred['result']}\n")
                
                f.write("\n")
                bet_number += 1
            
            f.write("\n")
        
        # Tracking instructions
        f.write("="*120 + "\n")
        f.write("📝 TRACKING INSTRUCTIONS\n")
        f.write("="*120 + "\n")
        f.write("1. After each match completes, fill in:\n")
        f.write("   - Result: COMPLETE\n")
        f.write("   - Actual_outcome: e.g., 'Away team got 2 cards' or 'Home won 2-1'\n")
        f.write("   - Won: YES or NO\n\n")
        f.write("2. Calculate final statistics:\n")
        f.write("   - Count total WON bets\n")
        f.write("   - Win Rate = WON / TOTAL\n")
        f.write("   - Compare to backtest win rates\n\n")
        f.write("3. Stop conditions:\n")
        f.write("   - After 3 consecutive losses\n")
        f.write("   - If win rate drops 10%+ below backtest\n")
        f.write("   - After 50% of bankroll loss\n\n")
        f.write("="*120 + "\n")
        
        # Critical warnings
        f.write("\n⚠️  CRITICAL WARNINGS\n")
        f.write("="*120 + "\n")
        f.write("• NO FORWARD VALIDATION - These predictions are based on BACKTESTING ONLY\n")
        f.write("• PAPER TRADE FIRST - Strongly recommended before risking real money\n")
        f.write("• CORRELATION RISK - Same patterns across multiple leagues = correlated failure risk\n")
        f.write("• STAKE SIZE - Never exceed 1-2% of bankroll per bet\n")
        f.write("• DIVERSIFICATION - Don't bet on all predictions, pick 3-5 highest confidence\n")
        f.write("• TRACK EVERYTHING - Essential for validating system performance\n")
        f.write("="*120 + "\n\n")
        
        # JSON export for programmatic access
        f.write("\n" + "="*120 + "\n")
        f.write("📦 JSON DATA (for programmatic tracking)\n")
        f.write("="*120 + "\n")
        json_data = {
            'generated_at': datetime.now().isoformat(),
            'date_range': {
                'start': start_date.date().isoformat(),
                'end': end_date.date().isoformat()
            },
            'total_predictions': len(all_predictions),
            'predictions': all_predictions
        }
        f.write(json.dumps(json_data, indent=2, ensure_ascii=False))
        f.write("\n")
    
    print(f"\n✅ Saved {len(all_predictions)} predictions to: {output_file}")
    print(f"📊 Total bets: {total_predictions}")
    print(f"📅 Date range: {start_date.date()} → {end_date.date()}")
    print(f"📈 Completed: {completed} | Pending: {pending}")
    if completed > 0:
        print(f"🎯 Win Rate: {win_rate:.1f}% ({won} wins / {lost} losses)")
        if win_rate >= 85:
            print(f"   ✅ EXCELLENT - Exceeds expectations!")
        elif win_rate >= 70:
            print(f"   ✅ GOOD - Within expected range")
        else:
            print(f"   ⚠️  WARNING - Below expected performance")


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Save future betting predictions to a file')
    parser.add_argument('--start-date', type=str, required=True,
                       help='Start date (YYYY-MM-DD format)')
    parser.add_argument('--end-date', type=str, required=True,
                       help='End date (YYYY-MM-DD format, inclusive)')
    parser.add_argument('--output', type=str, default=None,
                       help='Output file path (default: predictions_YYYYMMDD_YYYYMMDD.txt)')
    
    args = parser.parse_args()
    
    # Parse dates
    try:
        start_date = datetime.strptime(args.start_date, '%Y-%m-%d')
        end_date = datetime.strptime(args.end_date, '%Y-%m-%d')
        end_date = end_date.replace(hour=23, minute=59, second=59)
    except ValueError:
        print(f"❌ Invalid date format. Use YYYY-MM-DD")
        sys.exit(1)
    
    # Validate date range
    if end_date < start_date:
        print(f"❌ End date must be after start date")
        sys.exit(1)
    
    # Create Predictions_results directory if it doesn't exist
    predictions_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'Predictions_results')
    os.makedirs(predictions_dir, exist_ok=True)
    
    # Generate output filename if not provided
    if args.output is None:
        # Format: predictions_YYYY-MM-DD_to_YYYY-MM-DD_generated_TIMESTAMP.txt
        # Example: predictions_2025-11-16_to_2025-11-24_generated_20251117_221530.txt
        start_str = start_date.strftime('%Y-%m-%d')
        end_str = end_date.strftime('%Y-%m-%d')
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"predictions_{start_str}_to_{end_str}_generated_{timestamp}.txt"
        args.output = os.path.join(predictions_dir, filename)
    else:
        # If user provides a filename, still save it in Predictions_results directory
        # unless they provided an absolute path
        if not os.path.isabs(args.output):
            args.output = os.path.join(predictions_dir, args.output)
    
    # Generate predictions
    try:
        save_predictions_to_file(start_date, end_date, args.output)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
