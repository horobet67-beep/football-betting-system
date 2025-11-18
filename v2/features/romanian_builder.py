"""
Enhanced feature engineering specifically for Romanian league data.
Includes proper rolling statistics and team performance metrics.
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class RomanianFeatureBuilder:
    """
    Enhanced feature builder optimized for Romanian league data.
    Focuses on rolling statistics and team performance indicators.
    """
    
    def __init__(
        self,
        rolling_window: int = 6,  # Number of matches for rolling averages
        min_matches: int = 3      # Minimum matches before features are valid
    ):
        """
        Initialize feature builder for Romanian data.
        
        Args:
            rolling_window: Number of recent matches for rolling statistics
            min_matches: Minimum matches before features are reliable
        """
        self.rolling_window = rolling_window
        self.min_matches = min_matches
        
    def build_team_features(self, matches_df: pd.DataFrame) -> pd.DataFrame:
        """
        Build comprehensive team-based features.
        
        Args:
            matches_df: DataFrame with match data
            
        Returns:
            DataFrame with team features for each match
        """
        logger.info(f"Building team features for {len(matches_df)} matches")
        
        # Sort by date to ensure chronological order
        matches_df = matches_df.sort_values('Date').reset_index(drop=True)
        
        # Initialize feature dataframe
        features_df = matches_df[['Date', 'HomeTeam', 'AwayTeam']].copy()
        
        # Build features for each match
        home_features = []
        away_features = []
        
        for idx, match in matches_df.iterrows():
            home_team = match['HomeTeam']
            away_team = match['AwayTeam']
            match_date = match['Date']
            
            # Get team statistics up to this match
            home_stats = self._get_team_stats(matches_df, home_team, match_date, idx)
            away_stats = self._get_team_stats(matches_df, away_team, match_date, idx)
            
            home_features.append(home_stats)
            away_features.append(away_stats)
        
        # Convert to DataFrames and add to features
        home_df = pd.DataFrame(home_features)
        away_df = pd.DataFrame(away_features)
        
        # Rename columns to indicate home/away
        home_df.columns = ['home_' + col for col in home_df.columns]
        away_df.columns = ['away_' + col for col in away_df.columns]
        
        # Combine all features
        features_df = pd.concat([features_df, home_df, away_df], axis=1)
        
        # Add match-specific features
        match_features = self._build_match_features(matches_df)
        features_df = pd.concat([features_df, match_features], axis=1)
        
        # Add head-to-head features
        h2h_features = self._build_h2h_features_fast(matches_df)
        features_df = pd.concat([features_df, h2h_features], axis=1)
        
        # Fill NaN values
        numeric_columns = features_df.select_dtypes(include=[np.number]).columns
        features_df[numeric_columns] = features_df[numeric_columns].fillna(0)
        
        logger.info(f"Built {len(numeric_columns)} features")
        return features_df
    
    def _get_team_stats(self, matches_df: pd.DataFrame, team: str, match_date: pd.Timestamp, current_idx: int) -> Dict:
        """Get rolling statistics for a team up to a specific date."""
        
        # Find team's recent matches (both home and away)
        team_matches = matches_df[
            (
                (matches_df['HomeTeam'] == team) | 
                (matches_df['AwayTeam'] == team)
            ) & 
            (matches_df.index < current_idx)  # Only use previous matches
        ].tail(self.rolling_window)
        
        if len(team_matches) < self.min_matches:
            # Return default values if insufficient data
            return {
                'goals_scored_avg': 0.0,
                'goals_conceded_avg': 0.0,
                'goals_scored_home_avg': 0.0,
                'goals_conceded_home_avg': 0.0,
                'goals_scored_away_avg': 0.0,
                'goals_conceded_away_avg': 0.0,
                'corners_for_avg': 0.0,
                'corners_against_avg': 0.0,
                'cards_for_avg': 0.0,
                'cards_against_avg': 0.0,
                'shots_for_avg': 0.0,
                'shots_against_avg': 0.0,
                'wins': 0.0,
                'draws': 0.0,
                'losses': 0.0,
                'points_avg': 0.0,
                'home_advantage': 0.0,
                'recent_form': 0.0,
                'matches_played': 0
            }
        
        # Calculate statistics
        stats = {'matches_played': len(team_matches)}
        
        # Goals
        goals_for = []
        goals_against = []
        goals_for_home = []
        goals_against_home = []
        goals_for_away = []
        goals_against_away = []
        
        # Other stats
        corners_for = []
        corners_against = []
        cards_for = []
        cards_against = []
        shots_for = []
        shots_against = []
        
        # Results
        points = []
        
        for _, team_match in team_matches.iterrows():
            is_home = team_match['HomeTeam'] == team
            
            if is_home:
                # Team was playing at home
                gf = team_match['FTHG']
                ga = team_match['FTAG']
                cf = team_match.get('HC', 0)
                ca = team_match.get('AC', 0)
                cards_f = team_match.get('HY', 0) + team_match.get('HR', 0)
                cards_a = team_match.get('AY', 0) + team_match.get('AR', 0)
                shots_f = team_match.get('HS', 0)
                shots_a = team_match.get('AS', 0)
                
                goals_for_home.append(gf)
                goals_against_home.append(ga)
                
                # Points
                if team_match['FTR'] == 'H':
                    points.append(3)
                elif team_match['FTR'] == 'D':
                    points.append(1)
                else:
                    points.append(0)
            else:
                # Team was playing away
                gf = team_match['FTAG']
                ga = team_match['FTHG']
                cf = team_match.get('AC', 0)
                ca = team_match.get('HC', 0)
                cards_f = team_match.get('AY', 0) + team_match.get('AR', 0)
                cards_a = team_match.get('HY', 0) + team_match.get('HR', 0)
                shots_f = team_match.get('AS', 0)
                shots_a = team_match.get('HS', 0)
                
                goals_for_away.append(gf)
                goals_against_away.append(ga)
                
                # Points
                if team_match['FTR'] == 'A':
                    points.append(3)
                elif team_match['FTR'] == 'D':
                    points.append(1)
                else:
                    points.append(0)
            
            goals_for.append(gf)
            goals_against.append(ga)
            corners_for.append(cf)
            corners_against.append(ca)
            cards_for.append(cards_f)
            cards_against.append(cards_a)
            shots_for.append(shots_f)
            shots_against.append(shots_a)
        
        # Calculate averages and ratios
        stats.update({
            'goals_scored_avg': np.mean(goals_for),
            'goals_conceded_avg': np.mean(goals_against),
            'goals_scored_home_avg': np.mean(goals_for_home) if goals_for_home else 0,
            'goals_conceded_home_avg': np.mean(goals_against_home) if goals_against_home else 0,
            'goals_scored_away_avg': np.mean(goals_for_away) if goals_for_away else 0,
            'goals_conceded_away_avg': np.mean(goals_against_away) if goals_against_away else 0,
            'corners_for_avg': np.mean(corners_for),
            'corners_against_avg': np.mean(corners_against),
            'cards_for_avg': np.mean(cards_for),
            'cards_against_avg': np.mean(cards_against),
            'shots_for_avg': np.mean(shots_for),
            'shots_against_avg': np.mean(shots_against),
            'points_avg': np.mean(points),
        })
        
        # Form and streaks
        wins = sum(1 for p in points if p == 3)
        draws = sum(1 for p in points if p == 1)
        losses = sum(1 for p in points if p == 0)
        
        stats.update({
            'wins': wins,
            'draws': draws,
            'losses': losses,
            'recent_form': np.mean(points[-3:]) if len(points) >= 3 else np.mean(points),  # Last 3 matches
        })
        
        # Home advantage (difference between home and away performance)
        if goals_for_home and goals_for_away:
            stats['home_advantage'] = np.mean(goals_for_home) - np.mean(goals_for_away)
        else:
            stats['home_advantage'] = 0.0
        
        return stats
    
    def _build_match_features(self, matches_df: pd.DataFrame) -> pd.DataFrame:
        """Build match-specific features (non-team dependent)."""
        features = pd.DataFrame()
        
        # Time-based features
        features['day_of_week'] = matches_df['Date'].dt.dayofweek
        features['month'] = matches_df['Date'].dt.month
        features['is_weekend'] = (matches_df['Date'].dt.dayofweek >= 5).astype(int)
        
        # Season progress (approximate)
        features['days_since_season_start'] = (
            matches_df['Date'] - matches_df['Date'].min()
        ).dt.days
        
        return features
    
    def _build_h2h_features_fast(self, matches_df: pd.DataFrame) -> pd.DataFrame:
        """Build head-to-head features efficiently."""
        features = pd.DataFrame()
        
        # Initialize H2H columns
        features['h2h_home_wins'] = 0.0
        features['h2h_draws'] = 0.0
        features['h2h_away_wins'] = 0.0
        features['h2h_matches'] = 0.0
        
        # Calculate H2H for recent matches only (for speed)
        for idx in range(len(matches_df)):
            if idx < 50:  # Skip early matches for speed
                continue
                
            match = matches_df.iloc[idx]
            home_team = match['HomeTeam']
            away_team = match['AwayTeam']
            
            # Find previous H2H matches (last 5 meetings)
            h2h_matches = matches_df[
                (
                    (
                        (matches_df['HomeTeam'] == home_team) & 
                        (matches_df['AwayTeam'] == away_team)
                    ) | (
                        (matches_df['HomeTeam'] == away_team) & 
                        (matches_df['AwayTeam'] == home_team)
                    )
                ) & 
                (matches_df.index < idx)
            ].tail(5)
            
            if len(h2h_matches) > 0:
                home_wins = 0
                draws = 0
                away_wins = 0
                
                for _, h2h_match in h2h_matches.iterrows():
                    if ((h2h_match['HomeTeam'] == home_team and h2h_match['FTR'] == 'H') or
                        (h2h_match['AwayTeam'] == home_team and h2h_match['FTR'] == 'A')):
                        home_wins += 1
                    elif h2h_match['FTR'] == 'D':
                        draws += 1
                    else:
                        away_wins += 1
                
                total = len(h2h_matches)
                features.loc[idx, 'h2h_home_wins'] = home_wins / total
                features.loc[idx, 'h2h_draws'] = draws / total
                features.loc[idx, 'h2h_away_wins'] = away_wins / total
                features.loc[idx, 'h2h_matches'] = min(total, 5)
        
        return features
    
    def build_features(self, matches_df: pd.DataFrame, pattern_name: str) -> Optional[np.ndarray]:
        """
        Build features for ML training on a specific pattern.
        
        Args:
            matches_df: Historical match data
            pattern_name: Name of the betting pattern
            
        Returns:
            Feature matrix as numpy array, or None if insufficient data
        """
        try:
            # Build team features
            features_df = self.build_team_features(matches_df)
            
            # Get only numeric feature columns
            feature_columns = [col for col in features_df.columns 
                             if col not in ['Date', 'HomeTeam', 'AwayTeam'] and 
                             features_df[col].dtype in [np.float64, np.int64]]
            
            if len(feature_columns) == 0:
                return None
                
            # Extract feature matrix
            feature_matrix = features_df[feature_columns].values
            
            # Remove rows with all zeros (insufficient data)
            valid_rows = ~np.all(feature_matrix == 0, axis=1)
            if np.sum(valid_rows) < self.min_matches:
                return None
                
            return feature_matrix[valid_rows]
            
        except Exception as e:
            logger.error(f"Error building features for {pattern_name}: {e}")
            return None
    
    def build_match_features(self, match_data: pd.Series, historical_data: pd.DataFrame) -> Optional[np.ndarray]:
        """
        Build features for a single upcoming match prediction.
        
        Args:
            match_data: Single match information (teams, date, etc.)
            historical_data: Historical matches for team statistics
            
        Returns:
            Feature vector as numpy array, or None if insufficient data
        """
        try:
            home_team = match_data.get('HomeTeam', '')
            away_team = match_data.get('AwayTeam', '')
            
            if not home_team or not away_team:
                return None
            
            # Get team stats from historical data
            home_stats = self._get_team_stats_from_history(historical_data, home_team)
            away_stats = self._get_team_stats_from_history(historical_data, away_team)
            
            # Build feature vector
            feature_vector = []
            
            # Add home team stats
            for key in sorted(home_stats.keys()):
                feature_vector.append(home_stats[key])
            
            # Add away team stats  
            for key in sorted(away_stats.keys()):
                feature_vector.append(away_stats[key])
                
            # Add basic match features
            # Day of week (assume Saturday = 5)
            feature_vector.append(5.0)  # day_of_week
            feature_vector.append(11.0)  # month (November)
            feature_vector.append(1.0)  # is_weekend
            feature_vector.append(100.0)  # days_since_season_start
            
            # Add basic H2H features (simplified)
            feature_vector.extend([0.33, 0.33, 0.33, 3.0])  # h2h stats
            
            return np.array(feature_vector)
            
        except Exception as e:
            logger.error(f"Error building match features: {e}")
            return None
    
    def _get_team_stats_from_history(self, historical_data: pd.DataFrame, team: str) -> Dict:
        """Get team statistics from historical data with recent form weighting for prediction accuracy."""
        
        # Find team's recent matches (more for better form analysis)
        team_matches = historical_data[
            (historical_data['HomeTeam'] == team) | 
            (historical_data['AwayTeam'] == team)
        ].tail(15)  # Increased from rolling_window to get more context
        
        if len(team_matches) < self.min_matches:
            # Return league average stats if insufficient data
            return {
                'goals_scored_avg': 1.2,
                'goals_conceded_avg': 1.1,
                'goals_scored_home_avg': 1.4,
                'goals_conceded_home_avg': 0.9,
                'goals_scored_away_avg': 1.0,
                'goals_conceded_away_avg': 1.3,
                'corners_for_avg': 4.5,
                'corners_against_avg': 4.5,
                'cards_for_avg': 2.0,
                'cards_against_avg': 2.0,
                'shots_for_avg': 12.0,
                'shots_against_avg': 12.0,
                'wins': 2.0,
                'draws': 1.0,
                'losses': 3.0,
                'points_avg': 1.5,
                'home_advantage': 0.2,
                'recent_form': 1.5,
                'matches_played': 6
            }
        
        # Calculate actual statistics (reuse existing logic)
        stats = {'matches_played': len(team_matches)}
        
        goals_for = []
        goals_against = []
        goals_for_home = []
        goals_against_home = []
        goals_for_away = []
        goals_against_away = []
        corners_for = []
        corners_against = []
        cards_for = []
        cards_against = []
        shots_for = []
        shots_against = []
        points = []
        
        for _, team_match in team_matches.iterrows():
            is_home = team_match['HomeTeam'] == team
            
            if is_home:
                gf = team_match.get('FTHG', 0)
                ga = team_match.get('FTAG', 0)
                cf = team_match.get('HC', 0)
                ca = team_match.get('AC', 0)
                cards_f = team_match.get('HY', 0) + team_match.get('HR', 0)
                cards_a = team_match.get('AY', 0) + team_match.get('AR', 0)
                shots_f = team_match.get('HS', 0)
                shots_a = team_match.get('AS', 0)
                
                goals_for_home.append(gf)
                goals_against_home.append(ga)
                
                if team_match.get('FTR') == 'H':
                    points.append(3)
                elif team_match.get('FTR') == 'D':
                    points.append(1)
                else:
                    points.append(0)
            else:
                gf = team_match.get('FTAG', 0)
                ga = team_match.get('FTHG', 0)
                cf = team_match.get('AC', 0)
                ca = team_match.get('HC', 0)
                cards_f = team_match.get('AY', 0) + team_match.get('AR', 0)
                cards_a = team_match.get('HY', 0) + team_match.get('HR', 0)
                shots_f = team_match.get('AS', 0)
                shots_a = team_match.get('HS', 0)
                
                goals_for_away.append(gf)
                goals_against_away.append(ga)
                
                if team_match.get('FTR') == 'A':
                    points.append(3)
                elif team_match.get('FTR') == 'D':
                    points.append(1)
                else:
                    points.append(0)
            
            goals_for.append(gf)
            goals_against.append(ga)
            corners_for.append(cf)
            corners_against.append(ca)
            cards_for.append(cards_f)
            cards_against.append(cards_a)
            shots_for.append(shots_f)
            shots_against.append(shots_a)
        
        # Calculate statistics with recent form weighting (last 5 matches count 3x more)
        num_matches = len(team_matches)
        if num_matches > 0:
            # Create weights: recent matches (last 5) count 3x more for prediction accuracy
            weights = []
            for i in range(num_matches):
                if i >= num_matches - 5:  # Last 5 matches
                    weights.append(3.0)
                else:
                    weights.append(1.0)
            
            weights = np.array(weights)
            
            # Weighted averages for better prediction accuracy
            stats.update({
                'goals_scored_avg': np.average(goals_for, weights=weights) if goals_for else 0,
                'goals_conceded_avg': np.average(goals_against, weights=weights) if goals_against else 0,
                'corners_for_avg': np.average(corners_for, weights=weights) if corners_for else 0,
                'corners_against_avg': np.average(corners_against, weights=weights) if corners_against else 0,
                'cards_for_avg': np.average(cards_for, weights=weights) if cards_for else 0,
                'cards_against_avg': np.average(cards_against, weights=weights) if cards_against else 0,
                'shots_for_avg': np.average(shots_for, weights=weights) if shots_for else 0,
                'shots_against_avg': np.average(shots_against, weights=weights) if shots_against else 0,
                'points_avg': np.average(points, weights=weights) if points else 0,
            })
            
            # Home/Away specific stats (use simple average if insufficient data)
            if goals_for_home:
                home_indices = [i for i, match in enumerate(team_matches.iterrows()) if match[1]['HomeTeam'] == team]
                home_weights = weights[home_indices] if len(home_indices) > 0 else [1.0] * len(goals_for_home)
                stats['goals_scored_home_avg'] = np.average(goals_for_home, weights=home_weights)
                stats['goals_conceded_home_avg'] = np.average(goals_against_home, weights=home_weights)
            else:
                stats['goals_scored_home_avg'] = 0
                stats['goals_conceded_home_avg'] = 0
                
            if goals_for_away:
                away_indices = [i for i, match in enumerate(team_matches.iterrows()) if match[1]['AwayTeam'] == team]
                away_weights = weights[away_indices] if len(away_indices) > 0 else [1.0] * len(goals_for_away)
                stats['goals_scored_away_avg'] = np.average(goals_for_away, weights=away_weights)
                stats['goals_conceded_away_avg'] = np.average(goals_against_away, weights=away_weights)
            else:
                stats['goals_scored_away_avg'] = 0
                stats['goals_conceded_away_avg'] = 0
                
            # Form momentum indicators for prediction accuracy
            if num_matches >= 5:
                recent_goals_for = np.array(goals_for[-3:])
                older_goals_for = np.array(goals_for[:-3]) if num_matches > 3 else np.array(goals_for)
                stats['attack_momentum'] = np.mean(recent_goals_for) - np.mean(older_goals_for) if len(older_goals_for) > 0 else 0
                
                recent_goals_against = np.array(goals_against[-3:])
                older_goals_against = np.array(goals_against[:-3]) if num_matches > 3 else np.array(goals_against)
                stats['defense_momentum'] = np.mean(older_goals_against) - np.mean(recent_goals_against) if len(older_goals_against) > 0 else 0
                
                recent_corners = np.array(corners_for[-3:]) + np.array(corners_against[-3:])
                older_corners = np.array(corners_for[:-3]) + np.array(corners_against[:-3]) if num_matches > 3 else np.array(corners_for) + np.array(corners_against)
                stats['corner_momentum'] = np.mean(recent_corners) - np.mean(older_corners) if len(older_corners) > 0 else 0
            else:
                stats['attack_momentum'] = 0
                stats['defense_momentum'] = 0
                stats['corner_momentum'] = 0
        else:
            # Fallback to zeros
            stats.update({
                'goals_scored_avg': 0, 'goals_conceded_avg': 0,
                'goals_scored_home_avg': 0, 'goals_conceded_home_avg': 0,
                'goals_scored_away_avg': 0, 'goals_conceded_away_avg': 0,
                'corners_for_avg': 0, 'corners_against_avg': 0,
                'cards_for_avg': 0, 'cards_against_avg': 0,
                'shots_for_avg': 0, 'shots_against_avg': 0,
                'points_avg': 0, 'attack_momentum': 0,
                'defense_momentum': 0, 'corner_momentum': 0,
            })
        
        # Form and derived stats
        wins = sum(1 for p in points if p == 3)
        draws = sum(1 for p in points if p == 1)
        losses = sum(1 for p in points if p == 0)
        
        stats.update({
            'wins': wins,
            'draws': draws,
            'losses': losses,
            'recent_form': np.mean(points[-3:]) if len(points) >= 3 else np.mean(points) if points else 0,
        })
        
        if goals_for_home and goals_for_away:
            stats['home_advantage'] = np.mean(goals_for_home) - np.mean(goals_for_away)
        else:
            stats['home_advantage'] = 0.0
        
        return stats


def build_romanian_features(matches_df: pd.DataFrame, config: Optional[Dict] = None) -> Tuple[pd.DataFrame, List[str]]:
    """
    Build features optimized for Romanian league data.
    
    Args:
        matches_df: Romanian league match data
        config: Optional configuration
        
    Returns:
        Tuple of (features_df, feature_column_names)
    """
    if config is None:
        config = {}
    
    builder = RomanianFeatureBuilder(**config)
    features_df = builder.build_team_features(matches_df)
    
    # Get feature column names (exclude meta columns)
    feature_columns = [col for col in features_df.columns 
                      if col not in ['Date', 'HomeTeam', 'AwayTeam']]
    
    return features_df, feature_columns