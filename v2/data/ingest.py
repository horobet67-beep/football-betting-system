"""
Data ingestion and validation for football match data.
Handles CSV loading, cleaning, and schema validation.
"""
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class DataValidationError(Exception):
    """Raised when data validation fails."""
    pass


class MatchDataIngester:
    """Handles loading and validation of match CSV data."""
    
    # Required columns for match data
    REQUIRED_COLUMNS = [
        'Date', 'HomeTeam', 'AwayTeam', 'FTHG', 'FTAG',
        'FTR', 'HTHG', 'HTAG', 'HTR'
    ]
    
    # Optional columns commonly present
    OPTIONAL_COLUMNS = [
        'HC', 'AC', 'HF', 'AF', 'HY', 'AY', 'HR', 'AR',  # Stats
        'B365H', 'B365D', 'B365A', 'BWH', 'BWD', 'BWA',  # Odds
        'Referee'
    ]
    
    def __init__(self, data_dir: str):
        """
        Initialize data ingester.
        
        Args:
            data_dir: Path to directory containing CSV files
        """
        self.data_dir = Path(data_dir)
        
    def load_league_data(self, league_name: str, seasons: Optional[List[str]] = None) -> pd.DataFrame:
        """
        Load and combine data for a specific league.
        
        Args:
            league_name: Name of the league (used to find CSV files)
            seasons: Optional list of seasons to load (e.g., ['2021-22', '2022-23'])
            
        Returns:
            Combined and cleaned DataFrame
            
        Raises:
            DataValidationError: If data validation fails
            FileNotFoundError: If no matching CSV files found
        """
        # Find CSV files for the league
        csv_files = self._find_league_files(league_name, seasons)
        
        if not csv_files:
            raise FileNotFoundError(f"No CSV files found for league '{league_name}' in {self.data_dir}")
        
        logger.info(f"Loading {len(csv_files)} files for league '{league_name}'")
        
        # Load and combine all files
        dataframes = []
        for csv_file in csv_files:
            df = self._load_single_file(csv_file)
            dataframes.append(df)
        
        # Combine all dataframes
        combined_df = pd.concat(dataframes, ignore_index=True)
        
        # Clean and validate
        cleaned_df = self._clean_data(combined_df)
        self._validate_data(cleaned_df, league_name)
        
        logger.info(f"Loaded {len(cleaned_df)} matches for league '{league_name}'")
        return cleaned_df
    
    def _find_league_files(self, league_name: str, seasons: Optional[List[str]] = None) -> List[Path]:
        """Find CSV files matching the league name and optional seasons."""
        csv_files = []
        
        # Search patterns: league_name.csv, league_name_YYYY-YY.csv, etc.
        patterns = [
            f"{league_name}.csv",
            f"{league_name}_*.csv"
        ]
        
        if seasons:
            for season in seasons:
                patterns.append(f"{league_name}_{season}.csv")
        
        for pattern in patterns:
            matches = list(self.data_dir.glob(pattern))
            csv_files.extend(matches)
        
        # Remove duplicates and sort
        csv_files = sorted(list(set(csv_files)))
        return csv_files
    
    def _load_single_file(self, csv_file: Path) -> pd.DataFrame:
        """Load a single CSV file with error handling."""
        try:
            # Try different encodings
            for encoding in ['utf-8', 'latin-1', 'cp1252']:
                try:
                    df = pd.read_csv(csv_file, encoding=encoding)
                    logger.debug(f"Loaded {csv_file} with encoding {encoding}")
                    return df
                except UnicodeDecodeError:
                    continue
            
            # If all encodings fail, raise error
            raise ValueError(f"Could not decode {csv_file} with any standard encoding")
            
        except Exception as e:
            logger.error(f"Failed to load {csv_file}: {e}")
            raise
    
    def _clean_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean and standardize the data."""
        df = df.copy()
        
        # Parse dates
        df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
        
        # Remove matches with invalid dates
        invalid_dates = df['Date'].isna()
        if invalid_dates.any():
            logger.warning(f"Removing {invalid_dates.sum()} matches with invalid dates")
            df = df[~invalid_dates]
        
        # Remove canceled/postponed matches (common indicators)
        canceled_indicators = ['Psp.', 'Can.', 'Awd.', 'Abd.']
        for indicator in canceled_indicators:
            mask = (
                (df['FTR'] == indicator) |
                (df.get('HomeTeam', '').str.contains(indicator, na=False)) |
                (df.get('AwayTeam', '').str.contains(indicator, na=False))
            )
            if mask.any():
                logger.warning(f"Removing {mask.sum()} matches with indicator '{indicator}'")
                df = df[~mask]
        
        # Clean numeric columns - replace sentinel values
        numeric_columns = ['FTHG', 'FTAG', 'HTHG', 'HTAG', 'HC', 'AC', 'HF', 'AF', 'HY', 'AY', 'HR', 'AR']
        for col in numeric_columns:
            if col in df.columns:
                # Replace common sentinel values with NaN
                df[col] = pd.to_numeric(df[col], errors='coerce')
                df[col] = df[col].replace([-1, -99, 999], np.nan)
        
        # Clean odds columns
        odds_columns = [col for col in df.columns if any(bookmaker in col for bookmaker in ['B365', 'BW', 'IW', 'PS'])]
        for col in odds_columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
            # Remove obviously invalid odds (< 1.01 or > 100)
            df[col] = df[col].where((df[col] >= 1.01) & (df[col] <= 100))
        
        # Sort by date
        df = df.sort_values('Date').reset_index(drop=True)
        
        return df
    
    def _validate_data(self, df: pd.DataFrame, league_name: str) -> None:
        """Validate the cleaned data meets requirements."""
        # Check required columns
        missing_columns = set(self.REQUIRED_COLUMNS) - set(df.columns)
        if missing_columns:
            raise DataValidationError(f"Missing required columns: {missing_columns}")
        
        # Check for empty dataframe
        if len(df) == 0:
            raise DataValidationError(f"No valid matches found for league '{league_name}'")
        
        # Check date range
        date_range = df['Date'].max() - df['Date'].min()
        logger.info(f"Data spans {date_range.days} days from {df['Date'].min().date()} to {df['Date'].max().date()}")
        
        # Check for reasonable number of teams
        n_teams = len(set(df['HomeTeam'].unique()) | set(df['AwayTeam'].unique()))
        if n_teams < 4:
            logger.warning(f"Only {n_teams} teams found - data may be incomplete")
        
        # Check for basic data integrity
        invalid_scores = (df['FTHG'] < 0) | (df['FTAG'] < 0) | df['FTHG'].isna() | df['FTAG'].isna()
        if invalid_scores.any():
            raise DataValidationError(f"{invalid_scores.sum()} matches have invalid scores")
        
        logger.info(f"Data validation passed: {len(df)} matches, {n_teams} teams")


def load_match_data(data_dir: str, league_name: str, seasons: Optional[List[str]] = None) -> pd.DataFrame:
    """
    Convenience function to load match data.
    
    Args:
        data_dir: Path to data directory
        league_name: Name of the league
        seasons: Optional list of seasons to load
        
    Returns:
        Cleaned and validated DataFrame
    """
    ingester = MatchDataIngester(data_dir)
    return ingester.load_league_data(league_name, seasons)
