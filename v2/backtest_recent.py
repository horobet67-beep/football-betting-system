#!/usr/bin/env python3
"""
Romanian Liga I Backtest System

Backtest the enhanced prediction system against recent completed matches
to validate accuracy and profitability of our betting recommendations.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sys
import glob
from typing import List, Dict, Tuple

# Add v2 to path
sys.path.append('.')

from simple_predict_range import SimpleRomanianPredictor, SimpleBettingRecommendation


def load_romanian_data() -> pd.DataFrame:
    """Load and process Romanian Liga I data"""
    csv_files = glob.glob('data/liga1-romania/*.csv')
    data_frames = []
    
    for file in csv_files:
        df = pd.read_csv(file)
        
        # Map to standard format
        df_mapped = pd.DataFrame({
            'HomeTeam': df['home_team_name'],
            'AwayTeam': df['away_team_name'],
            'FTHG': df['home_team_goal_count'],
            'FTAG': df['away_team_goal_count'],
            'HC': df['home_team_corner_count'],
            'AC': df['away_team_corner_count'],
            'HY': df['home_team_yellow_cards'],
            'AY': df['away_team_yellow_cards'],
            'Date': df['date_GMT'],
            'Status': df['status'],
            'Timestamp': df['timestamp']
        })
        
        # Add result for completed matches
        def get_result(row):
            if pd.isna(row['FTHG']) or pd.isna(row['FTAG']):
                return None
            return 'H' if row['FTHG'] > row['FTAG'] else ('A' if row['FTAG'] > row['FTHG'] else 'D')
        
        df_mapped['FTR'] = df_mapped.apply(get_result, axis=1)
        data_frames.append(df_mapped)
    
    combined_data = pd.concat(data_frames, ignore_index=True)
    combined_data = combined_data.dropna(subset=['HomeTeam', 'AwayTeam'])
    combined_data['DateTime'] = pd.to_datetime(combined_data['Timestamp'], unit='s')
    
    return combined_data


def check_bet_result(bet: SimpleBettingRecommendation, actual_match: pd.Series) -> Tuple[bool, str]:
    """Check if a bet would have won based on actual match results"""
    
    home_goals = actual_match['FTHG']
    away_goals = actual_match['FTAG']
    home_corners = actual_match['HC'] if not pd.isna(actual_match['HC']) else 0
    away_corners = actual_match['AC'] if not pd.isna(actual_match['AC']) else 0
    home_cards = actual_match['HY'] if not pd.isna(actual_match['HY']) else 0
    away_cards = actual_match['AY'] if not pd.isna(actual_match['AY']) else 0
    
    pattern = bet.pattern_name
    
    # Check pattern results
    if pattern == 'total_over_8_5_corners':
        total_corners = home_corners + away_corners
        won = total_corners > 8.5
        result_detail = f"Total corners: {total_corners} ({'✅ WIN' if won else '❌ LOSS'})"
        
    elif pattern == 'total_over_9_5_corners':
        total_corners = home_corners + away_corners
        won = total_corners > 9.5
        result_detail = f"Total corners: {total_corners} ({'✅ WIN' if won else '❌ LOSS'})"
        
    elif pattern == 'total_over_7_5_corners':
        total_corners = home_corners + away_corners
        won = total_corners > 7.5
        result_detail = f"Total corners: {total_corners} ({'✅ WIN' if won else '❌ LOSS'})"
        
    elif pattern == 'total_over_10_5_corners':
        total_corners = home_corners + away_corners
        won = total_corners > 10.5
        result_detail = f"Total corners: {total_corners} ({'✅ WIN' if won else '❌ LOSS'})"
        
    elif pattern == 'home_over_0_5_goals':
        won = home_goals > 0.5
        result_detail = f"Home goals: {home_goals} ({'✅ WIN' if won else '❌ LOSS'})"
        
    elif pattern == 'away_over_1_5_goals':
        won = away_goals > 1.5
        result_detail = f"Away goals: {away_goals} ({'✅ WIN' if won else '❌ LOSS'})"
        
    elif pattern == 'both_teams_to_score':
        won = home_goals > 0 and away_goals > 0
        result_detail = f"Goals: {home_goals}-{away_goals} ({'✅ WIN' if won else '❌ LOSS'})"
        
    elif pattern == 'total_over_3_5_goals':
        total_goals = home_goals + away_goals
        won = total_goals > 3.5
        result_detail = f"Total goals: {total_goals} ({'✅ WIN' if won else '❌ LOSS'})"
        
    elif pattern == 'home_over_1_5_cards':
        won = home_cards > 1.5
        result_detail = f"Home cards: {home_cards} ({'✅ WIN' if won else '❌ LOSS'})"
        
    else:
        won = False
        result_detail = "Pattern not implemented for backtest"
    
    return won, result_detail


def run_backtest(days_back: int = 10):
    """Run backtest on last N days of completed matches"""
    
    print(f"🔍 ROMANIAN LIGA I BACKTEST")
    print(f"📅 Testing last {days_back} days of completed matches")
    print("=" * 60)
    
    # Load all data
    all_data = load_romanian_data()
    completed_matches = all_data[all_data['Status'] == 'complete'].copy()
    
    if len(completed_matches) == 0:
        print("❌ No completed matches found")
        return
    
    # Get date range for backtest
    latest_date = completed_matches['DateTime'].max()
    start_date = latest_date - timedelta(days=days_back)
    
    print(f"📊 Latest completed match: {latest_date.strftime('%Y-%m-%d')}")
    print(f"🔙 Backtesting from: {start_date.strftime('%Y-%m-%d')}")
    
    # Get matches in backtest period
    backtest_matches = completed_matches[
        completed_matches['DateTime'] >= start_date
    ].copy().sort_values('DateTime')
    
    print(f"🎯 Found {len(backtest_matches)} matches to backtest")
    print()
    
    # Initialize predictor
    predictor = SimpleRomanianPredictor()
    
    # Track results
    all_bets = []
    winning_bets = []
    losing_bets = []
    total_stake = 0
    total_return = 0
    
    print("📋 BACKTEST RESULTS - ALL MATCHES")
    print("=" * 45)
    
    # Process each match
    match_counter = 0
    for idx, match in backtest_matches.iterrows():
        match_counter += 1
        
        # Get historical data (everything before this match)
        historical_data = completed_matches[completed_matches['DateTime'] < match['DateTime']].copy()
        
        # Display match header
        print(f"\n{match_counter}. {match['DateTime'].strftime('%m-%d %H:%M')} - {match['HomeTeam']} vs {match['AwayTeam']}")
        print(f"   📊 Actual Result: {int(match['FTHG'])}-{int(match['FTAG'])} (Corners: {int(match['HC'])}-{int(match['AC'])})")
        
        if len(historical_data) < 20:  # Need sufficient historical data
            print(f"   ⚠️ INSUFFICIENT DATA: Only {len(historical_data)} historical matches")
            continue
        
        # Get predictions for this match
        recommendations = predictor.predict_match(
            match['HomeTeam'], match['AwayTeam'], historical_data
        )
        
        # Find best bet recommendation
        bet_recs = [r for r in recommendations if r.recommendation == "BET"]
        
        if bet_recs:
            best_bet = max(bet_recs, key=lambda x: x.expected_value)
            
            # Check actual result
            won, result_detail = check_bet_result(best_bet, match)
            
            # Calculate returns (assuming 1 unit stake)
            stake = 1.0
            actual_odds = predictor.get_expected_odds(best_bet.pattern_name)
            returns = stake * actual_odds if won else 0
            profit = returns - stake
            
            # Track statistics
            all_bets.append({
                'match': f"{match['HomeTeam']} vs {match['AwayTeam']}",
                'date': match['DateTime'].strftime('%Y-%m-%d'),
                'bet': best_bet,
                'won': won,
                'stake': stake,
                'returns': returns,
                'profit': profit,
                'result_detail': result_detail
            })
            
            total_stake += stake
            total_return += returns
            
            if won:
                winning_bets.append(best_bet)
            else:
                losing_bets.append(best_bet)
            
            # Display result
            status = "🟢 BET & WIN" if won else "🔴 BET & LOSS"
            print(f"   {status}")
            print(f"   💰 Bet: {best_bet.bet_type}")
            print(f"   📊 Confidence: {best_bet.confidence:.1%} (threshold: {best_bet.threshold:.1%})")
            print(f"   🎯 {result_detail}")
            print(f"   💵 Profit: {profit:+.2f} units")
        
        else:
            # NO BET case - show why
            print(f"   ❌ NO BET: No patterns met confidence threshold")
            
            # Show best pattern that didn't qualify
            if recommendations:
                best_non_bet = max(recommendations, key=lambda x: x.confidence)
                print(f"   � Best pattern: {best_non_bet.bet_type}")
                print(f"   � Confidence: {best_non_bet.confidence:.1%} (needed: {best_non_bet.threshold:.1%})")
                
                # Show what would have happened if we bet anyway
                hypothetical_won, hypothetical_result = check_bet_result(best_non_bet, match)
                hypothetical_status = "would have WON" if hypothetical_won else "would have LOST"
                print(f"   � Hypothetical: {hypothetical_result} - {hypothetical_status}")
            else:
                print(f"   ⚠️ No recommendations generated")
    
    # Calculate final statistics
    if all_bets:
        win_rate = len(winning_bets) / len(all_bets)
        total_profit = total_return - total_stake
        roi = (total_profit / total_stake) * 100 if total_stake > 0 else 0
        
        print("📈 BACKTEST SUMMARY")
        print("=" * 30)
        print(f"🎯 Total bets placed: {len(all_bets)}")
        print(f"✅ Winning bets: {len(winning_bets)}")
        print(f"❌ Losing bets: {len(losing_bets)}")
        print(f"📊 Win rate: {win_rate:.1%}")
        print(f"💰 Total stake: {total_stake:.1f} units")
        print(f"💵 Total returns: {total_return:.1f} units")
        print(f"🏆 Net profit: {total_profit:+.1f} units")
        print(f"📈 ROI: {roi:+.1f}%")
        
        if winning_bets:
            avg_winning_confidence = np.mean([b.confidence for b in winning_bets])
            print(f"💎 Average winning confidence: {avg_winning_confidence:.1%}")
        
        if losing_bets:
            avg_losing_confidence = np.mean([b.confidence for b in losing_bets])
            print(f"⚠️ Average losing confidence: {avg_losing_confidence:.1%}")
        
        # Pattern analysis
        print(f"\n🎨 PATTERN PERFORMANCE:")
        pattern_stats = {}
        for bet_data in all_bets:
            pattern = bet_data['bet'].pattern_name
            if pattern not in pattern_stats:
                pattern_stats[pattern] = {'wins': 0, 'total': 0, 'profit': 0}
            pattern_stats[pattern]['total'] += 1
            pattern_stats[pattern]['profit'] += bet_data['profit']
            if bet_data['won']:
                pattern_stats[pattern]['wins'] += 1
        
        for pattern, stats in pattern_stats.items():
            win_rate_pattern = stats['wins'] / stats['total']
            print(f"   • {pattern}: {win_rate_pattern:.1%} win rate, {stats['profit']:+.1f} units profit")
        
        print(f"\n🔮 VALIDATION:")
        if win_rate >= 0.67:  # Our target accuracy
            print(f"✅ Win rate {win_rate:.1%} meets/exceeds 67% target!")
        else:
            print(f"⚠️ Win rate {win_rate:.1%} below 67% target")
        
        if roi > 20:  # Target ROI
            print(f"✅ ROI {roi:+.1f}% exceeds 20% target!")
        else:
            print(f"⚠️ ROI {roi:+.1f}% below 20% target")
    
    else:
        print("❌ No bets were placed during backtest period")
        print("💡 Try increasing the date range or checking data availability")


def main():
    import argparse
    parser = argparse.ArgumentParser(description='Backtest Romanian Liga I predictions')
    parser.add_argument('--days', type=int, default=10, help='Days to backtest (default: 10)')
    
    args = parser.parse_args()
    run_backtest(args.days)


if __name__ == "__main__":
    main()