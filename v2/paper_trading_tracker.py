"""
Paper Trading Tracker - Forward Validation System

Track predictions BEFORE matches to validate forward-looking performance.
This is CRITICAL before betting real money - backtest ≠ real trading.

Usage:
    1. Generate daily predictions: python paper_trading_tracker.py generate
    2. Update with results: python paper_trading_tracker.py update
    3. View performance: python paper_trading_tracker.py report
"""

import json
import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional
import argparse

from data.serie_a_adapter import load_serie_a_data
from data.bundesliga_adapter import load_bundesliga_data
from data.la_liga_adapter import load_la_liga_data
from data.premier_league_adapter import load_premier_league_data
from patterns.registry import clear_patterns

from simple_serie_a_predictor import SimpleSerieAPredictor
from simple_bundesliga_predictor import SimpleBundesligaPredictor
from simple_la_liga_predictor import SimpleLaLigaPredictor
from simple_premier_league_predictor import SimplePremierLeaguePredictor
from simple_romanian_predictor import SimpleRomanianPredictor


class PaperTradingTracker:
    """Track predictions forward to validate real-world performance"""
    
    def __init__(self, db_file: str = "paper_trading.json"):
        self.db_file = Path(db_file)
        self.predictions = self._load_predictions()
    
    def _load_predictions(self) -> List[Dict]:
        """Load existing predictions from JSON database"""
        if self.db_file.exists():
            with open(self.db_file, 'r') as f:
                return json.load(f)
        return []
    
    def _save_predictions(self):
        """Save predictions to JSON database"""
        with open(self.db_file, 'w') as f:
            json.dump(self.predictions, f, indent=2, default=str)
    
    def generate_predictions(self, target_date: Optional[datetime] = None):
        """
        Generate predictions for upcoming matches.
        
        Args:
            target_date: Date to predict for (default: tomorrow)
        """
        if target_date is None:
            target_date = datetime.now() + timedelta(days=1)
        
        print(f"\n🔮 Generating predictions for {target_date.strftime('%Y-%m-%d')}")
        print("="*80)
        
        all_predictions = []
        
        # Serie A
        print("\n🇮🇹 Serie A:")
        try:
            predictor = SimpleSerieAPredictor()
            data = predictor.data
            matches = data[data['Date'].dt.date == target_date.date()]
            
            for _, match in matches.iterrows():
                pred = predictor.predict_match(
                    match['HomeTeam'],
                    match['AwayTeam'],
                    match['Date']
                )
                if pred:
                    all_predictions.append({
                        'league': 'Serie A',
                        'date': target_date.strftime('%Y-%m-%d'),
                        'home_team': match['HomeTeam'],
                        'away_team': match['AwayTeam'],
                        'pattern': pred.pattern_name,
                        'confidence': pred.confidence,
                        'risk_adjusted_confidence': pred.risk_adjusted_confidence,
                        'threshold': pred.threshold,
                        'prediction_time': datetime.now().isoformat(),
                        'result': None,  # To be filled later
                        'actual_outcome': None
                    })
                    print(f"  ✅ {match['HomeTeam']} vs {match['AwayTeam']}: "
                          f"{pred.pattern_name} ({pred.risk_adjusted_confidence:.1%})")
        except Exception as e:
            print(f"  ⚠️ Error: {e}")
        
        # Bundesliga
        print("\n🇩🇪 Bundesliga:")
        try:
            from data.bundesliga_adapter import load_bundesliga_data
            clear_patterns()
            from patterns.bundesliga_patterns import register_bundesliga_patterns
            register_bundesliga_patterns()
            
            predictor = SimpleBundesligaPredictor()
            data = load_bundesliga_data()
            matches = data[data['Date'].dt.date == target_date.date()]
            
            for _, match in matches.iterrows():
                pred = predictor.predict_match(
                    match['HomeTeam'],
                    match['AwayTeam'],
                    data[data['Date'] < match['Date']],
                    match['Date']
                )
                if pred:
                    all_predictions.append({
                        'league': 'Bundesliga',
                        'date': target_date.strftime('%Y-%m-%d'),
                        'home_team': match['HomeTeam'],
                        'away_team': match['AwayTeam'],
                        'pattern': pred.pattern_name,
                        'confidence': pred.confidence,
                        'risk_adjusted_confidence': pred.risk_adjusted_confidence,
                        'threshold': pred.threshold,
                        'prediction_time': datetime.now().isoformat(),
                        'result': None,
                        'actual_outcome': None
                    })
                    print(f"  ✅ {match['HomeTeam']} vs {match['AwayTeam']}: "
                          f"{pred.pattern_name} ({pred.risk_adjusted_confidence:.1%})")
        except Exception as e:
            print(f"  ⚠️ Error: {e}")
        
        # Add similar blocks for La Liga, Premier League, Romania...
        
        # Save all predictions
        self.predictions.extend(all_predictions)
        self._save_predictions()
        
        print(f"\n✅ Saved {len(all_predictions)} predictions")
        print(f"📊 Total predictions in database: {len(self.predictions)}")
    
    def update_results(self, match_date: datetime):
        """
        Update predictions with actual results after matches complete.
        
        Args:
            match_date: Date of matches to update
        """
        print(f"\n📝 Updating results for {match_date.strftime('%Y-%m-%d')}")
        print("="*80)
        
        updated = 0
        date_str = match_date.strftime('%Y-%m-%d')
        
        for pred in self.predictions:
            if pred['date'] == date_str and pred['result'] is None:
                # Load actual match data
                # TODO: Implement actual result lookup from data files
                print(f"  ⚠️ Manual update required for: {pred['home_team']} vs {pred['away_team']}")
                # For now, mark as needing manual update
                pred['needs_manual_update'] = True
                updated += 1
        
        self._save_predictions()
        print(f"\n✅ Marked {updated} predictions for manual update")
        print("💡 Tip: Edit paper_trading.json to add 'result': true/false and 'actual_outcome': '...'")
    
    def generate_report(self, days: int = 30):
        """
        Generate performance report for paper trading.
        
        Args:
            days: Number of days to include in report
        """
        cutoff = datetime.now() - timedelta(days=days)
        recent = [p for p in self.predictions 
                  if datetime.fromisoformat(p['prediction_time']) >= cutoff]
        
        completed = [p for p in recent if p['result'] is not None]
        pending = [p for p in recent if p['result'] is None]
        
        print(f"\n📊 Paper Trading Report (Last {days} Days)")
        print("="*80)
        
        print(f"\n📈 Overall Statistics:")
        print(f"  Total Predictions: {len(recent)}")
        print(f"  Completed: {len(completed)}")
        print(f"  Pending: {len(pending)}")
        
        if completed:
            wins = sum(1 for p in completed if p['result'])
            wr = wins / len(completed) * 100
            print(f"\n🎯 Performance:")
            print(f"  Win Rate: {wr:.1f}% ({wins}/{len(completed)})")
            print(f"  Target: 75%+ (to proceed to real money)")
            
            if wr >= 75:
                print(f"  ✅ PASSING - Consider micro-stakes testing")
            elif wr >= 70:
                print(f"  ⚠️ MARGINAL - Continue paper trading")
            else:
                print(f"  ❌ FAILING - System needs improvement")
            
            # By league
            print(f"\n🌍 By League:")
            leagues = set(p['league'] for p in completed)
            for league in sorted(leagues):
                league_preds = [p for p in completed if p['league'] == league]
                league_wins = sum(1 for p in league_preds if p['result'])
                league_wr = league_wins / len(league_preds) * 100
                print(f"  {league:20s}: {league_wr:5.1f}% ({league_wins}/{len(league_preds)})")
            
            # By pattern
            print(f"\n🎲 By Pattern:")
            patterns = {}
            for p in completed:
                pattern = p['pattern']
                if pattern not in patterns:
                    patterns[pattern] = {'total': 0, 'wins': 0}
                patterns[pattern]['total'] += 1
                if p['result']:
                    patterns[pattern]['wins'] += 1
            
            for pattern, stats in sorted(patterns.items(), 
                                        key=lambda x: x[1]['wins']/x[1]['total'], 
                                        reverse=True)[:10]:
                wr = stats['wins'] / stats['total'] * 100
                print(f"  {pattern:30s}: {wr:5.1f}% ({stats['wins']}/{stats['total']})")
        
        print(f"\n💡 Next Steps:")
        if len(completed) < 30:
            print(f"  → Continue paper trading (need {30-len(completed)} more completed predictions)")
        elif completed and wins / len(completed) >= 0.75:
            print(f"  → ✅ Ready for micro-stakes (€1-2 per bet)")
        elif completed and wins / len(completed) >= 0.70:
            print(f"  → ⚠️ Continue paper trading (marginal performance)")
        else:
            print(f"  → ❌ Review strategy (underperforming)")


def main():
    parser = argparse.ArgumentParser(description='Paper Trading Tracker')
    parser.add_argument('action', choices=['generate', 'update', 'report'],
                       help='Action to perform')
    parser.add_argument('--date', type=str,
                       help='Date (YYYY-MM-DD) for generate/update')
    parser.add_argument('--days', type=int, default=30,
                       help='Days to include in report')
    
    args = parser.parse_args()
    
    tracker = PaperTradingTracker()
    
    if args.action == 'generate':
        date = datetime.strptime(args.date, '%Y-%m-%d') if args.date else None
        tracker.generate_predictions(date)
    
    elif args.action == 'update':
        if not args.date:
            print("Error: --date required for update")
            return
        date = datetime.strptime(args.date, '%Y-%m-%d')
        tracker.update_results(date)
    
    elif args.action == 'report':
        tracker.generate_report(args.days)


if __name__ == '__main__':
    main()
