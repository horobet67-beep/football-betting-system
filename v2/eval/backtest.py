"""
Simple backtesting engine for the v2 system.
MVP implementation focusing on clarity and core functionality.
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


@dataclass
class BacktestResult:
    """Results from a backtest run."""
    league: str
    start_date: str
    end_date: str
    total_matches: int
    total_bets: int
    winning_bets: int
    total_stake: float
    total_return: float
    win_rate: float
    roi: float
    pattern_stats: Dict[str, Dict]


def run_simple_backtest(
    league_name: str,
    start_date: str,
    end_date: str,
    config: Optional[Dict] = None
) -> BacktestResult:
    """
    Run a simple backtest on Romanian league data.
    
    Args:
        league_name: League name (currently supports 'Romania')
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD)
        config: Optional configuration
        
    Returns:
        BacktestResult with performance metrics
    """
    if config is None:
        config = {}
    
    logger.info(f"Starting backtest: {league_name} from {start_date} to {end_date}")
    
    # Load data
    if league_name.lower() in ['romania', 'romanian', 'liga1']:
        from data.romanian_adapter import load_romanian_data
        matches_df = load_romanian_data()
    else:
        raise ValueError(f"League '{league_name}' not supported yet")
    
    # Filter date range
    start_dt = pd.to_datetime(start_date)
    end_dt = pd.to_datetime(end_date)
    
    # Split into training and test periods
    training_end = start_dt - timedelta(days=1)
    training_matches = matches_df[matches_df['Date'] <= training_end].copy()
    test_matches = matches_df[
        (matches_df['Date'] >= start_dt) & 
        (matches_df['Date'] <= end_dt)
    ].copy()
    
    logger.info(f"Training period: {len(training_matches)} matches")
    logger.info(f"Test period: {len(test_matches)} matches")
    
    if len(training_matches) < 100:
        raise ValueError("Insufficient training data")
    if len(test_matches) == 0:
        raise ValueError("No test matches found in date range")
    
    # Import required modules
    from patterns.registry import get_pattern_registry
    from models.logistic import train_pattern_model
    
    # Get patterns to test
    registry = get_pattern_registry()
    patterns_to_test = ['home_over_1_5_goals', 'total_over_2_5_goals', 'home_over_4_corners']
    
    # Simple feature engineering
    def create_simple_features(df):
        features = pd.DataFrame()
        features['home_goals'] = df['FTHG']
        features['away_goals'] = df['FTAG']
        features['home_corners'] = df['HC']
        features['away_corners'] = df['AC']
        features['total_goals'] = df['FTHG'] + df['FTAG']
        features['total_corners'] = df['HC'] + df['AC']
        return features
    
    # Train models for major teams
    teams = ['FCSB', 'CFR Cluj', 'CS U Craiova', 'Rapid Bucureşti']
    trained_models = {}
    
    training_features = create_simple_features(training_matches)
    
    for team in teams:
        for pattern_name in patterns_to_test:
            pattern = registry.get_pattern(pattern_name)
            
            # Get team's home matches for training
            team_mask = (training_matches['HomeTeam'] == team)
            team_matches = training_matches[team_mask]
            
            if len(team_matches) >= 10:
                team_features = training_features[team_mask]
                team_labels = team_matches.apply(pattern.label_fn, axis=1)
                
                if team_labels.sum() >= 2:  # Need at least 2 positive examples
                    try:
                        model = train_pattern_model(
                            team_features,
                            team_labels,
                            pattern_name,
                            team
                        )
                        trained_models[(team, pattern_name)] = {
                            'model': model,
                            'pattern': pattern,
                            'positive_rate': team_labels.mean()
                        }
                        logger.debug(f"Trained {team}/{pattern_name}")
                    except Exception as e:
                        logger.warning(f"Failed to train {team}/{pattern_name}: {e}")
    
    logger.info(f"Trained {len(trained_models)} team/pattern models")
    
    # Run backtest on test period
    total_bets = 0
    winning_bets = 0
    total_stake = 0.0
    total_return = 0.0
    pattern_stats = {}
    
    test_features = create_simple_features(test_matches)
    
    for idx, match in test_matches.iterrows():
        home_team = match['HomeTeam']
        
        # Check if we have models for this team
        best_bet = None
        best_confidence = 0.0
        
        for (team, pattern_name), model_info in trained_models.items():
            if team == home_team:
                model = model_info['model']
                pattern = model_info['pattern']
                
                # Get features for this match
                match_features = test_features.loc[[idx]]
                
                try:
                    # Predict probability
                    proba = model.predict_proba(match_features)
                    confidence = proba[0][1]  # Probability of positive class
                    
                    # Apply threshold
                    threshold = pattern.default_threshold
                    if confidence > threshold and confidence > best_confidence:
                        best_confidence = confidence
                        best_bet = {
                            'pattern_name': pattern_name,
                            'confidence': confidence,
                            'pattern_fn': pattern.label_fn
                        }
                        
                except Exception as e:
                    logger.warning(f"Prediction failed for {team}/{pattern_name}: {e}")
        
        # Place bet if we found a good pattern
        if best_bet:
            stake = 1.0  # Unit stake
            total_stake += stake
            total_bets += 1
            
            # Check if bet won
            actual_result = best_bet['pattern_fn'](match)
            
            if actual_result:
                winning_bets += 1
                # Simple return calculation (assume 2.0 odds for simplicity)
                bet_return = stake * 2.0
                total_return += bet_return
                
                logger.debug(f"WIN: {match['HomeTeam']} vs {match['AwayTeam']} - {best_bet['pattern_name']}")
            else:
                logger.debug(f"LOSS: {match['HomeTeam']} vs {match['AwayTeam']} - {best_bet['pattern_name']}")
            
            # Track pattern statistics
            pattern_name = best_bet['pattern_name']
            if pattern_name not in pattern_stats:
                pattern_stats[pattern_name] = {'bets': 0, 'wins': 0, 'stake': 0.0, 'return': 0.0}
            
            pattern_stats[pattern_name]['bets'] += 1
            pattern_stats[pattern_name]['stake'] += stake
            if actual_result:
                pattern_stats[pattern_name]['wins'] += 1
                pattern_stats[pattern_name]['return'] += bet_return
    
    # Calculate metrics
    win_rate = winning_bets / total_bets if total_bets > 0 else 0.0
    roi = (total_return - total_stake) / total_stake if total_stake > 0 else 0.0
    
    # Calculate pattern-level metrics
    for pattern_name in pattern_stats:
        stats = pattern_stats[pattern_name]
        stats['win_rate'] = stats['wins'] / stats['bets']
        stats['roi'] = (stats['return'] - stats['stake']) / stats['stake']
    
    result = BacktestResult(
        league=league_name,
        start_date=start_date,
        end_date=end_date,
        total_matches=len(test_matches),
        total_bets=total_bets,
        winning_bets=winning_bets,
        total_stake=total_stake,
        total_return=total_return,
        win_rate=win_rate,
        roi=roi,
        pattern_stats=pattern_stats
    )
    
    logger.info(f"Backtest complete: {total_bets} bets, {win_rate:.3f} win rate, {roi:.3f} ROI")
    return result


def print_backtest_results(result: BacktestResult) -> None:
    """Print formatted backtest results."""
    print(f"\n{'='*60}")
    print(f"BACKTEST RESULTS - {result.league}")
    print(f"{'='*60}")
    print(f"Period: {result.start_date} to {result.end_date}")
    print(f"Total matches: {result.total_matches}")
    print(f"Total bets: {result.total_bets}")
    print(f"Winning bets: {result.winning_bets}")
    print(f"Win rate: {result.win_rate:.3%}")
    print(f"Total stake: {result.total_stake:.2f}")
    print(f"Total return: {result.total_return:.2f}")
    print(f"ROI: {result.roi:.3%}")
    
    if result.pattern_stats:
        print(f"\nPattern Performance:")
        print(f"{'Pattern':<20} {'Bets':<6} {'Wins':<6} {'WinRate':<8} {'ROI':<8}")
        print(f"{'-'*50}")
        
        for pattern_name, stats in result.pattern_stats.items():
            print(f"{pattern_name:<20} {stats['bets']:<6} {stats['wins']:<6} "
                  f"{stats['win_rate']:<8.3%} {stats['roi']:<8.3%}")
    
    print(f"{'='*60}")
