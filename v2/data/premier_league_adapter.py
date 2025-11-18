"""
Premier League data adapter for loading and preprocessing match data.
Similar structure to Bundesliga but with Premier League specifics.
"""

import pandas as pd
from pathlib import Path
from typing import List, Optional

# Premier League data directory
PREMIER_LEAGUE_DATA_DIR = Path(__file__).parent / "premiere_league"

# Column mapping from Premier League CSV format to internal format
COLUMN_MAPPING = {
    'timestamp': 'timestamp',
    'date_GMT': 'Date',  # Standardized to 'Date' like other adapters
    'home_team_name': 'HomeTeam',
    'away_team_name': 'AwayTeam',
    'home_team_goal_count': 'FTHG',
    'away_team_goal_count': 'FTAG',
    'home_team_corner_count': 'HC',
    'away_team_corner_count': 'AC',
    'home_team_yellow_cards': 'HY',
    'away_team_yellow_cards': 'AY',
    'home_team_red_cards': 'HR',
    'away_team_red_cards': 'AR'
}


class PremierLeagueDataAdapter:
    """Adapter for loading Premier League match data."""
    
    def __init__(self, data_dir: Optional[Path] = None):
        """
        Initialize the Premier League data adapter.
        
        Args:
            data_dir: Directory containing Premier League CSV files.
                     Defaults to v2/data/premiere_league/
        """
        self.data_dir = data_dir or PREMIER_LEAGUE_DATA_DIR
        
    def load_season(self, season_start_year: int, include_future: bool = False) -> pd.DataFrame:
        """
        Load a single Premier League season.
        
        Args:
            season_start_year: Starting year of season (e.g., 2023 for 2023-24)
            include_future: If True, include incomplete/future matches. Default False.
            
        Returns:
            DataFrame with standardized columns
        """
        season_end_year = season_start_year + 1
        filename = f"england-premier-league-matches-{season_start_year}-to-{season_end_year}-stats.csv"
        filepath = self.data_dir / filename
        
        if not filepath.exists():
            raise FileNotFoundError(f"Season file not found: {filepath}")
            
        # Read CSV
        df = pd.read_csv(filepath)
        
        # Filter by status unless include_future is True
        if not include_future:
            df = df[df['status'] == 'complete'].copy()
        
        # Rename columns to internal format
        df = df.rename(columns=COLUMN_MAPPING)
        
        # Keep only needed columns
        needed_cols = list(COLUMN_MAPPING.values())
        df = df[needed_cols]
        
        # Convert Date to datetime
        df['Date'] = pd.to_datetime(df['Date'], format='%b %d %Y - %I:%M%p')
        
        # Sort by Date
        df = df.sort_values('Date').reset_index(drop=True)
        
        # Add season identifier
        df['season'] = f"{season_start_year}-{season_end_year}"
        
        return df
    
    def load_all_seasons(self, seasons: Optional[List[int]] = None, include_future: bool = False) -> pd.DataFrame:
        """
        Load multiple Premier League seasons.
        
        Args:
            seasons: List of season start years. Defaults to [2023, 2024, 2025]
                    (Note: 2022 file is Community Shield, not league matches)
            include_future: If True, include incomplete/future matches. Default False.
            
        Returns:
            Combined DataFrame with all seasons
        """
        if seasons is None:
            # Default to available league seasons (exclude 2022 Community Shield)
            seasons = [2023, 2024, 2025]
            
        all_data = []
        for season_year in seasons:
            try:
                season_df = self.load_season(season_year, include_future=include_future)
                all_data.append(season_df)
                print(f"Loaded Premier League {season_year}-{season_year+1}: {len(season_df)} matches")
            except FileNotFoundError as e:
                print(f"Warning: {e}")
                continue
                
        if not all_data:
            raise ValueError("No Premier League season data could be loaded")
            
        # Combine all seasons
        df = pd.concat(all_data, ignore_index=True)
        
        # Sort by Date
        df = df.sort_values('Date').reset_index(drop=True)
        
        return df


def load_premier_league_data(seasons: Optional[List[int]] = None, include_future: bool = False) -> pd.DataFrame:
    """
    Convenience function to load Premier League data.
    
    Args:
        seasons: List of season start years to load. Defaults to [2023, 2024, 2025]
        include_future: If True, include incomplete/future matches. Default False.
        
    Returns:
        DataFrame with Premier League match data
        
    Example:
        >>> df = load_premier_league_data()  # Load completed matches only
        >>> df = load_premier_league_data(include_future=True)  # Include upcoming fixtures
    """
    adapter = PremierLeagueDataAdapter()
    return adapter.load_all_seasons(seasons, include_future=include_future)


if __name__ == "__main__":
    # Test the adapter
    print("Testing Premier League Data Adapter")
    print("=" * 60)
    
    df = load_premier_league_data()
    
    print(f"\nTotal matches loaded: {len(df)}")
    print(f"Date range: {df['Date'].min()} to {df['Date'].max()}")
    print(f"\nSeasons:")
    print(df['season'].value_counts().sort_index())
    
    print(f"\nSample data:")
    print(df.head())
    
    print(f"\nBasic stats:")
    print(f"Average goals per match: {(df['FTHG'] + df['FTAG']).mean():.2f}")
    print(f"Average corners per match: {(df['HC'] + df['AC']).mean():.2f}")
    print(f"Average cards per match: {(df['HY'] + df['AY'] + df['HR'] + df['AR']).mean():.2f}")
