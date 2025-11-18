"""
Backtest all 5 leagues over the last 14 days to validate current performance.
"""

from datetime import datetime, timedelta
import pandas as pd
from collections import defaultdict

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


def backtest_league(league_name, predictor, all_data, days=14):
    """
    Backtest a single league over the last N days.
    
    Args:
        league_name: Name of the league
        predictor: Predictor instance
        all_data: Full dataset including recent matches
        days: Number of days to backtest
        
    Returns:
        Dictionary with results
    """
    print(f"\n{'='*100}")
    print(f"📊 {league_name}")
    print('='*100)
    
    # Get the latest date in historical data
    latest_date = predictor.data['Date'].max()
    cutoff_date = latest_date - timedelta(days=days)
    
    print(f"Latest historical: {latest_date.date()}")
    print(f"Backtesting from: {cutoff_date.date()} to {latest_date.date()}")
    
    # Get matches in the backtest period
    test_matches = all_data[
        (all_data['Date'] > cutoff_date) & 
        (all_data['Date'] <= latest_date)
    ].sort_values('Date')
    
    print(f"Found {len(test_matches)} matches to test")
    
    if len(test_matches) == 0:
        print("⚠️  No matches in backtest period")
        return None
    
    # Results tracking
    predictions = []
    correct = 0
    total = 0
    by_pattern = defaultdict(lambda: {'correct': 0, 'total': 0})
    
    # Test each match
    for idx, match in test_matches.iterrows():
        # Get historical data up to (but not including) this match
        historical = predictor.data[predictor.data['Date'] < match['Date']]
        
        if len(historical) < 30:
            continue
        
        try:
            # Get prediction
            prediction = None
            
            # Try different predictor interfaces
            if hasattr(predictor, 'predict_match') and 'historical_data' not in predictor.predict_match.__code__.co_varnames:
                prediction = predictor.predict_match(
                    home_team=match['HomeTeam'],
                    away_team=match['AwayTeam'],
                    match_date=historical['Date'].max()
                )
            elif hasattr(predictor, 'predict_match_simple'):
                # Update predictor's data temporarily
                old_data = predictor.data
                predictor.data = historical
                prediction = predictor.predict_match_simple(
                    home_team=match['HomeTeam'],
                    away_team=match['AwayTeam'],
                    match_date=historical['Date'].max()
                )
                predictor.data = old_data
            elif hasattr(predictor, 'predict_match'):
                prediction = predictor.predict_match(
                    home_team=match['HomeTeam'],
                    away_team=match['AwayTeam'],
                    historical_data=historical,
                    match_date=historical['Date'].max()
                )
            
            if not prediction:
                continue
            
            # Extract prediction details
            risk_adj = getattr(prediction, 'risk_adjusted_confidence', None)
            threshold = getattr(prediction, 'threshold', None)
            pattern_name = getattr(prediction, 'pattern_name', None)
            
            # Handle dict returns (La Liga)
            if isinstance(prediction, dict):
                risk_adj = prediction.get('risk_adjusted_confidence')
                threshold = prediction.get('threshold')
                pattern_name = prediction.get('pattern_name')
            
            if not risk_adj or not threshold or not pattern_name:
                continue
            
            if risk_adj < threshold:
                continue
            
            # Check if prediction was correct
            from patterns.registry import get_pattern_registry
            registry = get_pattern_registry()
            pattern = registry.get_pattern(pattern_name)
            
            if pattern:
                actual_result = pattern.label_fn(match)
                is_correct = actual_result == True
                
                predictions.append({
                    'date': match['Date'],
                    'home': match['HomeTeam'],
                    'away': match['AwayTeam'],
                    'pattern': pattern_name,
                    'confidence': risk_adj,
                    'correct': is_correct
                })
                
                total += 1
                by_pattern[pattern_name]['total'] += 1
                
                if is_correct:
                    correct += 1
                    by_pattern[pattern_name]['correct'] += 1
        
        except Exception as e:
            continue
    
    # Calculate results
    if total == 0:
        print("⚠️  No valid predictions generated")
        return None
    
    win_rate = (correct / total) * 100
    
    print(f"\n📊 OVERALL RESULTS:")
    print(f"   Total Predictions: {total}")
    print(f"   Correct: {correct}")
    print(f"   Win Rate: {win_rate:.1f}%")
    
    # Pattern breakdown
    if by_pattern:
        print(f"\n🎯 BY PATTERN:")
        for pattern, stats in sorted(by_pattern.items(), key=lambda x: -x[1]['total']):
            pattern_wr = (stats['correct'] / stats['total']) * 100 if stats['total'] > 0 else 0
            print(f"   {pattern:35} {stats['correct']:3}/{stats['total']:3} = {pattern_wr:5.1f}%")
    
    return {
        'league': league_name,
        'total': total,
        'correct': correct,
        'win_rate': win_rate,
        'by_pattern': dict(by_pattern),
        'predictions': predictions
    }


def main():
    """Run backtest on all leagues"""
    
    print("\n" + "="*100)
    print("🎯 MULTI-LEAGUE 14-DAY BACKTEST")
    print("="*100)
    print(f"📅 Testing last 14 days of predictions")
    print("="*100)
    
    # League configurations
    leagues = [
        {
            'name': 'Serie A',
            'emoji': '🇮🇹',
            'predictor_class': SimpleSerieAPredictor,
            'adapter_func': load_serie_a_data,
            'backtest_wr': 91.4
        },
        {
            'name': 'Bundesliga',
            'emoji': '🇩🇪',
            'predictor_class': SimpleBundesligaPredictor,
            'adapter_func': load_bundesliga_data,
            'backtest_wr': 92.7
        },
        {
            'name': 'La Liga',
            'emoji': '🇪🇸',
            'predictor_class': SimpleLaLigaPredictor,
            'adapter_func': load_la_liga_data,
            'backtest_wr': 96.1
        },
        {
            'name': 'Premier League',
            'emoji': '🏴󠁧󠁢󠁥󠁮󠁧󠁿',
            'predictor_class': SimplePremierLeaguePredictor,
            'adapter_func': load_premier_league_data,
            'backtest_wr': 85.4
        },
        {
            'name': 'Romania Liga 1',
            'emoji': '🇷🇴',
            'predictor_class': SimpleRomanianPredictor,
            'adapter_func': load_romanian_data,
            'backtest_wr': 93.8
        }
    ]
    
    all_results = []
    
    # Test each league
    for league_config in leagues:
        try:
            # Initialize predictor
            print(f"\n📥 Loading {league_config['emoji']} {league_config['name']}...")
            predictor = league_config['predictor_class']()
            
            # Load all data (including recent)
            all_data = league_config['adapter_func'](include_future=False)
            
            # Run backtest
            result = backtest_league(
                f"{league_config['emoji']} {league_config['name']}", 
                predictor, 
                all_data,
                days=14
            )
            
            if result:
                result['expected_wr'] = league_config['backtest_wr']
                all_results.append(result)
        
        except Exception as e:
            print(f"❌ Error testing {league_config['name']}: {e}")
            import traceback
            traceback.print_exc()
            continue
    
    # Consolidated results
    print("\n" + "="*100)
    print("📊 CONSOLIDATED 14-DAY BACKTEST RESULTS")
    print("="*100)
    
    if not all_results:
        print("❌ No results to display")
        return
    
    total_preds = sum(r['total'] for r in all_results)
    total_correct = sum(r['correct'] for r in all_results)
    overall_wr = (total_correct / total_preds * 100) if total_preds > 0 else 0
    
    print(f"\n🌍 OVERALL PERFORMANCE:")
    print(f"   Total Predictions: {total_preds}")
    print(f"   Correct: {total_correct}")
    print(f"   Win Rate: {overall_wr:.1f}%")
    
    print(f"\n📊 BY LEAGUE:")
    print(f"{'League':<25} {'Preds':<8} {'Correct':<8} {'Win Rate':<10} {'Expected':<10} {'Diff':<10}")
    print("-"*100)
    
    for result in sorted(all_results, key=lambda x: -x['win_rate']):
        diff = result['win_rate'] - result['expected_wr']
        diff_str = f"{diff:+.1f}%"
        print(f"{result['league']:<25} {result['total']:<8} {result['correct']:<8} {result['win_rate']:<9.1f}% {result['expected_wr']:<9.1f}% {diff_str:<10}")
    
    # Pattern analysis across all leagues
    print(f"\n🎯 TOP PATTERNS (Across All Leagues):")
    all_patterns = defaultdict(lambda: {'correct': 0, 'total': 0})
    
    for result in all_results:
        for pattern, stats in result['by_pattern'].items():
            all_patterns[pattern]['correct'] += stats['correct']
            all_patterns[pattern]['total'] += stats['total']
    
    # Sort by total predictions
    sorted_patterns = sorted(all_patterns.items(), key=lambda x: -x[1]['total'])[:15]
    
    print(f"{'Pattern':<35} {'Correct':<8} {'Total':<8} {'Win Rate':<10}")
    print("-"*100)
    for pattern, stats in sorted_patterns:
        pattern_wr = (stats['correct'] / stats['total']) * 100 if stats['total'] > 0 else 0
        print(f"{pattern:<35} {stats['correct']:<8} {stats['total']:<8} {pattern_wr:<9.1f}%")
    
    # Analysis
    print(f"\n" + "="*100)
    print("💡 ANALYSIS")
    print("="*100)
    
    if overall_wr >= 85:
        print("✅ EXCELLENT: System performing at 85%+ win rate")
    elif overall_wr >= 75:
        print("✅ GOOD: System performing at 75-85% win rate")
    elif overall_wr >= 65:
        print("⚠️  ACCEPTABLE: System performing at 65-75% win rate")
    else:
        print("❌ WARNING: System performing below 65% win rate")
    
    # Check each league
    print(f"\n📊 League-by-League Assessment:")
    for result in all_results:
        diff = result['win_rate'] - result['expected_wr']
        
        if diff >= -5:
            status = "✅ ON TARGET"
        elif diff >= -10:
            status = "⚠️  SLIGHTLY BELOW"
        else:
            status = "❌ SIGNIFICANTLY BELOW"
        
        print(f"   {result['league']:<25} {status:<20} ({diff:+.1f}%)")
    
    print("="*100)
    
    # Save detailed results
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_file = f"backtest_14days_{timestamp}.txt"
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("="*100 + "\n")
        f.write("🎯 14-DAY BACKTEST RESULTS\n")
        f.write("="*100 + "\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Overall Win Rate: {overall_wr:.1f}%\n")
        f.write(f"Total Predictions: {total_preds}\n")
        f.write(f"Correct: {total_correct}\n")
        f.write("="*100 + "\n\n")
        
        for result in all_results:
            f.write(f"\n{result['league']}\n")
            f.write("-"*100 + "\n")
            f.write(f"Win Rate: {result['win_rate']:.1f}% (Expected: {result['expected_wr']:.1f}%)\n")
            f.write(f"Predictions: {result['correct']}/{result['total']}\n\n")
            
            f.write("By Pattern:\n")
            for pattern, stats in sorted(result['by_pattern'].items(), key=lambda x: -x[1]['total']):
                pattern_wr = (stats['correct'] / stats['total']) * 100 if stats['total'] > 0 else 0
                f.write(f"  {pattern:35} {stats['correct']:3}/{stats['total']:3} = {pattern_wr:5.1f}%\n")
            f.write("\n")
    
    print(f"\n📄 Detailed results saved to: {output_file}")


if __name__ == '__main__':
    main()
