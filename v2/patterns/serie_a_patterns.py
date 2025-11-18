"""
Serie A (Italy) specific betting patterns.
Optimized for Italian football characteristics:
- Defensive play (under goals)
- Many yellow cards (tactical fouls)
- Moderate corners
- Strong home advantage
"""
import pandas as pd
from patterns.registry import register_pattern
from patterns.categories import PatternCategory


# Goals Patterns - Serie A is DEFENSIVE
def home_over_0_5_goals(row: pd.Series) -> bool:
    """Home team scores at least 1 goal."""
    return row['FTHG'] > 0.5

def away_over_0_5_goals(row: pd.Series) -> bool:
    """Away team scores at least 1 goal."""
    return row['FTAG'] > 0.5

def home_over_1_5_goals(row: pd.Series) -> bool:
    """Home team scores over 1.5 goals."""
    return row['FTHG'] > 1.5

def away_over_1_5_goals(row: pd.Series) -> bool:
    """Away team scores over 1.5 goals."""
    return row['FTAG'] > 1.5

def total_over_1_5_goals(row: pd.Series) -> bool:
    """Total goals over 1.5."""
    return (row['FTHG'] + row['FTAG']) > 1.5

def total_over_2_5_goals(row: pd.Series) -> bool:
    """Total goals over 2.5."""
    return (row['FTHG'] + row['FTAG']) > 2.5

def total_under_2_5_goals(row: pd.Series) -> bool:
    """Total goals under 2.5 - STRONG in Serie A."""
    return (row['FTHG'] + row['FTAG']) < 2.5

def total_under_1_5_goals(row: pd.Series) -> bool:
    """Total goals under 1.5 - very defensive matches."""
    return (row['FTHG'] + row['FTAG']) < 1.5

def both_teams_to_score(row: pd.Series) -> bool:
    """Both teams score at least 1 goal."""
    return row['FTHG'] > 0 and row['FTAG'] > 0

def both_teams_not_to_score(row: pd.Series) -> bool:
    """At least one team doesn't score - common in Serie A."""
    return row['FTHG'] == 0 or row['FTAG'] == 0


# Result Patterns
def home_win(row: pd.Series) -> bool:
    """Home team wins."""
    return row['FTR'] == 'H'

def away_win_or_draw(row: pd.Series) -> bool:
    """Away team wins or draws."""
    return row['FTR'] in ['A', 'D']

def home_win_or_draw(row: pd.Series) -> bool:
    """Home team wins or draws."""
    return row['FTR'] in ['H', 'D']

def draw(row: pd.Series) -> bool:
    """Match ends in draw - common in Serie A."""
    return row['FTR'] == 'D'

def home_win_clean_sheet(row: pd.Series) -> bool:
    """Home team wins without conceding."""
    return row['FTR'] == 'H' and row['FTAG'] == 0


# Corners Patterns - Moderate in Serie A
def home_over_3_5_corners(row: pd.Series) -> bool:
    """Home team over 3.5 corners."""
    return row.get('HC', 0) > 3.5

def home_over_4_5_corners(row: pd.Series) -> bool:
    """Home team over 4.5 corners."""
    return row.get('HC', 0) > 4.5

def away_over_2_5_corners(row: pd.Series) -> bool:
    """Away team over 2.5 corners."""
    return row.get('AC', 0) > 2.5

def away_over_3_5_corners(row: pd.Series) -> bool:
    """Away team over 3.5 corners."""
    return row.get('AC', 0) > 3.5

def total_over_6_5_corners(row: pd.Series) -> bool:
    """Total corners over 6.5."""
    return (row.get('HC', 0) + row.get('AC', 0)) > 6.5

def total_over_8_5_corners(row: pd.Series) -> bool:
    """Total corners over 8.5."""
    return (row.get('HC', 0) + row.get('AC', 0)) > 8.5

def total_over_9_5_corners(row: pd.Series) -> bool:
    """Total corners over 9.5."""
    return (row.get('HC', 0) + row.get('AC', 0)) > 9.5

def total_over_10_5_corners(row: pd.Series) -> bool:
    """Total corners over 10.5."""
    return (row.get('HC', 0) + row.get('AC', 0)) > 10.5

def total_under_8_5_corners(row: pd.Series) -> bool:
    """Total corners under 8.5."""
    return (row.get('HC', 0) + row.get('AC', 0)) < 8.5


# Cards Patterns - VERY STRONG in Serie A (tactical fouls)
def home_over_0_5_cards(row: pd.Series) -> bool:
    """Home team gets at least 1 card - very common."""
    return (row.get('HY', 0) + row.get('HR', 0)) > 0.5

def away_over_0_5_cards(row: pd.Series) -> bool:
    """Away team gets at least 1 card - very common."""
    return (row.get('AY', 0) + row.get('AR', 0)) > 0.5

def home_over_1_5_cards(row: pd.Series) -> bool:
    """Home team gets over 1.5 cards."""
    return (row.get('HY', 0) + row.get('HR', 0)) > 1.5

def away_over_1_5_cards(row: pd.Series) -> bool:
    """Away team gets over 1.5 cards."""
    return (row.get('AY', 0) + row.get('AR', 0)) > 1.5

def home_over_2_5_cards(row: pd.Series) -> bool:
    """Home team gets over 2.5 cards."""
    return (row.get('HY', 0) + row.get('HR', 0)) > 2.5

def away_over_2_5_cards(row: pd.Series) -> bool:
    """Away team gets over 2.5 cards."""
    return (row.get('AY', 0) + row.get('AR', 0)) > 2.5

def home_over_3_5_cards(row: pd.Series) -> bool:
    """Home team gets over 3.5 cards."""
    return (row.get('HY', 0) + row.get('HR', 0)) > 3.5

def away_over_3_5_cards(row: pd.Series) -> bool:
    """Away team gets over 3.5 cards."""
    return (row.get('AY', 0) + row.get('AR', 0)) > 3.5

def home_over_4_5_cards(row: pd.Series) -> bool:
    """Home team gets over 4.5 cards."""
    return (row.get('HY', 0) + row.get('HR', 0)) > 4.5

def away_over_4_5_cards(row: pd.Series) -> bool:
    """Away team gets over 4.5 cards."""
    return (row.get('AY', 0) + row.get('AR', 0)) > 4.5

def total_over_3_5_cards(row: pd.Series) -> bool:
    """Total cards over 3.5 - common in Serie A."""
    return (row.get('HY', 0) + row.get('AY', 0) + row.get('HR', 0) + row.get('AR', 0)) > 3.5

def total_over_4_5_cards(row: pd.Series) -> bool:
    """Total cards over 4.5."""
    return (row.get('HY', 0) + row.get('AY', 0) + row.get('HR', 0) + row.get('AR', 0)) > 4.5

def total_over_5_5_cards(row: pd.Series) -> bool:
    """Total cards over 5.5 - heated matches."""
    return (row.get('HY', 0) + row.get('AY', 0) + row.get('HR', 0) + row.get('AR', 0)) > 5.5

def total_over_1_5_cards(row: pd.Series) -> bool:
    """Total cards over 1.5."""
    return (row.get('HY', 0) + row.get('AY', 0) + row.get('HR', 0) + row.get('AR', 0)) > 1.5

def total_under_1_5_cards(row: pd.Series) -> bool:
    """Total cards under 1.5."""
    return (row.get('HY', 0) + row.get('AY', 0) + row.get('HR', 0) + row.get('AR', 0)) < 1.5

def total_over_2_5_cards(row: pd.Series) -> bool:
    """Total cards over 2.5."""
    return (row.get('HY', 0) + row.get('AY', 0) + row.get('HR', 0) + row.get('AR', 0)) > 2.5

def total_under_2_5_cards(row: pd.Series) -> bool:
    """Total cards under 2.5."""
    return (row.get('HY', 0) + row.get('AY', 0) + row.get('HR', 0) + row.get('AR', 0)) < 2.5

def home_over_8_5_corners(row: pd.Series) -> bool:
    """Home team gets over 8.5 corners."""
    return row.get('HC', 0) > 8.5

def home_under_8_5_corners(row: pd.Series) -> bool:
    """Home team gets under 8.5 corners."""
    return row.get('HC', 0) < 8.5

def away_over_8_5_corners(row: pd.Series) -> bool:
    """Away team gets over 8.5 corners."""
    return row.get('AC', 0) > 8.5

def away_under_8_5_corners(row: pd.Series) -> bool:
    """Away team gets under 8.5 corners."""
    return row.get('AC', 0) < 8.5

def total_over_4_5_goals(row: pd.Series) -> bool:
    """Total goals over 4.5."""
    return (row['FTHG'] + row['FTAG']) > 4.5

def total_under_4_5_goals(row: pd.Series) -> bool:
    """Total goals under 4.5."""
    return (row['FTHG'] + row['FTAG']) < 4.5

def total_over_5_5_goals(row: pd.Series) -> bool:
    """Total goals over 5.5."""
    return (row['FTHG'] + row['FTAG']) > 5.5

def total_under_5_5_goals(row: pd.Series) -> bool:
    """Total goals under 5.5."""
    return (row['FTHG'] + row['FTAG']) < 5.5


# Registration function
def register_serie_a_patterns():
    """Register all Serie A patterns with optimized thresholds"""
    
    # Goals patterns - higher thresholds due to defensive nature
    register_pattern("home_over_0_5_goals", PatternCategory.GOALS, home_over_0_5_goals, 0.65, 15, "Home team scores at least 1 goal")
    register_pattern("away_over_0_5_goals", PatternCategory.GOALS, away_over_0_5_goals, 0.60, 15, "Away team scores at least 1 goal")
    register_pattern("home_over_1_5_goals", PatternCategory.GOALS, home_over_1_5_goals, 0.68, 20, "Home team scores over 1.5 goals")
    register_pattern("away_over_1_5_goals", PatternCategory.GOALS, away_over_1_5_goals, 0.70, 20, "Away team scores over 1.5 goals")
    register_pattern("total_over_1_5_goals", PatternCategory.GOALS, total_over_1_5_goals, 0.60, 15, "Total goals over 1.5")
    register_pattern("total_over_2_5_goals", PatternCategory.GOALS, total_over_2_5_goals, 0.68, 20, "Total goals over 2.5")
    register_pattern("total_under_2_5_goals", PatternCategory.GOALS, total_under_2_5_goals, 0.55, 15, "Total under 2.5 - STRONG in Serie A")
    register_pattern("total_under_1_5_goals", PatternCategory.GOALS, total_under_1_5_goals, 0.70, 20, "Total under 1.5 - very defensive")
    register_pattern("both_teams_to_score", PatternCategory.GOALS, both_teams_to_score, 0.65, 15, "Both teams score")
    register_pattern("both_teams_not_to_score", PatternCategory.GOALS, both_teams_not_to_score, 0.60, 15, "At least one team doesn't score")
    
    # Result patterns - home advantage still strong (use GOALS category for results)
    register_pattern("home_win", PatternCategory.GOALS, home_win, 0.65, 15, "Home team wins")
    register_pattern("away_win_or_draw", PatternCategory.GOALS, away_win_or_draw, 0.60, 15, "Away team wins or draws")
    register_pattern("home_win_or_draw", PatternCategory.GOALS, home_win_or_draw, 0.65, 15, "Home team wins or draws")
    register_pattern("draw", PatternCategory.GOALS, draw, 0.70, 20, "Match ends in draw")
    register_pattern("home_win_clean_sheet", PatternCategory.GOALS, home_win_clean_sheet, 0.70, 20, "Home wins without conceding")
    
    # Corners patterns - moderate thresholds
    register_pattern("home_over_3_5_corners", PatternCategory.CORNERS, home_over_3_5_corners, 0.63, 15, "Home over 3.5 corners")
    register_pattern("home_over_4_5_corners", PatternCategory.CORNERS, home_over_4_5_corners, 0.68, 20, "Home over 4.5 corners")
    register_pattern("away_over_2_5_corners", PatternCategory.CORNERS, away_over_2_5_corners, 0.63, 15, "Away over 2.5 corners")
    register_pattern("away_over_3_5_corners", PatternCategory.CORNERS, away_over_3_5_corners, 0.68, 20, "Away over 3.5 corners")
    register_pattern("total_over_6_5_corners", PatternCategory.CORNERS, total_over_6_5_corners, 0.72, 18, "Total over 6.5 corners")
    register_pattern("total_over_8_5_corners", PatternCategory.CORNERS, total_over_8_5_corners, 0.62, 15, "Total over 8.5 corners")
    register_pattern("total_over_9_5_corners", PatternCategory.CORNERS, total_over_9_5_corners, 0.65, 18, "Total over 9.5 corners")
    register_pattern("total_over_10_5_corners", PatternCategory.CORNERS, total_over_10_5_corners, 0.70, 20, "Total over 10.5 corners")
    register_pattern("total_under_8_5_corners", PatternCategory.CORNERS, total_under_8_5_corners, 0.60, 15, "Total under 8.5 corners")
    
    # Cards patterns - LOWEST thresholds (very predictable in Serie A)
    register_pattern("home_over_0_5_cards", PatternCategory.CARDS, home_over_0_5_cards, 0.55, 15, "Home team at least 1 card")
    register_pattern("away_over_0_5_cards", PatternCategory.CARDS, away_over_0_5_cards, 0.55, 15, "Away team at least 1 card")
    register_pattern("home_over_1_5_cards", PatternCategory.CARDS, home_over_1_5_cards, 0.62, 15, "Home team over 1.5 cards")
    register_pattern("away_over_1_5_cards", PatternCategory.CARDS, away_over_1_5_cards, 0.62, 15, "Away team over 1.5 cards")
    register_pattern("home_over_2_5_cards", PatternCategory.CARDS, home_over_2_5_cards, 0.68, 20, "Home team over 2.5 cards")
    register_pattern("away_over_2_5_cards", PatternCategory.CARDS, away_over_2_5_cards, 0.68, 20, "Away team over 2.5 cards")
    register_pattern("home_over_3_5_cards", PatternCategory.CARDS, home_over_3_5_cards, 0.80, 25, "Home team over 3.5 cards")
    register_pattern("away_over_3_5_cards", PatternCategory.CARDS, away_over_3_5_cards, 0.80, 25, "Away team over 3.5 cards")
    register_pattern("home_over_4_5_cards", PatternCategory.CARDS, home_over_4_5_cards, 0.99, 30, "Home team over 4.5 cards")
    register_pattern("away_over_4_5_cards", PatternCategory.CARDS, away_over_4_5_cards, 0.99, 30, "Away team over 4.5 cards")
    register_pattern("total_over_3_5_cards", PatternCategory.CARDS, total_over_3_5_cards, 0.60, 15, "Total over 3.5 cards")
    register_pattern("total_over_4_5_cards", PatternCategory.CARDS, total_over_4_5_cards, 0.65, 18, "Total over 4.5 cards")
    register_pattern("total_over_5_5_cards", PatternCategory.CARDS, total_over_5_5_cards, 0.70, 20, "Total over 5.5 cards")
    register_pattern("total_over_1_5_cards", PatternCategory.CARDS, total_over_1_5_cards, 0.60, 15, "Total over 1.5 cards")  # NEW threshold
    register_pattern("total_under_1_5_cards", PatternCategory.CARDS, total_under_1_5_cards, 0.70, 15, "Total under 1.5 cards")  # NEW threshold
    register_pattern("total_over_2_5_cards", PatternCategory.CARDS, total_over_2_5_cards, 0.65, 18, "Total over 2.5 cards")  # NEW threshold
    register_pattern("total_under_2_5_cards", PatternCategory.CARDS, total_under_2_5_cards, 0.70, 18, "Total under 2.5 cards")  # NEW threshold
    
    # NEW Corner patterns - 8.5 threshold for home/away
    register_pattern("home_over_8_5_corners", PatternCategory.CORNERS, home_over_8_5_corners, 0.99, 30, "Home team over 8.5 corners")  # Very high threshold - disabled initially
    register_pattern("home_under_8_5_corners", PatternCategory.CORNERS, home_under_8_5_corners, 0.99, 30, "Home team under 8.5 corners")  # Very high threshold - disabled initially
    register_pattern("away_over_8_5_corners", PatternCategory.CORNERS, away_over_8_5_corners, 0.99, 30, "Away team over 8.5 corners")  # Very high threshold - disabled initially
    register_pattern("away_under_8_5_corners", PatternCategory.CORNERS, away_under_8_5_corners, 0.99, 30, "Away team under 8.5 corners")  # Very high threshold - disabled initially
    
    # NEW Goals patterns - 4.5 and 5.5 thresholds
    register_pattern("total_over_4_5_goals", PatternCategory.GOALS, total_over_4_5_goals, 0.85, 30, "Total goals over 4.5")  # NEW threshold - very high
    register_pattern("total_under_4_5_goals", PatternCategory.GOALS, total_under_4_5_goals, 0.65, 25, "Total goals under 4.5")  # NEW threshold
    register_pattern("total_over_5_5_goals", PatternCategory.GOALS, total_over_5_5_goals, 0.99, 35, "Total goals over 5.5")  # NEW threshold - extremely high, disabled
    register_pattern("total_under_5_5_goals", PatternCategory.GOALS, total_under_5_5_goals, 0.60, 25, "Total goals under 5.5")  # NEW threshold


if __name__ == '__main__':
    from patterns.registry import get_pattern_registry, clear_patterns
    
    clear_patterns()
    register_serie_a_patterns()
    
    registry = get_pattern_registry()
    patterns = registry.list_patterns()
    
    print(f"✅ Registered {len(patterns)} Serie A patterns")
    print("\nPattern categories:")
    
    goals = [p for p in patterns if 'goal' in p]
    cards = [p for p in patterns if 'card' in p]
    corners = [p for p in patterns if 'corner' in p]
    results = [p for p in patterns if any(x in p for x in ['win', 'draw'])]
    
    print(f"  Goals: {len(goals)}")
    print(f"  Cards: {len(cards)} (STRONGEST in Serie A)")
    print(f"  Corners: {len(corners)}")
    print(f"  Results: {len(results)}")
