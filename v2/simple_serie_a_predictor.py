"""
Simple Serie A predictor using pattern-based approach.
Optimized for Italian football - defensive, tactical, many cards.
WITH MULTI-TIMEFRAME ENSEMBLE: Recent trends weighted more, validated across seasons!
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Optional
from dataclasses import dataclass

from data.serie_a_adapter import load_serie_a_data
from patterns.registry import get_pattern_registry, clear_patterns
from patterns.serie_a_patterns import register_serie_a_patterns
from patterns.risk_adjustment import calculate_risk_adjusted_confidence
from utils.confidence import calculate_multi_timeframe_confidence

# Optimal weight configuration from comprehensive testing (154 patterns across all leagues)
# Serie A optimal: long_term (64.2% WR, 32 patterns tested) - DIFFERENT from other leagues
SERIE_A_TIMEFRAME_WEIGHTS = {
    7: 0.15,      # Last 7 days (15%)
    14: 0.15,     # Last 14 days (15%)
    30: 0.20,     # Last 30 days (20%)
    90: 0.25,     # Last 90 days (25%)
    365: 0.25,    # Last 365 days (25%) - Serie A rewards long-term view
}


@dataclass
class BestBet:
    """Best betting recommendation for a match"""
    pattern_name: str
    confidence: float
    risk_adjusted_confidence: float
    threshold: float


class SimpleSerieAPredictor:
    """Simple Serie A predictor matching other leagues' approach"""
    
    def __init__(self):
        """Initialize with pattern registry and load data"""
        clear_patterns()
        register_serie_a_patterns()
        self.registry = get_pattern_registry()
        self.data = load_serie_a_data()
        
        # Optimized thresholds for Serie A
        # Lower thresholds for cards (very predictable)
        # Higher thresholds for goals (defensive league)
        self.thresholds = {
            # Cards - STRONGEST patterns (Italian football = tactical fouls)
            'home_over_0_5_cards': 0.55,
            'away_over_0_5_cards': 0.55,
            'home_over_1_5_cards': 0.60,
            'away_over_1_5_cards': 0.60,
            'total_over_3_5_cards': 0.58,
            'total_over_4_5_cards': 0.62,
            
            # Goals - higher thresholds (defensive league)
            'home_over_0_5_goals': 0.60,
            'away_over_0_5_goals': 0.58,
            'home_over_1_5_goals': 0.65,
            'total_over_1_5_goals': 0.58,
            'total_over_2_5_goals': 0.65,
            'total_under_2_5_goals': 0.55,  # Strong pattern
            'both_teams_to_score': 0.62,
            
            # Corners - moderate
            'home_over_3_5_corners': 0.60,
            'home_over_4_5_corners': 0.65,
            'away_over_2_5_corners': 0.60,
            'away_over_3_5_corners': 0.65,
            'total_over_8_5_corners': 0.58,
            'total_over_9_5_corners': 0.62,
            
            # Results
            'home_win': 0.62,
            'away_win_or_draw': 0.58,
            'draw': 0.68,  # Common in Serie A
            'home_win_clean_sheet': 0.65,
        }
    
    def predict_match(
        self,
        home_team: str,
        away_team: str,
        match_date: datetime,
        use_ensemble: bool = True
    ) -> Optional[BestBet]:
        """
        Predict best bet for a match using multi-timeframe ensemble approach.
        
        Uses 5 timeframes (7d, 14d, 30d, 90d, 365d) with dynamic weights favoring
        recent data, plus adjustments for trends, consistency, and sample size.
        
        Args:
            home_team: Home team name
            away_team: Away team name
            match_date: Date of the match
            use_ensemble: If True (default), use multi-timeframe ensemble. 
                         If False, use legacy 30-day average (not recommended!)
            
        Returns:
            BestBet if confidence exceeds threshold, None otherwise
        """
        best_pattern = None
        best_confidence = 0.0
        best_risk_adjusted = 0.0
        
        # Test each pattern
        for pattern_name in self.registry.list_patterns():
            if pattern_name not in self.thresholds:
                continue
            
            pattern = self.registry.get_pattern(pattern_name)
            threshold = self.thresholds[pattern_name]
            
            if use_ensemble:
                # Using optimized long_term weights from comprehensive testing
                # Serie A: 64.2% WR across 32 active patterns - long_term performs best
                confidence, debug_info = calculate_multi_timeframe_confidence(
                    self.data,
                    match_date,
                    pattern.label_fn,
                    min_matches_7d=3,
                    min_matches_30d=10,
                    custom_timeframes=SERIE_A_TIMEFRAME_WEIGHTS,
                    use_all_history=True  # UPGRADE #1: Use all historical data for trend analysis
                )
            else:
                # LEGACY: Simple 30-day average (old approach)
                cutoff_date = match_date - timedelta(days=30)
                recent_data = self.data[
                    (self.data['Date'] >= cutoff_date) & 
                    (self.data['Date'] < match_date)
                ]
                if len(recent_data) < 10:
                    continue
                results = recent_data.apply(pattern.label_fn, axis=1)
                confidence = results.mean() if len(results) > 0 else 0.5
            
            # Calculate risk-adjusted confidence
            risk_adjusted = calculate_risk_adjusted_confidence(confidence, pattern_name)
            
            # Check if meets threshold and is best so far
            if risk_adjusted >= threshold and risk_adjusted > best_risk_adjusted:
                best_pattern = pattern_name
                best_confidence = confidence
                best_risk_adjusted = risk_adjusted
        
        if best_pattern:
            return BestBet(
                pattern_name=best_pattern,
                confidence=best_confidence,
                risk_adjusted_confidence=best_risk_adjusted,
                threshold=self.thresholds[best_pattern]
            )
        
        return None


def main():
    """Test Serie A predictor"""
    import sys
    
    try:
        predictor = SimpleSerieAPredictor()
        data = predictor.data
        
        print(f"✅ Loaded {len(data)} Serie A matches")
        print(f"Date range: {data['Date'].min().date()} to {data['Date'].max().date()}")
        
        # Test on recent matches
        recent_matches = data.tail(10)
        
        print(f"\n🔮 Testing predictions on last 10 matches:\n")
        
        wins = 0
        total = 0
        
        for _, match in recent_matches.iterrows():
            prediction = predictor.predict_match(
                match['HomeTeam'],
                match['AwayTeam'],
                match['Date']
            )
            
            if prediction:
                total += 1
                pattern = predictor.registry.get_pattern(prediction.pattern_name)
                actual = pattern.label_fn(match)
                result = "✅" if actual else "❌"
                if actual:
                    wins += 1
                
                print(f"{match['Date'].strftime('%Y-%m-%d')} | {match['HomeTeam']:20s} vs {match['AwayTeam']:20s}")
                print(f"  Pattern: {prediction.pattern_name:30s} | Confidence: {prediction.risk_adjusted_confidence:.1%} | {result}")
                print(f"  Score: {int(match['FTHG'])}-{int(match['FTAG'])}")
        
        if total > 0:
            print(f"\n📊 Test Results: {wins}/{total} ({wins/total*100:.1f}% Win Rate)")
        else:
            print("\n⚠️ No predictions generated - try lowering thresholds")
        
    except FileNotFoundError as e:
        print(f"❌ {e}")
        print("\n📥 To use Serie A predictor:")
        print("1. Download Serie A CSV files from https://www.football-data.co.uk/italym.php")
        print("2. Save them as: v2/data/serie_a/I1_2021-22.csv, I1_2022-23.csv, etc.")
        print("3. Run this script again")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
