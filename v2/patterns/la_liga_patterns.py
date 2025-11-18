"""
La Liga (Spain) specific betting patterns.
Optimized for Spanish first division characteristics and team behaviors.
La Liga known for: Technical play, lower cards than PL, moderate corners, tactical discipline.
"""
import pandas as pd
from patterns.registry import register_pattern
from patterns.categories import PatternCategory


# Goals Patterns - La Liga averages ~2.5 goals/match (similar to Bundesliga)
def home_over_0_5_goals(row: pd.Series) -> bool:
    """Home team scores over 0.5 goals."""
    return row['FTHG'] > 0.5

def away_over_0_5_goals(row: pd.Series) -> bool:
    """Away team scores over 0.5 goals."""
    return row['FTAG'] > 0.5

def home_over_1_5_goals(row: pd.Series) -> bool:
    """Home team scores over 1.5 goals."""
    return row['FTHG'] > 1.5

def home_over_2_5_goals(row: pd.Series) -> bool:
    """Home team scores over 2.5 goals."""
    return row['FTHG'] > 2.5

def away_over_1_5_goals(row: pd.Series) -> bool:
    """Away team scores over 1.5 goals."""
    return row['FTAG'] > 1.5

def away_over_2_5_goals(row: pd.Series) -> bool:
    """Away team scores over 2.5 goals."""
    return row['FTAG'] > 2.5

def total_over_1_5_goals(row: pd.Series) -> bool:
    """Total goals over 1.5."""
    return (row['FTHG'] + row['FTAG']) > 1.5

def total_over_2_5_goals(row: pd.Series) -> bool:
    """Total goals over 2.5."""
    return (row['FTHG'] + row['FTAG']) > 2.5

def total_under_2_5_goals(row: pd.Series) -> bool:
    """Total goals under 2.5."""
    return (row['FTHG'] + row['FTAG']) < 2.5

def total_over_3_5_goals(row: pd.Series) -> bool:
    """Total goals over 3.5."""
    return (row['FTHG'] + row['FTAG']) > 3.5

def both_teams_to_score(row: pd.Series) -> bool:
    """Both teams score (BTTS)."""
    return row['FTHG'] > 0 and row['FTAG'] > 0

def home_win_and_over_2_5(row: pd.Series) -> bool:
    """Home win and over 2.5 total goals."""
    return row['FTR'] == 'H' and (row['FTHG'] + row['FTAG']) > 2.5

def draw_and_under_2_5(row: pd.Series) -> bool:
    """Draw result and under 2.5 goals."""
    return row['FTR'] == 'D' and (row['FTHG'] + row['FTAG']) < 2.5


# Corners Patterns - La Liga averages ~10 corners/match (higher than PL/Bundesliga)
def home_over_2_5_corners(row: pd.Series) -> bool:
    """Home team gets over 2.5 corners."""
    return row.get('HC', 0) > 2.5

def home_over_3_5_corners(row: pd.Series) -> bool:
    """Home team gets over 3.5 corners."""
    return row.get('HC', 0) > 3.5

def home_over_4_5_corners(row: pd.Series) -> bool:
    """Home team gets over 4.5 corners."""
    return row.get('HC', 0) > 4.5

def home_over_5_5_corners(row: pd.Series) -> bool:
    """Home team gets over 5.5 corners."""
    return row.get('HC', 0) > 5.5

def away_over_2_5_corners(row: pd.Series) -> bool:
    """Away team gets over 2.5 corners."""
    return row.get('AC', 0) > 2.5

def away_over_3_5_corners(row: pd.Series) -> bool:
    """Away team gets over 3.5 corners."""
    return row.get('AC', 0) > 3.5

def away_over_4_5_corners(row: pd.Series) -> bool:
    """Away team gets over 4.5 corners."""
    return row.get('AC', 0) > 4.5

def home_over_6_5_corners(row: pd.Series) -> bool:
    """Home team gets over 6.5 corners."""
    return row.get('HC', 0) > 6.5

def away_over_6_5_corners(row: pd.Series) -> bool:
    """Away team gets over 6.5 corners."""
    return row.get('AC', 0) > 6.5

def total_over_6_5_corners(row: pd.Series) -> bool:
    """Total corners over 6.5."""
    home_corners = row.get('HC', 0)
    away_corners = row.get('AC', 0)
    return (home_corners + away_corners) > 6.5

def total_over_7_5_corners(row: pd.Series) -> bool:
    """Total corners over 7.5."""
    home_corners = row.get('HC', 0)
    away_corners = row.get('AC', 0)
    return (home_corners + away_corners) > 7.5

def total_over_8_5_corners(row: pd.Series) -> bool:
    """Total corners over 8.5."""
    home_corners = row.get('HC', 0)
    away_corners = row.get('AC', 0)
    return (home_corners + away_corners) > 8.5

def total_over_9_5_corners(row: pd.Series) -> bool:
    """Total corners over 9.5."""
    home_corners = row.get('HC', 0)
    away_corners = row.get('AC', 0)
    return (home_corners + away_corners) > 9.5

def total_over_10_5_corners(row: pd.Series) -> bool:
    """Total corners over 10.5 - La Liga sweet spot."""
    home_corners = row.get('HC', 0)
    away_corners = row.get('AC', 0)
    return (home_corners + away_corners) > 10.5

def total_over_11_5_corners(row: pd.Series) -> bool:
    """Total corners over 11.5."""
    home_corners = row.get('HC', 0)
    away_corners = row.get('AC', 0)
    return (home_corners + away_corners) > 11.5

def total_under_8_5_corners(row: pd.Series) -> bool:
    """Total corners under 8.5."""
    home_corners = row.get('HC', 0)
    away_corners = row.get('AC', 0)
    return (home_corners + away_corners) < 8.5


# Cards Patterns - La Liga has LOWER card counts than Premier League
def home_over_0_5_cards(row: pd.Series) -> bool:
    """Home team gets over 0.5 cards."""
    home_yellows = row.get('HY', 0)
    home_reds = row.get('HR', 0)
    return (home_yellows + home_reds) > 0.5

def home_over_1_5_cards(row: pd.Series) -> bool:
    """Home team gets over 1.5 cards."""
    home_yellows = row.get('HY', 0)
    home_reds = row.get('HR', 0)
    return (home_yellows + home_reds) > 1.5

def home_over_2_5_cards(row: pd.Series) -> bool:
    """Home team gets over 2.5 cards."""
    home_yellows = row.get('HY', 0)
    home_reds = row.get('HR', 0)
    return (home_yellows + home_reds) > 2.5

def away_over_0_5_cards(row: pd.Series) -> bool:
    """Away team gets over 0.5 cards."""
    away_yellows = row.get('AY', 0)
    away_reds = row.get('AR', 0)
    return (away_yellows + away_reds) > 0.5

def away_over_1_5_cards(row: pd.Series) -> bool:
    """Away team gets over 1.5 cards."""
    away_yellows = row.get('AY', 0)
    away_reds = row.get('AR', 0)
    return (away_yellows + away_reds) > 1.5

def away_over_2_5_cards(row: pd.Series) -> bool:
    """Away team gets over 2.5 cards."""
    away_yellows = row.get('AY', 0)
    away_reds = row.get('AR', 0)
    return (away_yellows + away_reds) > 2.5

def home_over_3_5_cards(row: pd.Series) -> bool:
    """Home team gets over 3.5 cards."""
    home_yellows = row.get('HY', 0)
    home_reds = row.get('HR', 0)
    return (home_yellows + home_reds) > 3.5

def away_over_3_5_cards(row: pd.Series) -> bool:
    """Away team gets over 3.5 cards."""
    away_yellows = row.get('AY', 0)
    away_reds = row.get('AR', 0)
    return (away_yellows + away_reds) > 3.5

def home_over_4_5_cards(row: pd.Series) -> bool:
    """Home team gets over 4.5 cards."""
    home_yellows = row.get('HY', 0)
    home_reds = row.get('HR', 0)
    return (home_yellows + home_reds) > 4.5

def away_over_4_5_cards(row: pd.Series) -> bool:
    """Away team gets over 4.5 cards."""
    away_yellows = row.get('AY', 0)
    away_reds = row.get('AR', 0)
    return (away_yellows + away_reds) > 4.5

def total_over_3_5_cards(row: pd.Series) -> bool:
    """Total cards over 3.5."""
    total_cards = row.get('HY', 0) + row.get('HR', 0) + row.get('AY', 0) + row.get('AR', 0)
    return total_cards > 3.5

def total_over_4_5_cards(row: pd.Series) -> bool:
    """Total cards over 4.5."""
    total_cards = row.get('HY', 0) + row.get('HR', 0) + row.get('AY', 0) + row.get('AR', 0)
    return total_cards > 4.5

def total_over_5_5_cards(row: pd.Series) -> bool:
    """Total cards over 5.5."""
    total_cards = row.get('HY', 0) + row.get('HR', 0) + row.get('AY', 0) + row.get('AR', 0)
    return total_cards > 5.5

def total_over_1_5_cards(row: pd.Series) -> bool:
    """Total cards over 1.5."""
    total_cards = row.get('HY', 0) + row.get('HR', 0) + row.get('AY', 0) + row.get('AR', 0)
    return total_cards > 1.5

def total_under_1_5_cards(row: pd.Series) -> bool:
    """Total cards under 1.5."""
    total_cards = row.get('HY', 0) + row.get('HR', 0) + row.get('AY', 0) + row.get('AR', 0)
    return total_cards < 1.5

def total_over_2_5_cards(row: pd.Series) -> bool:
    """Total cards over 2.5."""
    total_cards = row.get('HY', 0) + row.get('HR', 0) + row.get('AY', 0) + row.get('AR', 0)
    return total_cards > 2.5

def total_under_2_5_cards(row: pd.Series) -> bool:
    """Total cards under 2.5."""
    total_cards = row.get('HY', 0) + row.get('HR', 0) + row.get('AY', 0) + row.get('AR', 0)
    return total_cards < 2.5

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

def total_under_3_5_cards(row: pd.Series) -> bool:
    """Total cards under 3.5."""
    total_cards = row.get('HY', 0) + row.get('HR', 0) + row.get('AY', 0) + row.get('AR', 0)
    return total_cards < 3.5


# Combination Patterns
def home_win_clean_sheet(row: pd.Series) -> bool:
    """Home wins without conceding."""
    return row['FTR'] == 'H' and row['FTAG'] == 0

def away_win_or_draw(row: pd.Series) -> bool:
    """Away team doesn't lose."""
    return row['FTR'] in ['A', 'D']

def high_scoring_draw(row: pd.Series) -> bool:
    """Draw with 3+ total goals."""
    return row['FTR'] == 'D' and (row['FTHG'] + row['FTAG']) >= 3


# Register all La Liga-specific patterns
def register_la_liga_patterns():
    """
    Register all La Liga specific patterns.
    Initial thresholds based on league characteristics:
    - Lower cards than Premier League (technical play)
    - Higher corners than Bundesliga (~10 avg vs ~7.5)
    - Moderate goals (~2.5 avg, similar to other top leagues)
    """
    
    # Goals patterns - OPTIMIZED based on 2024-25 analysis
    register_pattern("home_over_0_5_goals", PatternCategory.GOALS, home_over_0_5_goals, 0.65, 15, "Home team scores at least 1 goal")  # 79.2% WR - lowered
    register_pattern("away_over_0_5_goals", PatternCategory.GOALS, away_over_0_5_goals, 0.70, 15, "Away team scores at least 1 goal")  # 69.7% WR - raised
    register_pattern("home_over_1_5_goals", PatternCategory.GOALS, home_over_1_5_goals, 0.99, 20, "Home team scores over 1.5 goals")  # 38.0% WR - DISABLED
    register_pattern("home_over_2_5_goals", PatternCategory.GOALS, home_over_2_5_goals, 0.99, 25, "Home team scores over 2.5 goals")  # 17.2% WR - DISABLED
    register_pattern("away_over_1_5_goals", PatternCategory.GOALS, away_over_1_5_goals, 0.99, 20, "Away team scores over 1.5 goals")  # 32.2% WR - DISABLED
    register_pattern("away_over_2_5_goals", PatternCategory.GOALS, away_over_2_5_goals, 0.99, 25, "Away team scores over 2.5 goals")  # 10.8% WR - DISABLED
    register_pattern("total_over_1_5_goals", PatternCategory.GOALS, total_over_1_5_goals, 0.60, 15, "Total goals over 1.5")  # 72.3% WR - keep
    register_pattern("total_over_2_5_goals", PatternCategory.GOALS, total_over_2_5_goals, 0.99, 20, "Total goals over 2.5")  # 48.5% WR - DISABLED
    register_pattern("total_under_2_5_goals", PatternCategory.GOALS, total_under_2_5_goals, 0.99, 20, "Total goals under 2.5")  # 51.5% WR - DISABLED
    register_pattern("total_over_3_5_goals", PatternCategory.GOALS, total_over_3_5_goals, 0.99, 25, "Total goals over 3.5")  # 24.0% WR - DISABLED
    register_pattern("both_teams_to_score", PatternCategory.GOALS, both_teams_to_score, 0.99, 20, "Both teams to score")  # 54.4% WR - DISABLED
    register_pattern("home_win_and_over_2_5", PatternCategory.GOALS, home_win_and_over_2_5, 0.99, 25, "Home win and over 2.5 goals")  # 25.1% WR - DISABLED
    register_pattern("draw_and_under_2_5", PatternCategory.GOALS, draw_and_under_2_5, 0.99, 30, "Draw and under 2.5 goals")  # 20.6% WR - DISABLED
    
    # Corners patterns - OPTIMIZED based on 2024-25 analysis
    register_pattern("home_over_2_5_corners", PatternCategory.CORNERS, home_over_2_5_corners, 0.55, 15, "Home team over 2.5 corners")  # 86.0% WR - lowered ⭐
    register_pattern("home_over_3_5_corners", PatternCategory.CORNERS, home_over_3_5_corners, 0.70, 20, "Home team over 3.5 corners")  # 69.4% WR - raised
    register_pattern("home_over_4_5_corners", PatternCategory.CORNERS, home_over_4_5_corners, 0.99, 25, "Home team over 4.5 corners")  # 54.1% WR - DISABLED
    register_pattern("home_over_5_5_corners", PatternCategory.CORNERS, home_over_5_5_corners, 0.99, 30, "Home team over 5.5 corners")  # 39.3% WR - DISABLED
    register_pattern("away_over_2_5_corners", PatternCategory.CORNERS, away_over_2_5_corners, 0.60, 15, "Away team over 2.5 corners")  # 74.1% WR - keep
    register_pattern("away_over_3_5_corners", PatternCategory.CORNERS, away_over_3_5_corners, 0.99, 20, "Away team over 3.5 corners")  # 57.5% WR - DISABLED
    register_pattern("away_over_4_5_corners", PatternCategory.CORNERS, away_over_4_5_corners, 0.99, 25, "Away team over 4.5 corners")  # 38.8% WR - DISABLED
    register_pattern("home_over_6_5_corners", PatternCategory.CORNERS, home_over_6_5_corners, 0.99, 30, "Home team over 6.5 corners")
    register_pattern("away_over_6_5_corners", PatternCategory.CORNERS, away_over_6_5_corners, 0.99, 30, "Away team over 6.5 corners")
    register_pattern("total_over_6_5_corners", PatternCategory.CORNERS, total_over_6_5_corners, 0.72, 18, "Total corners over 6.5")
    register_pattern("total_over_7_5_corners", PatternCategory.CORNERS, total_over_7_5_corners, 0.60, 15, "Total corners over 7.5")  # 71.8% WR - keep
    register_pattern("total_over_8_5_corners", PatternCategory.CORNERS, total_over_8_5_corners, 0.99, 18, "Total corners over 8.5")  # 57.5% WR - DISABLED
    register_pattern("total_over_9_5_corners", PatternCategory.CORNERS, total_over_9_5_corners, 0.99, 20, "Total corners over 9.5")  # 46.7% WR - DISABLED
    register_pattern("total_over_10_5_corners", PatternCategory.CORNERS, total_over_10_5_corners, 0.99, 22, "Total corners over 10.5")  # 35.4% WR - DISABLED
    register_pattern("total_over_11_5_corners", PatternCategory.CORNERS, total_over_11_5_corners, 0.99, 25, "Total corners over 11.5")  # 24.5% WR - DISABLED
    register_pattern("total_under_8_5_corners", PatternCategory.CORNERS, total_under_8_5_corners, 0.99, 15, "Total corners under 8.5")  # 42.5% WR - DISABLED
    
    # Cards patterns - OPTIMIZED based on 2024-25 analysis
    register_pattern("home_over_0_5_cards", PatternCategory.CARDS, home_over_0_5_cards, 0.60, 15, "Home team over 0.5 cards")  # 87.9% WR - lowered ⭐
    register_pattern("home_over_1_5_cards", PatternCategory.CARDS, home_over_1_5_cards, 0.75, 20, "Home team over 1.5 cards")  # 65.7% WR - raised
    register_pattern("home_over_2_5_cards", PatternCategory.CARDS, home_over_2_5_cards, 0.99, 25, "Home team over 2.5 cards")  # 41.2% WR - DISABLED
    register_pattern("home_over_3_5_cards", PatternCategory.CARDS, home_over_3_5_cards, 0.99, 30, "Home team over 3.5 cards")
    register_pattern("home_over_4_5_cards", PatternCategory.CARDS, home_over_4_5_cards, 0.99, 30, "Home team over 4.5 cards")
    register_pattern("away_over_0_5_cards", PatternCategory.CARDS, away_over_0_5_cards, 0.60, 15, "Away team over 0.5 cards")  # 91.0% WR - lowered ⭐
    register_pattern("away_over_1_5_cards", PatternCategory.CARDS, away_over_1_5_cards, 0.75, 20, "Away team over 1.5 cards")  # 69.1% WR - raised
    register_pattern("away_over_2_5_cards", PatternCategory.CARDS, away_over_2_5_cards, 0.99, 25, "Away team over 2.5 cards")  # 43.5% WR - DISABLED
    register_pattern("away_over_3_5_cards", PatternCategory.CARDS, away_over_3_5_cards, 0.99, 30, "Away team over 3.5 cards")
    register_pattern("away_over_4_5_cards", PatternCategory.CARDS, away_over_4_5_cards, 0.99, 30, "Away team over 4.5 cards")
    register_pattern("total_over_3_5_cards", PatternCategory.CARDS, total_over_3_5_cards, 0.70, 20, "Total cards over 3.5")  # 67.3% WR - raised
    register_pattern("total_over_4_5_cards", PatternCategory.CARDS, total_over_4_5_cards, 0.99, 25, "Total cards over 4.5")  # 47.5% WR - DISABLED
    register_pattern("total_over_5_5_cards", PatternCategory.CARDS, total_over_5_5_cards, 0.99, 30, "Total cards over 5.5")
    register_pattern("total_over_1_5_cards", PatternCategory.CARDS, total_over_1_5_cards, 0.65, 15, "Total cards over 1.5")  # NEW threshold
    register_pattern("total_under_1_5_cards", PatternCategory.CARDS, total_under_1_5_cards, 0.75, 15, "Total cards under 1.5")  # NEW threshold
    register_pattern("total_over_2_5_cards", PatternCategory.CARDS, total_over_2_5_cards, 0.70, 18, "Total cards over 2.5")  # NEW threshold
    register_pattern("total_under_2_5_cards", PatternCategory.CARDS, total_under_2_5_cards, 0.75, 18, "Total cards under 2.5")  # NEW threshold
    register_pattern("total_under_3_5_cards", PatternCategory.CARDS, total_under_3_5_cards, 0.99, 15, "Total cards under 3.5")  # 32.7% WR - DISABLED
    
    # NEW Corner patterns - 8.5 threshold for home/away
    register_pattern("home_over_8_5_corners", PatternCategory.CORNERS, home_over_8_5_corners, 0.99, 30, "Home team over 8.5 corners")  # Very high threshold - disabled initially
    register_pattern("home_under_8_5_corners", PatternCategory.CORNERS, home_under_8_5_corners, 0.99, 30, "Home team under 8.5 corners")  # Very high threshold - disabled initially
    register_pattern("away_over_8_5_corners", PatternCategory.CORNERS, away_over_8_5_corners, 0.99, 30, "Away team over 8.5 corners")  # Very high threshold - disabled initially
    register_pattern("away_under_8_5_corners", PatternCategory.CORNERS, away_under_8_5_corners, 0.99, 30, "Away team under 8.5 corners")  # Very high threshold - disabled initially
    
    # NEW Goals patterns - 4.5 and 5.5 thresholds
    register_pattern("total_over_4_5_goals", PatternCategory.GOALS, total_over_4_5_goals, 0.85, 30, "Total goals over 4.5")  # NEW threshold - very high
    register_pattern("total_under_4_5_goals", PatternCategory.GOALS, total_under_4_5_goals, 0.70, 25, "Total goals under 4.5")  # NEW threshold
    register_pattern("total_over_5_5_goals", PatternCategory.GOALS, total_over_5_5_goals, 0.99, 35, "Total goals over 5.5")  # NEW threshold - extremely high, disabled
    register_pattern("total_under_5_5_goals", PatternCategory.GOALS, total_under_5_5_goals, 0.65, 25, "Total goals under 5.5")  # NEW threshold
    
    # Combination patterns - OPTIMIZED based on 2024-25 analysis
    register_pattern("home_win_clean_sheet", PatternCategory.GOALS, home_win_clean_sheet, 0.99, 25, "Home wins to nil")  # 24.8% WR - DISABLED
    register_pattern("away_win_or_draw", PatternCategory.GOALS, away_win_or_draw, 0.99, 15, "Away team doesn't lose")  # 55.7% WR - DISABLED
    register_pattern("high_scoring_draw", PatternCategory.GOALS, high_scoring_draw, 0.99, 30, "High scoring draw")  # 5.0% WR - DISABLED
