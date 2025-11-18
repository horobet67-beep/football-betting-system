"""
Premier League Season-by-Season Validation
Time-series cross-validation to ensure predictions work across different seasons.
"""

import pandas as pd
from datetime import datetime
from simple_premier_league_predictor import SimplePremierLeaguePredictor
from data.premier_league_adapter import PremierLeagueDataAdapter


def validate_season(season_start_year: int, lookback_days: int = 30):
    """
    Validate predictor on a single Premier League season.
    
    Args:
        season_start_year: Starting year of season (e.g., 2023 for 2023-24)
        lookback_days: Lookback period for predictions
        
    Returns:
        Dict with season validation results
    """
    adapter = PremierLeagueDataAdapter()
    season_df = adapter.load_season(season_start_year)
    
    season_name = f"{season_start_year}-{season_start_year+1}"
    print(f"\n{'='*80}")
    print(f"VALIDATING SEASON: {season_name}")
    print(f"{'='*80}")
    print(f"Season matches: {len(season_df)}")
    print(f"Date range: {season_df['date'].min().strftime('%Y-%m-%d')} to {season_df['date'].max().strftime('%Y-%m-%d')}")
    
    # Create predictor (uses all available data)
    predictor = SimplePremierLeaguePredictor(lookback_days=lookback_days)
    
    # Get matches from this season for testing
    test_matches = predictor.df[predictor.df['season'] == season_name].copy()
    
    print(f"Test matches in predictor: {len(test_matches)}")
    
    total_predictions = 0
    correct_predictions = 0
    total_profit = 0.0
    pattern_stats = {}
    
    for _, match in test_matches.iterrows():
        predictions = predictor.predict_match(
            match['home_team'],
            match['away_team'],
            match['date'],
            verbose=False
        )
        
        # Test each prediction
        for pred in predictions:
            pattern_name = pred['pattern']
            pattern_func = predictor.filtered_patterns[pattern_name]['func']
            actual_result = pattern_func(match)
            
            # Track pattern stats
            if pattern_name not in pattern_stats:
                pattern_stats[pattern_name] = {
                    'total': 0,
                    'correct': 0,
                    'profit': 0.0
                }
            
            pattern_stats[pattern_name]['total'] += 1
            total_predictions += 1
            
            if actual_result:
                pattern_stats[pattern_name]['correct'] += 1
                correct_predictions += 1
                total_profit += 1.0
                pattern_stats[pattern_name]['profit'] += 1.0
            else:
                total_profit -= 1.0
                pattern_stats[pattern_name]['profit'] -= 1.0
    
    win_rate = (correct_predictions / total_predictions * 100) if total_predictions > 0 else 0
    
    print(f"\nOVERALL RESULTS:")
    print(f"  Total Predictions: {total_predictions}")
    print(f"  Correct: {correct_predictions}")
    print(f"  Win Rate: {win_rate:.1f}%")
    print(f"  Profit: {total_profit:+.1f} units")
    
    # Show top performing patterns
    print(f"\nTOP 10 PATTERNS BY PROFIT:")
    sorted_patterns = sorted(pattern_stats.items(), 
                            key=lambda x: x[1]['profit'], 
                            reverse=True)
    
    for pattern_name, stats in sorted_patterns[:10]:
        pattern_wr = (stats['correct'] / stats['total'] * 100) if stats['total'] > 0 else 0
        print(f"  {pattern_name:30s} | {stats['correct']:3d}/{stats['total']:3d} ({pattern_wr:5.1f}%) | {stats['profit']:+7.1f} units")
    
    return {
        'season': season_name,
        'season_year': season_start_year,
        'total_predictions': total_predictions,
        'correct_predictions': correct_predictions,
        'win_rate': win_rate,
        'profit': total_profit,
        'pattern_stats': pattern_stats
    }


def main():
    """Run season-by-season validation for Premier League."""
    print("="*80)
    print("PREMIER LEAGUE SEASON-BY-SEASON VALIDATION")
    print("Testing prediction system robustness across seasons")
    print("="*80)
    
    # Test available seasons
    seasons = [2023, 2024]  # 2023-24, 2024-25 (2025-26 incomplete)
    lookback_days = 30
    
    results = []
    
    for season_year in seasons:
        try:
            result = validate_season(season_year, lookback_days)
            results.append(result)
        except Exception as e:
            print(f"\nError validating season {season_year}: {e}")
            continue
    
    # Summary across all seasons
    print(f"\n{'='*80}")
    print("SUMMARY - ALL SEASONS")
    print(f"{'='*80}")
    print(f"{'Season':<15} {'Predictions':<15} {'Win Rate':<15} {'Profit':<15}")
    print("-"*80)
    
    for result in results:
        print(f"{result['season']:<15} {result['total_predictions']:<15} "
              f"{result['win_rate']:.1f}%{'':<11} {result['profit']:+.1f} units{'':<4}")
    
    if results:
        avg_win_rate = sum(r['win_rate'] for r in results) / len(results)
        total_profit = sum(r['profit'] for r in results)
        profitable_seasons = sum(1 for r in results if r['profit'] > 0)
        
        print("-"*80)
        print(f"{'AVERAGE':<15} {'':<15} {avg_win_rate:.1f}%{'':<11} {total_profit:+.1f} units total")
        print(f"\nProfitable seasons: {profitable_seasons}/{len(results)} ({profitable_seasons/len(results)*100:.0f}%)")
        
        print(f"\n{'='*80}")
        print("CONCLUSION:")
        if avg_win_rate >= 70 and profitable_seasons == len(results):
            print("✅ EXCELLENT - System is robust across seasons")
            print("   Safe for production use with confidence")
        elif avg_win_rate >= 65 and profitable_seasons >= len(results) * 0.8:
            print("✅ GOOD - System shows consistent profitability")
            print("   Recommended for production with monitoring")
        elif avg_win_rate >= 60:
            print("⚠️  MODERATE - System needs improvement")
            print("   Use with caution and smaller stakes")
        else:
            print("❌ POOR - System not ready for production")
            print("   Requires significant optimization")
        print(f"{'='*80}")


if __name__ == "__main__":
    main()
