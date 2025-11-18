"""
Comprehensive Weight Optimization for All Leagues
Tests weight configurations across MULTIPLE time periods (14/30/50/90/120/180/365/730 days)
Finds average best performance to avoid overfitting to single period
"""
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
import sys

# Import all league adapters
from data.serie_a_adapter import load_serie_a_data
from data.bundesliga_adapter import load_bundesliga_data
from data.la_liga_adapter import load_la_liga_data
from data.premier_league_adapter import load_premier_league_data
from data.romanian_adapter import load_romanian_data

# Import pattern registrations
from patterns.registry import get_pattern_registry, clear_patterns
from patterns.serie_a_patterns import register_serie_a_patterns
from patterns.bundesliga_patterns import register_bundesliga_patterns
from patterns.la_liga_patterns import register_la_liga_patterns
from patterns.premier_league_patterns import register_premier_league_patterns
from patterns.romanian_patterns import register_romanian_patterns

from utils.confidence import calculate_multi_timeframe_confidence


# Weight configurations to test
WEIGHT_CONFIGS = {
    "Current Default": {7: 0.30, 14: 0.25, 30: 0.20, 90: 0.15, 365: 0.10},
    "Ultra Recent Focus": {7: 0.35, 14: 0.25, 30: 0.20, 90: 0.12, 365: 0.08},
    "Balanced": {7: 0.20, 14: 0.20, 30: 0.20, 90: 0.15, 365: 0.15, 730: 0.10},
    "Stability Focus": {7: 0.15, 14: 0.15, 30: 0.20, 90: 0.20, 365: 0.20, 730: 0.10},
    "Extreme Recent": {7: 0.40, 14: 0.30, 30: 0.15, 90: 0.10, 365: 0.05},
    "Mid-Range Focus": {7: 0.15, 14: 0.25, 30: 0.30, 90: 0.20, 365: 0.10},
    "Equal Weights": {7: 0.20, 14: 0.20, 30: 0.20, 90: 0.20, 365: 0.20},
    "Progressive Decay": {7: 0.28, 14: 0.24, 30: 0.20, 90: 0.16, 365: 0.12},
}

# Test periods - comprehensive coverage
TEST_PERIODS = [14, 30, 50, 90, 120, 180, 365, 730]

# League configurations
LEAGUE_CONFIGS = {
    "Serie A": {
        "loader": load_serie_a_data,
        "register": register_serie_a_patterns,
        "thresholds": {
            'home_over_0_5_cards': 0.55, 'away_over_0_5_cards': 0.55,
            'home_over_1_5_cards': 0.60, 'away_over_1_5_cards': 0.60,
            'total_over_3_5_cards': 0.58, 'total_over_4_5_cards': 0.62,
            'home_over_0_5_goals': 0.60, 'away_over_0_5_goals': 0.58,
            'home_over_1_5_goals': 0.65, 'total_over_1_5_goals': 0.58,
            'total_over_2_5_goals': 0.65, 'total_under_2_5_goals': 0.55,
            'both_teams_to_score': 0.62, 'home_over_3_5_corners': 0.60,
            'home_over_4_5_corners': 0.65, 'away_over_2_5_corners': 0.60,
            'away_over_3_5_corners': 0.65, 'total_over_8_5_corners': 0.58,
            'total_over_9_5_corners': 0.62,
        }
    },
    "Bundesliga": {
        "loader": load_bundesliga_data,
        "register": register_bundesliga_patterns,
        "thresholds": {
            'home_over_0_5_cards': 0.55, 'away_over_0_5_cards': 0.55,
            'home_over_1_5_cards': 0.60, 'away_over_1_5_cards': 0.60,
            'total_over_3_5_cards': 0.58, 'total_over_4_5_cards': 0.62,
            'home_over_0_5_goals': 0.60, 'away_over_0_5_goals': 0.58,
            'home_over_1_5_goals': 0.65, 'total_over_1_5_goals': 0.58,
            'total_over_2_5_goals': 0.65, 'total_under_2_5_goals': 0.55,
            'both_teams_to_score': 0.62, 'home_over_3_5_corners': 0.60,
            'home_over_4_5_corners': 0.65, 'away_over_2_5_corners': 0.60,
            'away_over_3_5_corners': 0.65, 'total_over_8_5_corners': 0.58,
            'total_over_9_5_corners': 0.62,
        }
    },
    "La Liga": {
        "loader": load_la_liga_data,
        "register": register_la_liga_patterns,
        "thresholds": {
            'home_over_0_5_cards': 0.55, 'away_over_0_5_cards': 0.55,
            'home_over_1_5_cards': 0.60, 'away_over_1_5_cards': 0.60,
            'total_over_3_5_cards': 0.58, 'total_over_4_5_cards': 0.62,
            'home_over_0_5_goals': 0.60, 'away_over_0_5_goals': 0.58,
            'home_over_1_5_goals': 0.65, 'total_over_1_5_goals': 0.58,
            'total_over_2_5_goals': 0.65, 'total_under_2_5_goals': 0.55,
            'both_teams_to_score': 0.62, 'home_over_3_5_corners': 0.60,
            'home_over_4_5_corners': 0.65, 'away_over_2_5_corners': 0.60,
            'away_over_3_5_corners': 0.65, 'total_over_8_5_corners': 0.58,
            'total_over_9_5_corners': 0.62,
        }
    },
    "Premier League": {
        "loader": load_premier_league_data,
        "register": register_premier_league_patterns,
        "thresholds": {
            'home_over_0_5_cards': 0.55, 'away_over_0_5_cards': 0.55,
            'home_over_1_5_cards': 0.60, 'away_over_1_5_cards': 0.60,
            'total_over_3_5_cards': 0.58, 'total_over_4_5_cards': 0.62,
            'home_over_0_5_goals': 0.60, 'away_over_0_5_goals': 0.58,
            'home_over_1_5_goals': 0.65, 'total_over_1_5_goals': 0.58,
            'total_over_2_5_goals': 0.65, 'total_under_2_5_goals': 0.55,
            'both_teams_to_score': 0.62, 'home_over_3_5_corners': 0.60,
            'home_over_4_5_corners': 0.65, 'away_over_2_5_corners': 0.60,
            'away_over_3_5_corners': 0.65, 'total_over_8_5_corners': 0.58,
            'total_over_9_5_corners': 0.62,
        }
    },
    "Romania": {
        "loader": load_romanian_data,
        "register": register_romanian_patterns,
        "thresholds": {
            'home_over_0_5_cards': 0.55, 'away_over_0_5_cards': 0.55,
            'home_over_1_5_cards': 0.60, 'away_over_1_5_cards': 0.60,
            'total_over_3_5_cards': 0.58, 'total_over_4_5_cards': 0.62,
            'home_over_0_5_goals': 0.60, 'away_over_0_5_goals': 0.58,
            'home_over_1_5_goals': 0.65, 'total_over_1_5_goals': 0.58,
            'total_over_2_5_goals': 0.65, 'total_under_2_5_goals': 0.55,
            'both_teams_to_score': 0.62, 'home_over_3_5_corners': 0.60,
            'home_over_4_5_corners': 0.65, 'away_over_2_5_corners': 0.60,
            'away_over_3_5_corners': 0.65, 'total_over_8_5_corners': 0.58,
            'total_over_9_5_corners': 0.62,
        }
    },
}


def test_weight_on_period(
    data,
    registry,
    thresholds: Dict[str, float],
    weights: Dict[int, float],
    days: int,
    max_bets: int = 200
) -> Tuple[int, int, int, float, float]:
    """Test a weight configuration on a specific period"""
    
    latest_date = data['Date'].max()
    start_date = latest_date - timedelta(days=days)
    period_matches = data[(data['Date'] >= start_date) & (data['Date'] <= latest_date)]
    
    wins = 0
    losses = 0
    total_confidence = 0
    bets_made = 0
    
    for idx, match in period_matches.iterrows():
        if bets_made >= max_bets:
            break
            
        match_date = match['Date']
        
        # Find best pattern
        best_confidence = 0
        best_pattern_name = None
        best_risk_adjusted = 0
        
        for pattern_name in registry.list_patterns():
            if pattern_name not in thresholds:
                continue
            
            pattern = registry.get_pattern(pattern_name)
            threshold = thresholds[pattern_name]
            
            confidence, debug_info = calculate_multi_timeframe_confidence(
                data,
                match_date,
                pattern.label_fn,
                custom_timeframes=weights,
                use_all_history=True,
                min_matches_7d=2,
                min_matches_30d=8
            )
            
            # Risk adjustment
            risk_adjusted = confidence * 0.98 if 'cards' in pattern_name else confidence
            
            if risk_adjusted >= threshold and risk_adjusted > best_risk_adjusted:
                best_confidence = confidence
                best_pattern_name = pattern_name
                best_risk_adjusted = risk_adjusted
        
        if best_pattern_name:
            bets_made += 1
            pattern = registry.get_pattern(best_pattern_name)
            actual_result = pattern.label_fn(match)
            
            if actual_result:
                wins += 1
            else:
                losses += 1
            
            total_confidence += best_risk_adjusted
    
    if bets_made == 0:
        return 0, 0, 0, 0.0, 0.0
    
    win_rate = wins / bets_made
    avg_confidence = total_confidence / bets_made
    
    return bets_made, wins, losses, win_rate, avg_confidence


def optimize_league_comprehensive(league_name: str):
    """Optimize weights for a league across ALL test periods"""
    
    print("\n" + "="*120)
    print(f" "*35 + f"🎯 COMPREHENSIVE OPTIMIZATION: {league_name.upper()} 🎯")
    print("="*120)
    
    # Load league data
    config = LEAGUE_CONFIGS[league_name]
    print(f"\n📥 Loading {league_name} data...")
    data = config["loader"]()
    
    print(f"✅ Loaded {len(data)} matches from {data['Date'].min().date()} to {data['Date'].max().date()}")
    
    # Register patterns
    clear_patterns()
    config["register"]()
    registry = get_pattern_registry()
    print(f"✅ Registered {len(registry.list_patterns())} patterns")
    
    # Test all configurations across all periods
    print(f"\n🧪 Testing 8 configurations across {len(TEST_PERIODS)} time periods...")
    print(f"   Periods: {TEST_PERIODS}")
    print(f"   Max bets per period: 200")
    
    all_results = {}
    
    for config_name, weights in WEIGHT_CONFIGS.items():
        print(f"\n{'─'*120}")
        print(f"Testing: {config_name}")
        print(f"{'─'*120}")
        
        period_results = []
        
        for days in TEST_PERIODS:
            bets, wins, losses, win_rate, avg_conf = test_weight_on_period(
                data, registry, config["thresholds"], weights, days, max_bets=200
            )
            
            composite_score = (win_rate * 0.7) + (avg_conf * 0.3)
            
            period_results.append({
                'days': days,
                'bets': bets,
                'wins': wins,
                'losses': losses,
                'win_rate': win_rate,
                'avg_confidence': avg_conf,
                'composite_score': composite_score
            })
            
            print(f"  {days:3d} days: {wins:3d}/{bets:3d} bets ({win_rate*100:5.1f}% WR, "
                  f"{avg_conf*100:5.1f}% conf, score: {composite_score:.3f})")
        
        # Calculate averages across all periods
        total_bets = sum(r['bets'] for r in period_results)
        total_wins = sum(r['wins'] for r in period_results)
        avg_win_rate = sum(r['win_rate'] for r in period_results) / len(period_results)
        avg_confidence = sum(r['avg_confidence'] for r in period_results) / len(period_results)
        avg_composite = sum(r['composite_score'] for r in period_results) / len(period_results)
        
        all_results[config_name] = {
            'weights': weights,
            'period_results': period_results,
            'total_bets': total_bets,
            'total_wins': total_wins,
            'total_losses': total_bets - total_wins,
            'overall_win_rate': total_wins / total_bets if total_bets > 0 else 0,
            'avg_win_rate': avg_win_rate,
            'avg_confidence': avg_confidence,
            'avg_composite_score': avg_composite
        }
        
        print(f"\n  AVERAGES: WR={avg_win_rate*100:.1f}%, Conf={avg_confidence*100:.1f}%, "
              f"Composite={avg_composite:.3f}")
        print(f"  OVERALL:  {total_wins}/{total_bets} bets = {(total_wins/total_bets*100 if total_bets > 0 else 0):.1f}%")
    
    # Rank by average composite score
    ranked = sorted(all_results.items(), key=lambda x: x[1]['avg_composite_score'], reverse=True)
    
    # Print final ranking
    print("\n" + "="*120)
    print(f"{'FINAL RANKING - AVERAGE ACROSS ALL PERIODS':^120}")
    print("="*120)
    print(f"\n{'Rank':<6} {'Configuration':<25} {'Avg WR':<10} {'Avg Conf':<10} "
          f"{'Avg Score':<12} {'Total Bets':<12} {'Overall WR':<12} {'Status'}")
    print("─"*120)
    
    for i, (config_name, result) in enumerate(ranked, 1):
        status = "⭐ WINNER" if i == 1 else ""
        print(f"{i:<6} {config_name:<25} {result['avg_win_rate']*100:>8.1f}%  "
              f"{result['avg_confidence']*100:>8.1f}%  {result['avg_composite_score']:>10.3f}  "
              f"{result['total_bets']:>10}  {result['overall_win_rate']*100:>10.1f}%  {status}")
    
    winner = ranked[0]
    winner_name = winner[0]
    winner_data = winner[1]
    
    print("\n" + "="*120)
    print(f"🏆 OPTIMAL CONFIGURATION FOR {league_name.upper()}: {winner_name}")
    print(f"   Average Win Rate: {winner_data['avg_win_rate']*100:.1f}%")
    print(f"   Average Confidence: {winner_data['avg_confidence']*100:.1f}%")
    print(f"   Average Composite Score: {winner_data['avg_composite_score']:.3f}")
    print(f"   Overall Win Rate: {winner_data['overall_win_rate']*100:.1f}% ({winner_data['total_wins']}/{winner_data['total_bets']} bets)")
    print(f"   Weights: {winner_data['weights']}")
    
    # Show period breakdown for winner
    print(f"\n   Period Breakdown:")
    print(f"   {'Days':<8} {'Bets':<8} {'Win Rate':<12} {'Confidence':<12} {'Score'}")
    print(f"   {'-'*60}")
    for period in winner_data['period_results']:
        print(f"   {period['days']:<8} {period['bets']:<8} {period['win_rate']*100:>10.1f}%  "
              f"{period['avg_confidence']*100:>10.1f}%  {period['composite_score']:>8.3f}")
    
    print("="*120)
    
    return winner_name, winner_data


def main():
    """Run comprehensive optimization for all leagues"""
    
    print("\n" + "="*120)
    print(" "*30 + "🌍 COMPREHENSIVE MULTI-LEAGUE WEIGHT OPTIMIZATION 🌍")
    print(" "*25 + "Testing across 8 time periods: 14/30/50/90/120/180/365/730 days")
    print("="*120)
    
    # Check if specific league requested
    if len(sys.argv) > 1:
        league_name = sys.argv[1]
        if league_name in LEAGUE_CONFIGS:
            winner_name, winner_data = optimize_league_comprehensive(league_name)
            return
        else:
            print(f"❌ Unknown league: {league_name}")
            print(f"Available leagues: {', '.join(LEAGUE_CONFIGS.keys())}")
            return
    
    # Optimize all leagues
    all_winners = {}
    
    for league_name in LEAGUE_CONFIGS.keys():
        winner_name, winner_data = optimize_league_comprehensive(league_name)
        all_winners[league_name] = {
            'config_name': winner_name,
            'weights': winner_data['weights'],
            'avg_win_rate': winner_data['avg_win_rate'],
            'avg_confidence': winner_data['avg_confidence'],
            'avg_composite_score': winner_data['avg_composite_score'],
            'overall_win_rate': winner_data['overall_win_rate'],
            'total_bets': winner_data['total_bets']
        }
        print("\n⏸️  Press Enter to continue to next league...\n")
        input()
    
    # Final summary
    print("\n" + "="*120)
    print(" "*40 + "📊 FINAL SUMMARY - ALL LEAGUES")
    print("="*120)
    print(f"\n{'League':<20} {'Best Config':<25} {'Avg WR':<10} {'Overall WR':<12} "
          f"{'Avg Conf':<10} {'Score':<10} {'Total Bets'}")
    print("─"*120)
    
    for league_name, winner in all_winners.items():
        print(f"{league_name:<20} {winner['config_name']:<25} {winner['avg_win_rate']*100:>8.1f}%  "
              f"{winner['overall_win_rate']*100:>10.1f}%  {winner['avg_confidence']*100:>8.1f}%  "
              f"{winner['avg_composite_score']:>8.3f}  {winner['total_bets']:>10}")
    
    print("\n" + "="*120)
    print("✅ Comprehensive optimization complete!")
    print("   These weights are tested across multiple periods for robustness.")
    print("="*120)


if __name__ == "__main__":
    main()
