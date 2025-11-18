"""
Premier League Advanced Improvement Analysis
Look for ensemble patterns, team clustering, and confidence calibration.
"""

import pandas as pd
import numpy as np
from datetime import datetime
from simple_premier_league_predictor import SimplePremierLeaguePredictor
from data.premier_league_adapter import load_premier_league_data


def analyze_confidence_calibration():
    """Analyze if confidence scores are well-calibrated (predicted vs actual)."""
    
    print("="*80)
    print("PREMIER LEAGUE CONFIDENCE CALIBRATION ANALYSIS")
    print("="*80)
    
    df = load_premier_league_data()
    season_df = df[df['season'] == '2024-2025'].copy()
    
    # Prepare data
    season_df['FTR'] = season_df.apply(
        lambda row: 'H' if row['home_goals'] > row['away_goals'] 
                    else ('A' if row['away_goals'] > row['home_goals'] else 'D'),
        axis=1
    )
    season_df = season_df.rename(columns={
        'home_goals': 'FTHG', 'away_goals': 'FTAG',
        'home_corners': 'HC', 'away_corners': 'AC',
        'home_yellows': 'HY', 'away_yellows': 'AY',
        'home_reds': 'HR', 'away_reds': 'AR'
    })
    
    predictor = SimplePremierLeaguePredictor(lookback_days=60)
    
    # Collect predictions with confidence scores
    confidence_buckets = {
        '55-60%': {'total': 0, 'correct': 0},
        '60-65%': {'total': 0, 'correct': 0},
        '65-70%': {'total': 0, 'correct': 0},
        '70-75%': {'total': 0, 'correct': 0},
        '75-80%': {'total': 0, 'correct': 0},
        '80-85%': {'total': 0, 'correct': 0},
        '85-90%': {'total': 0, 'correct': 0},
        '90-95%': {'total': 0, 'correct': 0},
        '95-100%': {'total': 0, 'correct': 0},
    }
    
    for _, match in season_df.iterrows():
        predictions = predictor.predict_match(
            match['home_team'], match['away_team'], match['date'], verbose=False
        )
        
        for pred in predictions:
            pattern_func = predictor.filtered_patterns[pred['pattern']]['func']
            actual = pattern_func(match)
            confidence = pred['confidence']
            
            # Bucket by confidence
            if confidence >= 0.95:
                bucket = '95-100%'
            elif confidence >= 0.90:
                bucket = '90-95%'
            elif confidence >= 0.85:
                bucket = '85-90%'
            elif confidence >= 0.80:
                bucket = '80-85%'
            elif confidence >= 0.75:
                bucket = '75-80%'
            elif confidence >= 0.70:
                bucket = '70-75%'
            elif confidence >= 0.65:
                bucket = '65-70%'
            elif confidence >= 0.60:
                bucket = '60-65%'
            else:
                bucket = '55-60%'
            
            confidence_buckets[bucket]['total'] += 1
            if actual:
                confidence_buckets[bucket]['correct'] += 1
    
    print("\nCONFIDENCE CALIBRATION:")
    print("-"*80)
    print(f"{'Confidence Range':<20} {'Predictions':<15} {'Actual WR':<15} {'Expected WR':<15} {'Calibration':<15}")
    print("-"*80)
    
    for bucket, stats in confidence_buckets.items():
        if stats['total'] > 0:
            actual_wr = stats['correct'] / stats['total']
            expected_wr = float(bucket.split('-')[0].replace('%', '')) / 100
            calibration = actual_wr - expected_wr
            
            calibration_status = "✅ Good" if abs(calibration) < 0.05 else ("⚠️ Over-confident" if calibration < -0.05 else "⚠️ Under-confident")
            
            print(f"{bucket:<20} {stats['total']:<15} {actual_wr:>13.1%} {expected_wr:>13.1%} {calibration:>+13.1%} {calibration_status}")


def analyze_pattern_combinations():
    """Find patterns that often fire together (ensemble opportunities)."""
    
    print("\n" + "="*80)
    print("PATTERN COMBINATION ANALYSIS")
    print("="*80)
    
    df = load_premier_league_data()
    season_df = df[df['season'] == '2024-2025'].copy()
    
    # Prepare data
    season_df['FTR'] = season_df.apply(
        lambda row: 'H' if row['home_goals'] > row['away_goals'] 
                    else ('A' if row['away_goals'] > row['home_goals'] else 'D'),
        axis=1
    )
    season_df = season_df.rename(columns={
        'home_goals': 'FTHG', 'away_goals': 'FTAG',
        'home_corners': 'HC', 'away_corners': 'AC',
        'home_yellows': 'HY', 'away_yellows': 'AY',
        'home_reds': 'HR', 'away_reds': 'AR'
    })
    
    predictor = SimplePremierLeaguePredictor(lookback_days=60)
    
    # Track which patterns fire together
    match_patterns = []
    
    for _, match in season_df.iterrows():
        predictions = predictor.predict_match(
            match['home_team'], match['away_team'], match['date'], verbose=False
        )
        
        if predictions:
            fired_patterns = [p['pattern'] for p in predictions]
            match_patterns.append({
                'patterns': fired_patterns,
                'count': len(fired_patterns)
            })
    
    # Find common combinations
    print("\nMATCHES WITH MULTIPLE PATTERNS:")
    print("-"*80)
    
    pattern_counts = [m['count'] for m in match_patterns if m['count'] > 0]
    if pattern_counts:
        print(f"Avg patterns per match: {np.mean(pattern_counts):.1f}")
        print(f"Max patterns in one match: {max(pattern_counts)}")
        print(f"Matches with 10+ patterns: {sum(1 for c in pattern_counts if c >= 10)}")
        print(f"Matches with 5-9 patterns: {sum(1 for c in pattern_counts if 5 <= c < 10)}")
        print(f"Matches with 1-4 patterns: {sum(1 for c in pattern_counts if 1 <= c < 5)}")


def analyze_team_specialties():
    """Identify teams with specific pattern tendencies."""
    
    print("\n" + "="*80)
    print("TEAM SPECIALTY ANALYSIS")
    print("="*80)
    
    df = load_premier_league_data()
    season_df = df[df['season'] == '2024-2025'].copy()
    
    # Prepare data
    season_df['FTR'] = season_df.apply(
        lambda row: 'H' if row['home_goals'] > row['away_goals'] 
                    else ('A' if row['away_goals'] > row['home_goals'] else 'D'),
        axis=1
    )
    season_df = season_df.rename(columns={
        'home_goals': 'FTHG', 'away_goals': 'FTAG',
        'home_corners': 'HC', 'away_corners': 'AC',
        'home_yellows': 'HY', 'away_yellows': 'AY',
        'home_reds': 'HR', 'away_reds': 'AR'
    })
    
    # Calculate team stats
    team_stats = {}
    
    for team in set(season_df['home_team'].unique()) | set(season_df['away_team'].unique()):
        home_matches = season_df[season_df['home_team'] == team]
        away_matches = season_df[season_df['away_team'] == team]
        
        team_stats[team] = {
            'avg_home_corners': home_matches['HC'].mean() if len(home_matches) > 0 else 0,
            'avg_away_corners': away_matches['AC'].mean() if len(away_matches) > 0 else 0,
            'avg_home_cards': (home_matches['HY'] + home_matches['HR']).mean() if len(home_matches) > 0 else 0,
            'avg_away_cards': (away_matches['AY'] + away_matches['AR']).mean() if len(away_matches) > 0 else 0,
            'avg_home_goals': home_matches['FTHG'].mean() if len(home_matches) > 0 else 0,
            'avg_away_goals': away_matches['FTAG'].mean() if len(away_matches) > 0 else 0,
            'total_corners': (home_matches['HC'].sum() + home_matches['AC'].sum() + 
                            away_matches['HC'].sum() + away_matches['AC'].sum()) / 
                           (len(home_matches) + len(away_matches)) if (len(home_matches) + len(away_matches)) > 0 else 0
        }
    
    print("\nTOP 10 HIGH CORNER TEAMS (Total corners per match):")
    print("-"*80)
    print(f"{'Team':<25} {'Avg Total Corners':<20} {'Home Corners':<15} {'Away Corners':<15}")
    print("-"*80)
    
    sorted_teams = sorted(team_stats.items(), key=lambda x: x[1]['total_corners'], reverse=True)
    for team, stats in sorted_teams[:10]:
        print(f"{team:<25} {stats['total_corners']:>18.1f} {stats['avg_home_corners']:>13.1f} {stats['avg_away_corners']:>13.1f}")
    
    print("\nTOP 10 HIGH CARD TEAMS (Cards per match):")
    print("-"*80)
    print(f"{'Team':<25} {'Home Cards':<15} {'Away Cards':<15}")
    print("-"*80)
    
    sorted_teams = sorted(team_stats.items(), key=lambda x: x[1]['avg_home_cards'] + x[1]['avg_away_cards'], reverse=True)
    for team, stats in sorted_teams[:10]:
        print(f"{team:<25} {stats['avg_home_cards']:>13.1f} {stats['avg_away_cards']:>13.1f}")
    
    print("\nTOP 10 LOW CORNER TEAMS (avoid for corner bets):")
    print("-"*80)
    print(f"{'Team':<25} {'Avg Total Corners':<20}")
    print("-"*80)
    
    sorted_teams = sorted(team_stats.items(), key=lambda x: x[1]['total_corners'])
    for team, stats in sorted_teams[:10]:
        print(f"{team:<25} {stats['total_corners']:>18.1f}")


def analyze_lookback_sensitivity():
    """Test if different lookback periods would improve results."""
    
    print("\n" + "="*80)
    print("LOOKBACK PERIOD SENSITIVITY ANALYSIS")
    print("="*80)
    
    df = load_premier_league_data()
    test_df = df[(df['date'] >= '2025-09-01') & (df['date'] < '2025-10-10')].copy()
    
    # Prepare data
    test_df['FTR'] = test_df.apply(
        lambda row: 'H' if row['home_goals'] > row['away_goals'] 
                    else ('A' if row['away_goals'] > row['home_goals'] else 'D'),
        axis=1
    )
    test_df = test_df.rename(columns={
        'home_goals': 'FTHG', 'away_goals': 'FTAG',
        'home_corners': 'HC', 'away_corners': 'AC',
        'home_yellows': 'HY', 'away_yellows': 'AY',
        'home_reds': 'HR', 'away_reds': 'AR'
    })
    
    print(f"\nTest matches: {len(test_df)}")
    print(f"Period: {test_df['date'].min().strftime('%Y-%m-%d')} to {test_df['date'].max().strftime('%Y-%m-%d')}")
    print("\nTesting lookback periods: 14, 21, 30, 45, 60, 90 days")
    print("-"*80)
    print(f"{'Lookback':<12} {'Predictions':<15} {'Win Rate':<15} {'Profit':<15}")
    print("-"*80)
    
    results = []
    for lookback in [14, 21, 30, 45, 60, 90]:
        predictor = SimplePremierLeaguePredictor(lookback_days=lookback)
        
        total = 0
        correct = 0
        profit = 0.0
        
        for _, match in test_df.iterrows():
            predictions = predictor.predict_match(
                match['home_team'], match['away_team'], match['date'], verbose=False
            )
            
            for pred in predictions:
                pattern_func = predictor.filtered_patterns[pred['pattern']]['func']
                actual = pattern_func(match)
                
                total += 1
                if actual:
                    correct += 1
                    profit += 1.0
                else:
                    profit -= 1.0
        
        wr = (correct / total * 100) if total > 0 else 0
        results.append({'lookback': lookback, 'total': total, 'wr': wr, 'profit': profit})
        
        print(f"{lookback} days{'':<5} {total:<15} {wr:>13.1f}% {profit:>+13.1f}")
    
    best = max(results, key=lambda x: x['profit'])
    print(f"\n✅ Best lookback: {best['lookback']} days ({best['wr']:.1f}% WR, {best['profit']:+.1f} units)")


if __name__ == "__main__":
    analyze_confidence_calibration()
    analyze_pattern_combinations()
    analyze_team_specialties()
    analyze_lookback_sensitivity()
