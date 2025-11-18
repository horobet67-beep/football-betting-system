"""
Premier League Pattern-Based Predictor
Implements improvements 1-4 with optimized thresholds for English football.
WITH MULTI-TIMEFRAME ENSEMBLE: Recent trends weighted more, validated across seasons!
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from data.premier_league_adapter import load_premier_league_data
from patterns.registry import get_pattern_registry, clear_patterns
from patterns.premier_league_patterns import register_premier_league_patterns
from patterns.risk_adjustment import calculate_risk_adjusted_confidence, explain_risk_adjustment
from utils.confidence import calculate_multi_timeframe_confidence

# Optimal weight configuration from comprehensive testing (154 patterns across all leagues)
# Premier League optimal: extreme_recent (72.1% WR, 28 patterns tested)
PREMIER_LEAGUE_TIMEFRAME_WEIGHTS = {
    7: 0.40,      # Last 7 days - Ultra Recent (40%)
    14: 0.30,     # Last 14 days - Recent (30%)
    30: 0.15,     # Last 30 days - Short Term (15%)
    90: 0.10,     # Last 90 days - Quarter (10%)
    365: 0.05,    # Last 365 days - Full Season (5%)
}


@dataclass
class BestBet:
    """Best betting recommendation for a match"""
    pattern_name: str
    confidence: float
    risk_adjusted_confidence: float
    threshold: float


class SimplePremierLeaguePredictor:
    """
    Premier League predictor with improvements:
    1. Pattern filtering (BTTS/away_over_1.5/total_over_3.5 disabled)
    2. Advanced corner style analysis
    3. Dynamic confidence thresholds
    4. Ensemble confidence scoring
    """
    
    def __init__(self, lookback_days: int = 30):
        """
        Initialize Premier League predictor.
        
        Args:
            lookback_days: Number of days of history to use for predictions
        """
        self.lookback_days = lookback_days
        self.df = load_premier_league_data()
        
        # Data already has standardized column names (FTHG, FTAG, HC, AC, HY, AY, HR, AR)
        # Create FTR if not present
        if 'FTR' not in self.df.columns:
            self.df['FTR'] = self.df.apply(
                lambda row: 'H' if row['FTHG'] > row['FTAG'] 
                            else ('A' if row['FTAG'] > row['FTHG'] else 'D'),
                axis=1
            )
        
        # Store as data for predictor interface compatibility
        self.data = self.df
        
        # Clear and register Premier League patterns
        clear_patterns()
        register_premier_league_patterns()
        
        # Get all registered patterns from registry
        registry = get_pattern_registry()
        all_patterns_list = registry.get_all_patterns()
        self.all_patterns = {p.name: {'func': p.label_fn, 'threshold': p.default_threshold} 
                            for p in all_patterns_list}
        
        # IMPROVEMENT 1: Filter out underperforming patterns
        self.filtered_patterns = {
            name: pattern for name, pattern in self.all_patterns.items()
            if name not in ['both_teams_to_score', 'away_over_1_5_goals', 'total_over_3_5_goals']
        }
        
        print(f"Loaded {len(self.df)} Premier League matches")
        print(f"Using {len(self.filtered_patterns)} patterns (filtered from {len(self.all_patterns)})")
        
    def get_team_corner_style(self, team: str, is_home: bool, lookback_df: pd.DataFrame) -> Dict[str, float]:
        """
        IMPROVEMENT 2: Analyze team's corner generation style.
        
        Returns:
            Dictionary with corner statistics for the team
        """
        if is_home:
            team_matches = lookback_df[lookback_df['HomeTeam'] == team]
            corners = team_matches['HC'].values if len(team_matches) > 0 else []
        else:
            team_matches = lookback_df[lookback_df['AwayTeam'] == team]
            corners = team_matches['AC'].values if len(team_matches) > 0 else []
            
        if len(corners) == 0:
            return {'avg': 5.0, 'std': 2.0, 'recent_trend': 0.0}
            
        avg_corners = np.mean(corners)
        std_corners = np.std(corners) if len(corners) > 1 else 2.0
        
        # Recent trend: last 3 matches vs overall average
        recent_corners = corners[-3:] if len(corners) >= 3 else corners
        recent_avg = np.mean(recent_corners)
        trend = (recent_avg - avg_corners) / (std_corners + 0.1)  # Normalized
        
        return {
            'avg': avg_corners,
            'std': std_corners,
            'recent_trend': trend
        }
    
    def get_team_specialty_boost(
        self,
        pattern_name: str,
        home_team: str,
        away_team: str,
        lookback_df: pd.DataFrame
    ) -> float:
        """
        IMPROVEMENT 5: Team-specific specialty adjustments.
        Based on analysis showing teams like Tottenham (11.8 corners) vs West Ham (9.4).
        
        Returns:
            Adjustment to confidence (-0.03 to +0.03)
        """
        # Corner pattern team adjustments
        if 'corner' in pattern_name.lower():
            # High corner teams (10.5+ avg total corners)
            high_corner_teams = {'Tottenham Hotspur', 'Newcastle United', 'Brentford', 
                               'AFC Bournemouth', 'Nottingham Forest', 'Liverpool'}
            # Low corner teams (9.7- avg total corners)
            low_corner_teams = {'West Ham United', 'Fulham', 'Wolverhampton Wanderers',
                              'Leicester City', 'Arsenal', 'Brighton & Hove Albion'}
            
            both_high = (home_team in high_corner_teams and away_team in high_corner_teams)
            both_low = (home_team in low_corner_teams and away_team in low_corner_teams)
            one_high = (home_team in high_corner_teams or away_team in high_corner_teams)
            
            if 'over' in pattern_name.lower():
                # Boost for high corner matchups
                if both_high:
                    return 0.03
                elif one_high and not both_low:
                    return 0.02
                # Penalty for low corner matchups
                elif both_low:
                    return -0.03
            elif 'under' in pattern_name.lower():
                # Reverse for under patterns
                if both_low:
                    return 0.03
                elif both_high:
                    return -0.03
        
        # Card pattern team adjustments
        if 'card' in pattern_name.lower():
            # High card teams (2.0+ avg cards/match)
            high_card_teams = {'Chelsea', 'AFC Bournemouth', 'Ipswich Town', 'Southampton',
                             'Nottingham Forest', 'Manchester United'}
            
            both_high_cards = (home_team in high_card_teams and away_team in high_card_teams)
            one_high_cards = (home_team in high_card_teams or away_team in high_card_teams)
            
            if 'over' in pattern_name.lower():
                if both_high_cards:
                    return 0.02
                elif one_high_cards:
                    return 0.01
        
        return 0.0
    
    def get_ensemble_confidence_boost(
        self, 
        pattern_name: str,
        home_team: str,
        away_team: str,
        lookback_df: pd.DataFrame
    ) -> float:
        """
        IMPROVEMENT 4: Ensemble confidence scoring.
        Boost confidence when multiple related patterns agree.
        
        Returns:
            Confidence boost value (0.0 to 0.05)
        """
        # Corner pattern ensembles
        if 'corner' in pattern_name.lower():
            home_style = self.get_team_corner_style(home_team, True, lookback_df)
            away_style = self.get_team_corner_style(away_team, False, lookback_df)
            
            # Both teams trending high corners
            if home_style['recent_trend'] > 0.5 and away_style['recent_trend'] > 0.5:
                return 0.03
            # One team strongly trending high
            elif max(home_style['recent_trend'], away_style['recent_trend']) > 1.0:
                return 0.02
                
        # Goal pattern ensembles
        if 'goal' in pattern_name.lower() and 'over' in pattern_name.lower():
            # Check if both teams score frequently
            home_goals = lookback_df[lookback_df['HomeTeam'] == home_team]['FTHG']
            away_goals = lookback_df[lookback_df['AwayTeam'] == away_team]['FTAG']
            
            if len(home_goals) > 0 and len(away_goals) > 0:
                if np.mean(home_goals) > 1.5 and np.mean(away_goals) > 1.0:
                    return 0.02
                    
        return 0.0
    
    def apply_confidence_calibration(self, raw_confidence: float) -> float:
        """
        IMPROVEMENT 6: Calibrate confidence scores based on analysis.
        Analysis showed over-confidence in 85-95% range.
        
        Returns:
            Calibrated confidence
        """
        # Apply calibration based on analysis findings
        if raw_confidence >= 0.90:
            # 90-95% range was 8.5% over-confident, 95-100% was 11.6% over
            return raw_confidence * 0.92  # Conservative reduction
        elif raw_confidence >= 0.85:
            # 85-90% range was 12% over-confident
            return raw_confidence * 0.90  # Larger reduction for most over-confident range
        elif raw_confidence >= 0.75:
            # 75-85% range was well calibrated (-1.9% to -2.5%)
            return raw_confidence * 0.98  # Small reduction
        elif raw_confidence <= 0.65:
            # 55-65% range was under-confident (+8.7% to +28.3%)
            return min(0.75, raw_confidence * 1.05)  # Small boost, cap at 75%
        else:
            # 65-75% range was well calibrated
            return raw_confidence
    
    def predict(
        self, 
        home_team: str, 
        away_team: str, 
        match_date: datetime,
        verbose: bool = False
    ) -> List[Dict]:
        """
        Predict patterns for a specific match using historical data.
        
        Args:
            home_team: Home team name
            away_team: Away team name  
            match_date: Date of the match
            verbose: Print detailed prediction info
            
        Returns:
            List of predictions with pattern, confidence, and recommendation
        """
        # Convert match_date to scalar if it's a Series/array (from iterrows)
        if hasattr(match_date, 'iloc') or isinstance(match_date, pd.Series):
            match_date = pd.Timestamp(match_date.iloc[0] if hasattr(match_date, 'iloc') else match_date.values[0])
        elif hasattr(match_date, '__iter__') and not isinstance(match_date, str):
            # Handle numpy array or similar
            match_date = pd.Timestamp(match_date[0]) if len(match_date) > 0 else match_date
        
        # Get lookback window
        start_date = match_date - timedelta(days=self.lookback_days)
        lookback_df = self.df[
            (self.df['Date'] >= start_date) & 
            (self.df['Date'] < match_date)
        ].copy()
        
        if len(lookback_df) == 0:
            if verbose:
                print(f"No historical data in lookback window")
            return None
            
        # Get matches involving these teams
        team_matches = lookback_df[
            (lookback_df['HomeTeam'] == home_team) |
            (lookback_df['AwayTeam'] == away_team) |
            (lookback_df['HomeTeam'] == away_team) |
            (lookback_df['AwayTeam'] == home_team)
        ].copy()
        
        if len(team_matches) < 3:
            if verbose:
                print(f"Insufficient team history: {len(team_matches)} matches")
            return []
            
        # IMPROVEMENT 2: Get corner styles for dynamic thresholds
        home_corner_style = self.get_team_corner_style(home_team, True, lookback_df)
        away_corner_style = self.get_team_corner_style(away_team, False, lookback_df)
        
        predictions = []
        
        # Test each pattern
        for pattern_name, pattern_info in self.filtered_patterns.items():
            pattern_func = pattern_info['func']
            base_threshold = pattern_info['threshold']
            
            # Calculate pattern success rate with MULTI-TIMEFRAME ENSEMBLE
            # Using optimized extreme_recent weights from comprehensive testing
            # Premier League: 72.1% WR across 28 active patterns
            success_rate, debug_info = calculate_multi_timeframe_confidence(
                self.df.rename(columns={'date': 'Date'}),  # Utils expects 'Date' column
                match_date,
                pattern_func,
                min_matches_7d=2,
                min_matches_30d=8,
                custom_timeframes=PREMIER_LEAGUE_TIMEFRAME_WEIGHTS,
                use_all_history=True  # UPGRADE #1: Use all historical data for trend analysis
            )
            
            # IMPROVEMENT 3: Dynamic thresholds based on corner styles
            adjusted_threshold = base_threshold
            
            if 'corner' in pattern_name.lower():
                # Adjust threshold based on team corner tendencies
                total_avg_corners = home_corner_style['avg'] + away_corner_style['avg']
                
                # Premier League avg is 10.42 - adjust around this
                if total_avg_corners > 11.5:  # High corner teams
                    adjusted_threshold -= 0.03
                elif total_avg_corners < 9.0:  # Low corner teams
                    adjusted_threshold += 0.03
                    
                # Adjust for recent trends
                if home_corner_style['recent_trend'] > 0.5 and away_corner_style['recent_trend'] > 0.5:
                    adjusted_threshold -= 0.02  # Both teams trending high
                    
            # IMPROVEMENT 4: Apply ensemble confidence boost
            ensemble_boost = self.get_ensemble_confidence_boost(
                pattern_name, home_team, away_team, lookback_df
            )
            
            # IMPROVEMENT 5: Apply team specialty boost
            specialty_boost = self.get_team_specialty_boost(
                pattern_name, home_team, away_team, lookback_df
            )
            
            # Calculate raw confidence
            raw_confidence = success_rate + ensemble_boost + specialty_boost
            
            # IMPROVEMENT 6: Apply confidence calibration
            confidence = self.apply_confidence_calibration(raw_confidence)
            
            # Make recommendation based on adjusted threshold
            if confidence >= adjusted_threshold:
                predictions.append({
                    'pattern': pattern_name,
                    'confidence': confidence,
                    'base_threshold': base_threshold,
                    'adjusted_threshold': adjusted_threshold,
                    'ensemble_boost': ensemble_boost,
                    'specialty_boost': specialty_boost,
                    'calibrated': raw_confidence != confidence,
                    'sample_size': len(team_matches),
                    'recommendation': 'BET'
                })
        
        # Sort by confidence first (for display)
        predictions.sort(key=lambda x: x['confidence'], reverse=True)
        
        # Select BEST BET per match using RISK-ADJUSTED confidence
        # This accounts for pattern variance (corners more stable than goals)
        best_bet = None
        if predictions:
            # Calculate risk-adjusted scores for all predictions
            for pred in predictions:
                pred['risk_adjusted_confidence'] = calculate_risk_adjusted_confidence(
                    pred['confidence'],
                    pred['pattern']
                )
            
            # Select bet with HIGHEST risk-adjusted confidence
            best_bet = max(predictions, key=lambda x: x['risk_adjusted_confidence'])
        
        if verbose:
            print(f"\n{'='*80}")
            print(f"Premier League Prediction: {home_team} vs {away_team}")
            print(f"Match Date: {match_date.strftime('%Y-%m-%d')}")
            print(f"Lookback: {self.lookback_days} days, {len(team_matches)} relevant matches")
            print(f"Corner Styles - Home: {home_corner_style['avg']:.1f}±{home_corner_style['std']:.1f}, "
                  f"Away: {away_corner_style['avg']:.1f}±{away_corner_style['std']:.1f}")
            
            if best_bet:
                print(f"\n🎯 BEST BET (Risk-Adjusted Selection):")
                print(f"  {best_bet['pattern']:30s} | Raw Confidence: {best_bet['confidence']:.1%} "
                      f"→ Risk-Adjusted: {best_bet['risk_adjusted_confidence']:.1%}")
                print(f"  Threshold: {best_bet['adjusted_threshold']:.1%} | ✅ BET")
                
                if len(predictions) > 1:
                    print(f"\n📋 Alternative Patterns (not recommended - correlation risk):")
                    for pred in predictions[1:6]:  # Show up to 5 alternatives
                        print(f"  {pred['pattern']:30s} | Confidence: {pred['confidence']:.1%} "
                              f"→ Risk-Adj: {pred.get('risk_adjusted_confidence', 0):.1%}")
            else:
                print(f"\n❌ NO BET RECOMMENDED")
                print(f"  No patterns met confidence thresholds")
            
            print(f"{'='*80}\n")
        
        # Return best bet as BestBet object (None if no bet recommended)
        if best_bet:
            return BestBet(
                pattern_name=best_bet['pattern'],
                confidence=best_bet['confidence'],
                risk_adjusted_confidence=best_bet['risk_adjusted_confidence'],
                threshold=best_bet['adjusted_threshold']
            )
        return None
    
    def predict_match(self, home_team: str, away_team: str, match_date: datetime, verbose: bool = False) -> Optional[BestBet]:
        """
        Alias for predict() to match interface of other league predictors.
        
        Args:
            home_team: Home team name
            away_team: Away team name  
            match_date: Date of the match
            verbose: Print detailed prediction info
            
        Returns:
            BestBet object if recommendation found, None otherwise
        """
        return self.predict(home_team, away_team, match_date, verbose)


def main():
    """Test the Premier League predictor."""
    predictor = SimplePremierLeaguePredictor(lookback_days=30)
    
    # Test with a recent match
    test_date = pd.to_datetime('2024-11-09')
    test_matches = predictor.df[predictor.df['date'] == test_date]
    
    if len(test_matches) == 0:
        print("No matches on test date, using latest matches")
        test_date = predictor.df['date'].max()
        test_matches = predictor.df[predictor.df['date'] == test_date]
    
    print(f"\nTesting with matches from {test_date.strftime('%Y-%m-%d')}")
    print(f"Found {len(test_matches)} matches\n")
    
    for _, match in test_matches.head(3).iterrows():
        predictions = predictor.predict_match(
            match['home_team'],
            match['away_team'],
            match['date'],
            verbose=True
        )


if __name__ == "__main__":
    main()
