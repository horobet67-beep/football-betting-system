"""
Universal Weight Optimization for All Leagues
Tests 8 different weight configurations for each league independently
Finds the optimal balance for each league's characteristics
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


# League configurations
LEAGUE_CONFIGS = {
    "Serie A": {
        "loader": load_serie_a_data,
        "register": register_serie_a_patterns,
        "thresholds": {
            'home_over_0_5_cards': 0.55,
            'away_over_0_5_cards': 0.55,
            'home_over_1_5_cards': 0.60,
            'away_over_1_5_cards': 0.60,
            'total_over_3_5_cards': 0.58,
            'total_over_4_5_cards': 0.62,
            'home_over_0_5_goals': 0.60,
            'away_over_0_5_goals': 0.58,
            'home_over_1_5_goals': 0.65,
            'total_over_1_5_goals': 0.58,
            'total_over_2_5_goals': 0.65,
            'total_under_2_5_goals': 0.55,
            'both_teams_to_score': 0.62,
            'home_over_3_5_corners': 0.60,
            'home_over_4_5_corners': 0.65,
            'away_over_2_5_corners': 0.60,
            'away_over_3_5_corners': 0.65,
            'total_over_8_5_corners': 0.58,
            'total_over_9_5_corners': 0.62,
        }
    },
    "Bundesliga": {
        "loader": load_bundesliga_data,
        "register": register_bundesliga_patterns,
        "thresholds": {
            'home_over_0_5_cards': 0.55,
            'away_over_0_5_cards': 0.55,
            'home_over_1_5_cards': 0.60,
            'away_over_1_5_cards': 0.60,
            'total_over_3_5_cards': 0.58,
            'total_over_4_5_cards': 0.62,
            'home_over_0_5_goals': 0.60,
            'away_over_0_5_goals': 0.58,
            'home_over_1_5_goals': 0.65,
            'total_over_1_5_goals': 0.58,
            'total_over_2_5_goals': 0.65,
            'total_under_2_5_goals': 0.55,
            'both_teams_to_score': 0.62,
            'home_over_3_5_corners': 0.60,
            'home_over_4_5_corners': 0.65,
            'away_over_2_5_corners': 0.60,
            'away_over_3_5_corners': 0.65,
            'total_over_8_5_corners': 0.58,
            'total_over_9_5_corners': 0.62,
        }
    },
    "La Liga": {
        "loader": load_la_liga_data,
        "register": register_la_liga_patterns,
        "thresholds": {
            'home_over_0_5_cards': 0.55,
            'away_over_0_5_cards': 0.55,
            'home_over_1_5_cards': 0.60,
            'away_over_1_5_cards': 0.60,
            'total_over_3_5_cards': 0.58,
            'total_over_4_5_cards': 0.62,
            'home_over_0_5_goals': 0.60,
            'away_over_0_5_goals': 0.58,
            'home_over_1_5_goals': 0.65,
            'total_over_1_5_goals': 0.58,
            'total_over_2_5_goals': 0.65,
            'total_under_2_5_goals': 0.55,
            'both_teams_to_score': 0.62,
            'home_over_3_5_corners': 0.60,
            'home_over_4_5_corners': 0.65,
            'away_over_2_5_corners': 0.60,
            'away_over_3_5_corners': 0.65,
            'total_over_8_5_corners': 0.58,
            'total_over_9_5_corners': 0.62,
        }
    },
    "Premier League": {
        "loader": load_premier_league_data,
        "register": register_premier_league_patterns,
        "thresholds": {
            'home_over_0_5_cards': 0.55,
            'away_over_0_5_cards': 0.55,
            'home_over_1_5_cards': 0.60,
            'away_over_1_5_cards': 0.60,
            'total_over_3_5_cards': 0.58,
            'total_over_4_5_cards': 0.62,
            'home_over_0_5_goals': 0.60,
            'away_over_0_5_goals': 0.58,
            'home_over_1_5_goals': 0.65,
            'total_over_1_5_goals': 0.58,
            'total_over_2_5_goals': 0.65,
            'total_under_2_5_goals': 0.55,
            'both_teams_to_score': 0.62,
            'home_over_3_5_corners': 0.60,
            'home_over_4_5_corners': 0.65,
            'away_over_2_5_corners': 0.60,
            'away_over_3_5_corners': 0.65,
            'total_over_8_5_corners': 0.58,
            'total_over_9_5_corners': 0.62,
        }
    },
    "Romania": {
        "loader": load_romanian_data,
        "register": register_romanian_patterns,
        "thresholds": {
            'home_over_0_5_cards': 0.55,
            'away_over_0_5_cards': 0.55,
            'home_over_1_5_cards': 0.60,
            'away_over_1_5_cards': 0.60,
            'total_over_3_5_cards': 0.58,
            'total_over_4_5_cards': 0.62,
            'home_over_0_5_goals': 0.60,
            'away_over_0_5_goals': 0.58,
            'home_over_1_5_goals': 0.65,
            'total_over_1_5_goals': 0.58,
            'total_over_2_5_goals': 0.65,
            'total_under_2_5_goals': 0.55,
            'both_teams_to_score': 0.62,
            'home_over_3_5_corners': 0.60,
            'home_over_4_5_corners': 0.65,
            'away_over_2_5_corners': 0.60,
            'away_over_3_5_corners': 0.65,
            'total_over_8_5_corners': 0.58,
            'total_over_9_5_corners': 0.62,
        }
    },
}


def test_weight_configuration(
    league_name: str,
    data,
    registry,
    thresholds: Dict[str, float],
    weights: Dict[int, float],
    days: int = 30,
    max_bets: int = 50
) -> Tuple[int, int, float, float]:
    """Test a weight configuration on a specific league"""
    
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
        return 0, 0, 0.0, 0.0
    
    win_rate = wins / bets_made
    avg_confidence = total_confidence / bets_made
    
    return wins, losses, win_rate, avg_confidence


def optimize_league(league_name: str):
    """Optimize weights for a specific league"""
    
    print("\n" + "="*120)
    print(f" "*40 + f"🎯 OPTIMIZING {league_name.upper()} 🎯")
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
    
    # Test all weight configurations
    results = []
    
    print(f"\n🧪 Testing 8 weight configurations on last 30 days (max 50 bets each)...\n")
    
    for config_name, weights in WEIGHT_CONFIGS.items():
        wins, losses, win_rate, avg_confidence = test_weight_configuration(
            league_name,
            data,
            registry,
            config["thresholds"],
            weights,
            days=30,
            max_bets=50
        )
        
        total_bets = wins + losses
        
        # Composite score: 70% win rate + 30% confidence
        composite_score = (win_rate * 0.7) + (avg_confidence * 0.3)
        
        results.append({
            'name': config_name,
            'weights': weights,
            'bets': total_bets,
            'wins': wins,
            'losses': losses,
            'win_rate': win_rate,
            'avg_confidence': avg_confidence,
            'composite_score': composite_score
        })
        
        print(f"  {config_name:25s}: {wins:2d}/{total_bets:2d} bets "
              f"({win_rate*100:5.1f}% WR, {avg_confidence*100:5.1f}% conf, "
              f"score: {composite_score:.3f})")
    
    # Sort by composite score
    results.sort(key=lambda x: x['composite_score'], reverse=True)
    
    # Print summary
    print("\n" + "─"*120)
    print(f"{'Rank':<6} {'Configuration':<25} {'Bets':<6} {'Wins':<6} {'Win Rate':<12} "
          f"{'Avg Conf':<12} {'Score':<10} {'Status'}")
    print("─"*120)
    
    for i, result in enumerate(results, 1):
        status = "⭐ WINNER" if i == 1 else ""
        print(f"{i:<6} {result['name']:<25} {result['bets']:<6} {result['wins']:<6} "
              f"{result['win_rate']*100:>10.1f}%  {result['avg_confidence']*100:>10.1f}%  "
              f"{result['composite_score']:>8.3f}  {status}")
    
    winner = results[0]
    print("\n" + "="*120)
    print(f"🏆 OPTIMAL CONFIGURATION FOR {league_name.upper()}: {winner['name']}")
    print(f"   Win Rate: {winner['win_rate']*100:.1f}% ({winner['wins']}/{winner['bets']} bets)")
    print(f"   Avg Confidence: {winner['avg_confidence']*100:.1f}%")
    print(f"   Composite Score: {winner['composite_score']:.3f}")
    print(f"   Weights: {winner['weights']}")
    print("="*120)
    
    return winner


def main():
    """Run optimization for all leagues"""
    
    print("\n" + "="*120)
    print(" "*35 + "🌍 MULTI-LEAGUE WEIGHT OPTIMIZATION 🌍")
    print(" "*30 + "Finding optimal weights for each league independently")
    print("="*120)
    
    # Check if specific league requested
    if len(sys.argv) > 1:
        league_name = sys.argv[1]
        if league_name in LEAGUE_CONFIGS:
            winner = optimize_league(league_name)
            return
        else:
            print(f"❌ Unknown league: {league_name}")
            print(f"Available leagues: {', '.join(LEAGUE_CONFIGS.keys())}")
            return
    
    # Optimize all leagues
    all_winners = {}
    
    for league_name in LEAGUE_CONFIGS.keys():
        winner = optimize_league(league_name)
        all_winners[league_name] = winner
        print("\n" + "⏸️  Press Enter to continue to next league..." + "\n")
        input()
    
    # Final summary
    print("\n" + "="*120)
    print(" "*40 + "📊 FINAL SUMMARY - ALL LEAGUES")
    print("="*120)
    print(f"\n{'League':<20} {'Best Config':<25} {'Win Rate':<12} {'Avg Conf':<12} {'Score':<10}")
    print("─"*120)
    
    for league_name, winner in all_winners.items():
        print(f"{league_name:<20} {winner['name']:<25} {winner['win_rate']*100:>10.1f}%  "
              f"{winner['avg_confidence']*100:>10.1f}%  {winner['composite_score']:>8.3f}")
    
    print("\n" + "="*120)
    print("✅ Optimization complete! Apply these configurations to each league's predictor.")
    print("="*120)


if __name__ == "__main__":
    main()
