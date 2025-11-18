"""
Optimize Multi-Timeframe Weights for Best Performance

Tests different weight combinations to find optimal balance between
recent trends and long-term stability.
"""

from data.serie_a_adapter import load_serie_a_data
from simple_serie_a_predictor import SimpleSerieAPredictor
from patterns.registry import get_pattern_registry
from utils.confidence import calculate_multi_timeframe_confidence
from datetime import datetime, timedelta
import itertools


def test_weight_configuration(data, test_period_days=30, weight_config=None):
    """
    Test a specific weight configuration on recent data.
    
    Returns:
        dict with wins, losses, win_rate for the configuration
    """
    predictor = SimpleSerieAPredictor()
    registry = get_pattern_registry()
    
    latest_date = data['Date'].max()
    start_date = latest_date - timedelta(days=test_period_days)
    test_matches = data[(data['Date'] >= start_date) & (data['Date'] <= latest_date)]
    
    wins = 0
    losses = 0
    total_confidence = 0
    
    for idx, match in test_matches.iterrows():
        match_date = match['Date']
        
        # Test each pattern with custom weights
        best_confidence = 0
        best_pattern = None
        
        for pattern_name in registry.list_patterns():
            if pattern_name not in predictor.thresholds:
                continue
                
            pattern = registry.get_pattern(pattern_name)
            threshold = predictor.thresholds[pattern_name]
            
            # Calculate confidence with custom weights
            confidence, debug = calculate_multi_timeframe_confidence(
                data,
                match_date,
                pattern.label_fn,
                custom_timeframes=weight_config,
                use_all_history=True
            )
            
            if confidence >= threshold and confidence > best_confidence:
                best_confidence = confidence
                best_pattern = pattern_name
        
        if best_pattern:
            pattern = registry.get_pattern(best_pattern)
            actual = pattern.label_fn(match)
            
            if actual:
                wins += 1
            else:
                losses += 1
            
            total_confidence += best_confidence
    
    total_bets = wins + losses
    win_rate = (wins / total_bets) if total_bets > 0 else 0
    avg_confidence = (total_confidence / total_bets) if total_bets > 0 else 0
    
    return {
        'wins': wins,
        'losses': losses,
        'total': total_bets,
        'win_rate': win_rate,
        'avg_confidence': avg_confidence
    }


def main():
    print("="*100)
    print(" "*25 + "🔬 MULTI-TIMEFRAME WEIGHT OPTIMIZATION 🔬")
    print("="*100 + "\n")
    
    data = load_serie_a_data()
    
    print("Testing different weight configurations on Serie A (last 30 days)")
    print("This will help us find the optimal balance between recent and historical data.\n")
    
    # Define weight configurations to test
    test_configs = [
        # Current default
        ("Current Default", {
            7: 0.30, 14: 0.23, 30: 0.18, 90: 0.14, 365: 0.10, 730: 0.05
        }),
        
        # More weight on ultra-recent
        ("Ultra Recent Focus", {
            7: 0.40, 14: 0.25, 30: 0.15, 90: 0.10, 365: 0.07, 730: 0.03
        }),
        
        # Balanced across all periods
        ("Balanced", {
            7: 0.20, 14: 0.20, 30: 0.20, 90: 0.15, 365: 0.15, 730: 0.10
        }),
        
        # More weight on long-term stability
        ("Stability Focus", {
            7: 0.15, 14: 0.15, 30: 0.20, 90: 0.20, 365: 0.20, 730: 0.10
        }),
        
        # Heavy recent emphasis (risky)
        ("Extreme Recent", {
            7: 0.50, 14: 0.25, 30: 0.12, 90: 0.08, 365: 0.03, 730: 0.02
        }),
        
        # Mid-range focus (30-90 days)
        ("Mid-Range Focus", {
            7: 0.15, 14: 0.20, 30: 0.30, 90: 0.25, 365: 0.07, 730: 0.03
        }),
        
        # Equal weights (baseline)
        ("Equal Weights", {
            7: 0.167, 14: 0.167, 30: 0.166, 90: 0.167, 365: 0.167, 730: 0.166
        }),
        
        # Progressive decay
        ("Progressive Decay", {
            7: 0.32, 14: 0.24, 30: 0.18, 90: 0.13, 365: 0.09, 730: 0.04
        }),
    ]
    
    results = []
    
    print(f"{'Configuration':<25} {'Bets':<8} {'Wins':<8} {'Win Rate':<12} {'Avg Conf':<12} {'Score'}")
    print("-" * 100)
    
    for name, config in test_configs:
        result = test_weight_configuration(data, test_period_days=30, weight_config=config)
        
        # Calculate composite score (WR * 0.7 + Avg Conf * 0.3)
        score = result['win_rate'] * 0.7 + result['avg_confidence'] * 0.3
        
        results.append({
            'name': name,
            'config': config,
            'result': result,
            'score': score
        })
        
        print(f"{name:<25} {result['total']:<8} {result['wins']:<8} "
              f"{result['win_rate']:>10.1%}  {result['avg_confidence']:>10.1%}  {score:>6.3f}")
    
    # Find best configuration
    best = max(results, key=lambda x: x['score'])
    
    print("\n" + "="*100)
    print("🏆 BEST CONFIGURATION:")
    print("="*100)
    print(f"\nName: {best['name']}")
    print(f"Win Rate: {best['result']['win_rate']:.1%}")
    print(f"Avg Confidence: {best['result']['avg_confidence']:.1%}")
    print(f"Composite Score: {best['score']:.3f}\n")
    print("Weights:")
    for days, weight in sorted(best['config'].items()):
        if days == 99999:
            print(f"  All History: {weight:.1%}")
        else:
            print(f"  {days:4d} days: {weight:.1%}")
    
    print("\n" + "="*100)
    print("💡 INSIGHTS:")
    print("="*100)
    
    # Compare top 3
    top_3 = sorted(results, key=lambda x: x['score'], reverse=True)[:3]
    print(f"\nTop 3 configurations:")
    for i, r in enumerate(top_3, 1):
        print(f"{i}. {r['name']:<25} WR: {r['result']['win_rate']:.1%}  Score: {r['score']:.3f}")
    
    # Analyze weight trends
    recent_heavy = [r for r in results if r['config'][7] >= 0.35]
    stable_heavy = [r for r in results if r['config'][365] >= 0.15]
    
    print(f"\nRecent-heavy configs (7d >= 35%): {len(recent_heavy)} tested")
    if recent_heavy:
        avg_wr = sum(r['result']['win_rate'] for r in recent_heavy) / len(recent_heavy)
        print(f"  Average WR: {avg_wr:.1%}")
    
    print(f"\nStability-heavy configs (365d >= 15%): {len(stable_heavy)} tested")
    if stable_heavy:
        avg_wr = sum(r['result']['win_rate'] for r in stable_heavy) / len(stable_heavy)
        print(f"  Average WR: {avg_wr:.1%}")
    
    print("\n" + "="*100)
    print("✅ Optimization complete! Use the best weights in your predictor configuration.")
    print("="*100)


if __name__ == '__main__':
    main()
