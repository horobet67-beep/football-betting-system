"""
Generate predictions for upcoming Serie A matches.
Clean implementation using the fixed adapter with include_future parameter.
"""

from simple_serie_a_predictor import SimpleSerieAPredictor
from data.serie_a_adapter import load_serie_a_data
from datetime import datetime, timedelta
import sys


def predict_serie_a_matches(start_date=None, end_date=None, days_ahead=7):
    """
    Generate predictions for upcoming Serie A matches.
    
    Args:
        start_date: datetime or None (default: today)
        end_date: datetime or None (default: start_date + days_ahead)
        days_ahead: int, how many days ahead to predict (default: 7)
    """
    # Initialize predictor (loads historical data only)
    print("\n" + "="*80)
    print("🔮 Serie A Upcoming Match Predictions")
    print("="*80)
    print("Loading historical data for training...")
    
    predictor = SimpleSerieAPredictor()
    latest_historical_date = predictor.data['Date'].max()
    
    print(f"✅ Loaded {len(predictor.data)} historical matches")
    print(f"📅 Training data up to: {latest_historical_date.date()}")
    print(f"⚙️  Using: BALANCED weights (20/20/20/15/15/10) - 91.4% WR")
    
    # Load all data including future matches
    print(f"\n{'='*80}")
    print("Loading upcoming fixtures...")
    all_data = load_serie_a_data(include_future=True)
    
    # Set date range
    if start_date is None:
        start_date = datetime.now()
    if end_date is None:
        end_date = start_date + timedelta(days=days_ahead)
    
    # Find upcoming matches in date range
    upcoming_matches = all_data[
        (all_data['Date'] >= start_date) & 
        (all_data['Date'] <= end_date)
    ].sort_values('Date')
    
    if len(upcoming_matches) == 0:
        print(f"\n⚠️ No matches found between {start_date.date()} and {end_date.date()}")
        return
    
    print(f"✅ Found {len(upcoming_matches)} upcoming matches")
    print(f"📅 Date Range: {start_date.date()} → {end_date.date()}")
    
    # Generate predictions
    print(f"\n{'='*80}")
    print("🎯 GENERATING PREDICTIONS")
    print("="*80)
    
    bet_recommendations = []
    no_bets = []
    
    for idx, match in upcoming_matches.iterrows():
        match_date_str = match['Date'].strftime('%b %d, %I:%M%p')
        match_info = f"{match_date_str} - {match['HomeTeam']} vs {match['AwayTeam']}"
        
        try:
            # Generate prediction using historical data
            prediction = predictor.predict_match(
                home_team=match['HomeTeam'],
                away_team=match['AwayTeam'],
                match_date=latest_historical_date  # Use latest historical date
            )
            
            if prediction and prediction.risk_adjusted_confidence >= prediction.threshold:
                bet_recommendations.append({
                    'date': match['Date'],
                    'match': match_info,
                    'home': match['HomeTeam'],
                    'away': match['AwayTeam'],
                    'pattern': prediction.pattern_name,
                    'confidence': prediction.confidence,
                    'risk_adj': prediction.risk_adjusted_confidence,
                    'threshold': prediction.threshold,
                    'margin': prediction.risk_adjusted_confidence - prediction.threshold
                })
            else:
                no_bets.append({
                    'match': match_info,
                    'reason': 'No pattern meets threshold' if not prediction 
                             else f'Below threshold ({prediction.risk_adjusted_confidence:.1%} < {prediction.threshold:.1%})'
                })
                
        except Exception as e:
            no_bets.append({
                'match': match_info,
                'reason': f'Error: {str(e)}'
            })
    
    # Display results
    print("\n" + "="*80)
    print("✅ BET RECOMMENDATIONS")
    print("="*80)
    
    if bet_recommendations:
        for i, bet in enumerate(bet_recommendations, 1):
            print(f"\n{i}. {bet['match']}")
            print(f"   🎯 Pattern: {bet['pattern']}")
            print(f"   📊 Raw Confidence: {bet['confidence']:.1%}")
            print(f"   🎲 Risk-Adjusted: {bet['risk_adj']:.1%}")
            print(f"   🚧 Threshold: {bet['threshold']:.1%}")
            print(f"   📈 Margin: +{bet['margin']*100:.1f}% above threshold")
            print(f"   ✅ RECOMMENDATION: **BET**")
    else:
        print("\n   No bets recommended for this period.")
    
    print("\n" + "="*80)
    print("❌ NO BET (Below Threshold)")
    print("="*80)
    
    if no_bets:
        for i, no_bet in enumerate(no_bets, 1):
            print(f"\n{i}. {no_bet['match']}")
            print(f"   ❌ Reason: {no_bet['reason']}")
    else:
        print("\n   All matches qualified for betting!")
    
    # Summary
    print("\n" + "="*80)
    print("📊 SUMMARY")
    print("="*80)
    print(f"Total Matches Analyzed: {len(upcoming_matches)}")
    print(f"✅ BET: {len(bet_recommendations)}")
    print(f"❌ NO BET: {len(no_bets)}")
    
    if bet_recommendations:
        avg_confidence = sum(b['risk_adj'] for b in bet_recommendations) / len(bet_recommendations)
        print(f"\n📈 Average Risk-Adjusted Confidence: {avg_confidence:.1%}")
        
        print(f"\n⚠️ CRITICAL REMINDERS:")
        print(f"   • These are based on BACKTESTED performance (91.4% WR)")
        print(f"   • NO forward validation yet - paper trade first!")
        print(f"   • Start with €1-2 per bet maximum if testing")
        print(f"   • Never exceed 2% of bankroll per bet")
        print(f"   • Stop after 3 consecutive losses")
        print(f"   • Track all results for validation")
    
    print("="*80 + "\n")


def main():
    """Main entry point with command line arguments"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Predict upcoming Serie A matches')
    parser.add_argument('--days', type=int, default=7, 
                       help='Number of days ahead to predict (default: 7)')
    parser.add_argument('--start-date', type=str, 
                       help='Start date (YYYY-MM-DD format)')
    parser.add_argument('--end-date', type=str,
                       help='End date (YYYY-MM-DD format)')
    
    args = parser.parse_args()
    
    # Parse dates if provided
    start_date = None
    end_date = None
    
    if args.start_date:
        try:
            start_date = datetime.strptime(args.start_date, '%Y-%m-%d')
        except ValueError:
            print(f"❌ Invalid start date format. Use YYYY-MM-DD")
            sys.exit(1)
    
    if args.end_date:
        try:
            end_date = datetime.strptime(args.end_date, '%Y-%m-%d')
            # Include entire end day
            end_date = end_date.replace(hour=23, minute=59, second=59)
        except ValueError:
            print(f"❌ Invalid end date format. Use YYYY-MM-DD")
            sys.exit(1)
    
    # Generate predictions
    try:
        predict_serie_a_matches(
            start_date=start_date,
            end_date=end_date,
            days_ahead=args.days
        )
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
