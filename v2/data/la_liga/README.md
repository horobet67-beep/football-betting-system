# La Liga Data Setup

## Overview
La Liga (Spanish La Liga) integration for the football betting system v2.

## Data Requirements
Download CSV files from your data source and place them in this directory with the following naming convention:

```
spain-la-liga-matches-2022-to-2023-stats.csv
spain-la-liga-matches-2023-to-2024-stats.csv
spain-la-liga-matches-2024-to-2025-stats.csv
spain-la-liga-matches-2025-to-2026-stats.csv
```

## Required Columns
The CSV files should contain these columns (same format as Bundesliga/Premier League):

### Basic Match Info
- `date_GMT` - Match date
- `home_team_name` - Home team name
- `away_team_name` - Away team name
- `referee` - Referee name (optional)

### Goals
- `home_team_goal_count` - Full-time home goals
- `away_team_goal_count` - Full-time away goals
- `home_team_goal_count_half_time` - Half-time home goals
- `away_team_goal_count_half_time` - Half-time away goals

### Corners
- `home_team_corner_count` - Home team corners
- `away_team_corner_count` - Away team corners

### Cards
- `home_team_yellow_cards` - Home team yellow cards
- `home_team_red_cards` - Home team red cards
- `away_team_yellow_cards` - Away team yellow cards
- `away_team_red_cards` - Away team red cards

### Shots (Optional)
- `home_team_shots` - Home team shots
- `away_team_shots` - Away team shots
- `home_team_shots_on_target` - Home team shots on target
- `away_team_shots_on_target` - Away team shots on target

### Other (Optional)
- `home_team_fouls` - Home team fouls
- `away_team_fouls` - Away team fouls
- `odds_ft_home_team_win` - Home win odds
- `odds_ft_draw` - Draw odds
- `odds_ft_away_team_win` - Away win odds

## La Liga Characteristics
- **Average Corners**: ~10 per match (higher than Premier League/Bundesliga)
- **Average Goals**: ~2.5 per match (similar to other top leagues)
- **Average Cards**: Lower than Premier League (more technical, less physical play)
- **Teams**: 20 teams, 38 matches per season
- **Season**: August to May

## Next Steps
1. Download data files from your source
2. Place CSV files in this directory
3. Run validation: `python validate_la_liga_seasons.py`
4. Analyze patterns and optimize thresholds
5. Compare to Premier League/Bundesliga performance

## Initial Pattern Strategy
Based on La Liga characteristics:
- **Corners**: Start with lower thresholds (higher corner volume)
  - `total_over_10_5_corners` at 0.68 threshold (vs 0.75+ for other leagues)
- **Cards**: Start with higher thresholds (lower card volume)
  - `away_over_0_5_cards` at 0.65 (vs 0.60 for Premier League)
- **Goals**: Conservative approach initially
  - BTTS, away_over_1.5_goals, total_over_3.5_goals DISABLED (0.99 threshold)

## Optimization Process
After initial validation:
1. Identify high-performing patterns (75%+ WR, 20+ bets)
2. Lower thresholds on proven patterns
3. Disable underperforming patterns (<50% WR)
4. Identify team specialties (corner specialists, card-heavy teams)
5. Apply improvements 5-6 (team specialties, confidence calibration)
6. Re-validate and compare to other leagues
