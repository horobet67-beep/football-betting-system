#!/usr/bin/env python3
"""
Test threshold optimization on Bundesliga champion patterns
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sys

sys.path.append('.')

from simple_bundesliga_predictor import SimpleBundesligaPredictor
from data.bundesliga_adapter import load_bundesliga_data
from patterns.bundesliga_patterns import register_bundesliga_patterns
from patterns.registry import clear_patterns, get_pattern_registry


def backtest_with_thresholds(all_data: pd.DataFrame, thresholds: dict, label: str):
    """Backtest with custom thresholds"""
    
    predictor = SimpleBundesligaPredictor()
    # Override thresholds
    predictor.confidence_thresholds.update(thresholds)
    
    # 90-day lookback
    lookback_days = 90
    cutoff_date = all_data['Date'].max() - timedelta(days=lookback_days)
    test_data = all_data[all_data['Date'] > cutoff_date]
    
    total_bets = 0
    wins = 0
    losses = 0
    units = 0.0
    pattern_stats = {}
    
    for _, match in test_data.iterrows():
        historical = all_data[all_data['Date'] < match['Date']].tail(500)
        
        if len(historical) < 50:
            continue
        
        recommendations = predictor.predict_match(
            match['HomeTeam'],
            match['AwayTeam'],
            historical,
            match['Date']
        )
        
        for rec in recommendations:
            if rec.recommendation != "BET":
                continue
            
            pattern = get_pattern_registry().get_pattern(rec.pattern_name)
            if not pattern:
                continue
            
            outcome = pattern.label_fn(match)
            
            if rec.pattern_name not in pattern_stats:
                pattern_stats[rec.pattern_name] = {'bets': 0, 'wins': 0, 'units': 0.0}
            
            total_bets += 1
            pattern_stats[rec.pattern_name]['bets'] += 1
            
            if outcome:
                wins += 1
                pattern_stats[rec.pattern_name]['wins'] += 1
                estimated_odds = predictor._estimate_odds(rec.pattern_name)
                profit = estimated_odds - 1
                units += profit
                pattern_stats[rec.pattern_name]['units'] += profit
            else:
                losses += 1
                units -= 1.0
                pattern_stats[rec.pattern_name]['units'] -= 1.0
    
    return {
        'label': label,
        'total_bets': total_bets,
        'wins': wins,
        'losses': losses,
        'units': units,
        'pattern_stats': pattern_stats
    }


def main():
    print("="*80)
    print("BUNDESLIGA THRESHOLD OPTIMIZATION TEST (90-day period)")
    print("="*80)
    print()
    
    # Load data
    all_data = load_bundesliga_data()
    all_data = all_data[(all_data['HC'] >= 0) & (all_data['AC'] >= 0)]
    
    # Register patterns
    clear_patterns()
    register_bundesliga_patterns()
    
    # Test scenarios
    print("Testing 3 threshold configurations...\n")
    
    # BASELINE (current)
    baseline_thresholds = {
        'home_over_2_5_corners': 0.65,
        'away_over_2_5_corners': 0.65,
        'total_over_7_5_corners': 0.68,
        'total_over_8_5_corners': 0.70,
    }
    
    # OPTIMIZED (lower thresholds on champions)
    optimized_thresholds = {
        'home_over_2_5_corners': 0.60,  # 81.7% WR - can afford lower
        'away_over_2_5_corners': 0.60,  # 79.0% WR - can afford lower
        'total_over_7_5_corners': 0.63,  # 73.1% WR - slight lower
        'total_over_8_5_corners': 0.65,  # 69.2% WR - slight lower
    }
    
    # AGGRESSIVE (even lower)
    aggressive_thresholds = {
        'home_over_2_5_corners': 0.55,
        'away_over_2_5_corners': 0.55,
        'total_over_7_5_corners': 0.60,
        'total_over_8_5_corners': 0.60,
    }
    
    # Run tests
    baseline_results = backtest_with_thresholds(all_data, baseline_thresholds, "BASELINE")
    optimized_results = backtest_with_thresholds(all_data, optimized_thresholds, "OPTIMIZED")
    aggressive_results = backtest_with_thresholds(all_data, aggressive_thresholds, "AGGRESSIVE")
    
    # Display results
    print("="*80)
    print("RESULTS COMPARISON")
    print("="*80)
    print(f"{'Configuration':<15} {'Bets':>6} {'Wins':>6} {'Win%':>7} {'Units':>8} {'ROI%':>7}")
    print("-"*80)
    
    for results in [baseline_results, optimized_results, aggressive_results]:
        if results['total_bets'] > 0:
            win_rate = results['wins'] / results['total_bets'] * 100
            roi = (results['units'] / results['total_bets']) * 100
            print(f"{results['label']:<15} {results['total_bets']:>6} {results['wins']:>6} "
                  f"{win_rate:>6.1f}% {results['units']:>+8.1f} {roi:>+6.1f}%")
    
    print()
    print("="*80)
    print("DETAILED COMPARISON - Corner Patterns Only")
    print("="*80)
    
    for results in [baseline_results, optimized_results, aggressive_results]:
        print(f"\n{results['label']}:")
        print(f"{'Pattern':<30} {'Bets':>6} {'Win%':>7} {'Units':>8}")
        print("-"*80)
        
        corner_patterns = {k: v for k, v in results['pattern_stats'].items() 
                          if 'corner' in k.lower() and v['bets'] >= 3}
        
        sorted_patterns = sorted(corner_patterns.items(), 
                                key=lambda x: x[1]['units'], reverse=True)
        
        for pattern_name, stats in sorted_patterns:
            win_rate = stats['wins'] / stats['bets'] * 100
            print(f"{pattern_name:<30} {stats['bets']:>6} {win_rate:>6.1f}% {stats['units']:>+8.1f}")
    
    print()
    print("="*80)
    print("RECOMMENDATION")
    print("="*80)
    
    # Compare baseline vs optimized
    baseline_wr = baseline_results['wins'] / baseline_results['total_bets'] * 100
    optimized_wr = optimized_results['wins'] / optimized_results['total_bets'] * 100
    aggressive_wr = aggressive_results['wins'] / aggressive_results['total_bets'] * 100
    
    baseline_roi = (baseline_results['units'] / baseline_results['total_bets']) * 100
    optimized_roi = (optimized_results['units'] / optimized_results['total_bets']) * 100
    aggressive_roi = (aggressive_results['units'] / aggressive_results['total_bets']) * 100
    
    wr_diff = optimized_wr - baseline_wr
    roi_diff = optimized_roi - baseline_roi
    units_diff = optimized_results['units'] - baseline_results['units']
    bets_increase = ((optimized_results['total_bets'] - baseline_results['total_bets']) / 
                     baseline_results['total_bets'] * 100)
    
    print(f"\nOPTIMIZED vs BASELINE:")
    print(f"  Win Rate: {baseline_wr:.1f}% → {optimized_wr:.1f}% ({wr_diff:+.1f}%)")
    print(f"  ROI: {baseline_roi:+.1f}% → {optimized_roi:+.1f}% ({roi_diff:+.1f}%)")
    print(f"  Total Units: {baseline_results['units']:+.1f} → {optimized_results['units']:+.1f} ({units_diff:+.1f})")
    print(f"  Bet Volume: {baseline_results['total_bets']} → {optimized_results['total_bets']} ({bets_increase:+.1f}%)")
    print()
    
    # Decision logic
    if optimized_wr >= baseline_wr - 1.0 and optimized_results['units'] > baseline_results['units']:
        print("✅ DEPLOY OPTIMIZED THRESHOLDS")
        print("   → Win rate maintained or improved")
        print("   → Higher total profit")
        print("   → More betting opportunities")
    elif aggressive_wr >= baseline_wr and aggressive_results['units'] > optimized_results['units']:
        print("✅ CONSIDER AGGRESSIVE THRESHOLDS")
        print("   → Best total profit")
        print("   → Win rate still acceptable")
    else:
        print("⚠️  KEEP BASELINE THRESHOLDS")
        print("   → Optimization didn't improve performance")
        print("   → Current system already optimal")
    
    print("="*80)


if __name__ == '__main__':
    main()
