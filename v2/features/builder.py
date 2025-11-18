"""
Feature engineering module for football match prediction.
Builds rolling statistics and team-based features for model training.
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class FeatureBuilder:
    """
    Builds predictive features from match data.
    Focuses on rolling statistics and team performance metrics.
    """
    
    def __init__(
        self,
        rolling_window_days: int = 14,
        min_team_matches: int = 5,
        feature_groups: Optional[List[str]] = None
    ):
        """
        Initialize feature builder.
        
        Args:
            rolling_window_days: Days for rolling statistics
            min_team_matches: Minimum matches before features are reliable
            feature_groups: List of feature groups to include
        """
        self.rolling_window_days = rolling_window_days
        self.min_team_matches = min_team_matches
        
        # Default feature groups to include
        if feature_groups is None:
            feature_groups = ['basic', 'rolling', 'form', 'h2h']
        self.feature_groups = feature_groups
        
        # Feature columns that will be created
        self._feature_columns = []
    
    def build_features(
        self,
        matches_df: pd.DataFrame,
        target_date: Optional[str] = None
    ) -> Tuple[pd.DataFrame, List[str]]:
        """
        Build features for all matches or up to a target date.
        
        Args:
            matches_df: DataFrame with match data
            target_date: Optional cutoff date (for walk-forward)
            
        Returns:
            Tuple of (features_df, feature_column_names)
        """
        logger.info(f"Building features for {len(matches_df)} matches")
        
        # Filter data if target date specified
        if target_date:
            target_dt = pd.to_datetime(target_date)
            matches_df = matches_df[matches_df['Date'] <= target_dt].copy()
        
        # Sort by date to ensure proper chronological order
        matches_df = matches_df.sort_values('Date').reset_index(drop=True)
        
        # Initialize features dataframe
        features_df = matches_df[['Date', 'HomeTeam', 'AwayTeam']].copy()
        
        # Build different feature groups
        if 'basic' in self.feature_groups:
            basic_features = self._build_basic_features(matches_df)
            features_df = pd.concat([features_df, basic_features], axis=1)
        
        if 'rolling' in self.feature_groups:
            rolling_features = self._build_rolling_features(matches_df)
            features_df = pd.concat([features_df, rolling_features], axis=1)
        
        if 'form' in self.feature_groups:
            form_features = self._build_form_features(matches_df)
            features_df = pd.concat([features_df, form_features], axis=1)
        
        if 'h2h' in self.feature_groups:
            h2h_features = self._build_h2h_features(matches_df)
            features_df = pd.concat([features_df, h2h_features], axis=1)
        
        # Get feature column names (exclude meta columns)
        feature_columns = [col for col in features_df.columns 
                          if col not in ['Date', 'HomeTeam', 'AwayTeam']]
        
        # Fill NaN values
        features_df[feature_columns] = features_df[feature_columns].fillna(0)
        
        logger.info(f"Built {len(feature_columns)} features for {len(features_df)} matches")
        return features_df, feature_columns
    
    def _build_basic_features(self, matches_df: pd.DataFrame) -> pd.DataFrame:
        """Build basic non-temporal features."""
        features = pd.DataFrame(index=matches_df.index)
        
        # Day of week (0=Monday, 6=Sunday)
        features['day_of_week'] = matches_df['Date'].dt.dayofweek
        
        # Month
        features['month'] = matches_df['Date'].dt.month
        
        # Is weekend
        features['is_weekend'] = (matches_df['Date'].dt.dayofweek >= 5).astype(int)
        
        return features
    
    def _build_rolling_features(self, matches_df: pd.DataFrame) -> pd.DataFrame:
        """Build rolling statistics for each team."""
        features = pd.DataFrame(index=matches_df.index)
        
        # Statistics to calculate rolling averages for
        stat_cols = {
            'goals_scored': ['FTHG', 'FTAG'],  # Home goals when home, away goals when away
            'goals_conceded': ['FTAG', 'FTHG'],  # Away goals when home, home goals when away  
            'corners_for': ['HC', 'AC'],
            'corners_against': ['AC', 'HC'],
            'cards_for': ['HTotalCards', 'ATotalCards'],
            'cards_against': ['ATotalCards', 'HTotalCards'],
            'shots_for': ['HS', 'AS'],
            'shots_against': ['AS', 'HS']
        }
        
        # Calculate for both home and away teams
        for team_type in ['home', 'away']:
            team_col = 'HomeTeam' if team_type == 'home' else 'AwayTeam'
            
            for stat_name, (home_col, away_col) in stat_cols.items():
                # Get appropriate column based on team type
                stat_col = home_col if team_type == 'home' else away_col
                
                if stat_col in matches_df.columns:
                    rolling_avg = self._calculate_team_rolling_avg(
                        matches_df, team_col, stat_col, matches_df['Date']
                    )
                    features[f'{team_type}_{stat_name}_avg'] = rolling_avg
        
        return features
    
    def _build_form_features(self, matches_df: pd.DataFrame) -> pd.DataFrame:
        """Build recent form features."""
        features = pd.DataFrame(index=matches_df.index)
        
        # Points from last N matches (3 for win, 1 for draw, 0 for loss)
        for team_type in ['home', 'away']:
            team_col = 'HomeTeam' if team_type == 'home' else 'AwayTeam'
            
            # Calculate points for this team type
            if team_type == 'home':
                points = matches_df['FTR'].map({'H': 3, 'D': 1, 'A': 0})
            else:
                points = matches_df['FTR'].map({'A': 3, 'D': 1, 'H': 0})
            
            # Rolling average points
            rolling_points = self._calculate_team_rolling_avg(
                matches_df, team_col, points, matches_df['Date']
            )
            features[f'{team_type}_form_points'] = rolling_points
            
            # Win percentage
            wins = points == 3
            win_pct = self._calculate_team_rolling_avg(
                matches_df, team_col, wins.astype(int), matches_df['Date']
            )
            features[f'{team_type}_win_pct'] = win_pct
        
        return features
    
    def _build_h2h_features(self, matches_df: pd.DataFrame) -> pd.DataFrame:
        """Build head-to-head features."""
        features = pd.DataFrame(index=matches_df.index)
        
        # Initialize H2H features
        features['h2h_home_wins'] = 0.0
        features['h2h_draws'] = 0.0
        features['h2h_away_wins'] = 0.0
        features['h2h_total_matches'] = 0.0
        
        # Calculate H2H for each match
        for idx, row in matches_df.iterrows():
            home_team = row['HomeTeam']
            away_team = row['AwayTeam']
            match_date = row['Date']
            
            # Find previous H2H matches
            h2h_mask = (
                (
                    (matches_df['HomeTeam'] == home_team) & 
                    (matches_df['AwayTeam'] == away_team)
                ) | (
                    (matches_df['HomeTeam'] == away_team) & 
                    (matches_df['AwayTeam'] == home_team)
                )
            ) & (matches_df['Date'] < match_date)
            
            h2h_matches = matches_df[h2h_mask]
            
            if len(h2h_matches) > 0:
                # Count results from home team's perspective
                home_wins = sum(
                    ((h2h_matches['HomeTeam'] == home_team) & (h2h_matches['FTR'] == 'H')) |
                    ((h2h_matches['AwayTeam'] == home_team) & (h2h_matches['FTR'] == 'A'))
                )
                draws = sum(h2h_matches['FTR'] == 'D')
                away_wins = sum(
                    ((h2h_matches['HomeTeam'] == away_team) & (h2h_matches['FTR'] == 'H')) |
                    ((h2h_matches['AwayTeam'] == away_team) & (h2h_matches['FTR'] == 'A'))
                )
                
                total_matches = len(h2h_matches)
                
                # Store as proportions
                features.loc[idx, 'h2h_home_wins'] = home_wins / total_matches
                features.loc[idx, 'h2h_draws'] = draws / total_matches
                features.loc[idx, 'h2h_away_wins'] = away_wins / total_matches
                features.loc[idx, 'h2h_total_matches'] = min(total_matches, 10)  # Cap at 10
        
        return features
    
    def _calculate_team_rolling_avg(
        self,
        matches_df: pd.DataFrame,
        team_col: str,
        value_col: pd.Series,
        date_col: pd.Series
    ) -> pd.Series:
        """
        Calculate rolling average for a team's statistic.
        
        Args:
            matches_df: Full matches dataframe
            team_col: Column name for team ('HomeTeam' or 'AwayTeam')
            value_col: Series with values to average
            date_col: Series with match dates
            
        Returns:
            Series with rolling averages
        """
        result = pd.Series(0.0, index=matches_df.index)
        
        for idx, row in matches_df.iterrows():
            team = row[team_col]
            match_date = row['Date']
            
            # Find previous matches for this team within rolling window
            cutoff_date = match_date - timedelta(days=self.rolling_window_days)
            
            # Get team's previous matches (both home and away)
            team_mask = (
                ((matches_df['HomeTeam'] == team) | (matches_df['AwayTeam'] == team)) &
                (matches_df['Date'] >= cutoff_date) &
                (matches_df['Date'] < match_date)
            )
            
            team_matches = matches_df[team_mask]
            
            if len(team_matches) >= self.min_team_matches:
                # Get values for this team's matches
                team_values = []
                for _, team_match in team_matches.iterrows():
                    match_idx = team_match.name
                    if team_match['HomeTeam'] == team and team_col == 'HomeTeam':
                        team_values.append(value_col.iloc[match_idx])
                    elif team_match['AwayTeam'] == team and team_col == 'AwayTeam':
                        team_values.append(value_col.iloc[match_idx])
                    elif team_match['HomeTeam'] == team and team_col == 'AwayTeam':
                        # Team was home, but we want away stat
                        team_values.append(value_col.iloc[match_idx])
                    elif team_match['AwayTeam'] == team and team_col == 'HomeTeam':
                        # Team was away, but we want home stat
                        team_values.append(value_col.iloc[match_idx])
                
                if team_values:
                    result.iloc[idx] = np.mean(team_values)
        
        return result


def build_match_features(
    matches_df: pd.DataFrame,
    config: Optional[Dict] = None,
    target_date: Optional[str] = None
) -> Tuple[pd.DataFrame, List[str]]:
    """
    Convenience function to build features.
    
    Args:
        matches_df: DataFrame with match data
        config: Optional configuration dict
        target_date: Optional cutoff date
        
    Returns:
        Tuple of (features_df, feature_column_names)
    """
    if config is None:
        config = {}
    
    builder = FeatureBuilder(**config)
    return builder.build_features(matches_df, target_date)
