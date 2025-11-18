"""
Analyze Prediction Performance

Compare win rates between all bets vs filtered high-confidence bets.
Shows performance by league, pattern, and confidence threshold.

Usage:
    python3 analyze_prediction_performance.py predictions_20251101_20251109_backtest.txt
    python3 analyze_prediction_performance.py predictions_20251101_20251109_backtest.txt --threshold 80
"""

import json
import argparse
from pathlib import Path
from collections import defaultdict
from typing import List, Dict


def analyze_predictions(prediction_file: str, confidence_threshold: float = 85.0):
    """
    Analyze prediction performance with filtering.
    
    Args:
        prediction_file: Path to prediction file (must have results filled in)
        confidence_threshold: Minimum R-Adj confidence for filtered bets
    """
    # Load predictions
    input_path = Path(prediction_file)
    if not input_path.exists():
        print(f"❌ File not found: {prediction_file}")
        return
    
    print(f"📖 Analyzing {prediction_file}...")
    txt = input_path.read_text(encoding='utf-8')
    
    # Extract JSON
    idx = txt.find('📦 JSON')
    if idx == -1:
        print("❌ No JSON data found")
        return
    
    json_start = txt[idx:].find('{')
    json_data = txt[idx + json_start:]
    data = json.loads(json_data)
    predictions = data['predictions']
    
    # Separate completed vs pending
    completed = [p for p in predictions if p.get('result') == 'COMPLETE']
    pending = [p for p in predictions if p.get('result') != 'COMPLETE']
    
    if not completed:
        print("⚠️  No completed predictions found. Run update_prediction_results.py first!")
        return
    
    # Filter high-confidence bets
    high_conf = [p for p in completed 
                 if float(p['risk_adjusted'].strip('%')) >= confidence_threshold]
    
    print(f"\n📊 Total predictions: {len(predictions)}")
    print(f"   Completed: {len(completed)}")
    print(f"   Pending: {len(pending)}")
    print(f"   High-confidence (≥{confidence_threshold}%): {len(high_conf)}")
    
    # Calculate win rates
    def calc_stats(bets):
        if not bets:
            return {'total': 0, 'won': 0, 'lost': 0, 'win_rate': 0.0}
        
        won = sum(1 for b in bets if b.get('won') == 'YES')
        lost = sum(1 for b in bets if b.get('won') == 'NO')
        return {
            'total': len(bets),
            'won': won,
            'lost': lost,
            'win_rate': won / len(bets) * 100 if bets else 0
        }
    
    all_stats = calc_stats(completed)
    filtered_stats = calc_stats(high_conf)
    
    # Print overall comparison
    print("\n" + "="*80)
    print("🎯 OVERALL PERFORMANCE COMPARISON")
    print("="*80)
    
    print(f"\nAll Bets ({all_stats['total']} bets):")
    print(f"  ✅ Won:       {all_stats['won']:3d} ({all_stats['win_rate']:.1f}%)")
    print(f"  ❌ Lost:      {all_stats['lost']:3d} ({100-all_stats['win_rate']:.1f}%)")
    
    print(f"\nFiltered Bets (R-Adj ≥ {confidence_threshold}%, {filtered_stats['total']} bets):")
    print(f"  ✅ Won:       {filtered_stats['won']:3d} ({filtered_stats['win_rate']:.1f}%)")
    print(f"  ❌ Lost:      {filtered_stats['lost']:3d} ({100-filtered_stats['win_rate']:.1f}%)")
    
    # Calculate improvement
    if all_stats['total'] > 0 and filtered_stats['total'] > 0:
        improvement = filtered_stats['win_rate'] - all_stats['win_rate']
        print(f"\n📈 Filtering Improvement: {improvement:+.1f} percentage points")
        
        if improvement > 5:
            print("   ✅ SIGNIFICANT IMPROVEMENT - Filtering is highly effective!")
        elif improvement > 0:
            print("   ✅ POSITIVE IMPROVEMENT - Filtering helps")
        elif improvement > -5:
            print("   ⚠️  MINIMAL DIFFERENCE - Filtering not critical")
        else:
            print("   ❌ NEGATIVE IMPACT - Filtering reduces performance")
    
    # By league comparison
    print("\n" + "="*80)
    print("📊 PERFORMANCE BY LEAGUE")
    print("="*80)
    
    leagues = {}
    for pred in completed:
        league = pred['league']
        if league not in leagues:
            leagues[league] = {'all': [], 'filtered': []}
        leagues[league]['all'].append(pred)
        
        if float(pred['risk_adjusted'].strip('%')) >= confidence_threshold:
            leagues[league]['filtered'].append(pred)
    
    print(f"\n{'League':<20} {'All Bets':<25} {'Filtered (≥{:.0f}%)'.format(confidence_threshold):<25} {'Improvement':<15}")
    print("-"*80)
    
    for league in sorted(leagues.keys()):
        all_bets = leagues[league]['all']
        filt_bets = leagues[league]['filtered']
        
        all_s = calc_stats(all_bets)
        filt_s = calc_stats(filt_bets)
        
        improvement = filt_s['win_rate'] - all_s['win_rate'] if filt_s['total'] > 0 else 0
        
        all_str = f"{all_s['won']}/{all_s['total']} ({all_s['win_rate']:.1f}%)"
        filt_str = f"{filt_s['won']}/{filt_s['total']} ({filt_s['win_rate']:.1f}%)" if filt_s['total'] > 0 else "N/A"
        imp_str = f"{improvement:+.1f}pp" if filt_s['total'] > 0 else "-"
        
        print(f"{league:<20} {all_str:<25} {filt_str:<25} {imp_str:<15}")
    
    # By pattern comparison
    print("\n" + "="*80)
    print("📊 PERFORMANCE BY PATTERN (Top 10)")
    print("="*80)
    
    patterns = defaultdict(lambda: {'all': [], 'filtered': []})
    for pred in completed:
        pattern = pred['pattern']
        patterns[pattern]['all'].append(pred)
        
        if float(pred['risk_adjusted'].strip('%')) >= confidence_threshold:
            patterns[pattern]['filtered'].append(pred)
    
    # Sort by total bets
    sorted_patterns = sorted(patterns.items(), key=lambda x: len(x[1]['all']), reverse=True)[:10]
    
    print(f"\n{'Pattern':<35} {'All Bets':<25} {'Filtered':<25} {'Diff':<10}")
    print("-"*80)
    
    for pattern, bets in sorted_patterns:
        all_s = calc_stats(bets['all'])
        filt_s = calc_stats(bets['filtered'])
        
        improvement = filt_s['win_rate'] - all_s['win_rate'] if filt_s['total'] > 0 else 0
        
        all_str = f"{all_s['won']}/{all_s['total']} ({all_s['win_rate']:.1f}%)"
        filt_str = f"{filt_s['won']}/{filt_s['total']} ({filt_s['win_rate']:.1f}%)" if filt_s['total'] > 0 else "N/A"
        imp_str = f"{improvement:+.1f}pp" if filt_s['total'] > 0 else "-"
        
        print(f"{pattern:<35} {all_str:<25} {filt_str:<25} {imp_str:<10}")
    
    # Confidence calibration
    print("\n" + "="*80)
    print("📊 CONFIDENCE CALIBRATION")
    print("="*80)
    
    # Group by confidence ranges
    ranges = [
        (70, 75, "70-75%"),
        (75, 80, "75-80%"),
        (80, 85, "80-85%"),
        (85, 90, "85-90%"),
        (90, 95, "90-95%"),
        (95, 100, "95-100%"),
    ]
    
    print(f"\n{'R-Adj Range':<15} {'Bets':<10} {'Win Rate':<15} {'Calibration':<20}")
    print("-"*80)
    
    for min_conf, max_conf, label in ranges:
        range_bets = [p for p in completed 
                     if min_conf <= float(p['risk_adjusted'].strip('%')) < max_conf]
        
        if range_bets:
            stats = calc_stats(range_bets)
            avg_conf = sum(float(p['risk_adjusted'].strip('%')) for p in range_bets) / len(range_bets)
            calibration = stats['win_rate'] - avg_conf
            
            calib_str = f"{calibration:+.1f}pp"
            if abs(calibration) < 3:
                calib_str += " ✅ Well calibrated"
            elif calibration > 0:
                calib_str += " ⚠️  Underconfident"
            else:
                calib_str += " ⚠️  Overconfident"
            
            print(f"{label:<15} {stats['total']:<10} {stats['win_rate']:.1f}%{'':<10} {calib_str:<20}")
    
    # Recommendation
    print("\n" + "="*80)
    print("💡 RECOMMENDATIONS")
    print("="*80)
    
    if filtered_stats['win_rate'] > all_stats['win_rate'] + 5:
        print(f"\n✅ FILTERING HIGHLY RECOMMENDED")
        print(f"   Using R-Adj ≥ {confidence_threshold}% improves win rate by {filtered_stats['win_rate'] - all_stats['win_rate']:.1f}pp")
        print(f"   Reduces bet count from {all_stats['total']} to {filtered_stats['total']} ({filtered_stats['total']/all_stats['total']*100:.0f}%)")
        print(f"   Focus on quality over quantity!")
    elif filtered_stats['win_rate'] > all_stats['win_rate']:
        print(f"\n✅ FILTERING RECOMMENDED")
        print(f"   Small improvement of {filtered_stats['win_rate'] - all_stats['win_rate']:.1f}pp")
        print(f"   Consider R-Adj ≥ {confidence_threshold}% for safer bets")
    else:
        print(f"\n⚠️  FILTERING NOT BENEFICIAL")
        print(f"   All bets perform better than filtered subset")
        print(f"   Consider lowering threshold or using all bets")
    
    # Best performing combinations
    print("\n🌟 BEST PERFORMING COMBINATIONS:")
    
    # Find best league+pattern combos in filtered set
    combos = defaultdict(list)
    for pred in high_conf:
        key = (pred['league'], pred['pattern'])
        combos[key].append(pred)
    
    # Filter combos with at least 3 bets and calculate win rate
    good_combos = []
    for (league, pattern), bets in combos.items():
        if len(bets) >= 3:
            stats = calc_stats(bets)
            if stats['win_rate'] >= 80:
                good_combos.append((league, pattern, stats))
    
    # Sort by win rate
    good_combos.sort(key=lambda x: (x[2]['win_rate'], x[2]['total']), reverse=True)
    
    if good_combos:
        for league, pattern, stats in good_combos[:5]:
            print(f"   {league} | {pattern}")
            print(f"      {stats['won']}/{stats['total']} bets ({stats['win_rate']:.1f}% win rate)")
    else:
        print("   None found (need ≥3 bets and ≥80% win rate)")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Analyze prediction performance with filtering'
    )
    parser.add_argument('prediction_file', help='Prediction file with results')
    parser.add_argument('--threshold', '-t', type=float, default=85.0,
                       help='Confidence threshold for filtering (default: 85.0)')
    
    args = parser.parse_args()
    
    analyze_predictions(args.prediction_file, args.threshold)


if __name__ == '__main__':
    main()
