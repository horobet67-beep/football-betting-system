"""
Bundesliga (Germany) data adapter for the v2 system.
Converts Bundesliga CSV format to standardized match data format.
"""
import pandas as pd
import numpy as np
from pathlib import Path
from typing import List, Optional
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class BundesligaDataAdapter:
    """
    Adapter for Bundesliga CSV data format.
    Converts to standardized format expected by the v2 system.
    Same format as Romanian data - uses identical column structure.
    """
    
    # Column mapping from Bundesliga format to standard format
    COLUMN_MAPPING = {
        # Basic match info
        'date_GMT': 'Date',
        'home_team_name': 'HomeTeam',
        'away_team_name': 'AwayTeam', 
        'referee': 'Referee',
        
        # Goals
        'home_team_goal_count': 'FTHG',
        'away_team_goal_count': 'FTAG',
        'home_team_goal_count_half_time': 'HTHG',
        'away_team_goal_count_half_time': 'HTAG',
        
        # Corners
        'home_team_corner_count': 'HC',
        'away_team_corner_count': 'AC',
        
        # Cards
        'home_team_yellow_cards': 'HY',
        'home_team_red_cards': 'HR',
        'away_team_yellow_cards': 'AY',
        'away_team_red_cards': 'AR',
        
        # Shots
        'home_team_shots': 'HS',
        'away_team_shots': 'AS',
        'home_team_shots_on_target': 'HST',
        'away_team_shots_on_target': 'AST',
        
        # Fouls
        'home_team_fouls': 'HF',
        'away_team_fouls': 'AF',
        
        # Odds (if available)
        'odds_ft_home_team_win': 'B365H',
        'odds_ft_draw': 'B365D', 
        'odds_ft_away_team_win': 'B365A'
    }
    
    def __init__(self, data_dir: str):
        """
        Initialize adapter.
        
        Args:
            data_dir: Path to directory containing Bundesliga CSV files
        """
        self.data_dir = Path(data_dir)
        
    def load_season_data(self, season_files: List[str]) -> pd.DataFrame:
        """
        Load and convert multiple season files.
        
        Args:
            season_files: List of CSV filenames to load
            
        Returns:
            Combined DataFrame in standard format
        """
        dataframes = []
        
        for filename in season_files:
            filepath = self.data_dir / "bundesliga" / filename
            if filepath.exists():
                df = self._load_single_season(filepath)
                dataframes.append(df)
                logger.info(f"Loaded {len(df)} matches from {filename}")
            else:
                logger.warning(f"File not found: {filepath}")
        
        if not dataframes:
            raise FileNotFoundError("No valid season files found")
        
        # Combine all seasons
        combined_df = pd.concat(dataframes, ignore_index=True)
        
        # Final cleaning and validation
        cleaned_df = self._final_cleaning(combined_df)
        
        logger.info(f"Total loaded: {len(cleaned_df)} matches across {len(season_files)} seasons")
        return cleaned_df
    
    def _load_single_season(self, filepath: Path) -> pd.DataFrame:
        """Load and convert a single season file."""
        # Load raw data
        df = pd.read_csv(filepath)
        
        # Convert to standard format
        converted_df = self._convert_format(df)
        
        return converted_df
    
    def _convert_format(self, df: pd.DataFrame) -> pd.DataFrame:
        """Convert Bundesliga format to standard format."""
        converted = pd.DataFrame()
        
        # Map columns that exist
        for bundesliga_col, standard_col in self.COLUMN_MAPPING.items():
            if bundesliga_col in df.columns:
                converted[standard_col] = df[bundesliga_col]
        
        # Parse and standardize date
        if 'Date' in converted.columns:
            converted['Date'] = pd.to_datetime(converted['Date'], errors='coerce')
        
        # Calculate match result (FTR)
        if 'FTHG' in converted.columns and 'FTAG' in converted.columns:
            converted['FTR'] = converted.apply(self._calculate_result, axis=1)
        
        # Calculate half-time result (HTR)  
        if 'HTHG' in converted.columns and 'HTAG' in converted.columns:
            converted['HTR'] = converted.apply(
                lambda row: self._calculate_result_ht(row['HTHG'], row['HTAG']), axis=1
            )
        
        # Add derived features from Bundesliga data
        self._add_derived_features(converted, df)
        
        return converted
    
    def _calculate_result(self, row) -> str:
        """Calculate full-time result."""
        home_goals = row['FTHG']
        away_goals = row['FTAG']
        
        if pd.isna(home_goals) or pd.isna(away_goals):
            return 'N/A'
        
        if home_goals > away_goals:
            return 'H'
        elif away_goals > home_goals:
            return 'A'
        else:
            return 'D'
    
    def _calculate_result_ht(self, home_ht, away_ht) -> str:
        """Calculate half-time result."""
        if pd.isna(home_ht) or pd.isna(away_ht):
            return 'N/A'
        
        if home_ht > away_ht:
            return 'H'
        elif away_ht > home_ht:
            return 'A'
        else:
            return 'D'
    
    def _add_derived_features(self, converted_df: pd.DataFrame, original_df: pd.DataFrame) -> None:
        """Add derived features from Bundesliga-specific columns."""
        # Total cards per team
        if all(col in converted_df.columns for col in ['HY', 'HR']):
            converted_df['HTotalCards'] = converted_df['HY'] + converted_df['HR']
        
        if all(col in converted_df.columns for col in ['AY', 'AR']):
            converted_df['ATotalCards'] = converted_df['AY'] + converted_df['AR']
        
        # Total corners
        if all(col in converted_df.columns for col in ['HC', 'AC']):
            converted_df['TotalCorners'] = converted_df['HC'] + converted_df['AC']
        
        # Total goals
        if all(col in converted_df.columns for col in ['FTHG', 'FTAG']):
            converted_df['TotalGoals'] = converted_df['FTHG'] + converted_df['FTAG']
        
        # xG if available
        if 'team_a_xg' in original_df.columns:
            converted_df['HxG'] = original_df['team_a_xg']
        if 'team_b_xg' in original_df.columns:
            converted_df['AxG'] = original_df['team_b_xg']
        
        # Possession if available
        if 'home_team_possession' in original_df.columns:
            converted_df['HPossession'] = original_df['home_team_possession']
        if 'away_team_possession' in original_df.columns:
            converted_df['APossession'] = original_df['away_team_possession']
    
    def _final_cleaning(self, df: pd.DataFrame) -> pd.DataFrame:
        """Final data cleaning and validation."""
        df = df.copy()
        
        # Remove invalid dates
        df = df[df['Date'].notna()]
        
        # Remove invalid scores
        df = df[df['FTHG'].notna() & df['FTAG'].notna()]
        df = df[(df['FTHG'] >= 0) & (df['FTAG'] >= 0)]
        
        # Sort by date
        df = df.sort_values('Date').reset_index(drop=True)
        
        # Fill NaN values for optional columns
        numeric_columns = ['HC', 'AC', 'HY', 'HR', 'AY', 'AR', 'HS', 'AS', 'HST', 'AST', 'HF', 'AF']
        for col in numeric_columns:
            if col in df.columns:
                df[col] = df[col].fillna(0).astype(int)
        
        return df


def load_bundesliga_data(
    data_dir: str = "/Users/iuliuscezar/VisualStudioProjects/SOCCER MLL/v2/data",
    seasons: Optional[List[str]] = None,
    include_future: bool = False
) -> pd.DataFrame:
    """
    Convenience function to load Bundesliga data.
    
    Args:
        data_dir: Path to data directory
        seasons: Optional list of season files to load
        include_future: If True, include matches with status='incomplete' (future fixtures)
        
    Returns:
        Standardized match DataFrame
    """
    if seasons is None:
        # Load all available seasons
        seasons = [
            "germany-bundesliga-matches-2022-to-2023-stats.csv",
            "germany-bundesliga-matches-2023-to-2024-stats.csv", 
            "germany-bundesliga-matches-2024-to-2025-stats.csv",
            "germany-bundesliga-matches-2025-to-2026-stats.csv"
        ]
    
    adapter = BundesligaDataAdapter(data_dir)
    data = adapter.load_season_data(seasons)
    
    # Filter based on include_future flag
    if not include_future and 'status' in data.columns:
        data = data[data['status'] == 'complete'].copy()
    
    return data
