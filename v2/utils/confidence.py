"""
Multi-timeframe confidence calculation with dynamic weighting.

This module implements an ensemble approach that combines pattern success rates
across multiple timeframes with intelligent adjustments for trends, consistency,
and sample size validation.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Callable, Dict, Tuple


def calculate_multi_timeframe_confidence(
    data: pd.DataFrame,
    match_date: datetime,
    pattern_fn: Callable,
    min_matches_7d: int = 3,
    min_matches_30d: int = 10,
    custom_timeframes: Dict[int, float] = None,
    use_all_history: bool = True
) -> Tuple[float, Dict]:
    """
    Calculate pattern confidence using multi-timeframe ensemble with dynamic adjustments.
    
    This method:
    1. Evaluates pattern across multiple timeframes (7d, 14d, 30d, 90d, 365d, ALL)
    2. Combines them with weights favoring recent data
    3. Adjusts for trends (recent vs historical performance)
    4. Adjusts for consistency (standard deviation across timeframes)
    5. Validates sufficient sample sizes
    
    Args:
        data: Historical match DataFrame with 'Date' column
        match_date: Date of the match to predict
        pattern_fn: Function that takes a match row and returns True/False
        min_matches_7d: Minimum matches required in last 7 days
        min_matches_30d: Minimum matches required in last 30 days
        custom_timeframes: Optional custom timeframes dict {days: weight}. If None, uses defaults.
        use_all_history: If True, includes ALL available data as a timeframe (recommended!)
        
    Returns:
        Tuple of (final_confidence, debug_info_dict)
        
    Example:
        >>> confidence, info = calculate_multi_timeframe_confidence(
        ...     data, datetime(2025, 11, 9), away_over_0_5_cards, use_all_history=True
        ... )
        >>> print(f"Confidence: {confidence:.1%}, Trend: {info['trend']}")
    """
    # Define timeframes with their weights (default configuration)
    # These weights can be optimized per league/pattern type
    if custom_timeframes:
        timeframes = custom_timeframes
    else:
        timeframes = {
            7: 0.30,     # Last 7 days - Ultra Recent (30% weight)
            14: 0.23,    # Last 14 days - Recent (23% weight)
            30: 0.18,    # Last 30 days - Short Term (18% weight)
            90: 0.14,    # Last 90 days - Quarter (14% weight)
            365: 0.10,   # Last 365 days - Full Season (10% weight)
            730: 0.05,   # Last 2 years - Multi-Season (5% weight) - NEW!
        }
        
        # Add ALL historical data timeframe if requested
        if use_all_history:
            # Calculate days from earliest data to match_date
            earliest_date = data['Date'].min()
            all_history_days = (match_date - earliest_date).days
            if all_history_days > 730:  # Only add if we have more than 2 years
                timeframes[99999] = 0.00  # All history gets 0% direct weight
                                           # (but used for trend/consistency analysis)
    
    # Calculate success rate for each timeframe
    timeframe_results = {}
    confidences = []
    
    for days, weight in timeframes.items():
        if days == 99999:
            # ALL historical data
            tf_data = data[data['Date'] < match_date]
        else:
            cutoff = match_date - timedelta(days=days)
            tf_data = data[(data['Date'] >= cutoff) & (data['Date'] < match_date)]
        
        if len(tf_data) > 0:
            success_rate = tf_data.apply(pattern_fn, axis=1).mean()
            timeframe_results[days] = {
                'matches': len(tf_data),
                'success': success_rate,
                'weight': weight
            }
            # Only include in consistency check if weight > 0
            if weight > 0:
                confidences.append(success_rate)
    
    # If we don't have enough data, return low confidence
    if not timeframe_results:
        return 0.5, {'error': 'No historical data available'}
    
    # Calculate weighted ensemble confidence (only weighted timeframes)
    ensemble_confidence = 0
    total_weight = 0
    
    for days, result in timeframe_results.items():
        if result['weight'] > 0:
            ensemble_confidence += result['success'] * result['weight']
            total_weight += result['weight']
    
    ensemble_confidence = ensemble_confidence / total_weight if total_weight > 0 else 0.5
    
    # Trend analysis - compare recent to historical
    recent_7 = timeframe_results.get(7, {}).get('success', ensemble_confidence)
    recent_30 = timeframe_results.get(30, {}).get('success', ensemble_confidence)
    season = timeframe_results.get(365, {}).get('success', ensemble_confidence)
    all_history = timeframe_results.get(99999, {}).get('success', ensemble_confidence)
    
    trend_7_vs_30 = recent_7 - recent_30
    trend_30_vs_season = recent_30 - season
    trend_season_vs_all = season - all_history if 99999 in timeframe_results else 0
    
    # Determine trend category (use 7d vs 30d as primary, but validate with longer trends)
    if trend_7_vs_30 > 0.03 and trend_30_vs_season >= -0.02:
        trend = 'strong_uptrend'
        trend_adjustment = 0.02
    elif trend_7_vs_30 < -0.03 and trend_30_vs_season <= 0.02:
        trend = 'downtrend'
        trend_adjustment = -0.02
    else:
        trend = 'stable'
        trend_adjustment = 0.0
    
    # Consistency check (standard deviation across timeframes)
    std_dev = np.std(confidences) if len(confidences) > 1 else 0
    
    if std_dev < 0.03:
        consistency = 'high'
        consistency_adjustment = 0.01
    elif std_dev < 0.05:
        consistency = 'moderate'
        consistency_adjustment = 0.0
    else:
        consistency = 'low'
        consistency_adjustment = -0.02
    
    # Sample size validation
    matches_7d = timeframe_results.get(7, {}).get('matches', 0)
    matches_30d = timeframe_results.get(30, {}).get('matches', 0)
    
    if matches_7d >= min_matches_7d and matches_30d >= min_matches_30d:
        sample_quality = 'sufficient'
        sample_adjustment = 0.0
    elif matches_7d >= max(2, min_matches_7d - 1) and matches_30d >= max(8, min_matches_30d - 2):
        sample_quality = 'adequate'
        sample_adjustment = -0.02
    else:
        sample_quality = 'insufficient'
        sample_adjustment = -0.05
    
    # Calculate final confidence with all adjustments
    final_confidence = ensemble_confidence + trend_adjustment + consistency_adjustment + sample_adjustment
    
    # Clamp to valid range [0, 1]
    final_confidence = max(0.0, min(1.0, final_confidence))
    
    # Build debug info
    debug_info = {
        'ensemble_confidence': ensemble_confidence,
        'final_confidence': final_confidence,
        'timeframe_results': timeframe_results,
        'trend': trend,
        'trend_adjustment': trend_adjustment,
        'trend_7_vs_30': trend_7_vs_30,
        'trend_30_vs_season': trend_30_vs_season,
        'trend_season_vs_all': trend_season_vs_all,
        'consistency': consistency,
        'consistency_adjustment': consistency_adjustment,
        'std_dev': std_dev,
        'sample_quality': sample_quality,
        'sample_adjustment': sample_adjustment,
        'matches_7d': matches_7d,
        'matches_30d': matches_30d,
        'all_history_matches': timeframe_results.get(99999, {}).get('matches', 0),
        'all_history_success': all_history,
    }
    
    return final_confidence, debug_info


def format_confidence_explanation(debug_info: Dict) -> str:
    """
    Format the debug info into a human-readable explanation.
    
    Args:
        debug_info: Debug dictionary returned from calculate_multi_timeframe_confidence
        
    Returns:
        Formatted string explaining the confidence calculation
    """
    lines = []
    lines.append(f"Base Ensemble: {debug_info['ensemble_confidence']:.1%}")
    
    if debug_info['trend_adjustment'] != 0:
        lines.append(f"  Trend ({debug_info['trend']}): {debug_info['trend_adjustment']:+.1%}")
    
    if debug_info['consistency_adjustment'] != 0:
        lines.append(f"  Consistency ({debug_info['consistency']}): {debug_info['consistency_adjustment']:+.1%}")
    
    if debug_info['sample_adjustment'] != 0:
        lines.append(f"  Sample ({debug_info['sample_quality']}): {debug_info['sample_adjustment']:+.1%}")
    
    lines.append(f"Final: {debug_info['final_confidence']:.1%}")
    
    return "\n".join(lines)
