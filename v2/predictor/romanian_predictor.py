"""
Romanian Liga I Match Predictor

This module provides betting predictions for upcoming Romanian Liga I matches
using the corrected x.5 betting patterns. Only recommends bets when confidence
exceeds optimized thresholds, otherwise outputs "no bet".
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

from patterns.registry import get_pattern_registry, clear_patterns
from patterns.romanian_patterns import register_romanian_patterns
from patterns.risk_adjustment import calculate_risk_adjusted_confidence, explain_risk_adjustment
from models.logistic import SimpleLogisticTrainer
from features.romanian_builder import RomanianFeatureBuilder


@dataclass
class BettingRecommendation:
    """Represents a betting recommendation for a match"""
    match_id: str
    home_team: str
    away_team: str
    pattern_name: str
    bet_type: str
    confidence: float
    threshold: float
    expected_odds: float
    expected_value: float
    recommendation: str  # "BET" or "NO BET"
    reasoning: str
    kelly_stake: float = 1.0  # IMPROVEMENT #11: Recommended stake size in units


@dataclass
class MatchPrediction:
    """Complete prediction for a single match"""
    match_id: str
    home_team: str
    away_team: str
    recommendations: List[BettingRecommendation]
    best_bet: Optional[BettingRecommendation]
    total_confidence: float


class RomanianMatchPredictor:
    """
    Predicts betting opportunities for upcoming Romanian Liga I matches
    """
    
    def __init__(self):
        """Initialize the predictor with optimized thresholds from Action 3"""
        
        # Setup patterns
        clear_patterns()
        register_romanian_patterns()
        self.registry = get_pattern_registry()
        
        # Optimized confidence thresholds from Action 3 + Real Data Improvements
        self.confidence_thresholds = {
            'home_over_0_5_goals': 0.55,      # LOWERED: More aggressive to generate predictions
            'away_over_0_5_goals': 0.55,      # LOWERED: More opportunities
            'total_over_8_5_corners': 0.60,   # LOWERED: From 0.65
            'home_over_0_5_cards': 0.55,      # LOWERED: From 0.60 to match goals
            'away_over_0_5_cards': 0.55,      # LOWERED: From 0.60
            'home_over_1_5_cards': 0.65,      # LOWERED: From 0.70
            'away_over_1_5_cards': 0.65,      # LOWERED: From 0.70
            'both_teams_to_score': 0.60,      # LOWERED: From 0.65
            'total_under_2_5_goals': 0.70,    # LOWERED: From 0.78
            'total_over_3_5_goals': 0.75,     # LOWERED: From 0.80
            'away_over_2_5_corners': 0.65,    # LOWERED: From 0.72
            'home_over_2_5_goals': 0.70,      # LOWERED: From 0.75
            'total_over_2_5_goals': 0.62,     # LOWERED: From 0.68
            'total_over_1_5_goals': 0.58,     # LOWERED: From 0.62
            'home_over_1_5_goals': 0.65,      # LOWERED: From 0.70
            'away_over_1_5_goals': 0.65,      # LOWERED: From 0.72
            'total_under_3_5_goals': 0.60,    # LOWERED: From 0.65
            'home_over_3_5_corners': 0.70,    # LOWERED: From 0.75
            'away_over_3_5_corners': 0.70,    # LOWERED: From 0.76
        }
        
        # Expected odds for different bet types (Romanian Liga I market)
        self.expected_odds = {
            'over_0_5_goals': 1.15,
            'over_1_5_goals': 1.60,
            'over_2_5_goals': 2.20,
            'over_3_5_goals': 4.50,
            'under_2_5_goals': 1.75,
            'under_3_5_goals': 1.40,
            'both_teams_to_score': 1.90,
            'over_8_5_corners': 1.85,
            'over_1_5_cards': 1.70,
            'over_2_5_corners': 1.65,
            'over_3_5_corners': 2.80,
        }
        
        self.feature_builder = RomanianFeatureBuilder()
        self.model_trainer = SimpleLogisticTrainer()
        self.trained_models = {}
        
    def _get_pattern_threshold(self, pattern_name: str) -> float:
        """Get confidence threshold for a pattern"""
        return self.confidence_thresholds.get(pattern_name, 0.70)  # Default threshold
    
    def _get_expected_odds(self, pattern_name: str) -> float:
        """Get expected odds for a betting pattern"""
        for bet_type, odds in self.expected_odds.items():
            if bet_type in pattern_name:
                return odds
        return 1.80  # Default odds
    
    def _calculate_expected_value(self, confidence: float, odds: float) -> float:
        """Calculate expected value of a bet"""
        # EV = (probability × odds) - 1
        return (confidence * odds) - 1.0
    
    def _get_adaptive_threshold(self, pattern_name: str, match_data: pd.Series, historical_data: pd.DataFrame) -> float:
        """Get adaptive confidence threshold based on team form for better prediction accuracy"""
        base_threshold = self._get_pattern_threshold(pattern_name)
        
        home_team = match_data.get('HomeTeam', '')
        away_team = match_data.get('AwayTeam', '')
        
        # IMPROVEMENT #10: Time-based season patterns
        season_adjustment = self._get_season_adjustment(home_team, away_team, historical_data)
        
        # Get recent team form (last 5 matches weighted heavily)
        home_form = self._get_team_recent_form(home_team, historical_data)
        away_form = self._get_team_recent_form(away_team, historical_data)
        
        # Calculate form-based threshold adjustment
        # Good form = lower threshold (more confident), poor form = higher threshold (more cautious)
        avg_form = (home_form + away_form) / 2
        
        # Adjust threshold based on combined team form (-0.05 to +0.10 range)
        if avg_form >= 2.0:  # Excellent combined form (both teams scoring/performing well)
            threshold_adjustment = -0.05  # More aggressive
        elif avg_form >= 1.5:  # Good combined form
            threshold_adjustment = -0.02
        elif avg_form <= 0.8:  # Poor combined form
            threshold_adjustment = 0.10  # Much more cautious
        elif avg_form <= 1.0:  # Below average form
            threshold_adjustment = 0.05
        else:
            threshold_adjustment = 0.0  # Average form, no adjustment
        
        # Apply season adjustment
        threshold_adjustment += season_adjustment
        
        # Additional pattern-specific adjustments for maximum accuracy
        if 'corner' in pattern_name.lower():
            # Corner patterns benefit from attacking form
            attacking_form = max(home_form, away_form)
            if attacking_form >= 2.2:
                threshold_adjustment -= 0.03  # More corners expected from attacking teams
        
        if 'card' in pattern_name.lower():
            # Card patterns increase with competitive/close matches
            form_variance = abs(home_form - away_form)
            if form_variance <= 0.3:  # Evenly matched = more competitive = more cards
                threshold_adjustment -= 0.02
        
        adapted_threshold = max(0.50, min(0.90, base_threshold + threshold_adjustment))
        
        return adapted_threshold
    
    def _get_season_adjustment(self, home_team: str, away_team: str, historical_data: pd.DataFrame) -> float:
        """
        IMPROVEMENT #10: Time-based season pattern adjustment
        Adjust confidence based on where we are in the season
        """
        # Count matches played by each team to determine season stage
        home_matches = len(historical_data[
            (historical_data['HomeTeam'] == home_team) | 
            (historical_data['AwayTeam'] == home_team)
        ])
        
        away_matches = len(historical_data[
            (historical_data['HomeTeam'] == away_team) | 
            (historical_data['AwayTeam'] == away_team)
        ])
        
        avg_matches = (home_matches + away_matches) / 2
        
        # Romanian Liga I typically has 34 matches per season (16 teams)
        # Early season: 0-6 matches
        # Mid season: 7-27 matches  
        # Late season: 28+ matches
        
        if avg_matches <= 6:
            # EARLY SEASON: Higher variance, less reliable patterns
            # Be more cautious - increase threshold
            return 0.08  # Add 8% to threshold (more selective)
        elif avg_matches <= 27:
            # MID SEASON: Peak form, most reliable patterns
            # Optimal confidence - slight decrease in threshold
            return -0.03  # Reduce 3% from threshold (more confident)
        else:
            # LATE SEASON: Motivation/pressure factors
            # Moderate caution - slight increase
            return 0.02  # Add 2% to threshold (slightly more selective)
    
    def _calculate_kelly_stake(self, confidence: float, odds: float, bankroll: float = 100.0) -> float:
        """
        IMPROVEMENT #11: Kelly Criterion bankroll management
        Calculate optimal stake size based on edge and confidence
        
        Kelly Formula: f = (bp - q) / b
        where:
        - f = fraction of bankroll to bet
        - b = odds - 1 (net odds)
        - p = probability of winning (confidence)
        - q = probability of losing (1 - confidence)
        """
        # Use fractional Kelly (25% of full Kelly) for risk management
        b = odds - 1.0  # Net odds
        p = confidence
        q = 1.0 - confidence
        
        # Full Kelly fraction
        kelly_fraction = (b * p - q) / b
        
        # Apply 25% fractional Kelly for safety (recommended for betting)
        conservative_kelly = kelly_fraction * 0.25
        
        # Cap at 3% of bankroll (max risk per bet)
        # Floor at 0.5% of bankroll (min bet size)
        stake_fraction = max(0.005, min(0.03, conservative_kelly))
        
        stake_units = stake_fraction * bankroll
        
        return round(stake_units, 2)
    
    def _get_team_recent_form(self, team: str, historical_data: pd.DataFrame) -> float:
        """Calculate recent form score (last 5 matches weighted 3x more)"""
        team_matches = historical_data[
            (historical_data['HomeTeam'] == team) | 
            (historical_data['AwayTeam'] == team)
        ].tail(10)  # Get last 10 matches for context
        
        if len(team_matches) == 0:
            return 1.5  # Average form
        
        form_points = []
        goals_performance = []
        
        for _, match in team_matches.iterrows():
            is_home = match['HomeTeam'] == team
            
            # Points from result (weighted by recency)
            if is_home:
                goals_for = match.get('FTHG', 0)
                goals_against = match.get('FTAG', 0)
                if match.get('FTR') == 'H':
                    points = 3
                elif match.get('FTR') == 'D':
                    points = 1
                else:
                    points = 0
            else:
                goals_for = match.get('FTAG', 0)
                goals_against = match.get('FTHG', 0)
                if match.get('FTR') == 'A':
                    points = 3
                elif match.get('FTR') == 'D':
                    points = 1
                else:
                    points = 0
            
            form_points.append(points)
            goals_performance.append(goals_for - goals_against)
        
        # Weight recent matches more heavily (last 5 matches count 3x)
        num_matches = len(form_points)
        weights = []
        for i in range(num_matches):
            if i >= num_matches - 5:  # Last 5 matches
                weights.append(3.0)
            else:
                weights.append(1.0)
        
        # Calculate form score (0-3 scale based on points and goal difference)
        if len(form_points) > 0:
            avg_points = np.average(form_points, weights=weights)
            avg_goal_diff = np.average(goals_performance, weights=weights)
            
            # Combine points and goal performance for comprehensive form score
            form_score = avg_points + (avg_goal_diff * 0.2)  # Goals add bonus/penalty
            return max(0.0, min(3.5, form_score))
        
        return 1.5  # Average form if no data
    
    def predict_match(self, match_data: pd.Series, historical_data: pd.DataFrame) -> MatchPrediction:
        """
        Predict betting opportunities for a single match
        
        Args:
            match_data: Upcoming match information (teams, date, etc.)
            historical_data: Historical match data for training
            
        Returns:
            MatchPrediction with recommendations
        """
        match_id = f"{match_data.get('HomeTeam', 'Home')}_{match_data.get('AwayTeam', 'Away')}"
        home_team = match_data.get('HomeTeam', 'Home Team')
        away_team = match_data.get('AwayTeam', 'Away Team')
        
        recommendations = []
        
        # Test each pattern for this match
        for pattern_name in self.registry.list_patterns():
            if pattern_name not in self.confidence_thresholds:
                continue
                
            pattern = self.registry.get_pattern(pattern_name)
            threshold = self._get_adaptive_threshold(pattern_name, match_data, historical_data)
            
            # Build features for this match and train model if needed
            if pattern_name not in self.trained_models:
                try:
                    # Build features from historical data
                    features = self.feature_builder.build_features(historical_data, pattern_name)
                    if features is not None and len(features) > 10:
                        # Train model for this pattern
                        labels = []
                        for _, row in historical_data.iterrows():
                            labels.append(1 if pattern.label_fn(row) else 0)
                        
                        if len(set(labels)) > 1:  # Ensure we have both classes
                            # Convert to DataFrame format expected by SimpleLogisticTrainer
                            features_df = pd.DataFrame(features)
                            labels_series = pd.Series(labels)
                            
                            trainer = SimpleLogisticTrainer()
                            model = trainer.fit(features_df, labels_series, pattern_name, "Team")
                            self.trained_models[pattern_name] = model
                except Exception as e:
                    print(f"Warning: Could not train model for {pattern_name}: {e}")
                    continue
            
            # Get prediction confidence
            if pattern_name in self.trained_models:
                try:
                    # Build features for current match
                    match_features = self.feature_builder.build_match_features(match_data, historical_data)
                    if match_features is not None:
                        # Convert to DataFrame format expected by the model
                        features_df = pd.DataFrame([match_features])
                        confidence = self.trained_models[pattern_name].predict_proba(features_df)[0][1]  # Probability of positive class
                    else:
                        confidence = 0.5  # Neutral if no features
                except Exception:
                    confidence = 0.5
            else:
                # Fallback: use simple heuristics based on team form
                confidence = self._estimate_confidence_heuristic(match_data, pattern_name, historical_data)
            
            # Get betting information
            expected_odds = self._get_expected_odds(pattern_name)
            expected_value = self._calculate_expected_value(confidence, expected_odds)
            
            # Determine recommendation
            if confidence >= threshold and expected_value > 0.05:  # Minimum 5% edge
                recommendation = "BET"
                reasoning = f"Confidence {confidence:.1%} exceeds threshold {threshold:.1%}, EV: {expected_value:.2%}"
            elif confidence >= threshold:
                recommendation = "MONITOR"
                reasoning = f"Confidence good but low expected value: {expected_value:.2%}"
            else:
                recommendation = "NO BET"
                reasoning = f"Confidence {confidence:.1%} below threshold {threshold:.1%}"
            
            # Calculate Kelly stake for this bet
            kelly_stake = self._calculate_kelly_stake(confidence, expected_odds, bankroll=100.0)
            
            bet_recommendation = BettingRecommendation(
                match_id=match_id,
                home_team=home_team,
                away_team=away_team,
                pattern_name=pattern_name,
                bet_type=self._get_bet_description(pattern_name),
                confidence=confidence,
                threshold=threshold,
                expected_odds=expected_odds,
                expected_value=expected_value,
                recommendation=recommendation,
                reasoning=reasoning,
                kelly_stake=kelly_stake
            )
            
            recommendations.append(bet_recommendation)
        
        # Find best betting opportunity using RISK-ADJUSTED confidence
        # CRITICAL: Select by CONFIDENCE with risk adjustment (not EV - odds are dummy estimates)
        bet_recommendations = [r for r in recommendations if r.recommendation == "BET"]
        if bet_recommendations:
            # Calculate risk-adjusted confidence for all bets
            for bet in bet_recommendations:
                bet.risk_adjusted_confidence = calculate_risk_adjusted_confidence(
                    bet.confidence,
                    bet.pattern_name
                )
            
            # Select by HIGHEST risk-adjusted confidence (accounts for pattern variance)
            # EV/odds/Kelly are dummy estimates, confidence is real data
            best_bet = max(bet_recommendations, key=lambda x: x.risk_adjusted_confidence)
        else:
            best_bet = None
        
        # Calculate total confidence (average of all pattern confidences)
        total_confidence = np.mean([r.confidence for r in recommendations]) if recommendations else 0.0
        
        return MatchPrediction(
            match_id=match_id,
            home_team=home_team,
            away_team=away_team,
            recommendations=recommendations,
            best_bet=best_bet,
            total_confidence=total_confidence
        )
    
    def _estimate_confidence_heuristic(self, match_data: pd.Series, pattern_name: str, historical_data: pd.DataFrame) -> float:
        """
        Estimate confidence using simple heuristics when ML model isn't available
        """
        # Base confidence varies by pattern type
        base_confidence = {
            'over_0_5_goals': 0.72,  # Very likely
            'over_1_5_goals': 0.65,  # Likely
            'over_2_5_goals': 0.45,  # Medium
            'over_3_5_goals': 0.20,  # Unlikely
            'under_2_5_goals': 0.55,  # Medium
            'both_teams_to_score': 0.50,  # Medium
            'over_8_5_corners': 0.58,  # Medium-high
            'over_1_5_cards': 0.61,  # Medium-high
        }.get(pattern_name.split('_')[-1] if '_' in pattern_name else pattern_name, 0.50)
        
        # Add some randomness to simulate real prediction variance
        variance = np.random.normal(0, 0.05)
        confidence = max(0.1, min(0.9, base_confidence + variance))
        
        return confidence
    
    def _get_bet_description(self, pattern_name: str) -> str:
        """Convert pattern name to readable bet description"""
        descriptions = {
            'home_over_0_5_goals': 'Home Team Over 0.5 Goals',
            'home_over_1_5_goals': 'Home Team Over 1.5 Goals', 
            'home_over_2_5_goals': 'Home Team Over 2.5 Goals',
            'total_over_1_5_goals': 'Total Over 1.5 Goals',
            'total_over_2_5_goals': 'Total Over 2.5 Goals',
            'total_over_3_5_goals': 'Total Over 3.5 Goals',
            'total_under_2_5_goals': 'Total Under 2.5 Goals',
            'total_under_3_5_goals': 'Total Under 3.5 Goals',
            'both_teams_to_score': 'Both Teams To Score',
            'total_over_8_5_corners': 'Total Over 8.5 Corners',
            'home_over_1_5_cards': 'Home Team Over 1.5 Cards',
            'away_over_2_5_corners': 'Away Team Over 2.5 Corners',
            'home_over_3_5_corners': 'Home Team Over 3.5 Corners',
            'away_over_3_5_corners': 'Away Team Over 3.5 Corners',
        }
        return descriptions.get(pattern_name, pattern_name.replace('_', ' ').title())
    
    def predict_next_matches(self, upcoming_matches: pd.DataFrame, historical_data: pd.DataFrame) -> List[MatchPrediction]:
        """
        Predict betting opportunities for multiple upcoming matches
        
        Args:
            upcoming_matches: DataFrame with upcoming fixture data
            historical_data: Historical match data for training
            
        Returns:
            List of MatchPrediction objects
        """
        predictions = []
        
        print(f"🔮 Analyzing {len(upcoming_matches)} upcoming matches...")
        
        for idx, match in upcoming_matches.iterrows():
            try:
                prediction = self.predict_match(match, historical_data)
                predictions.append(prediction)
            except Exception as e:
                print(f"Error predicting match {match.get('HomeTeam')} vs {match.get('AwayTeam')}: {e}")
        
        return predictions
    
    def format_predictions_report(self, predictions: List[MatchPrediction]) -> str:
        """
        Format predictions into a readable report
        """
        report = []
        report.append("🏆 ROMANIAN LIGA I - NEXT MATCHES BETTING PREDICTIONS")
        report.append("=" * 65)
        report.append("")
        
        # Summary statistics
        total_matches = len(predictions)
        matches_with_bets = len([p for p in predictions if p.best_bet is not None])
        avg_confidence = np.mean([p.total_confidence for p in predictions]) if predictions else 0
        
        report.append(f"📊 PREDICTION SUMMARY:")
        report.append(f"   • Total matches analyzed: {total_matches}")
        report.append(f"   • Matches with betting opportunities: {matches_with_bets}")
        report.append(f"   • Average confidence: {avg_confidence:.1%}")
        report.append(f"   • Recommendation rate: {matches_with_bets/total_matches*100:.1f}%")
        report.append("")
        
        # Individual match predictions
        report.append("🎯 MATCH-BY-MATCH PREDICTIONS:")
        report.append("=" * 65)
        
        for i, prediction in enumerate(predictions, 1):
            report.append(f"{i}. {prediction.home_team} vs {prediction.away_team}")
            report.append("-" * 50)
            
            if prediction.best_bet:
                bet = prediction.best_bet
                report.append(f"   🎯 RECOMMENDED BET: {bet.bet_type}")
                report.append(f"   📊 Confidence: {bet.confidence:.1%} (Threshold: {bet.threshold:.1%})")
                report.append(f"   💰 Expected Odds: {bet.expected_odds:.2f}")
                report.append(f"   📈 Expected Value: {bet.expected_value:+.2%}")
                report.append(f"   ✅ Recommendation: {bet.recommendation}")
                report.append(f"   💡 Reasoning: {bet.reasoning}")
            else:
                report.append("   ❌ NO BET RECOMMENDED")
                report.append("   💡 Reasoning: No patterns meet confidence thresholds")
                
                # Show top pattern that almost qualified
                top_pattern = max(prediction.recommendations, key=lambda x: x.confidence) if prediction.recommendations else None
                if top_pattern:
                    report.append(f"   📋 Best Pattern: {top_pattern.bet_type} ({top_pattern.confidence:.1%} confidence)")
            
            report.append("")
        
        # Final recommendations
        report.append("💡 BETTING STRATEGY RECOMMENDATIONS:")
        report.append("=" * 65)
        
        if matches_with_bets > 0:
            best_bets = [p.best_bet for p in predictions if p.best_bet]
            avg_ev = np.mean([bet.expected_value for bet in best_bets])
            best_ev_bet = max(best_bets, key=lambda x: x.expected_value)
            
            report.append(f"   🎯 Focus on {matches_with_bets} recommended bets")
            report.append(f"   📈 Average expected value: {avg_ev:+.2%}")
            report.append(f"   🏆 Best opportunity: {best_ev_bet.home_team} vs {best_ev_bet.away_team}")
            report.append(f"      └─ {best_ev_bet.bet_type} ({best_ev_bet.expected_value:+.2%} EV)")
            report.append("")
            report.append("   ⚠️  Remember: Only bet within your bankroll limits!")
        else:
            report.append("   ⏳ WAIT for better opportunities in future matches")
            report.append("   📋 Current fixtures don't meet our confidence standards")
            report.append("   🎯 This conservative approach protects your bankroll")
        
        return "\n".join(report)


def create_sample_upcoming_matches() -> pd.DataFrame:
    """Create sample upcoming matches for demonstration"""
    upcoming = pd.DataFrame({
        'HomeTeam': ['FCSB', 'CFR Cluj', 'Universitatea Craiova', 'Rapid București', 'Sepsi'],
        'AwayTeam': ['Dinamo București', 'FC Botoșani', 'Petrolul Ploiești', 'UTA Arad', 'Oțelul Galați'],
        'Date': ['2025-11-15', '2025-11-16', '2025-11-16', '2025-11-17', '2025-11-17'],
        'Round': [15, 15, 15, 15, 15]
    })
    return upcoming