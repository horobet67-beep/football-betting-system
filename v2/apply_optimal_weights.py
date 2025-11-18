"""
Apply Optimal Weights to All League Predictors
Updates each predictor file with its league-specific optimal weight configuration
"""

# Optimal weights determined from testing
OPTIMAL_WEIGHTS = {
    "Serie A": {
        "config_name": "Balanced",
        "weights": {
            7: 0.20,    # Last 7 days: 20%
            14: 0.20,   # Last 14 days: 20%
            30: 0.20,   # Last 30 days: 20%
            90: 0.15,   # Last 90 days: 15%
            365: 0.15,  # Last 365 days: 15%
            730: 0.10   # Last 2 years: 10%
        },
        "win_rate": 96.0,
        "avg_confidence": 92.5
    },
    "Bundesliga": {
        "config_name": "Extreme Recent",
        "weights": {
            7: 0.40,    # Last 7 days: 40%
            14: 0.30,   # Last 14 days: 30%
            30: 0.15,   # Last 30 days: 15%
            90: 0.10,   # Last 90 days: 10%
            365: 0.05   # Last 365 days: 5%
        },
        "win_rate": 100.0,
        "avg_confidence": 96.8
    },
    "La Liga": {
        "config_name": "Extreme Recent",
        "weights": {
            7: 0.40,    # Last 7 days: 40%
            14: 0.30,   # Last 14 days: 30%
            30: 0.15,   # Last 30 days: 15%
            90: 0.10,   # Last 90 days: 10%
            365: 0.05   # Last 365 days: 5%
        },
        "win_rate": 100.0,
        "avg_confidence": 95.9
    },
    "Premier League": {
        "config_name": "Extreme Recent",
        "weights": {
            7: 0.40,    # Last 7 days: 40%
            14: 0.30,   # Last 14 days: 30%
            30: 0.15,   # Last 30 days: 15%
            90: 0.10,   # Last 90 days: 10%
            365: 0.05   # Last 365 days: 5%
        },
        "win_rate": 82.5,
        "avg_confidence": 89.5
    },
    "Romania": {
        "config_name": "Extreme Recent",
        "weights": {
            7: 0.40,    # Last 7 days: 40%
            14: 0.30,   # Last 14 days: 30%
            30: 0.15,   # Last 30 days: 15%
            90: 0.10,   # Last 90 days: 10%
            365: 0.05   # Last 365 days: 5%
        },
        "win_rate": 100.0,
        "avg_confidence": 96.5
    }
}


def format_weights_dict(weights: dict) -> str:
    """Format weights dictionary for Python code"""
    lines = ["{"]
    for days, weight in weights.items():
        lines.append(f"    {days}: {weight:.2f},")
    lines.append("}")
    return "\n".join(lines)


def main():
    """Display optimal weights for manual application"""
    
    print("=" * 100)
    print(" " * 30 + "🎯 OPTIMAL WEIGHTS APPLICATION GUIDE 🎯")
    print("=" * 100)
    
    print("\nOptimal configurations determined from 30-day backtesting:")
    print("\n" + "-" * 100)
    
    for league, config in OPTIMAL_WEIGHTS.items():
        print(f"\n{'=' * 100}")
        print(f"🔹 {league.upper()}")
        print(f"{'=' * 100}")
        print(f"Configuration: {config['config_name']}")
        print(f"Win Rate: {config['win_rate']:.1f}%")
        print(f"Avg Confidence: {config['avg_confidence']:.1f}%")
        print(f"\nWeights to apply:")
        print(format_weights_dict(config['weights']))
        print()
    
    print("=" * 100)
    print("\n📝 IMPLEMENTATION INSTRUCTIONS:\n")
    print("For each predictor file (simple_*_predictor.py):")
    print("1. Find the calculate_multi_timeframe_confidence() call")
    print("2. Add parameter: custom_timeframes=OPTIMAL_WEIGHTS")
    print("3. Define OPTIMAL_WEIGHTS constant at top of file with values above")
    print("4. Ensure use_all_history=True is set")
    print("\nExample:")
    print("""
# At top of file
OPTIMAL_WEIGHTS = {
    7: 0.40,
    14: 0.30,
    30: 0.15,
    90: 0.10,
    365: 0.05
}

# In prediction logic
confidence, debug_info = calculate_multi_timeframe_confidence(
    data,
    match_date,
    pattern.label_fn,
    custom_timeframes=OPTIMAL_WEIGHTS,  # <-- Add this
    use_all_history=True,
    min_matches_7d=2,
    min_matches_30d=8
)
""")
    
    print("\n" + "=" * 100)
    print("⚠️  NOTE: Serie A uses 6 timeframes (includes 730 days)")
    print("    Others use 5 timeframes (7/14/30/90/365 days)")
    print("=" * 100)
    
    # Summary table
    print("\n📊 QUICK REFERENCE TABLE:\n")
    print(f"{'League':<20} {'Configuration':<20} {'7d':<8} {'14d':<8} {'30d':<8} {'90d':<8} {'365d':<8} {'730d':<8}")
    print("-" * 100)
    
    for league, config in OPTIMAL_WEIGHTS.items():
        weights = config['weights']
        row = f"{league:<20} {config['config_name']:<20}"
        row += f" {weights.get(7, 0):.2f}   {weights.get(14, 0):.2f}   "
        row += f"{weights.get(30, 0):.2f}   {weights.get(90, 0):.2f}   "
        row += f"{weights.get(365, 0):.2f}   {weights.get(730, 0):.2f}"
        print(row)
    
    print("\n" + "=" * 100)


if __name__ == "__main__":
    main()
