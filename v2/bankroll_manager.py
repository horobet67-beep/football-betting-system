"""
Bankroll Manager - Kelly Criterion with Safety Limits

Implements proper stake sizing and risk management for betting.
NEVER bet without bankroll management!

Features:
- Kelly Criterion for optimal stake sizing
- Conservative quarter-Kelly (reduces variance)
- Max stake limits (2% bankroll per bet)
- Stop-loss protection (80% threshold)
- Daily bet limits
- Consecutive loss tracking
"""

from datetime import datetime, timedelta
from typing import Dict, Optional
import json
from pathlib import Path


class BankrollManager:
    """Manage betting bankroll with Kelly Criterion and safety limits"""
    
    def __init__(
        self,
        initial_bankroll: float,
        max_stake_pct: float = 0.02,  # 2% max per bet
        stop_loss_pct: float = 0.80,  # Stop at 80% bankroll
        max_daily_bets: int = 3,
        max_consecutive_losses: int = 3,
        kelly_fraction: float = 0.25,  # Quarter Kelly (conservative)
        db_file: str = "bankroll.json"
    ):
        """
        Initialize bankroll manager.
        
        Args:
            initial_bankroll: Starting bankroll amount
            max_stake_pct: Maximum stake as % of bankroll (0.02 = 2%)
            stop_loss_pct: Stop trading when bankroll drops below this (0.80 = 80%)
            max_daily_bets: Maximum bets per day
            max_consecutive_losses: Stop after this many losses in a row
            kelly_fraction: Fraction of Kelly to use (0.25 = quarter Kelly)
            db_file: JSON file to persist bankroll state
        """
        self.initial_bankroll = initial_bankroll
        self.current_bankroll = initial_bankroll
        self.max_stake_pct = max_stake_pct
        self.stop_loss_pct = stop_loss_pct
        self.max_daily_bets = max_daily_bets
        self.max_consecutive_losses = max_consecutive_losses
        self.kelly_fraction = kelly_fraction
        self.db_file = Path(db_file)
        
        self.bet_history = []
        self.consecutive_losses = 0
        self.daily_bets = {}  # {date: count}
        
        self._load_state()
    
    def _load_state(self):
        """Load bankroll state from JSON file"""
        if self.db_file.exists():
            with open(self.db_file, 'r') as f:
                state = json.load(f)
                self.current_bankroll = state.get('current_bankroll', self.initial_bankroll)
                self.bet_history = state.get('bet_history', [])
                self.consecutive_losses = state.get('consecutive_losses', 0)
                self.daily_bets = state.get('daily_bets', {})
    
    def _save_state(self):
        """Save bankroll state to JSON file"""
        state = {
            'initial_bankroll': self.initial_bankroll,
            'current_bankroll': self.current_bankroll,
            'bet_history': self.bet_history,
            'consecutive_losses': self.consecutive_losses,
            'daily_bets': self.daily_bets,
            'last_updated': datetime.now().isoformat()
        }
        with open(self.db_file, 'w') as f:
            json.dump(state, f, indent=2)
    
    def calculate_kelly_stake(
        self,
        confidence: float,
        odds: float,
        pattern_name: Optional[str] = None
    ) -> float:
        """
        Calculate optimal stake using Kelly Criterion.
        
        Formula: f* = (bp - q) / b
        where:
            b = odds - 1 (net odds)
            p = win probability (confidence)
            q = lose probability (1 - confidence)
        
        Args:
            confidence: Win probability (0-1)
            odds: Decimal odds (e.g., 1.30)
            pattern_name: Optional pattern name for logging
            
        Returns:
            Stake amount in currency units
        """
        if confidence <= 0.5 or odds <= 1.0:
            return 0.0  # No edge or invalid odds
        
        # Calculate Kelly fraction
        b = odds - 1  # Net odds
        p = confidence
        q = 1 - confidence
        
        kelly = (b * p - q) / b
        
        # Apply conservative fraction (quarter Kelly reduces variance)
        conservative_kelly = kelly * self.kelly_fraction
        
        # Convert to currency amount
        kelly_stake = conservative_kelly * self.current_bankroll
        
        # Apply maximum stake limit (2% of bankroll)
        max_stake = self.max_stake_pct * self.current_bankroll
        final_stake = min(kelly_stake, max_stake)
        
        # Round to 2 decimals
        final_stake = round(max(0, final_stake), 2)
        
        return final_stake
    
    def can_place_bet(self, date: Optional[str] = None) -> tuple[bool, str]:
        """
        Check if bet is allowed based on risk management rules.
        
        Args:
            date: Date string (YYYY-MM-DD), defaults to today
            
        Returns:
            (allowed: bool, reason: str)
        """
        if date is None:
            date = datetime.now().strftime('%Y-%m-%d')
        
        # Check stop-loss
        stop_loss_level = self.initial_bankroll * self.stop_loss_pct
        if self.current_bankroll < stop_loss_level:
            return False, f"🛑 STOP-LOSS triggered: Bankroll {self.current_bankroll:.2f} < {stop_loss_level:.2f}"
        
        # Check consecutive losses
        if self.consecutive_losses >= self.max_consecutive_losses:
            return False, f"🛑 Max consecutive losses ({self.consecutive_losses}) - COOLDOWN required"
        
        # Check daily bet limit
        today_bets = self.daily_bets.get(date, 0)
        if today_bets >= self.max_daily_bets:
            return False, f"🛑 Daily bet limit reached ({today_bets}/{self.max_daily_bets})"
        
        return True, "✅ Bet allowed"
    
    def place_bet(
        self,
        stake: float,
        pattern: str,
        confidence: float,
        odds: float,
        match_info: str,
        date: Optional[str] = None
    ) -> bool:
        """
        Record a bet placement.
        
        Args:
            stake: Stake amount
            pattern: Pattern name
            confidence: Win probability
            odds: Decimal odds
            match_info: Match description
            date: Date string (YYYY-MM-DD)
            
        Returns:
            True if bet placed successfully
        """
        if date is None:
            date = datetime.now().strftime('%Y-%m-%d')
        
        allowed, reason = self.can_place_bet(date)
        if not allowed:
            print(reason)
            return False
        
        # Record bet
        bet = {
            'date': date,
            'timestamp': datetime.now().isoformat(),
            'match': match_info,
            'pattern': pattern,
            'stake': stake,
            'odds': odds,
            'confidence': confidence,
            'result': None,  # To be filled when settled
            'profit': None
        }
        self.bet_history.append(bet)
        
        # Update daily counter
        self.daily_bets[date] = self.daily_bets.get(date, 0) + 1
        
        self._save_state()
        
        print(f"✅ Bet placed: {stake:.2f} on {pattern} @ {odds:.2f}")
        return True
    
    def settle_bet(self, bet_index: int, won: bool):
        """
        Settle a bet and update bankroll.
        
        Args:
            bet_index: Index in bet_history
            won: True if bet won, False if lost
        """
        if bet_index >= len(self.bet_history):
            print(f"❌ Invalid bet index: {bet_index}")
            return
        
        bet = self.bet_history[bet_index]
        if bet['result'] is not None:
            print(f"⚠️ Bet already settled")
            return
        
        stake = bet['stake']
        odds = bet['odds']
        
        if won:
            profit = stake * (odds - 1)
            self.current_bankroll += profit
            self.consecutive_losses = 0
            result_emoji = "✅"
        else:
            profit = -stake
            self.current_bankroll += profit  # Subtract loss
            self.consecutive_losses += 1
            result_emoji = "❌"
        
        bet['result'] = won
        bet['profit'] = profit
        bet['settled_at'] = datetime.now().isoformat()
        
        self._save_state()
        
        print(f"{result_emoji} Bet settled: {bet['match']}")
        print(f"   Profit: {profit:+.2f} | Bankroll: {self.current_bankroll:.2f} "
              f"({self.current_bankroll/self.initial_bankroll*100:.1f}%)")
        
        if self.consecutive_losses > 0:
            print(f"   ⚠️ Consecutive losses: {self.consecutive_losses}")
    
    def get_status(self) -> Dict:
        """Get current bankroll status"""
        settled_bets = [b for b in self.bet_history if b['result'] is not None]
        pending_bets = [b for b in self.bet_history if b['result'] is None]
        
        if settled_bets:
            wins = sum(1 for b in settled_bets if b['result'])
            total_profit = sum(b['profit'] for b in settled_bets)
            roi = (self.current_bankroll - self.initial_bankroll) / self.initial_bankroll * 100
        else:
            wins = 0
            total_profit = 0
            roi = 0
        
        return {
            'initial_bankroll': self.initial_bankroll,
            'current_bankroll': self.current_bankroll,
            'total_bets': len(self.bet_history),
            'settled_bets': len(settled_bets),
            'pending_bets': len(pending_bets),
            'wins': wins,
            'losses': len(settled_bets) - wins,
            'win_rate': wins / len(settled_bets) * 100 if settled_bets else 0,
            'total_profit': total_profit,
            'roi': roi,
            'consecutive_losses': self.consecutive_losses,
            'stop_loss_triggered': self.current_bankroll < (self.initial_bankroll * self.stop_loss_pct)
        }
    
    def print_status(self):
        """Print formatted status report"""
        status = self.get_status()
        
        print(f"\n{'='*60}")
        print(f"💰 BANKROLL STATUS")
        print(f"{'='*60}")
        print(f"Initial:  {status['initial_bankroll']:>10.2f}")
        print(f"Current:  {status['current_bankroll']:>10.2f} "
              f"({status['current_bankroll']/status['initial_bankroll']*100:.1f}%)")
        print(f"Profit:   {status['total_profit']:>+10.2f}")
        print(f"ROI:      {status['roi']:>+9.1f}%")
        print(f"\n📊 BETTING STATISTICS")
        print(f"{'='*60}")
        print(f"Total Bets:    {status['total_bets']:>3d}")
        print(f"Settled:       {status['settled_bets']:>3d}")
        print(f"Pending:       {status['pending_bets']:>3d}")
        if status['settled_bets'] > 0:
            print(f"Wins/Losses:   {status['wins']:>3d}/{status['losses']:>3d}")
            print(f"Win Rate:      {status['win_rate']:>5.1f}%")
        print(f"\n🚨 RISK METRICS")
        print(f"{'='*60}")
        print(f"Consecutive Losses: {status['consecutive_losses']}/{self.max_consecutive_losses}")
        print(f"Stop-Loss Level:    {self.initial_bankroll * self.stop_loss_pct:.2f}")
        
        if status['stop_loss_triggered']:
            print(f"\n🛑 STOP-LOSS TRIGGERED - STOP BETTING!")
        elif status['consecutive_losses'] >= self.max_consecutive_losses:
            print(f"\n⚠️ MAX CONSECUTIVE LOSSES - COOLDOWN REQUIRED!")
        else:
            print(f"\n✅ Risk checks: PASSED")
        
        print(f"{'='*60}\n")


def demo():
    """Demo bankroll manager"""
    print("Bankroll Manager Demo")
    print("="*60)
    
    # Initialize with €100 bankroll
    manager = BankrollManager(initial_bankroll=100.0)
    
    # Example bet 1: 85% confidence at 1.30 odds
    print("\n📋 Example Bet 1: away_over_0_5_cards")
    print(f"   Confidence: 85%, Odds: 1.30")
    
    allowed, reason = manager.can_place_bet()
    print(f"   {reason}")
    
    if allowed:
        stake = manager.calculate_kelly_stake(0.85, 1.30)
        print(f"   Recommended stake: €{stake:.2f}")
        
        manager.place_bet(
            stake=stake,
            pattern="away_over_0_5_cards",
            confidence=0.85,
            odds=1.30,
            match_info="Inter vs Juventus"
        )
    
    manager.print_status()


if __name__ == '__main__':
    demo()
