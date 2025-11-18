"""
Enhanced backtesting engine with better model training and selection logic.
Optimized for Romanian league analysis.
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
from datetime import datetime, timedelta
import logging
import json
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class EnhancedBacktestResult:
    """Enhanced backtest results with detailed analytics."""
    league: str
    start_date: str
    end_date: str
    config: Dict[str, Any]
    
    # Match statistics
    total_matches: int
    total_bets: int
    winning_bets: int
    
    # Financial metrics
    total_stake: float
    total_return: float
    win_rate: float
    roi: float
    max_drawdown: float
    profit_factor: float
    
    # Pattern performance
    pattern_stats: Dict[str, Dict]
    team_stats: Dict[str, Dict]
    
    # Time series data
    daily_pnl: List[float]
    cumulative_pnl: List[float]
    betting_dates: List[str]


def run_enhanced_backtest(
    league_name: str,
    start_date: str,
    end_date: str,
    config: Optional[Dict] = None
) -> EnhancedBacktestResult:
    """
    Run enhanced backtest with improved features and analytics.
    
    Args:
        league_name: League name
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD)
        config: Configuration dict
        
    Returns:
        Enhanced backtest results
    """
    if config is None:
        config = {}
    
    logger.info(f"Starting enhanced backtest: {league_name} from {start_date} to {end_date}")
    
    # Load data
    from data.romanian_adapter import load_romanian_data
    matches_df = load_romanian_data()
    
    # Import enhanced patterns
    import patterns.romanian_patterns  # This registers new patterns
    
    # Filter date range with proper training period
    start_dt = pd.to_datetime(start_date)
    end_dt = pd.to_datetime(end_date)
    
    # Use 90 days before start for training
    training_start = start_dt - timedelta(days=90)
    training_matches = matches_df[
        (matches_df['Date'] >= training_start) & 
        (matches_df['Date'] < start_dt)
    ].copy()
    
    test_matches = matches_df[
        (matches_df['Date'] >= start_dt) & 
        (matches_df['Date'] <= end_dt)
    ].copy()
    
    logger.info(f"Training period: {len(training_matches)} matches")
    logger.info(f"Test period: {len(test_matches)} matches")
    
    if len(training_matches) < 50:
        raise ValueError("Insufficient training data")
    if len(test_matches) == 0:
        raise ValueError("No test matches found")
    
    # Build enhanced features
    from features.romanian_builder import build_romanian_features
    from patterns.registry import get_pattern_registry
    from models.logistic import train_pattern_model
    
    # Get enhanced pattern set
    registry = get_pattern_registry()
    all_patterns = registry.list_patterns()
    
    # Focus on most promising patterns for Romanian league
    priority_patterns = [
        'home_over_1_5_goals', 'total_over_2_5_goals', 'both_teams_to_score',
        'home_over_4_corners', 'total_over_9_corners', 'home_over_3_corners',
        'home_over_2_cards', 'total_over_4_cards'
    ]
    
    patterns_to_test = [p for p in priority_patterns if p in all_patterns]
    logger.info(f"Testing {len(patterns_to_test)} priority patterns")
    
    # Build features for training and test sets
    training_features, feature_columns = build_romanian_features(training_matches)
    test_features, _ = build_romanian_features(test_matches)
    
    logger.info(f"Built {len(feature_columns)} enhanced features")
    
    # Get teams with sufficient data
    team_match_counts = training_matches['HomeTeam'].value_counts()
    active_teams = team_match_counts[team_match_counts >= 8].index.tolist()
    logger.info(f"Training models for {len(active_teams)} teams")
    
    # Train models
    trained_models = {}
    model_performance = {}
    
    for team in active_teams:
        for pattern_name in patterns_to_test:
            pattern = registry.get_pattern(pattern_name)
            
            # Get team's home matches for training  
            team_mask = (training_matches['HomeTeam'] == team)
            team_training_matches = training_matches[team_mask]
            
            if len(team_training_matches) >= 5:
                team_features = training_features[team_mask][feature_columns]
                team_labels = team_training_matches.apply(pattern.label_fn, axis=1)
                
                positive_rate = team_labels.mean()
                if positive_rate >= 0.1 and team_labels.sum() >= 2:  # At least 10% positive rate
                    try:
                        model = train_pattern_model(
                            team_features,
                            team_labels,
                            pattern_name,
                            team,
                            config={'random_state': 42}
                        )
                        
                        key = (team, pattern_name)
                        trained_models[key] = {
                            'model': model,
                            'pattern': pattern,
                            'positive_rate': positive_rate,
                            'training_matches': len(team_training_matches),
                            'positive_samples': team_labels.sum()
                        }
                        
                        # Calculate training accuracy for model selection
                        train_preds = model.predict_proba(team_features)
                        train_pred_binary = (train_preds[:, 1] > pattern.default_threshold).astype(int)
                        train_accuracy = (train_pred_binary == team_labels).mean()
                        
                        model_performance[key] = {
                            'train_accuracy': train_accuracy,
                            'positive_rate': positive_rate
                        }
                        
                        logger.debug(f"Trained {team}/{pattern_name}: {train_accuracy:.3f} accuracy, {positive_rate:.3f} rate")
                        
                    except Exception as e:
                        logger.warning(f"Training failed for {team}/{pattern_name}: {e}")
    
    logger.info(f"Successfully trained {len(trained_models)} models")
    
    # Run enhanced backtest
    results = _run_detailed_backtest(
        test_matches, test_features, feature_columns, trained_models, 
        model_performance, config
    )
    
    # Create enhanced result object
    enhanced_result = EnhancedBacktestResult(
        league=league_name,
        start_date=start_date,
        end_date=end_date,
        config=config,
        **results
    )
    
    logger.info(f"Backtest complete: {results['total_bets']} bets, "
               f"{results['win_rate']:.3f} win rate, {results['roi']:.3f} ROI")
    
    return enhanced_result


def _run_detailed_backtest(
    test_matches: pd.DataFrame,
    test_features: pd.DataFrame,
    feature_columns: List[str],
    trained_models: Dict,
    model_performance: Dict,
    config: Dict
) -> Dict:
    """Run detailed backtest with enhanced tracking."""
    
    # Initialize tracking
    bets_placed = []
    daily_pnl = []
    cumulative_pnl = []
    betting_dates = []
    pattern_stats = {}
    team_stats = {}
    
    total_stake = 0.0
    total_return = 0.0
    running_pnl = 0.0
    peak_pnl = 0.0
    max_drawdown = 0.0
    
    # Betting parameters
    unit_stake = config.get('unit_stake', 1.0)
    min_confidence = config.get('min_confidence', 0.65)
    max_bets_per_day = config.get('max_bets_per_day', 5)
    
    # Process each match
    current_date = None
    daily_bets = 0
    daily_profit = 0.0
    
    for idx, match in test_matches.iterrows():
        match_date = match['Date'].date()
        home_team = match['HomeTeam']
        away_team = match['AwayTeam']
        
        # Reset daily counters
        if current_date != match_date:
            if current_date is not None:
                daily_pnl.append(daily_profit)
                cumulative_pnl.append(running_pnl)
                betting_dates.append(str(current_date))
            
            current_date = match_date
            daily_bets = 0
            daily_profit = 0.0
        
        # Skip if we've reached daily bet limit
        if daily_bets >= max_bets_per_day:
            continue
        
        # Find best betting opportunity
        best_bets = []
        
        # Check models for home team
        for (team, pattern_name), model_info in trained_models.items():
            if team == home_team:
                model = model_info['model']
                pattern = model_info['pattern']
                
                try:
                    # Get match features
                    match_features = test_features.iloc[[idx]][feature_columns]
                    
                    # Predict probability
                    proba = model.predict_proba(match_features)
                    confidence = proba[0][1]
                    
                    # Apply minimum confidence threshold
                    if confidence >= max(pattern.default_threshold, min_confidence):
                        # Calculate expected value (simplified)
                        expected_odds = 2.0  # Simplified assumption
                        expected_value = (confidence * expected_odds) - 1
                        
                        best_bets.append({
                            'team': team,
                            'pattern_name': pattern_name,
                            'confidence': confidence,
                            'expected_value': expected_value,
                            'pattern_fn': pattern.label_fn,
                            'model_performance': model_performance.get((team, pattern_name), {})
                        })
                        
                except Exception as e:
                    logger.warning(f"Prediction error for {team}/{pattern_name}: {e}")
        
        # Select best bet (highest expected value)
        if best_bets:
            best_bet = max(best_bets, key=lambda x: x['expected_value'])
            
            # Place bet
            stake = unit_stake
            total_stake += stake
            daily_bets += 1
            
            # Check outcome
            actual_result = best_bet['pattern_fn'](match)
            
            bet_info = {
                'date': match_date,
                'home_team': home_team,
                'away_team': away_team,
                'pattern': best_bet['pattern_name'],
                'confidence': best_bet['confidence'],
                'stake': stake,
                'result': actual_result
            }
            
            if actual_result:
                # Win
                return_amount = stake * 2.0  # Simplified odds
                total_return += return_amount
                profit = return_amount - stake
                
                bet_info['return'] = return_amount
                bet_info['profit'] = profit
                
                logger.debug(f"WIN: {home_team} vs {away_team} - {best_bet['pattern_name']} "
                           f"({best_bet['confidence']:.3f})")
            else:
                # Loss
                profit = -stake
                bet_info['return'] = 0.0
                bet_info['profit'] = profit
                
                logger.debug(f"LOSS: {home_team} vs {away_team} - {best_bet['pattern_name']} "
                           f"({best_bet['confidence']:.3f})")
            
            # Update tracking
            running_pnl += profit
            daily_profit += profit
            
            # Track drawdown
            if running_pnl > peak_pnl:
                peak_pnl = running_pnl
            drawdown = peak_pnl - running_pnl
            if drawdown > max_drawdown:
                max_drawdown = drawdown
            
            bets_placed.append(bet_info)
            
            # Update pattern stats
            pattern_name = best_bet['pattern_name']
            if pattern_name not in pattern_stats:
                pattern_stats[pattern_name] = {
                    'bets': 0, 'wins': 0, 'stake': 0.0, 'return': 0.0, 
                    'confidences': []
                }
            
            pattern_stats[pattern_name]['bets'] += 1
            pattern_stats[pattern_name]['stake'] += stake
            pattern_stats[pattern_name]['confidences'].append(best_bet['confidence'])
            
            if actual_result:
                pattern_stats[pattern_name]['wins'] += 1
                pattern_stats[pattern_name]['return'] += return_amount
            
            # Update team stats
            if home_team not in team_stats:
                team_stats[home_team] = {'bets': 0, 'wins': 0, 'stake': 0.0, 'return': 0.0}
            
            team_stats[home_team]['bets'] += 1
            team_stats[home_team]['stake'] += stake
            
            if actual_result:
                team_stats[home_team]['wins'] += 1
                team_stats[home_team]['return'] += return_amount
    
    # Finalize daily tracking
    if current_date is not None:
        daily_pnl.append(daily_profit)
        cumulative_pnl.append(running_pnl)
        betting_dates.append(str(current_date))
    
    # Calculate final metrics
    total_bets = len(bets_placed)
    winning_bets = sum(1 for bet in bets_placed if bet['result'])
    win_rate = winning_bets / total_bets if total_bets > 0 else 0.0
    roi = (total_return - total_stake) / total_stake if total_stake > 0 else 0.0
    
    # Calculate profit factor
    gross_profit = sum(bet['profit'] for bet in bets_placed if bet['profit'] > 0)
    gross_loss = abs(sum(bet['profit'] for bet in bets_placed if bet['profit'] < 0))
    profit_factor = gross_profit / gross_loss if gross_loss > 0 else float('inf')
    
    # Enhance pattern stats
    for pattern_name in pattern_stats:
        stats = pattern_stats[pattern_name]
        stats['win_rate'] = stats['wins'] / stats['bets']
        stats['roi'] = (stats['return'] - stats['stake']) / stats['stake']
        stats['avg_confidence'] = np.mean(stats['confidences'])
        del stats['confidences']  # Remove raw data
    
    # Enhance team stats
    for team in team_stats:
        stats = team_stats[team]
        stats['win_rate'] = stats['wins'] / stats['bets']
        stats['roi'] = (stats['return'] - stats['stake']) / stats['stake']
    
    return {
        'total_matches': len(test_matches),
        'total_bets': total_bets,
        'winning_bets': winning_bets,
        'total_stake': total_stake,
        'total_return': total_return,
        'win_rate': win_rate,
        'roi': roi,
        'max_drawdown': max_drawdown,
        'profit_factor': profit_factor,
        'pattern_stats': pattern_stats,
        'team_stats': team_stats,
        'daily_pnl': daily_pnl,
        'cumulative_pnl': cumulative_pnl,
        'betting_dates': betting_dates
    }


def print_enhanced_results(result: EnhancedBacktestResult) -> None:
    """Print enhanced backtest results with detailed analytics."""
    print(f"\n{'='*80}")
    print(f"ENHANCED BACKTEST RESULTS - {result.league}")
    print(f"{'='*80}")
    print(f"Period: {result.start_date} to {result.end_date}")
    print(f"Total matches: {result.total_matches}")
    print(f"")
    print(f"BETTING PERFORMANCE:")
    print(f"  Total bets: {result.total_bets}")
    print(f"  Winning bets: {result.winning_bets}")
    print(f"  Win rate: {result.win_rate:.2%}")
    print(f"  Total stake: {result.total_stake:.2f}")
    print(f"  Total return: {result.total_return:.2f}")
    print(f"  Net profit: {result.total_return - result.total_stake:.2f}")
    print(f"  ROI: {result.roi:.2%}")
    print(f"  Max drawdown: {result.max_drawdown:.2f}")
    print(f"  Profit factor: {result.profit_factor:.2f}")
    
    if result.pattern_stats:
        print(f"\nPATTERN PERFORMANCE:")
        print(f"{'Pattern':<25} {'Bets':<5} {'WR':<8} {'ROI':<8} {'AvgConf':<8}")
        print(f"{'-'*60}")
        
        # Sort by ROI
        sorted_patterns = sorted(
            result.pattern_stats.items(), 
            key=lambda x: x[1]['roi'], 
            reverse=True
        )
        
        for pattern_name, stats in sorted_patterns:
            print(f"{pattern_name:<25} {stats['bets']:<5} "
                  f"{stats['win_rate']:<8.2%} {stats['roi']:<8.2%} "
                  f"{stats['avg_confidence']:<8.3f}")
    
    if result.team_stats:
        print(f"\nTOP TEAM PERFORMANCE:")
        print(f"{'Team':<20} {'Bets':<5} {'WR':<8} {'ROI':<8}")
        print(f"{'-'*45}")
        
        # Sort by ROI, show top 10
        sorted_teams = sorted(
            result.team_stats.items(),
            key=lambda x: x[1]['roi'],
            reverse=True
        )[:10]
        
        for team, stats in sorted_teams:
            print(f"{team:<20} {stats['bets']:<5} "
                  f"{stats['win_rate']:<8.2%} {stats['roi']:<8.2%}")
    
    print(f"{'='*80}")


def save_enhanced_results(result: EnhancedBacktestResult, output_dir: str) -> str:
    """Save enhanced results to JSON with all analytics."""
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Convert result to dict
    results_dict = {
        'league': result.league,
        'start_date': result.start_date,
        'end_date': result.end_date,
        'config': result.config,
        'performance': {
            'total_matches': result.total_matches,
            'total_bets': result.total_bets,
            'winning_bets': result.winning_bets,
            'win_rate': result.win_rate,
            'roi': result.roi,
            'max_drawdown': result.max_drawdown,
            'profit_factor': result.profit_factor,
            'total_stake': result.total_stake,
            'total_return': result.total_return
        },
        'pattern_stats': result.pattern_stats,
        'team_stats': result.team_stats,
        'time_series': {
            'daily_pnl': result.daily_pnl,
            'cumulative_pnl': result.cumulative_pnl,
            'betting_dates': result.betting_dates
        }
    }
    
    filename = f"enhanced_backtest_{result.league}_{result.start_date}_{result.end_date}.json"
    results_file = output_path / filename
    
    with open(results_file, 'w') as f:
        json.dump(results_dict, f, indent=2)
    
    return str(results_file)