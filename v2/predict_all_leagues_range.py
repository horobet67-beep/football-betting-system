"""
Generate predictions for all leagues within a specific date range.
Consolidates predictions across Serie A, Bundesliga, La Liga, Premier League, and Romania.
Automatically saves output to Predictions_results directory.
"""

from datetime import datetime, timedelta
from typing import List, Dict, Optional
import sys
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


class OutputCapture:
    """Captures print output to both console and file"""
    def __init__(self, filepath):
        self.filepath = filepath
        self.terminal = sys.stdout
        self.log = None
        
    def __enter__(self):
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(self.filepath), exist_ok=True)
        self.log = open(self.filepath, 'w', encoding='utf-8')
        return self
    
    def write(self, message):
        self.terminal.write(message)
        if self.log:
            self.log.write(message)
    
    def flush(self):
        self.terminal.flush()
        if self.log:
            self.log.flush()
    
    def __exit__(self, *args):
        if self.log:
            self.log.close()


def predict_all_leagues(start_date: datetime, end_date: datetime):
    """
    Generate predictions for all leagues within date range.
    
    Args:
        start_date: Start of prediction window
        end_date: End of prediction window (inclusive)
    """
    print("\n" + "="*100)
    print(f"🌍 MULTI-LEAGUE PREDICTION SYSTEM")
    print("="*100)
    print(f"📅 Date Range: {start_date.date()} → {end_date.date()} (inclusive)")
    print("="*100)
    
    all_predictions = []
    
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
    
    # Process each league
    for league_config in leagues:
        print(f"\n{'='*100}")
        print(f"{league_config['emoji']} {league_config['name']}")
        print("="*100)
        
        try:
            # Initialize predictor
            print(f"Loading {league_config['name']} predictor...")
            predictor = league_config['predictor_class']()
            latest_historical = predictor.data['Date'].max()
            
            print(f"✅ Historical data up to: {latest_historical.date()}")
            print(f"⚙️  Weights: {league_config['weights']}")
            print(f"📊 Optimization WR: {league_config['backtest_wr']:.1f}% ({league_config['patterns_tested']} patterns)")
            
            # Load future matches
            all_data = league_config['adapter_func'](include_future=True)
            
            # Filter by date range
            upcoming = all_data[
                (all_data['Date'] >= start_date) & 
                (all_data['Date'] <= end_date)
            ].sort_values('Date')
            
            print(f"\n🔮 Found {len(upcoming)} upcoming matches")
            
            if len(upcoming) == 0:
                print(f"   ⚠️  No matches in this date range")
                continue
            
            # Generate predictions
            league_bets = []
            league_no_bets = []
            
            for idx, match in upcoming.iterrows():
                try:
                    # Try different predictor interfaces
                    prediction = None
                    
                    # Method 1: Simple predictors (Serie A, Premier League, Romania)
                    if hasattr(predictor, 'predict_match') and 'historical_data' not in predictor.predict_match.__code__.co_varnames:
                        prediction = predictor.predict_match(
                            home_team=match['HomeTeam'],
                            away_team=match['AwayTeam'],
                            match_date=latest_historical
                        )
                    # Method 2: Bundesliga/La Liga style (need historical_data)
                    elif hasattr(predictor, 'predict_match_simple'):
                        prediction = predictor.predict_match_simple(
                            home_team=match['HomeTeam'],
                            away_team=match['AwayTeam'],
                            match_date=latest_historical
                        )
                    # Method 3: Romanian style (pass historical_data)
                    elif hasattr(predictor, 'predict_match'):
                        prediction = predictor.predict_match(
                            home_team=match['HomeTeam'],
                            away_team=match['AwayTeam'],
                            historical_data=predictor.data,
                            match_date=latest_historical
                        )
                    
                    match_data = {
                        'league': league_config['name'],
                        'league_emoji': league_config['emoji'],
                        'date': match['Date'],
                        'home': match['HomeTeam'],
                        'away': match['AwayTeam'],
                        'backtest_wr': league_config['backtest_wr']
                    }
                    
                    # Handle different prediction return types
                    if prediction:
                        # Extract attributes safely (handles both BestBet and SimpleBettingRecommendation)
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
                        
                        if risk_adj and confidence and threshold and pattern_name:
                            if risk_adj >= threshold:
                                match_data.update({
                                    'pattern': pattern_name,
                                    'confidence': confidence,
                                    'risk_adj': risk_adj,
                                    'threshold': threshold,
                                    'margin': risk_adj - threshold,
                                    'has_bet': True
                                })
                                league_bets.append(match_data)
                                all_predictions.append(match_data)
                            else:
                                match_data.update({
                                    'has_bet': False,
                                    'reason': 'Below threshold'
                                })
                                league_no_bets.append(match_data)
                        else:
                            match_data.update({
                                'has_bet': False,
                                'reason': 'No valid prediction data'
                            })
                            league_no_bets.append(match_data)
                    else:
                        match_data.update({
                            'has_bet': False,
                            'reason': 'No pattern meets threshold'
                        })
                        league_no_bets.append(match_data)
                        
                except Exception as e:
                    print(f"   ⚠️  Error predicting {match['HomeTeam']} vs {match['AwayTeam']}: {e}")
                    import traceback
                    traceback.print_exc()
                    continue
            
            # Display league summary
            print(f"\n   ✅ BET Recommendations: {len(league_bets)}")
            print(f"   ❌ NO BET: {len(league_no_bets)}")
            
            if league_bets:
                avg_conf = sum(b['risk_adj'] for b in league_bets) / len(league_bets)
                print(f"   📈 Average Confidence: {avg_conf:.1%}")
            
        except Exception as e:
            print(f"❌ Error processing {league_config['name']}: {e}")
            import traceback
            traceback.print_exc()
            continue
    
    # Generate consolidated report
    print(f"\n{'='*100}")
    print("📊 CONSOLIDATED REPORT")
    print("="*100)
    
    if not all_predictions:
        print("\n⚠️  No betting opportunities found across all leagues")
        return
    
    # Sort by date, then by confidence
    all_predictions.sort(key=lambda x: (x['date'], -x['risk_adj']))
    
    print(f"\n✅ Total Betting Opportunities: {len(all_predictions)}")
    print(f"📅 Date Range: {start_date.date()} → {end_date.date()}")
    
    # Group by date
    from collections import defaultdict
    by_date = defaultdict(list)
    for pred in all_predictions:
        date_key = pred['date'].date()
        by_date[date_key].append(pred)
    
    # Display by date
    print(f"\n{'='*100}")
    print("🗓️  PREDICTIONS BY DATE")
    print("="*100)
    
    for date_key in sorted(by_date.keys()):
        matches = by_date[date_key]
        print(f"\n📅 {date_key.strftime('%A, %B %d, %Y')} ({len(matches)} bets)")
        print("-"*100)
        
        for i, pred in enumerate(matches, 1):
            print(f"\n{i}. {pred['league_emoji']} {pred['league']} | {pred['date'].strftime('%H:%M')} | {pred['home']} vs {pred['away']}")
            print(f"   🎯 Pattern: {pred['pattern']}")
            print(f"   📊 Confidence: {pred['confidence']:.1%} → Risk-Adj: {pred['risk_adj']:.1%}")
            print(f"   🚧 Threshold: {pred['threshold']:.1%} | Margin: +{pred['margin']*100:.1f}%")
            print(f"   📈 League Backtest: {pred['backtest_wr']:.1f}% WR")
    
    # Summary statistics
    print(f"\n{'='*100}")
    print("📊 SUMMARY STATISTICS")
    print("="*100)
    
    # By league
    print(f"\n🌍 By League:")
    league_counts = defaultdict(int)
    league_conf = defaultdict(list)
    
    for pred in all_predictions:
        league_counts[pred['league']] += 1
        league_conf[pred['league']].append(pred['risk_adj'])
    
    for league in sorted(league_counts.keys()):
        avg = sum(league_conf[league]) / len(league_conf[league])
        print(f"   {league}: {league_counts[league]} bets (avg conf: {avg:.1%})")
    
    # By pattern
    print(f"\n🎯 By Pattern:")
    pattern_counts = defaultdict(int)
    for pred in all_predictions:
        pattern_counts[pred['pattern']] += 1
    
    for pattern, count in sorted(pattern_counts.items(), key=lambda x: -x[1])[:10]:
        print(f"   {pattern}: {count} bets")
    
    # Risk warnings
    print(f"\n{'='*100}")
    print("⚠️  CRITICAL REMINDERS")
    print("="*100)
    print(f"• Total Predictions: {len(all_predictions)} bets across 5 leagues")
    print(f"• Date Range: {(end_date - start_date).days + 1} days")
    print(f"• NO forward validation yet - these are based on backtesting only")
    print(f"• STRONGLY RECOMMENDED: Paper trade first (no real money)")
    print(f"• If betting: Max €1-2 per bet, never exceed 2% of bankroll")
    print(f"• Watch for correlation - same patterns across leagues may fail together")
    print(f"• Stop after 3 consecutive losses")
    print(f"• Track ALL results to validate system performance")
    print("="*100 + "\n")


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Predict matches across all leagues for date range')
    parser.add_argument('--start-date', type=str, required=True,
                       help='Start date (YYYY-MM-DD format)')
    parser.add_argument('--end-date', type=str, required=True,
                       help='End date (YYYY-MM-DD format, inclusive)')
    
    args = parser.parse_args()
    
    # Parse dates
    try:
        start_date = datetime.strptime(args.start_date, '%Y-%m-%d')
        end_date = datetime.strptime(args.end_date, '%Y-%m-%d')
        # Include entire end day
        end_date = end_date.replace(hour=23, minute=59, second=59)
    except ValueError:
        print(f"❌ Invalid date format. Use YYYY-MM-DD")
        sys.exit(1)
    
    # Validate date range
    if end_date < start_date:
        print(f"❌ End date must be after start date")
        sys.exit(1)
    
    if (end_date - start_date).days > 30:
        print(f"⚠️  Warning: Large date range ({(end_date - start_date).days} days)")
        print(f"   This may take several minutes to process...")
    
    # Generate output filename
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    start_str = start_date.strftime('%Y-%m-%d')
    end_str = end_date.strftime('%Y-%m-%d')
    output_file = f"Predictions_results/predictions_{start_str}_to_{end_str}_generated_{timestamp}.txt"
    
    # Generate predictions with output capture
    try:
        with OutputCapture(output_file) as output:
            sys.stdout = output
            predict_all_leagues(start_date, end_date)
            sys.stdout = output.terminal
        
        print(f"\n✅ Predictions saved to: {output_file}")
        
    except Exception as e:
        sys.stdout = sys.__stdout__  # Restore stdout on error
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
