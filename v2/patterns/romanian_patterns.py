"""
Romanian league specific betting patterns.
Optimized for Liga I characteristics and team behaviors.
"""
import pandas as pd
from patterns.registry import register_pattern
from patterns.categories import PatternCategory


# Goals Patterns - Optimized for Romanian Liga I
def home_over_0_5_goals(row: pd.Series) -> bool:
    """Home team scores over 0.5 goals."""
    return row['FTHG'] > 0.5

def away_over_0_5_goals(row: pd.Series) -> bool:
    """Away team scores over 0.5 goals."""
    return row['FTAG'] > 0.5

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


# Corners Patterns - Romanian teams vary significantly in corner counts
def home_over_2_5_corners(row: pd.Series) -> bool:
    """Home team gets over 2.5 corners."""
    return row.get('HC', 0) > 2.5

def home_over_3_5_corners(row: pd.Series) -> bool:
    """Home team gets over 3.5 corners."""
    return row.get('HC', 0) > 3.5

def home_over_4_5_corners(row: pd.Series) -> bool:
    """Home team gets over 4.5 corners."""
    return row.get('HC', 0) > 4.5

def away_over_2_5_corners(row: pd.Series) -> bool:
    """Away team gets over 2.5 corners."""
    return row.get('AC', 0) > 2.5

def away_over_3_5_corners(row: pd.Series) -> bool:
    """Away team gets over 3.5 corners."""
    return row.get('AC', 0) > 3.5

def total_over_8_5_corners(row: pd.Series) -> bool:
    """Total corners over 8.5."""
    home_corners = row.get('HC', 0)
    away_corners = row.get('AC', 0)
    return (home_corners + away_corners) > 8.5

def total_over_6_5_corners(row: pd.Series) -> bool:
    """Total corners over 6.5."""
    home_corners = row.get('HC', 0)
    away_corners = row.get('AC', 0)
    return (home_corners + away_corners) > 6.5

def total_over_7_5_corners(row: pd.Series) -> bool:
    """Total corners over 7.5 - aggressive corner pattern."""
    home_corners = row.get('HC', 0)
    away_corners = row.get('AC', 0)
    return (home_corners + away_corners) > 7.5

def total_over_9_5_corners(row: pd.Series) -> bool:
    """Total corners over 9.5 - conservative corner pattern."""
    home_corners = row.get('HC', 0)
    away_corners = row.get('AC', 0)
    return (home_corners + away_corners) > 9.5

def total_over_10_5_corners(row: pd.Series) -> bool:
    """Total corners over 10.5 - high corner games."""
    home_corners = row.get('HC', 0)
    away_corners = row.get('AC', 0)
    return (home_corners + away_corners) > 10.5

def total_under_7_5_corners(row: pd.Series) -> bool:
    """Total corners under 7.5."""
    home_corners = row.get('HC', 0)
    away_corners = row.get('AC', 0)
    return (home_corners + away_corners) < 7.5

def corner_advantage_home_1_5(row: pd.Series) -> bool:
    """Home team gets 1.5+ more corners than away."""
    home_corners = row.get('HC', 0)
    away_corners = row.get('AC', 0)
    return (home_corners - away_corners) > 1.5


# Cards Patterns - Romanian league can be physical
def home_over_0_5_cards(row: pd.Series) -> bool:
    """Home team gets over 0.5 cards (at least 1 card)."""
    home_yellows = row.get('HY', 0)
    home_reds = row.get('HR', 0)
    return (home_yellows + home_reds) > 0.5

def away_over_0_5_cards(row: pd.Series) -> bool:
    """Away team gets over 0.5 cards (at least 1 card)."""
    away_yellows = row.get('AY', 0)
    away_reds = row.get('AR', 0)
    return (away_yellows + away_reds) > 0.5

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

def total_under_2_5_cards(row: pd.Series) -> bool:
    """Total cards under 2.5."""
    total_cards = row.get('HY', 0) + row.get('HR', 0) + row.get('AY', 0) + row.get('AR', 0)
    return total_cards < 2.5

def red_card_shown(row: pd.Series) -> bool:
    """At least one red card shown."""
    return (row.get('HR', 0) + row.get('AR', 0)) > 0


# Combination Patterns - More complex conditions
def home_win_clean_sheet(row: pd.Series) -> bool:
    """Home wins without conceding."""
    return row['FTR'] == 'H' and row['FTAG'] == 0

def away_win_or_draw(row: pd.Series) -> bool:
    """Away team doesn't lose."""
    return row['FTR'] in ['A', 'D']

def high_scoring_home_win(row: pd.Series) -> bool:
    """Home wins with 3+ goals scored."""
    return row['FTR'] == 'H' and row['FTHG'] >= 3

def defensive_match(row: pd.Series) -> bool:
    """Low goals and low corners (defensive match)."""
    total_goals = row['FTHG'] + row['FTAG']
    total_corners = row.get('HC', 0) + row.get('AC', 0)
    return total_goals <= 1 and total_corners <= 6


# Register all Romanian-specific patterns
def register_romanian_patterns():
    """Register all Romanian Liga I specific patterns."""
    
    # Goals patterns
    register_pattern("home_over_0_5_goals", PatternCategory.GOALS, home_over_0_5_goals, 0.70, 15, "Home team scores at least 1 goal")
    register_pattern("away_over_0_5_goals", PatternCategory.GOALS, away_over_0_5_goals, 0.65, 15, "Away team scores at least 1 goal")
    register_pattern("home_over_2_5_goals", PatternCategory.GOALS, home_over_2_5_goals, 0.75, 25, "Home team scores over 2.5 goals")
    register_pattern("away_over_1_5_goals", PatternCategory.GOALS, away_over_1_5_goals, 0.65, 20, "Away team scores over 1.5 goals")
    register_pattern("away_over_2_5_goals", PatternCategory.GOALS, away_over_2_5_goals, 0.75, 25, "Away team scores over 2.5 goals")
    register_pattern("total_over_1_5_goals", PatternCategory.GOALS, total_over_1_5_goals, 0.60, 15, "Total goals over 1.5")
    register_pattern("total_over_2_5_goals", PatternCategory.GOALS, total_over_2_5_goals, 0.65, 20, "Total goals over 2.5")
    register_pattern("total_under_2_5_goals", PatternCategory.GOALS, total_under_2_5_goals, 0.60, 20, "Total goals under 2.5")
    register_pattern("total_over_3_5_goals", PatternCategory.GOALS, total_over_3_5_goals, 0.75, 25, "Total goals over 3.5")
    register_pattern("both_teams_to_score", PatternCategory.GOALS, both_teams_to_score, 0.95, 20, "Both teams to score")
    register_pattern("home_win_and_over_2_5", PatternCategory.GOALS, home_win_and_over_2_5, 0.70, 25, "Home win and over 2.5 goals")
    register_pattern("draw_and_under_2_5", PatternCategory.GOALS, draw_and_under_2_5, 0.75, 30, "Draw and under 2.5 goals")
    
    # Corners patterns
    register_pattern("home_over_2_5_corners", PatternCategory.CORNERS, home_over_2_5_corners, 0.65, 15, "Home team over 2.5 corners")
    register_pattern("home_over_3_5_corners", PatternCategory.CORNERS, home_over_3_5_corners, 0.70, 20, "Home team over 3.5 corners")
    register_pattern("home_over_4_5_corners", PatternCategory.CORNERS, home_over_4_5_corners, 0.75, 25, "Home team over 4.5 corners")
    register_pattern("away_over_2_5_corners", PatternCategory.CORNERS, away_over_2_5_corners, 0.65, 15, "Away team over 2.5 corners")
    register_pattern("away_over_3_5_corners", PatternCategory.CORNERS, away_over_3_5_corners, 0.70, 20, "Away team over 3.5 corners")
    register_pattern("total_over_6_5_corners", PatternCategory.CORNERS, total_over_6_5_corners, 0.72, 18, "Total corners over 6.5 - very aggressive")
    register_pattern("total_over_7_5_corners", PatternCategory.CORNERS, total_over_7_5_corners, 0.68, 18, "Total corners over 7.5 - aggressive")
    register_pattern("total_over_8_5_corners", PatternCategory.CORNERS, total_over_8_5_corners, 0.70, 20, "Total corners over 8.5 - sweet spot")
    register_pattern("total_over_9_5_corners", PatternCategory.CORNERS, total_over_9_5_corners, 0.75, 25, "Total corners over 9.5 - conservative")
    register_pattern("total_over_10_5_corners", PatternCategory.CORNERS, total_over_10_5_corners, 0.80, 30, "Total corners over 10.5 - high corner games")
    register_pattern("total_under_7_5_corners", PatternCategory.CORNERS, total_under_7_5_corners, 0.60, 15, "Total corners under 7.5")
    register_pattern("corner_advantage_home_1_5", PatternCategory.CORNERS, corner_advantage_home_1_5, 0.75, 25, "Home team 1.5+ corner advantage")
    
    # Cards patterns - Starting with 0.5+ (like other leagues)
    register_pattern("home_over_0_5_cards", PatternCategory.CARDS, home_over_0_5_cards, 0.60, 15, "Home team over 0.5 cards (at least 1)")
    register_pattern("away_over_0_5_cards", PatternCategory.CARDS, away_over_0_5_cards, 0.60, 15, "Away team over 0.5 cards (at least 1)")
    register_pattern("home_over_1_5_cards", PatternCategory.CARDS, home_over_1_5_cards, 0.70, 20, "Home team over 1.5 cards")
    register_pattern("home_over_2_5_cards", PatternCategory.CARDS, home_over_2_5_cards, 0.75, 25, "Home team over 2.5 cards")
    register_pattern("home_over_3_5_cards", PatternCategory.CARDS, home_over_3_5_cards, 0.80, 30, "Home team over 3.5 cards")
    register_pattern("home_over_4_5_cards", PatternCategory.CARDS, home_over_4_5_cards, 0.99, 30, "Home team over 4.5 cards")
    register_pattern("away_over_1_5_cards", PatternCategory.CARDS, away_over_1_5_cards, 0.70, 20, "Away team over 1.5 cards")
    register_pattern("away_over_2_5_cards", PatternCategory.CARDS, away_over_2_5_cards, 0.75, 25, "Away team over 2.5 cards")
    register_pattern("away_over_3_5_cards", PatternCategory.CARDS, away_over_3_5_cards, 0.80, 30, "Away team over 3.5 cards")
    register_pattern("away_over_4_5_cards", PatternCategory.CARDS, away_over_4_5_cards, 0.99, 30, "Away team over 4.5 cards")
    register_pattern("total_over_3_5_cards", PatternCategory.CARDS, total_over_3_5_cards, 0.65, 20, "Total cards over 3.5")
    register_pattern("total_over_4_5_cards", PatternCategory.CARDS, total_over_4_5_cards, 0.70, 25, "Total cards over 4.5")
    register_pattern("total_over_5_5_cards", PatternCategory.CARDS, total_over_5_5_cards, 0.80, 30, "Total cards over 5.5")
    register_pattern("total_over_1_5_cards", PatternCategory.CARDS, total_over_1_5_cards, 0.65, 15, "Total cards over 1.5")  # NEW threshold
    register_pattern("total_under_1_5_cards", PatternCategory.CARDS, total_under_1_5_cards, 0.75, 15, "Total cards under 1.5")  # NEW threshold
    register_pattern("total_over_2_5_cards", PatternCategory.CARDS, total_over_2_5_cards, 0.70, 18, "Total cards over 2.5")  # NEW threshold
    register_pattern("total_under_2_5_cards", PatternCategory.CARDS, total_under_2_5_cards, 0.65, 15, "Total cards under 2.5")
    register_pattern("red_card_shown", PatternCategory.CARDS, red_card_shown, 0.80, 30, "At least one red card")
    
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
    
    # Combination patterns
    register_pattern("home_win_clean_sheet", PatternCategory.GOALS, home_win_clean_sheet, 0.75, 25, "Home wins to nil")
    register_pattern("away_win_or_draw", PatternCategory.GOALS, away_win_or_draw, 0.60, 15, "Away team doesn't lose")
    register_pattern("high_scoring_home_win", PatternCategory.GOALS, high_scoring_home_win, 0.80, 30, "Home wins 3+ goals")
    register_pattern("defensive_match", PatternCategory.GOALS, defensive_match, 0.75, 25, "Low goals and corners")