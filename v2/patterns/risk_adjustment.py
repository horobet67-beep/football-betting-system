"""
Pattern Risk Adjustment
Assigns risk penalties to betting patterns based on historical variance and predictability.

Lower variance patterns (e.g., corners) get smaller penalties.
Higher variance patterns (e.g., goals) get larger penalties.

This helps select more reliable bets when multiple patterns have similar confidence levels.
"""

# Pattern risk penalties (0.0 = lowest risk, 0.15 = highest risk)
# Based on empirical variance analysis across multiple seasons
PATTERN_RISK_PENALTIES = {
    # ========== GOAL PATTERNS (High Variance) ==========
    # Goals are unpredictable - one moment can change everything
    'over_3_5_goals': 0.10,        # Very high variance
    'total_over_3_5_goals': 0.10,
    'over_2_5_goals': 0.06,        # High variance
    'total_over_2_5_goals': 0.06,
    'under_2_5_goals': 0.05,       # Moderate variance
    'total_under_2_5_goals': 0.05,
    'over_1_5_goals': 0.04,        # Moderate variance
    'total_over_1_5_goals': 0.04,
    'under_1_5_goals': 0.05,
    'over_0_5_goals': 0.02,        # Low variance (very likely)
    'total_over_0_5_goals': 0.02,
    
    # Home/Away goal patterns
    'home_over_2_5_goals': 0.07,
    'home_over_1_5_goals': 0.05,
    'home_over_0_5_goals': 0.02,
    'home_under_1_5_goals': 0.06,
    'away_over_2_5_goals': 0.08,   # Away goals even less predictable
    'away_over_1_5_goals': 0.06,
    'away_over_0_5_goals': 0.03,
    'away_under_1_5_goals': 0.05,
    
    # ========== CORNER PATTERNS (Low-Medium Variance) ==========
    # Corners are more consistent and predictable
    'over_11_5_corners': 0.04,     # High total - moderate risk
    'over_10_5_corners': 0.04,
    'total_over_10_5_corners': 0.04,
    'over_9_5_corners': 0.03,
    'total_over_9_5_corners': 0.03,
    'over_8_5_corners': 0.03,
    'total_over_8_5_corners': 0.03,
    'over_7_5_corners': 0.02,
    'total_over_7_5_corners': 0.02,
    'total_under_7_5_corners': 0.03,
    'over_2_5_corners': 0.02,      # Low threshold - low risk
    'over_0_5_corners': 0.01,      # Very low risk
    
    # Home/Away corner patterns
    'home_over_5_5_corners': 0.04,
    'home_over_4_5_corners': 0.03,
    'home_over_3_5_corners': 0.03,
    'home_over_2_5_corners': 0.02,
    'home_over_1_5_corners': 0.02,
    'home_over_0_5_corners': 0.01,
    'away_over_5_5_corners': 0.05,  # Away corners slightly less predictable
    'away_over_4_5_corners': 0.04,
    'away_over_3_5_corners': 0.03,
    'away_over_2_5_corners': 0.02,
    'away_over_1_5_corners': 0.02,
    'away_over_0_5_corners': 0.01,
    
    # ========== CARD PATTERNS (Medium Variance) ==========
    # Cards depend on referee and match intensity
    'over_5_5_cards': 0.06,        # High card totals - referee dependent
    'total_over_5_5_cards': 0.06,
    'over_4_5_cards': 0.05,
    'total_over_4_5_cards': 0.05,
    'over_3_5_cards': 0.04,
    'total_over_3_5_cards': 0.04,
    'over_2_5_cards': 0.04,
    'total_over_2_5_cards': 0.04,
    'over_1_5_cards': 0.03,
    'over_0_5_cards': 0.02,        # Low threshold - more predictable
    'total_over_0_5_cards': 0.02,
    
    # Home/Away card patterns
    'home_over_2_5_cards': 0.05,
    'home_over_1_5_cards': 0.04,
    'home_over_0_5_cards': 0.02,
    'away_over_2_5_cards': 0.05,
    'away_over_1_5_cards': 0.04,
    'away_over_0_5_cards': 0.02,
    
    # ========== SHOTS PATTERNS (Medium-High Variance) ==========
    # Shots can vary significantly match to match
    'over_20_5_shots': 0.05,
    'over_15_5_shots': 0.04,
    'over_10_5_shots': 0.03,
    'home_over_10_5_shots': 0.04,
    'home_over_5_5_shots': 0.03,
    'away_over_10_5_shots': 0.05,
    'away_over_5_5_shots': 0.04,
    
    # ========== RESULT PATTERNS (Highest Variance) ==========
    # Match results are most unpredictable
    'home_win': 0.08,
    'away_win': 0.09,
    'draw': 0.10,              # Draws are hardest to predict
}

# Default penalty for unknown patterns
DEFAULT_RISK_PENALTY = 0.05


def get_pattern_risk_penalty(pattern_name: str) -> float:
    """
    Get risk penalty for a pattern.
    
    Args:
        pattern_name: Name of the betting pattern
        
    Returns:
        Risk penalty (0.0 to 0.15) to subtract from confidence
    """
    return PATTERN_RISK_PENALTIES.get(pattern_name, DEFAULT_RISK_PENALTY)


def calculate_risk_adjusted_confidence(confidence: float, pattern_name: str) -> float:
    """
    Calculate risk-adjusted confidence score.
    
    Args:
        confidence: Raw confidence/win rate (0.0 to 1.0)
        pattern_name: Name of the betting pattern
        
    Returns:
        Risk-adjusted confidence (confidence - risk_penalty)
    """
    penalty = get_pattern_risk_penalty(pattern_name)
    adjusted = confidence - penalty
    
    # Ensure result stays in valid range
    return max(0.0, min(1.0, adjusted))


def get_pattern_category(pattern_name: str) -> str:
    """
    Categorize pattern by type for analysis.
    
    Returns:
        'goals', 'corners', 'cards', 'shots', or 'other'
    """
    pattern_lower = pattern_name.lower()
    
    if 'goal' in pattern_lower:
        return 'goals'
    elif 'corner' in pattern_lower:
        return 'corners'
    elif 'card' in pattern_lower or 'yellow' in pattern_lower or 'red' in pattern_lower:
        return 'cards'
    elif 'shot' in pattern_lower:
        return 'shots'
    else:
        return 'other'


def explain_risk_adjustment(pattern_name: str, raw_confidence: float, adjusted_confidence: float) -> str:
    """
    Generate human-readable explanation of risk adjustment.
    
    Returns:
        Explanation string
    """
    penalty = get_pattern_risk_penalty(pattern_name)
    category = get_pattern_category(pattern_name)
    
    risk_level = "low" if penalty < 0.03 else "medium" if penalty < 0.06 else "high"
    
    return (f"{pattern_name}: {raw_confidence:.1%} → {adjusted_confidence:.1%} "
            f"(−{penalty:.1%} {risk_level} variance penalty for {category})")
