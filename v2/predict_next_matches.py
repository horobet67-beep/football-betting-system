#!/usr/bin/env python3
"""
Romanian Liga I Next Match Predictor

CLI tool to predict betting opportunities for upcoming Romanian Liga I matches.
Uses optimized confidence thresholds to recommend only high-value bets.

Usage:
    python predict_next_matches.py --upcoming fixtures.csv --historical historical.csv
    python predict_next_matches.py --demo  # Run with sample data
"""

import argparse
import pandas as pd
import sys
import os
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from predictor.romanian_predictor import RomanianMatchPredictor, create_sample_upcoming_matches
from data.ingest import load_match_data


def load_upcoming_matches(file_path: str) -> pd.DataFrame:
    """Load upcoming matches from CSV file"""
    try:
        upcoming = pd.read_csv(file_path)
        
        # Ensure required columns exist
        required_cols = ['HomeTeam', 'AwayTeam']
        missing_cols = [col for col in required_cols if col not in upcoming.columns]
        
        if missing_cols:
            raise ValueError(f"Missing required columns: {missing_cols}")
        
        # Add default date if not present
        if 'Date' not in upcoming.columns:
            upcoming['Date'] = pd.Timestamp.now().strftime('%Y-%m-%d')
        
        # Convert date column
        upcoming['Date'] = pd.to_datetime(upcoming['Date'])
        
        return upcoming
        
    except Exception as e:
        print(f"❌ Error loading upcoming matches: {e}")
        sys.exit(1)


def main():
    """Main CLI function"""
    parser = argparse.ArgumentParser(
        description='Predict betting opportunities for Romanian Liga I matches',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Use custom data files
    python predict_next_matches.py --upcoming next_round.csv --historical season_data.csv
    
    # Run demo with sample data
    python predict_next_matches.py --demo
    
    # Show only recommended bets
    python predict_next_matches.py --demo --bets-only
        """
    )
    
    parser.add_argument(
        '--upcoming', 
        type=str,
        help='CSV file with upcoming matches (HomeTeam, AwayTeam, Date)'
    )
    
    parser.add_argument(
        '--historical', 
        type=str,
        help='CSV file with historical match data for training'
    )
    
    parser.add_argument(
        '--demo', 
        action='store_true',
        help='Run demonstration with sample data'
    )
    
    parser.add_argument(
        '--bets-only',
        action='store_true',
        help='Show only matches with betting recommendations'
    )
    
    parser.add_argument(
        '--min-confidence',
        type=float,
        default=0.0,
        help='Minimum confidence threshold override (0.0-1.0)'
    )
    
    parser.add_argument(
        '--min-ev',
        type=float,
        default=0.05,
        help='Minimum expected value threshold (default: 5%)'
    )
    
    args = parser.parse_args()
    
    print("🏆 ROMANIAN LIGA I - NEXT MATCH PREDICTOR")
    print("=" * 50)
    
    # Initialize predictor
    print("⚙️  Initializing predictor with optimized thresholds...")
    predictor = RomanianMatchPredictor()
    
    # Override thresholds if specified
    if args.min_confidence > 0:
        print(f"📊 Overriding confidence thresholds to {args.min_confidence:.1%}")
        for pattern in predictor.confidence_thresholds:
            predictor.confidence_thresholds[pattern] = args.min_confidence
    
    # Load data
    if args.demo:
        print("📁 Loading demonstration data...")
        upcoming_matches = create_sample_upcoming_matches()
        
        # Load sample historical data
        try:
            # Try to load Romanian Liga I data from available CSV files
            historical_data = load_match_data('data/liga1-romania', 'romania')
            print(f"✅ Loaded {len(historical_data)} historical matches")
        except Exception as e:
            print(f"⚠️  Could not load real historical data, creating sample data: {e}")
            # Create sample historical data
            import numpy as np
            np.random.seed(42)
            teams = upcoming_matches['HomeTeam'].tolist() + upcoming_matches['AwayTeam'].tolist()
            teams = list(set(teams))
            
            sample_matches = []
            for i in range(200):  # 200 sample matches
                home = np.random.choice(teams)
                away = np.random.choice([t for t in teams if t != home])
                
                # Romanian Liga I typical stats
                fthg = np.random.poisson(1.3)
                ftag = np.random.poisson(1.0)
                
                match = {
                    'Date': pd.Timestamp.now() - pd.Timedelta(days=np.random.randint(1, 365)),
                    'HomeTeam': home,
                    'AwayTeam': away,
                    'FTHG': fthg,
                    'FTAG': ftag,
                    'FTR': 'H' if fthg > ftag else ('A' if ftag > fthg else 'D'),
                    'HC': np.random.poisson(5),
                    'AC': np.random.poisson(4),
                    'HY': np.random.poisson(2),
                    'AY': np.random.poisson(2),
                    'HR': np.random.poisson(0.1),
                    'AR': np.random.poisson(0.1),
                    'HS': np.random.poisson(12),
                    'AS': np.random.poisson(10)
                }
                sample_matches.append(match)
            
            historical_data = pd.DataFrame(sample_matches)
            historical_data['Date'] = pd.to_datetime(historical_data['Date'])
            
    else:
        # Load from files
        if not args.upcoming or not args.historical:
            print("❌ Error: --upcoming and --historical files required (or use --demo)")
            parser.print_help()
            sys.exit(1)
        
        print(f"📁 Loading upcoming matches from {args.upcoming}...")
        upcoming_matches = load_upcoming_matches(args.upcoming)
        
        print(f"📁 Loading historical data from {args.historical}...")
        try:
            historical_data = pd.read_csv(args.historical)
            historical_data['Date'] = pd.to_datetime(historical_data['Date'])
        except Exception as e:
            print(f"❌ Error loading historical data: {e}")
            sys.exit(1)
    
    print(f"✅ Loaded {len(upcoming_matches)} upcoming matches")
    print(f"✅ Loaded {len(historical_data)} historical matches")
    print()
    
    # Generate predictions
    print("🔮 Analyzing matches and generating predictions...")
    predictions = predictor.predict_next_matches(upcoming_matches, historical_data)
    
    # Filter for bets only if requested
    if args.bets_only:
        predictions = [p for p in predictions if p.best_bet is not None]
        if not predictions:
            print("❌ No betting opportunities found with current thresholds")
            sys.exit(0)
    
    # Apply additional filters
    if args.min_ev > 0:
        filtered_predictions = []
        for p in predictions:
            if p.best_bet and p.best_bet.expected_value >= args.min_ev:
                filtered_predictions.append(p)
            elif not p.best_bet:
                filtered_predictions.append(p)  # Keep "no bet" matches if not --bets-only
        predictions = filtered_predictions
    
    # Generate and display report
    report = predictor.format_predictions_report(predictions)
    print(report)
    
    # Summary statistics
    print("\n" + "=" * 65)
    print("📊 PREDICTION SUMMARY")
    print("=" * 65)
    
    total_matches = len(predictions)
    bet_matches = len([p for p in predictions if p.best_bet])
    
    if bet_matches > 0:
        best_bets = [p.best_bet for p in predictions if p.best_bet]
        avg_confidence = sum(bet.confidence for bet in best_bets) / len(best_bets)
        avg_ev = sum(bet.expected_value for bet in best_bets) / len(best_bets)
        
        print(f"🎯 Betting opportunities: {bet_matches}/{total_matches} matches ({bet_matches/total_matches*100:.1f}%)")
        print(f"📊 Average confidence: {avg_confidence:.1%}")
        print(f"📈 Average expected value: {avg_ev:+.2%}")
        
        # Risk assessment
        if avg_ev > 0.10:
            risk_level = "🟢 LOW RISK - Excellent opportunities"
        elif avg_ev > 0.05:
            risk_level = "🟡 MODERATE RISK - Good opportunities"  
        else:
            risk_level = "🔴 HIGH RISK - Marginal opportunities"
        
        print(f"⚖️  Risk assessment: {risk_level}")
        
    else:
        print("❌ No betting opportunities found")
        print("💡 Consider lowering confidence thresholds or waiting for better fixtures")
    
    print("\n🏆 Analysis complete! Good luck with your betting! ⚽")


if __name__ == '__main__':
    main()