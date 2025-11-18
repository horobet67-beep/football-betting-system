"""
Serie A (Italy) data adapter.
Loads and standardizes Serie A match data from CSV files.
"""

import pandas as pd
from pathlib import Path
from typing import List


def load_serie_a_data(include_future: bool = False) -> pd.DataFrame:
    """
    Load Serie A data from multiple seasons and standardize format.
    
    Args:
        include_future: If True, include incomplete/future matches. Default False for training.
    
    Returns:
        DataFrame with standardized columns matching other leagues
    """
    data_dir = Path(__file__).parent / 'serie_a'
    
    # Find all CSV files in serie_a directory
    csv_files = sorted(data_dir.glob('*.csv'))
    
    if not csv_files:
        raise FileNotFoundError(
            f"No CSV files found in {data_dir}. "
            "Please download Serie A data from football-data.co.uk"
        )
    
    all_seasons = []
    
    for csv_file in csv_files:
        try:
            # Read CSV with latin-1 encoding (handles Italian characters)
            df = pd.read_csv(csv_file, encoding='latin-1')
            
            # Add season identifier
            season_name = csv_file.stem  # e.g., 'I1_2024-25'
            df['Season'] = season_name
            
            all_seasons.append(df)
            print(f"Loaded {csv_file.name}: {len(df)} matches")
            
        except Exception as e:
            print(f"Warning: Could not load {csv_file.name}: {e}")
            continue
    
    if not all_seasons:
        raise ValueError("No Serie A data could be loaded")
    
    # Combine all seasons
    combined = pd.concat(all_seasons, ignore_index=True)
    
    # Standardize column names and format
    standardized = standardize_serie_a_format(combined, include_future=include_future)
    
    print(f"\nTotal Serie A matches loaded: {len(standardized)}")
    print(f"Date range: {standardized['Date'].min()} to {standardized['Date'].max()}")
    
    return standardized


def standardize_serie_a_format(df: pd.DataFrame, include_future: bool = False) -> pd.DataFrame:
    """
    Standardize Serie A data format to match other leagues.
    
    Handles two formats:
    1. Football-data.co.uk format (Date, HomeTeam, FTHG, HC, etc.)
    2. Alternative format (timestamp, home_team_name, home_team_goal_count, etc.)
    
    Args:
        df: Raw Serie A DataFrame
        include_future: If True, include incomplete/future matches
        
    Returns:
        Standardized DataFrame
    """
    # Create standardized copy
    standardized = df.copy()
    
    # Detect format and map columns
    if 'date_GMT' in standardized.columns:
        # Alternative format - map to standard names
        column_mapping = {
            'date_GMT': 'Date',
            'home_team_name': 'HomeTeam',
            'away_team_name': 'AwayTeam',
            'home_team_goal_count': 'FTHG',
            'away_team_goal_count': 'FTAG',
            'home_team_goal_count_half_time': 'HTHG',
            'away_team_goal_count_half_time': 'HTAG',
            'home_team_shots': 'HS',
            'away_team_shots': 'AS',
            'home_team_shots_on_target': 'HST',
            'away_team_shots_on_target': 'AST',
            'home_team_corner_count': 'HC',
            'away_team_corner_count': 'AC',
            'home_team_fouls': 'HF',
            'away_team_fouls': 'AF',
            'home_team_yellow_cards': 'HY',
            'away_team_yellow_cards': 'AY',
            'home_team_red_cards': 'HR',
            'away_team_red_cards': 'AR'
        }
        
        # Rename columns that exist
        rename_dict = {old: new for old, new in column_mapping.items() if old in standardized.columns}
        standardized = standardized.rename(columns=rename_dict)
        
        # Parse date from date_GMT format (e.g., "Aug 23 2025 - 4:30pm")
        if 'Date' in standardized.columns:
            standardized['Date'] = pd.to_datetime(standardized['Date'], format='%b %d %Y - %I:%M%p', errors='coerce')
    
    # Convert date to datetime (for football-data.co.uk format or already converted)
    if 'Date' in standardized.columns:
        standardized['Date'] = pd.to_datetime(standardized['Date'], errors='coerce')
    
    # Ensure numeric columns
    numeric_cols = [
        'FTHG', 'FTAG', 'HTHG', 'HTAG',
        'HS', 'AS', 'HST', 'AST',
        'HC', 'AC', 'HF', 'AF',
        'HY', 'AY', 'HR', 'AR'
    ]
    
    for col in numeric_cols:
        if col in standardized.columns:
            standardized[col] = pd.to_numeric(standardized[col], errors='coerce').fillna(0)
    
    # Calculate derived statistics
    if 'FTHG' in standardized.columns and 'FTAG' in standardized.columns:
        standardized['TotalGoals'] = standardized['FTHG'] + standardized['FTAG']
    
    if 'HC' in standardized.columns and 'AC' in standardized.columns:
        standardized['TotalCorners'] = standardized['HC'] + standardized['AC']
    
    if 'HY' in standardized.columns and 'AY' in standardized.columns:
        standardized['HTotalCards'] = standardized['HY'] + standardized['HR']
        standardized['ATotalCards'] = standardized['AY'] + standardized['AR']
        standardized['TotalCards'] = standardized['HY'] + standardized['AY'] + standardized['HR'] + standardized['AR']
    
    # Create FTR (Full Time Result) if not present
    if 'FTR' not in standardized.columns and 'FTHG' in standardized.columns and 'FTAG' in standardized.columns:
        standardized['FTR'] = standardized.apply(
            lambda row: 'H' if row['FTHG'] > row['FTAG'] 
                        else ('A' if row['FTAG'] > row['FTHG'] else 'D'),
            axis=1
        )
    
    # Sort by date
    if 'Date' in standardized.columns:
        standardized = standardized.sort_values('Date').reset_index(drop=True)
    
    # Filter incomplete matches unless explicitly requested
    if not include_future:
        # Filter out future matches (where goals are still NaN or -1)
        # Also filter matches with status != 'complete'
        if 'status' in standardized.columns:
            standardized = standardized[standardized['status'] == 'complete'].copy()
        if 'FTHG' in standardized.columns:
            standardized = standardized[standardized['FTHG'] >= 0].copy()
    
    return standardized


def get_serie_a_teams(df: pd.DataFrame) -> List[str]:
    """Get list of unique Serie A teams"""
    home_teams = set(df['HomeTeam'].unique())
    away_teams = set(df['AwayTeam'].unique())
    return sorted(home_teams | away_teams)


def get_serie_a_date_range(df: pd.DataFrame) -> tuple:
    """Get date range of Serie A data"""
    return df['Date'].min(), df['Date'].max()


if __name__ == '__main__':
    # Test loading
    try:
        data = load_serie_a_data()
        print(f"\n✅ Successfully loaded {len(data)} Serie A matches")
        print(f"\nTeams ({len(get_serie_a_teams(data))}):")
        for team in get_serie_a_teams(data):
            print(f"  - {team}")
        
        print(f"\nSample match:")
        sample = data.iloc[-1]
        print(f"  {sample['Date'].strftime('%Y-%m-%d')}: {sample['HomeTeam']} {sample['FTHG']}-{sample['FTAG']} {sample['AwayTeam']}")
        print(f"  Corners: {sample.get('HC', 0)}-{sample.get('AC', 0)}")
        print(f"  Cards: {sample.get('HY', 0)}-{sample.get('AY', 0)} (Yellow), {sample.get('HR', 0)}-{sample.get('AR', 0)} (Red)")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print("\nTo use this adapter:")
        print("1. Download Serie A CSV files from https://www.football-data.co.uk/italym.php")
        print("2. Save them in: v2/data/serie_a/")
        print("3. Files should be named: I1_2021-22.csv, I1_2022-23.csv, etc.")
