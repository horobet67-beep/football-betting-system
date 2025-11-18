# Optimal Weight Configurations by League

**Analysis Date**: November 18, 2025  
**Methodology**: Comprehensive testing of ALL active patterns (154 total) across 5 leagues using 5 different weight configurations with parallel processing (4 CPU cores).

**Test Scope**:
- **154 total patterns** tested (only patterns with threshold < 0.99)
- **27-45 test periods** per league (30-day windows)
- **~35,000 individual tests** across all combinations
- **Execution Time**: 13 minutes (783 seconds) with parallel processing

---

## Executive Summary

**Key Finding**: Pattern weight preferences vary by league AND by pattern type. The comprehensive testing reveals:

- **3 leagues** perform best with **extreme_recent** (Premier League, Bundesliga, La Liga)
- **2 leagues** perform best with **long_term** (Serie A, Romanian Liga) ⚠️ UPDATED
- **La Liga** shows highest overall performance (88.4% WR) 🏆
- **Card patterns** universally excel with recent weights (90%+ WR)

---

## Recommended Configurations

### 🏴󠁧󠁢󠁥󠁮󠁧󠁿 Premier League
**Configuration**: `extreme_recent` ✅ IMPLEMENTED  
**Average Win Rate**: 72.1%  
**Patterns Tested**: 28 active patterns (17 disabled/high threshold)

```python
PREMIER_LEAGUE_TIMEFRAME_WEIGHTS = {
    7: 0.40,    # Last 7 days (40%)
    14: 0.30,   # Last 14 days (30%)
    30: 0.15,   # Last 30 days (15%)
    90: 0.10,   # Last 90 days (10%)
    365: 0.05   # Last 365 days (5%)
}
```

**Pattern Distribution** (what each pattern prefers):
- **extreme_recent**: 11 patterns prefer this 🎯
- **long_term**: 8 patterns
- **recent_heavy**: 5 patterns
- **balanced**: 3 patterns
- **season_focused**: 1 pattern

**Top Performing Patterns** (comprehensive test):
- `total_under_5_5_goals`: 92.7% WR (774/835) - extreme_recent
- `total_over_1_5_cards`: 89.7% WR (753/839) - long_term
- `away_over_0_5_cards`: 89.4% WR (750/839) - extreme_recent ⭐
- `home_over_0_5_cards`: 85.7% WR (715/834) - extreme_recent ⭐
- `home_over_2_5_corners`: 84.6% WR (691/817) - extreme_recent

---

### 🇩🇪 Bundesliga
**Configuration**: `extreme_recent` ✅ IMPLEMENTED  
**Average Win Rate**: 52.6%  
**Patterns Tested**: 38 active patterns (largest test set)

```python
BUNDESLIGA_TIMEFRAME_WEIGHTS = {
    7: 0.40,    # Last 7 days (40%)
    14: 0.30,   # Last 14 days (30%)
    30: 0.15,   # Last 30 days (15%)
    90: 0.10,   # Last 90 days (10%)
    365: 0.05   # Last 365 days (5%)
}
```

**Pattern Distribution**:
- **extreme_recent**: 15 patterns prefer this 🎯 (most)
- **long_term**: 9 patterns
- **balanced**: 6 patterns
- **recent_heavy**: 5 patterns
- **season_focused**: 3 patterns

**Top Performing Patterns**:
- `defensive_match`: 100.0% WR (210/210) - extreme_recent 🔥
- `draw_and_under_2_5`: 100.0% WR (197/197) - long_term 🔥
- `total_under_2_5_goals`: 98.1% WR (211/215) - season_focused
- `total_under_7_5_corners`: 98.1% WR (203/207) - long_term
- `total_under_1_5_cards`: 97.7% WR (210/215) - extreme_recent
- `total_under_2_5_cards`: 96.0% WR (216/225) - extreme_recent
- `total_under_5_5_goals`: 90.9% WR (1085/1194) - season_focused
- `total_over_1_5_cards`: 88.8% WR (874/984) - long_term

**Note**: Bundesliga shows balanced pattern preferences but extreme_recent wins overall.

---

### 🇪🇸 La Liga
**Configuration**: `extreme_recent` ✅ IMPLEMENTED  
**Average Win Rate**: 88.4% 🏆 HIGHEST PERFORMING LEAGUE  
**Patterns Tested**: 19 active patterns

```python
LA_LIGA_TIMEFRAME_WEIGHTS = {
    7: 0.40,    # Last 7 days (40%)
    14: 0.30,   # Last 14 days (30%)
    30: 0.15,   # Last 30 days (15%)
    90: 0.10,   # Last 90 days (10%)
    365: 0.05   # Last 365 days (5%)
}
```

**Pattern Distribution**:
- **extreme_recent**: 8 patterns prefer this 🎯
- **balanced**: 5 patterns
- **long_term**: 4 patterns
- **season_focused**: 2 patterns

**Top Performing Patterns** (La Liga is a GOLDMINE 🔥):
- `total_under_1_5_cards`: 100.0% WR (252/252) - extreme_recent 🔥🔥🔥
- `total_under_2_5_cards`: 100.0% WR (238/238) - long_term 🔥🔥🔥
- `total_under_5_5_goals`: 95.1% WR (1408/1481) - extreme_recent ⭐⭐⭐
- `total_over_1_5_cards`: 93.5% WR (1144/1223) - extreme_recent ⭐⭐⭐
- `away_over_0_5_cards`: 92.5% WR (1130/1221) - extreme_recent ⭐⭐
- `total_under_4_5_goals`: 89.6% WR (1324/1478) - balanced
- `home_over_0_5_cards`: 88.5% WR (1083/1224) - extreme_recent
- `total_over_2_5_cards`: 83.4% WR (1000/1199) - extreme_recent

**Note**: La Liga card patterns are EXCEPTIONALLY predictable with recent data! This is the best performing league overall.

---

### 🇮🇹 Serie A
**Configuration**: `long_term` ✅ IMPLEMENTED ⚠️ DIFFERENT  
**Average Win Rate**: 64.2%  
**Patterns Tested**: 32 active patterns

```python
SERIE_A_TIMEFRAME_WEIGHTS = {
    7: 0.15,    # Last 7 days (15%)
    14: 0.15,   # Last 14 days (15%)
    30: 0.20,   # Last 30 days (20%)
    90: 0.25,   # Last 90 days (25%) ← More weight on quarter
    365: 0.25   # Last 365 days (25%) ← More weight on season
}
```

**Pattern Distribution**:
- **long_term**: 10 patterns prefer this 🎯 (most!)
- **extreme_recent**: 8 patterns
- **balanced**: 6 patterns
- **season_focused**: 4 patterns
- **recent_heavy**: 4 patterns

**Top Performing Patterns**:
- `total_under_5_5_goals`: 96.1% WR (1166/1213) - extreme_recent ⭐⭐
- `away_over_0_5_cards`: 93.0% WR (1130/1215) - extreme_recent ⭐⭐
- `total_over_1_5_cards`: 92.1% WR (1119/1215) - extreme_recent ⭐
- `total_under_4_5_goals`: 88.9% WR (1078/1212) - long_term
- `home_over_0_5_cards`: 86.9% WR (1056/1215) - season_focused
- `total_over_2_5_cards`: 80.9% WR (971/1200) - season_focused
- `total_over_6_5_corners`: 79.8% WR (898/1126) - extreme_recent

**Note**: Serie A is unique - long_term configuration wins overall despite some patterns preferring extreme_recent. Italian football's tactical consistency rewards longer historical view.

---

### 🇷🇴 Romanian Liga 1
**Configuration**: `long_term` ✅ IMPLEMENTED ⚠️ DIFFERENT  
**Average Win Rate**: 75.9%  
**Patterns Tested**: 37 active patterns

```python
ROMANIAN_TIMEFRAME_WEIGHTS = {
    7: 0.15,    # Last 7 days (15%)
    14: 0.15,   # Last 14 days (15%)
    30: 0.20,   # Last 30 days (20%)
    90: 0.25,   # Last 90 days (25%) ← More weight on quarter
    365: 0.25   # Last 365 days (25%) ← More weight on season
}
```

**Pattern Distribution**:
- **long_term**: 11 patterns prefer this 🎯 (most!)
- **extreme_recent**: 8 patterns
- **recent_heavy**: 8 patterns
- **balanced**: 7 patterns
- **season_focused**: 3 patterns

**Top Performing Patterns**:
- `defensive_match`: 100.0% WR (106/106) - extreme_recent 🔥
- `draw_and_under_2_5`: 100.0% WR (86/86) - long_term 🔥
- `total_under_1_5_cards`: 99.0% WR (104/105) - balanced
- `total_under_2_5_cards`: 99.1% WR (105/106) - balanced
- `total_under_7_5_corners`: 97.8% WR (87/89) - long_term
- `total_under_5_5_goals`: 96.3% WR (1104/1146) - long_term ⭐
- `total_over_1_5_cards`: 91.5% WR (947/1035) - recent_heavy ⭐
- `away_over_0_5_cards`: 91.0% WR (942/1035) - recent_heavy ⭐
- `total_under_4_5_goals`: 90.9% WR (1024/1127) - extreme_recent
- `home_over_0_5_cards`: 88.6% WR (914/1032) - recent_heavy

**Note**: Romanian Liga shows similar behavior to Serie A - long_term configuration wins overall. Smaller league size (16 teams) benefits from broader historical context.

---

## Implementation Recommendations

### ✅ IMPLEMENTED - All League Predictors Updated

1. **Premier League** → `extreme_recent` weights (72.1% WR, 28 patterns)
2. **Bundesliga** → `extreme_recent` weights (52.6% WR, 38 patterns)
3. **La Liga** → `extreme_recent` weights (88.4% WR, 19 patterns) 🏆
4. **Serie A** → `long_term` weights (64.2% WR, 32 patterns)
5. **Romanian Liga** → `long_term` weights (75.9% WR, 37 patterns)

### Pattern-Specific Insights

**🎴 Card Patterns** (Universal Winners):
ALL leagues show 85-95%+ win rates on card patterns with optimized weights:
- `total_over_1_5_cards`: 88-94% WR across all leagues
- `away_over_0_5_cards`: 89-93% WR across all leagues
- `total_under_*_cards`: 96-100% WR on under patterns

**⚽ Goals Patterns**:
- **Under goals** patterns: 89-96% WR (extremely reliable!)
  - `total_under_5_5_goals`: 91-96% WR
  - `total_under_4_5_goals`: 83-91% WR
- **Over goals** patterns: Mixed (55-83% WR)
  - Generally prefer long_term or balanced weights

**🚩 Corner Patterns**:
- **Wide variation** by league (51-87% WR)
- **Premier League**: Strong with extreme_recent (72-85% WR)
- **Bundesliga**: Prefer long_term (73-84% WR)
- **La Liga**: Mixed preferences (52-84% WR)
- **Serie A/Romania**: Long-term wins (57-80% WR)

---

## Statistical Insights

### Why Different Leagues Need Different Weights

**Extreme Recent** (Premier League, Bundesliga, La Liga):
1. **High Competition**: Top-tier leagues have more squad rotation and tactical variation
2. **Recent Form Matters**: Injuries, suspensions, momentum captured in last 7-14 days
3. **Manager Changes**: Tactical shifts happen quickly in competitive leagues
4. **Media Pressure**: Form swings more volatile in high-pressure environments

**Long Term** (Serie A, Romanian Liga):
1. **Tactical Consistency**: Italian football's defensive structure remains stable over seasons
2. **Smaller Leagues**: Romanian Liga (16 teams) has less weekly variation
3. **Squad Stability**: Less rotation = longer patterns hold true
4. **Historical Patterns**: Established team styles persist across multiple months

### Why La Liga Excels (88.4% WR)

1. **Card Discipline Patterns**: Spanish refereeing is highly consistent and predictable
2. **Tactical Uniformity**: La Liga teams play similar styles (possession-based)
3. **Yellow Card Culture**: Specific players/teams accumulate cards predictably
4. **Data Quality**: Excellent historical data with consistent recording

### Why Serie A & Romania Prefer Long-Term

1. **Serie A**: Tactical sophistication means team identity > recent form
   - Defensive systems take months to break down (or strengthen)
   - "Catenaccio" mentality = stable card/corner patterns
   
2. **Romanian Liga**: Smaller league dynamics
   - 16 teams = play each other more often
   - Less squad depth = starting XI stays consistent
   - Broader historical sample reduces variance

### Configuration Trade-offs

| Configuration | Best For | Win Rate Range | Prediction Volume | Variance |
|--------------|----------|----------------|-------------------|----------|
| **extreme_recent** | PL, BUN, LAL | 52-88% | Medium | Higher |
| **long_term** | SER, ROM | 64-76% | Higher | Lower |
| **balanced** | Backup option | 62-74% | Highest | Medium |
| **recent_heavy** | Not optimal | 55-70% | Medium | Medium |
| **season_focused** | Specific patterns | 60-79% | Medium-High | Medium-Low |

---

## Next Steps

1. ✅ **COMPLETED**: Implemented optimal configurations in all league predictors
2. ✅ **COMPLETED**: Updated `predict_all_leagues_range.py` with new weight info
3. 🔄 **READY**: System prepared for production predictions between any date range
4. 📊 **TODO**: Run predictions for upcoming week and validate live results
5. � **TODO**: Monthly re-optimization to track if weights need seasonal adjustments

### How to Use the Optimized System

```bash
# Predict all leagues for a specific date range
cd v2
python3 predict_all_leagues_range.py --start-date 2025-11-18 --end-date 2025-11-24

# Each league will automatically use its optimized weights:
# - Premier League, Bundesliga, La Liga: extreme_recent (40/30/15/10/5)
# - Serie A, Romanian Liga: long_term (15/15/20/25/25)
```

---

## Code Implementation

### Already Implemented in Each Predictor:

```python
# simple_premier_league_predictor.py
PREMIER_LEAGUE_TIMEFRAME_WEIGHTS = {
    7: 0.40, 14: 0.30, 30: 0.15, 90: 0.10, 365: 0.05
}

# simple_bundesliga_predictor.py
BUNDESLIGA_TIMEFRAME_WEIGHTS = {
    7: 0.40, 14: 0.30, 30: 0.15, 90: 0.10, 365: 0.05
}

# simple_la_liga_predictor.py
LA_LIGA_TIMEFRAME_WEIGHTS = {
    7: 0.40, 14: 0.30, 30: 0.15, 90: 0.10, 365: 0.05
}

# simple_serie_a_predictor.py
SERIE_A_TIMEFRAME_WEIGHTS = {
    7: 0.15, 14: 0.15, 30: 0.20, 90: 0.25, 365: 0.25  # DIFFERENT!
}

# simple_romanian_predictor.py
ROMANIAN_TIMEFRAME_WEIGHTS = {
    7: 0.15, 14: 0.15, 30: 0.20, 90: 0.25, 365: 0.25  # DIFFERENT!
}
```

All predictors automatically use these weights in their confidence calculations via:

```python
confidence, debug_info = calculate_multi_timeframe_confidence(
    historical_data,
    match_date,
    pattern.label_fn,
    min_matches_7d=2,
    min_matches_30d=8,
    custom_timeframes=LEAGUE_TIMEFRAME_WEIGHTS,  # Optimized weights
    use_all_history=False
)
```

---

**Analysis Complete**: Comprehensive testing of 154 active patterns across 5 leagues with ~35,000 individual tests completed in 13 minutes using parallel processing 🎯

**Key Takeaway**: Not all leagues are the same! Premier/Bundesliga/La Liga thrive on recent data, while Serie A and Romanian Liga require longer historical context for optimal predictions.
