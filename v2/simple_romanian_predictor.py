"""
Simple Romanian Liga I predictor using pattern-based approach (like Bundesliga/La Liga)
WITH MULTI-TIMEFRAME ENSEMBLE: Recent trends weighted more, validated across seasons!
"""

import pandas as pd
from datetime import datetime, timedelta
from typing import Optional
from dataclasses import dataclass

from patterns.registry import get_pattern_registry, clear_patterns
from patterns.romanian_patterns import register_romanian_patterns
from patterns.risk_adjustment import calculate_risk_adjusted_confidence
from utils.confidence import calculate_multi_timeframe_confidence

# Optimal weight configuration from comprehensive testing (154 patterns across all leagues)
# Romanian Liga optimal: long_term (75.9% WR, 37 patterns tested) - DIFFERENT from other leagues
ROMANIAN_TIMEFRAME_WEIGHTS = {
    7: 0.15,      # Last 7 days (15%)
    14: 0.15,     # Last 14 days (15%)
    30: 0.20,     # Last 30 days (20%)
    90: 0.25,     # Last 90 days (25%)
    365: 0.25,    # Last 365 days (25%) - Romanian Liga rewards long-term view
}


@dataclass
class BestBet:
    """Best betting recommendation for a match"""
    pattern_name: str
    confidence: float
    risk_adjusted_confidence: float
    threshold: float


class SimpleRomanianPredictor:
    """Simple Romanian Liga I predictor matching Bundesliga/La Liga approach"""
    
    def __init__(self):
        """Initialize with pattern registry"""
        # Load data first
        from data.romanian_adapter import load_romanian_data
        self.data = load_romanian_data(include_future=False)
        print(f"Loaded {len(self.data)} Romanian Liga I matches")
        print(f"Date range: {self.data['Date'].min()} to {self.data['Date'].max()}")
        
        clear_patterns()
        register_romanian_patterns()
        self.registry = get_pattern_registry()
        
        # Optimized thresholds - lowered to generate more predictions
        self.thresholds = {
            'home_over_0_5_goals': 0.55,
            'away_over_0_5_goals': 0.55,
            'home_over_0_5_cards': 0.55,
            'away_over_0_5_cards': 0.55,
            'home_over_1_5_goals': 0.65,
            'away_over_1_5_goals': 0.65,
            'total_over_1_5_goals': 0.58,
            'total_over_2_5_goals': 0.62,
            'total_under_2_5_goals': 0.70,
            'both_teams_to_score': 0.60,
            'home_over_2_5_corners': 0.65,
            'away_over_2_5_corners': 0.65,
            'total_over_8_5_corners': 0.60,
            'home_over_1_5_cards': 0.65,
            'away_over_1_5_cards': 0.65,
        }
    
    def predict_match(
        self,
        home_team: str,
        away_team: str,
        historical_data: pd.DataFrame,
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
            historical_data: Historical match data
            match_date: Date of the match
            use_ensemble: If True (default), use multi-timeframe ensemble
            
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
                # Romanian Liga: 75.9% WR across 37 active patterns - long_term performs best
                confidence, debug_info = calculate_multi_timeframe_confidence(
                    historical_data,
                    match_date,
                    pattern.label_fn,
                    min_matches_7d=2,
                    min_matches_30d=8,
                    custom_timeframes=ROMANIAN_TIMEFRAME_WEIGHTS,
                    use_all_history=True  # UPGRADE #1: Use all historical data for trend analysis
                )
            else:
                # LEGACY: Simple 30-day average
                recent_data = historical_data.tail(30)
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
