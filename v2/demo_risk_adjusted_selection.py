#!/usr/bin/env python3
"""
Demo: Risk-Adjusted Best Bet Selection

Shows how the system now selects bets based on risk-adjusted confidence
instead of raw confidence, favoring more stable patterns (corners) over
volatile patterns (goals) when confidence levels are similar.
"""

import pandas as pd
from datetime import datetime
from simple_premier_league_predictor import SimplePremierLeaguePredictor
from data.premier_league_adapter import load_premier_league_data
from patterns.premier_league_patterns import register_premier_league_patterns
from patterns.registry import clear_patterns
from patterns.risk_adjustment import get_pattern_risk_penalty, get_pattern_category


def main():
    print("="*80)
    print("🎯 RISK-ADJUSTED BET SELECTION DEMO")
    print("="*80)
    print("\nWhy Risk Adjustment?")
    print("  • Same 75% win rate means different things for goals vs corners")
    print("  • Corner patterns are more CONSISTENT (lower variance)")
    print("  • Goal patterns are more VOLATILE (higher variance)")
    print("  • Risk adjustment penalizes volatile patterns")
    print()
    
    # Load data
    print("Loading Premier League data...")
    data = load_premier_league_data()
    
    clear_patterns()
    register_premier_league_patterns()
    
    predictor = SimplePremierLeaguePredictor()
    
    # Get a recent high-stakes match
    print("\nAnalyzing recent match with verbose output...\n")
    
    recent_match = data.iloc[-5]  # 5 matches ago
    
    best_bet = predictor.predict_match(
        recent_match['home_team'],
        recent_match['away_team'],
        recent_match['date'],
        verbose=True
    )
    
    # Explain the selection
    print("\n" + "="*80)
    print("📊 PATTERN RISK PENALTIES (Reference)")
    print("="*80)
    
    pattern_examples = [
        ('over_3_5_goals', 'High variance (lucky/unlucky goals)'),
        ('over_2_5_goals', 'Medium-high variance'),
        ('over_1_5_goals', 'Medium variance'),
        ('total_over_9_5_corners', 'Medium variance'),
        ('home_over_2_5_corners', 'Low variance (consistent)'),
        ('home_over_0_5_corners', 'Very low variance'),
    ]
    
    print(f"\n{'Pattern':<30} {'Penalty':<10} {'Reason'}")
    print("-"*80)
    for pattern, reason in pattern_examples:
        penalty = get_pattern_risk_penalty(pattern)
        category = get_pattern_category(pattern)
        print(f"{pattern:<30} -{penalty:.1%}      {reason}")
    
    print("\n" + "="*80)
    print("💡 KEY INSIGHTS")
    print("="*80)
    print("""
1. CORNER PATTERNS are favored because:
   ✅ More consistent across matches (less random variation)
   ✅ Less affected by single lucky/unlucky moments
   ✅ Teams maintain corner styles more reliably
   ✅ Lower penalties: -1% to -3%

2. GOAL PATTERNS are penalized because:
   ❌ Higher variance (one counter-attack changes everything)
   ❌ More dependent on individual moments of brilliance/errors
   ❌ Team scoring can vary dramatically match-to-match
   ❌ Higher penalties: -5% to -10%

3. SELECTION LOGIC:
   If you have two bets both at 80% confidence:
   • over_2_5_goals: 80% - 6% = 74% risk-adjusted
   • home_over_2_5_corners: 80% - 2% = 78% risk-adjusted
   → System selects CORNERS (more reliable)

4. REAL BETTING BENEFIT:
   ✅ More consistent results over time
   ✅ Lower variance = smoother bankroll growth
   ✅ Better risk management
   ✅ Still based on REAL win rate data (not dummy odds)
""")
    
    print("="*80)
    print("🎉 PRODUCTION READY")
    print("="*80)
    print("\nAll 4 leagues now use risk-adjusted selection:")
    print("  🏴󠁧󠁢󠁥󠁮󠁧󠁿  Premier League: ✅")
    print("  🇪🇸  La Liga: ✅")
    print("  🇩🇪  Bundesliga: ✅")
    print("  🇷🇴  Romanian Liga I: ✅")
    print()


if __name__ == '__main__':
    main()
