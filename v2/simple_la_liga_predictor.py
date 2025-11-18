#!/usr/bin/env python3
"""
Simple La Liga Predictor

Direct prediction system using form-weighted heuristics for Spanish La Liga.
Based on proven Premier League system with improvements 1-6.
WITH MULTI-TIMEFRAME ENSEMBLE: Recent trends weighted more, validated across seasons!
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import argparse
import sys
from typing import List, Dict, Tuple, Optional
import logging

# Add v2 to path
sys.path.append('.')

from patterns.registry import get_pattern_registry, clear_patterns
from patterns.la_liga_patterns import register_la_liga_patterns
from patterns.risk_adjustment import calculate_risk_adjusted_confidence, explain_risk_adjustment
from data.la_liga_adapter import load_la_liga_data
from utils.confidence import calculate_multi_timeframe_confidence

# Optimal weight configuration from comprehensive testing (154 patterns across all leagues)
# La Liga optimal: extreme_recent (88.4% WR, 19 patterns tested) - HIGHEST PERFORMING LEAGUE
LA_LIGA_TIMEFRAME_WEIGHTS = {
    7: 0.40,      # Last 7 days - Ultra Recent (40%)
    14: 0.30,     # Last 14 days - Recent (30%)
    30: 0.15,     # Last 30 days - Short Term (15%)
    90: 0.10,     # Last 90 days - Quarter (10%)
    365: 0.05,    # Last 365 days - Full Season (5%)
}

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)


class SimpleLaLigaPredictor:
    """
    La Liga predictor with Premier League-proven improvements 1-6:
    1. Pattern filtering
    2. Advanced corner style analysis
    3. Dynamic confidence thresholds
    4. Ensemble confidence scoring
    5. Team specialty adjustments
    6. Confidence calibration
    """
    
    def __init__(self, lookback_days: int = 30):
        """Initialize La Liga predictor with lookback period"""
        self.lookback_days = lookback_days
        
        # Load historical data
        self.data = load_la_liga_data(include_future=False)
        print(f"Loaded {len(self.data)} La Liga matches")
        print(f"Date range: {self.data['Date'].min()} to {self.data['Date'].max()}")
        
        # OPTIMIZED thresholds based on 2024-25 season analysis
        self.confidence_thresholds = {
            # Corner patterns - La Liga specific (86% WR home_over_2.5!)
            'home_over_2_5_corners': 0.55,    # 86.0% WR ⭐ LOWERED
            'away_over_2_5_corners': 0.60,    # 74.1% WR - keep
            'total_over_7_5_corners': 0.60,   # 71.8% WR - keep
            'home_over_3_5_corners': 0.70,    # 69.4% WR - raised
            'total_over_10_5_corners': 0.99,  # 35.4% WR - DISABLED
            'total_over_9_5_corners': 0.99,   # 46.7% WR - DISABLED
            'total_over_8_5_corners': 0.99,   # 57.5% WR - DISABLED
            'total_over_11_5_corners': 0.99,  # 24.5% WR - DISABLED
            'home_over_4_5_corners': 0.99,    # 54.1% WR - DISABLED
            'home_over_5_5_corners': 0.99,    # 39.3% WR - DISABLED
            'away_over_3_5_corners': 0.99,    # 57.5% WR - DISABLED
            'away_over_4_5_corners': 0.99,    # 38.8% WR - DISABLED
            'total_under_8_5_corners': 0.99,  # 42.5% WR - DISABLED
            
            # Card patterns - Stars: over_0.5 cards (87-91% WR!)
            'away_over_0_5_cards': 0.60,      # 91.0% WR ⭐ LOWERED
            'home_over_0_5_cards': 0.60,      # 87.9% WR ⭐ LOWERED
            'away_over_1_5_cards': 0.75,      # 69.1% WR - raised
            'home_over_1_5_cards': 0.75,      # 65.7% WR - raised
            'total_over_3_5_cards': 0.70,     # 67.3% WR - raised
            'home_over_2_5_cards': 0.99,      # 41.2% WR - DISABLED
            'away_over_2_5_cards': 0.99,      # 43.5% WR - DISABLED
            'total_over_4_5_cards': 0.99,     # 47.5% WR - DISABLED
            'total_under_3_5_cards': 0.99,    # 32.7% WR - DISABLED
            
            # Goal patterns - Optimized (most disabled, low WR in La Liga)
            'home_over_0_5_goals': 0.65,      # 79.2% WR - lowered
            'total_over_1_5_goals': 0.60,     # 72.3% WR - keep
            'away_over_0_5_goals': 0.70,      # 69.7% WR - raised
            'both_teams_to_score': 0.99,      # 54.4% WR - DISABLED
            'total_over_2_5_goals': 0.99,     # 48.5% WR - DISABLED
            'total_under_2_5_goals': 0.99,    # 51.5% WR - DISABLED
            'away_over_1_5_goals': 0.99,      # 32.2% WR - DISABLED
            'total_over_3_5_goals': 0.99,     # 24.0% WR - DISABLED
            'home_over_1_5_goals': 0.99,      # 38.0% WR - DISABLED
            'home_over_2_5_goals': 0.99,      # 17.2% WR - DISABLED
            'away_over_2_5_goals': 0.99,      # 10.8% WR - DISABLED
            
            # Combination patterns - All disabled (poor performance)
            'home_win_and_over_2_5': 0.99,    # 25.1% WR - DISABLED
            'draw_and_under_2_5': 0.99,       # 20.6% WR - DISABLED
            'home_win_clean_sheet': 0.99,     # 24.8% WR - DISABLED
            'away_win_or_draw': 0.99,         # 55.7% WR - DISABLED
            'high_scoring_draw': 0.99,        # 5.0% WR - DISABLED
        }
        
        # Expected odds
        self.expected_odds = {
            'over_0_5_goals': 1.20,
            'over_1_5_goals': 1.60,
            'over_2_5_goals': 2.20,
            'over_3_5_goals': 3.80,
            'under_2_5_goals': 1.80,
            'btts': 1.85,
            'over_0_5_cards': 1.30,
            'over_1_5_cards': 1.70,
            'over_2_5_cards': 2.80,
            'over_7_5_corners': 1.70,
            'over_8_5_corners': 1.90,
            'over_9_5_corners': 2.20,
            'over_10_5_corners': 2.60,
            'over_11_5_corners': 3.50,
        }
    
    def get_team_recent_form(self, team: str, historical_data: pd.DataFrame) -> float:
        """Calculate recent form score with 3x weighting for last 5 matches"""
        team_matches = historical_data[
            (historical_data['HomeTeam'] == team) | 
            (historical_data['AwayTeam'] == team)
        ].tail(10)
        
        if len(team_matches) < 3:
            return 0.5
        
        last_5 = team_matches.tail(5)
        prev_5 = team_matches.head(len(team_matches) - 5) if len(team_matches) > 5 else pd.DataFrame()
        
        recent_score = self._calculate_form_score(last_5, team)
        older_score = self._calculate_form_score(prev_5, team) if len(prev_5) > 0 else 0.5
        
        return 0.75 * recent_score + 0.25 * older_score
    
    def _calculate_form_score(self, matches: pd.DataFrame, team: str) -> float:
        """Calculate form score for given matches"""
        if len(matches) == 0:
            return 0.5
        
        scores = []
        for _, match in matches.iterrows():
            is_home = match['HomeTeam'] == team
            
            if match['FTR'] == ('H' if is_home else 'A'):
                result_score = 1.0
            elif match['FTR'] == 'D':
                result_score = 0.5
            else:
                result_score = 0.0
            
            goals = match['FTHG'] if is_home else match['FTAG']
            goal_score = min(goals / 3.0, 1.0)
            
            scores.append(0.7 * result_score + 0.3 * goal_score)
        
        return np.mean(scores)
    
    def get_team_corner_style(self, team: str, historical_data: pd.DataFrame, is_home: bool) -> Dict[str, float]:
        """IMPROVEMENT 2: Analyze team's corner-taking patterns"""
        team_matches = historical_data[
            (historical_data['HomeTeam'] == team) if is_home 
            else (historical_data['AwayTeam'] == team)
        ].tail(10)
        
        if len(team_matches) < 3:
            return {'avg': 5.0, 'volatility': 1.0, 'style': 'neutral'}
        
        corners = team_matches['HC' if is_home else 'AC'].values
        avg_corners = np.mean(corners)
        volatility = np.std(corners) if len(corners) > 1 else 1.0
        
        # Classify playing style (La Liga has higher corners)
        if avg_corners > 6.5:
            style = 'attacking'
        elif avg_corners < 4.0:
            style = 'defensive'
        else:
            style = 'balanced'
        
        return {
            'avg': avg_corners,
            'volatility': volatility,
            'style': style,
            'recent_trend': corners[-3:].mean() - corners[:-3].mean() if len(corners) >= 6 else 0
        }
    
    def get_team_specialty_boost(
        self,
        pattern_name: str,
        home_team: str,
        away_team: str,
        historical_data: pd.DataFrame
    ) -> float:
        """
        IMPROVEMENT 5: Team-specific specialty adjustments.
        Will identify La Liga corner/card specialists after initial testing.
        """
        # Placeholder - will identify specialists after analyzing data
        # La Liga teams known for: Barcelona/Real Madrid (high corners), 
        # Athletic Bilbao/Getafe (defensive, fewer corners)
        
        return 0.0  # Start neutral, optimize after data analysis
    
    def get_ensemble_confidence_boost(
        self, 
        pattern_name: str,
        home_style: Dict,
        away_style: Dict
    ) -> float:
        """IMPROVEMENT 4: Ensemble confidence scoring"""
        boost = 0.0
        
        if 'corner' in pattern_name.lower():
            total_avg = home_style['avg'] + away_style['avg']
            
            # La Liga specific thresholds (higher corners)
            if 'over_10_5' in pattern_name and total_avg > 10.5:
                boost += 0.05
            elif 'over_9_5' in pattern_name and total_avg > 9.5:
                boost += 0.05
            elif 'over_8_5' in pattern_name and total_avg > 8.5:
                boost += 0.05
            
            if home_style['style'] == 'attacking' and away_style['style'] == 'attacking':
                boost += 0.03
            
            if home_style['volatility'] < 1.5 and away_style['volatility'] < 1.5:
                boost += 0.02
        
        return boost
    
    def apply_confidence_calibration(self, raw_confidence: float) -> float:
        """
        IMPROVEMENT 6: Confidence calibration.
        Based on Premier League analysis showing over-confidence in 85-95% range.
        """
        if 0.85 <= raw_confidence < 0.90:
            return raw_confidence * 0.90  # 10% reduction
        elif 0.90 <= raw_confidence < 0.95:
            return raw_confidence * 0.92  # 8% reduction
        elif raw_confidence >= 0.95:
            return raw_confidence * 0.88  # 12% reduction
        else:
            return raw_confidence  # No adjustment below 85%
    
    def predict_match(
        self,
        home_team: str,
        away_team: str,
        historical_data: pd.DataFrame,
        match_date: Optional[datetime] = None
    ) -> List[Dict]:
        """Predict patterns for a single match"""
        
        if match_date is None:
            match_date = datetime.now()
        
        recommendations = []
        registry = get_pattern_registry()
        
        home_form = self.get_team_recent_form(home_team, historical_data)
        away_form = self.get_team_recent_form(away_team, historical_data)
        
        home_corner_style = self.get_team_corner_style(home_team, historical_data, is_home=True)
        away_corner_style = self.get_team_corner_style(away_team, historical_data, is_home=False)
        
        for pattern in registry.get_all_patterns():
            pattern_name = pattern.name
            
            threshold = self.confidence_thresholds.get(pattern_name, pattern.default_threshold)
            
            # Calculate base confidence with MULTI-TIMEFRAME ENSEMBLE
            confidence = self._calculate_pattern_confidence(
                pattern_name, home_team, away_team, historical_data, match_date
            )
            
            if confidence == 0:
                continue
            
            # IMPROVEMENT 3: Dynamic threshold adjustment based on form
            if 'home' in pattern_name:
                confidence *= (0.85 + 0.15 * home_form)
            elif 'away' in pattern_name:
                confidence *= (0.85 + 0.15 * away_form)
            else:
                confidence *= (0.85 + 0.15 * (home_form + away_form) / 2)
            
            # IMPROVEMENT 4: Ensemble boost
            ensemble_boost = self.get_ensemble_confidence_boost(
                pattern_name, home_corner_style, away_corner_style
            )
            confidence += ensemble_boost
            
            # IMPROVEMENT 5: Team specialty boost
            specialty_boost = self.get_team_specialty_boost(
                pattern_name, home_team, away_team, historical_data
            )
            confidence += specialty_boost
            
            # IMPROVEMENT 6: Confidence calibration
            confidence = self.apply_confidence_calibration(confidence)
            
            # Cap confidence
            confidence = min(confidence, 0.95)
            
            estimated_odds = self._estimate_odds(pattern_name)
            expected_value = (confidence * (estimated_odds - 1)) - (1 - confidence)
            
            reasoning = f"Form: H={home_form:.2f} A={away_form:.2f}"
            if ensemble_boost > 0:
                reasoning += f", Ensemble: +{ensemble_boost:.2f}"
            if specialty_boost != 0:
                reasoning += f", Specialty: {specialty_boost:+.2f}"
            
            rec = {
                'match_id': f"{home_team}_vs_{away_team}",
                'home_team': home_team,
                'away_team': away_team,
                'pattern_name': pattern_name,
                'confidence': confidence,
                'threshold': threshold,
                'expected_value': expected_value,
                'reasoning': reasoning,
                'recommendation': "BET" if confidence >= threshold and expected_value > 0.05 else "NO BET"
            }
            
            recommendations.append(rec)
        
        # Select BEST BET per match using RISK-ADJUSTED confidence
        # CRITICAL: Select by CONFIDENCE with risk adjustment (not EV - odds are dummy estimates)
        bet_recommendations = [r for r in recommendations if r['recommendation'] == "BET"]
        best_bet = None
        
        if bet_recommendations:
            # Calculate risk-adjusted confidence for all bets
            for bet in bet_recommendations:
                bet['risk_adjusted_confidence'] = calculate_risk_adjusted_confidence(
                    bet['confidence'],
                    bet['pattern_name']
                )
            
            # Select by HIGHEST risk-adjusted confidence (accounts for pattern variance)
            best_bet = max(bet_recommendations, key=lambda x: x['risk_adjusted_confidence'])
        
        return best_bet  # Return single best bet or None
    
    def predict_match_simple(self, home_team: str, away_team: str, match_date: datetime):
        """
        Wrapper for predict_match that uses stored historical data.
        Returns best bet using the internal data attribute.
        """
        return self.predict_match(home_team, away_team, self.data, match_date)
    
    def _calculate_pattern_confidence(
        self,
        pattern_name: str,
        home_team: str,
        away_team: str,
        historical_data: pd.DataFrame,
        match_date: Optional[datetime] = None
    ) -> float:
        """
        Calculate pattern confidence using MULTI-TIMEFRAME ENSEMBLE.
        Uses OPTIMIZED WEIGHTS (extreme_recent) for La Liga.
        Based on comprehensive testing: 88.4% WR across 19 active patterns (HIGHEST LEAGUE!).
        """
        registry = get_pattern_registry()
        pattern = registry.get_pattern(pattern_name)
        
        if not pattern:
            return 0.0
        
        # Use ensemble method if we have a match date
        if match_date:
            # Using optimized extreme_recent weights from comprehensive testing
            # La Liga: 88.4% WR across 19 active patterns - BEST PERFORMING LEAGUE
            confidence, debug_info = calculate_multi_timeframe_confidence(
                historical_data,
                match_date,
                pattern.label_fn,
                min_matches_7d=2,
                min_matches_30d=8,
                custom_timeframes=LA_LIGA_TIMEFRAME_WEIGHTS,
                use_all_history=True  # UPGRADE #1: Use all historical data for trend analysis
            )
            return confidence
        
        # Fallback to legacy method
        home_matches = historical_data[historical_data['HomeTeam'] == home_team].tail(10)
        away_matches = historical_data[historical_data['AwayTeam'] == away_team].tail(10)
        
        if len(home_matches) < 3 and len(away_matches) < 3:
            return 0.0
        
        if 'home' in pattern_name:
            relevant_matches = home_matches
        elif 'away' in pattern_name:
            relevant_matches = away_matches
        else:
            relevant_matches = pd.concat([home_matches, away_matches])
        
        if len(relevant_matches) == 0:
            return 0.0
        
        hits = relevant_matches.apply(pattern.label_fn, axis=1).sum()
        hit_rate = hits / len(relevant_matches)
        
        return hit_rate
    
    def _estimate_odds(self, pattern_name: str) -> float:
        """Estimate odds for a pattern"""
        for key, odds in self.expected_odds.items():
            if key.replace('_', ' ') in pattern_name.replace('_', ' '):
                return odds
        return 2.0


def main():
    """Main prediction function"""
    parser = argparse.ArgumentParser(description='Predict La Liga matches')
    parser.add_argument('--lookback', type=int, default=90,
                       help='Days of historical data to use')
    parser.add_argument('--start-date', type=str, required=True,
                       help='Start date (YYYY-MM-DD)')
    parser.add_argument('--end-date', type=str, required=True,
                       help='End date (YYYY-MM-DD)')
    
    args = parser.parse_args()
    
    logger.info("Loading La Liga data...")
    all_data = load_la_liga_data()
    
    # Filter valid matches
    all_data = all_data[(all_data['HC'] >= 0) & (all_data['AC'] >= 0)]
    
    # Register patterns
    clear_patterns()
    register_la_liga_patterns()
    
    start_date = datetime.strptime(args.start_date, '%Y-%m-%d')
    end_date = datetime.strptime(args.end_date, '%Y-%m-%d')
    
    test_matches = all_data[
        (all_data['Date'] >= start_date) & 
        (all_data['Date'] <= end_date)
    ]
    
    logger.info(f"Found {len(test_matches)} matches between {args.start_date} and {args.end_date}")
    
    predictor = SimpleLaLigaPredictor(lookback_days=args.lookback)
    
    all_recommendations = []
    
    for _, match in test_matches.iterrows():
        historical = all_data[all_data['Date'] < match['Date']].tail(args.lookback * 9 // 38)
        
        if len(historical) < 50:
            continue
        
        best_bet = predictor.predict_match(
            match['HomeTeam'],
            match['AwayTeam'],
            historical,
            match['Date']
        )
        
        if best_bet:
            logger.info(f"\n{match['Date'].date()} - {match['HomeTeam']} vs {match['AwayTeam']}")
            logger.info(f"  🎯 BEST BET: {best_bet['pattern_name']}: {best_bet['confidence']:.1%} "
                       f"(thresh: {best_bet['threshold']:.1%}, EV: {best_bet['expected_value']:+.1%})")
            all_recommendations.append(best_bet)
    
    total_bets = len(all_recommendations)
    logger.info(f"\n{'='*60}")
    logger.info(f"Total betting opportunities: {total_bets}")
    logger.info(f"{'='*60}")


if __name__ == '__main__':
    main()
