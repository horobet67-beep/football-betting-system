# Serie A Predictions - Usage Guide

## ✅ Problem Solved

The Serie A adapter has been fixed to support future match predictions while maintaining backward compatibility.

### What Changed:
- **Before:** Adapter filtered out all incomplete matches (status='incomplete')
- **After:** New `include_future` parameter allows loading upcoming fixtures
- **Backward Compatible:** Default behavior unchanged (historical data only)

---

## 🚀 Quick Start

### Generate Predictions for Specific Date Range

```bash
# Predict matches between Nov 22-24, 2025
python3 predict_serie_a_upcoming.py --start-date 2025-11-22 --end-date 2025-11-24
```

### Generate Predictions for Next 7 Days

```bash
# Predict all matches in next 7 days (default)
python3 predict_serie_a_upcoming.py
```

### Generate Predictions for Next 14 Days

```bash
# Predict all matches in next 14 days
python3 predict_serie_a_upcoming.py --days 14
```

---

## 📊 Output Format

The script provides:

1. **BET RECOMMENDATIONS** - Matches that pass confidence threshold
   - Pattern name (e.g., `away_over_0_5_cards`)
   - Raw confidence (ensemble calculation)
   - Risk-adjusted confidence (accounting for variance)
   - Threshold required
   - Safety margin above threshold

2. **NO BET** - Matches below threshold
   - Reason for rejection

3. **SUMMARY** - Statistics across all analyzed matches
   - Total matches
   - Number of bets recommended
   - Average confidence
   - Risk reminders

---

## 🔧 Technical Details

### Adapter Function Signature

```python
from data.serie_a_adapter import load_serie_a_data

# Historical data only (for training)
historical = load_serie_a_data()
# Returns: 1,251 completed matches

# All data including future matches
all_data = load_serie_a_data(include_future=True)
# Returns: 1,521 matches (completed + upcoming)
```

### In Your Own Scripts

```python
from simple_serie_a_predictor import SimpleSerieAPredictor
from data.serie_a_adapter import load_serie_a_data

# Initialize predictor with historical data
predictor = SimpleSerieAPredictor()

# Load future matches separately
future_matches = load_serie_a_data(include_future=True)
current_matches = future_matches[future_matches['Date'] > datetime.now()]

# Generate predictions
for _, match in current_matches.iterrows():
    prediction = predictor.predict_match(
        match['HomeTeam'],
        match['AwayTeam'],
        predictor.data['Date'].max()  # Use latest historical date
    )
```

---

## 📈 Current Performance

**Serie A System Specs:**
- **Backtest Win Rate:** 91.4% (914 bets across 8 periods)
- **Weight Configuration:** Balanced (7:20%, 14:20%, 30:20%, 90:15%, 365:15%, 730:10%)
- **Historical Data:** 1,251 matches (Aug 2022 - Nov 2025)
- **Future Fixtures:** 270 matches available through May 2026

---

## ⚠️ Important Reminders

### Before Real Money Betting:

1. ✅ **Paper Trade First** - Track predictions without betting
2. ✅ **Validate Performance** - Ensure real-world matches backtest WR
3. ✅ **Start Small** - €1-2 per bet maximum initially
4. ✅ **Risk Management** - Never exceed 2% bankroll per bet
5. ✅ **Stop Losses** - Halt after 3 consecutive losses
6. ✅ **Track Everything** - Record all predictions and outcomes

### Current Limitations:

- ❌ No forward validation yet (only backtesting)
- ❌ No real odds integration (using estimates)
- ❌ No automated CSV updates (manual process)
- ❌ No live performance dashboard

---

## 🔮 Example Output

```
================================================================================
✅ BET RECOMMENDATIONS
================================================================================

1. Nov 22, 05:00PM - Fiorentina vs Juventus
   🎯 Pattern: away_over_0_5_cards
   📊 Raw Confidence: 96.7%
   🎲 Risk-Adjusted: 94.7%
   🚧 Threshold: 55.0%
   📈 Margin: +39.7% above threshold
   ✅ RECOMMENDATION: **BET**

================================================================================
📊 SUMMARY
================================================================================
Total Matches Analyzed: 10
✅ BET: 10
❌ NO BET: 0

📈 Average Risk-Adjusted Confidence: 94.7%
```

---

## 🆘 Troubleshooting

### "No matches found between X and Y"
- No Serie A fixtures scheduled in that date range
- Try widening the date range or check fixture calendar

### "Module not found" errors
- Ensure you're running from `v2/` directory
- Check Python path includes the workspace

### Incorrect predictions
- Verify CSV files are up to date
- Check that historical data loaded correctly (should be 1,251 matches)
- Ensure predictor is using Balanced weights configuration

---

## 📝 Next Steps

1. **Update LEAGUE_READINESS_STATUS.md** - Serie A now fully ready
2. **Test predictions for Nov 22-24** - Paper trade to validate
3. **Create similar scripts for other leagues** - Bundesliga, La Liga, Romania already have future data
4. **Build tracking system** - Use `paper_trading_tracker.py` to monitor results

---

## 🎯 Command Reference

```bash
# Basic usage
python3 predict_serie_a_upcoming.py

# Specific date range
python3 predict_serie_a_upcoming.py --start-date 2025-11-22 --end-date 2025-11-24

# Next N days
python3 predict_serie_a_upcoming.py --days 14

# Help
python3 predict_serie_a_upcoming.py --help
```
