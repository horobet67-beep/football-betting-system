"""
Odds Scraper for Football Matches
Scrapes odds from multiple betting sites for upcoming matches.

Supported sources:
- Odds API (odds-api.com) - Requires API key but has free tier
- Manual scraping from public sites (as fallback)

Usage:
    python3 odds_scraper.py --league "Premier League" --days 7
    python3 odds_scraper.py --all-leagues --output odds_data.json
"""

import requests
import json
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import time
import sys
import argparse


class OddsScraper:
    """Scrape odds from various sources"""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize scraper.
        
        Args:
            api_key: Optional API key for odds-api.com
        """
        self.api_key = api_key
        self.base_url = "https://api.the-odds-api.com/v4"
        
        # Sport keys mapping
        self.sport_keys = {
            'soccer_epl': 'Premier League',
            'soccer_italy_serie_a': 'Serie A',
            'soccer_germany_bundesliga': 'Bundesliga',
            'soccer_spain_la_liga': 'La Liga',
            'soccer_romania_divizia_a': 'Romania Liga 1'
        }
        
    def get_sports(self) -> List[Dict]:
        """Get list of available sports from API"""
        if not self.api_key:
            print("⚠️  No API key provided. Get free key at: https://the-odds-api.com/")
            return []
        
        url = f"{self.base_url}/sports"
        params = {'apiKey': self.api_key}
        
        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"❌ Error fetching sports: {e}")
            return []
    
    def get_odds(self, sport_key: str, markets: List[str] = None, regions: str = 'eu') -> List[Dict]:
        """
        Get odds for a specific sport.
        
        Args:
            sport_key: Sport identifier (e.g., 'soccer_epl')
            markets: List of markets (e.g., ['h2h', 'totals', 'spreads'])
            regions: Regions to get odds from ('eu', 'us', 'uk', 'au')
            
        Returns:
            List of matches with odds
        """
        if not self.api_key:
            print("⚠️  No API key provided")
            return []
        
        url = f"{self.base_url}/sports/{sport_key}/odds"
        
        if markets is None:
            markets = ['h2h', 'totals']  # Head-to-head and totals (over/under)
        
        params = {
            'apiKey': self.api_key,
            'regions': regions,
            'markets': ','.join(markets),
            'oddsFormat': 'decimal',
            'dateFormat': 'iso'
        }
        
        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            # Check remaining requests
            remaining = response.headers.get('x-requests-remaining')
            used = response.headers.get('x-requests-used')
            
            if remaining:
                print(f"   📊 API Usage: {used} used, {remaining} remaining")
            
            return response.json()
        except Exception as e:
            print(f"❌ Error fetching odds for {sport_key}: {e}")
            return []
    
    def scrape_all_leagues(self, days_ahead: int = 7) -> Dict[str, List[Dict]]:
        """
        Scrape odds for all supported leagues.
        
        Args:
            days_ahead: Number of days ahead to get matches for
            
        Returns:
            Dictionary of league -> matches with odds
        """
        if not self.api_key:
            print("❌ API key required. Get free key at: https://the-odds-api.com/")
            print("   Free tier: 500 requests/month")
            return {}
        
        results = {}
        
        print(f"\n🔍 Scraping odds for next {days_ahead} days...")
        print("="*100)
        
        for sport_key, league_name in self.sport_keys.items():
            print(f"\n📥 {league_name} ({sport_key})...")
            
            odds_data = self.get_odds(sport_key, markets=['h2h', 'totals', 'spreads'])
            
            if odds_data:
                # Filter by date range
                cutoff_date = datetime.now() + timedelta(days=days_ahead)
                filtered = []
                
                for match in odds_data:
                    match_date = datetime.fromisoformat(match['commence_time'].replace('Z', '+00:00'))
                    if match_date <= cutoff_date:
                        filtered.append(match)
                
                results[league_name] = filtered
                print(f"   ✅ Found {len(filtered)} matches")
            else:
                print(f"   ⚠️  No odds data")
            
            # Rate limiting - be nice to the API
            time.sleep(1)
        
        return results
    
    def extract_key_odds(self, match: Dict) -> Dict:
        """
        Extract key odds from match data.
        
        Args:
            match: Match data from API
            
        Returns:
            Simplified odds dictionary
        """
        result = {
            'home_team': match['home_team'],
            'away_team': match['away_team'],
            'commence_time': match['commence_time'],
            'bookmakers': []
        }
        
        # Extract odds from each bookmaker
        for bookmaker in match.get('bookmakers', []):
            book_data = {
                'name': bookmaker['title'],
                'markets': {}
            }
            
            for market in bookmaker.get('markets', []):
                market_key = market['key']
                
                if market_key == 'h2h':
                    # Match winner odds
                    book_data['markets']['match_winner'] = {
                        outcome['name']: outcome['price']
                        for outcome in market['outcomes']
                    }
                elif market_key == 'totals':
                    # Over/Under goals
                    for outcome in market['outcomes']:
                        key = f"{outcome['name']}_{outcome['point']}"
                        book_data['markets'][key] = outcome['price']
                elif market_key == 'spreads':
                    # Handicap
                    for outcome in market['outcomes']:
                        key = f"handicap_{outcome['name']}_{outcome['point']}"
                        book_data['markets'][key] = outcome['price']
            
            result['bookmakers'].append(book_data)
        
        return result
    
    def find_best_odds(self, match: Dict, market: str) -> Dict:
        """
        Find best odds across all bookmakers for a specific market.
        
        Args:
            match: Match data
            market: Market to find best odds for
            
        Returns:
            Best odds dictionary
        """
        best_odds = {}
        
        for bookmaker in match.get('bookmakers', []):
            for mkt in bookmaker.get('markets', []):
                if mkt['key'] == market:
                    for outcome in mkt['outcomes']:
                        name = outcome['name']
                        price = outcome['price']
                        
                        if name not in best_odds or price > best_odds[name]['price']:
                            best_odds[name] = {
                                'price': price,
                                'bookmaker': bookmaker['title']
                            }
        
        return best_odds
    
    def calculate_implied_probability(self, odds: float) -> float:
        """
        Calculate implied probability from decimal odds.
        
        Args:
            odds: Decimal odds
            
        Returns:
            Implied probability (0-1)
        """
        return 1 / odds if odds > 0 else 0
    
    def format_odds_report(self, all_odds: Dict[str, List[Dict]]) -> str:
        """
        Format odds data into readable report.
        
        Args:
            all_odds: Dictionary of league -> matches
            
        Returns:
            Formatted string report
        """
        report = []
        report.append("="*100)
        report.append("⚽ FOOTBALL BETTING ODDS")
        report.append("="*100)
        report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")
        
        for league, matches in all_odds.items():
            if not matches:
                continue
            
            report.append(f"\n{'='*100}")
            report.append(f"🏆 {league}")
            report.append("="*100)
            report.append(f"Matches: {len(matches)}")
            report.append("")
            
            for i, match in enumerate(matches, 1):
                match_date = datetime.fromisoformat(match['commence_time'].replace('Z', '+00:00'))
                
                report.append(f"{i}. {match['home_team']} vs {match['away_team']}")
                report.append(f"   📅 {match_date.strftime('%Y-%m-%d %H:%M')}")
                
                # Best H2H odds
                best_h2h = self.find_best_odds(match, 'h2h')
                if best_h2h:
                    report.append(f"   💰 Match Winner (Best Odds):")
                    for team, data in best_h2h.items():
                        prob = self.calculate_implied_probability(data['price'])
                        report.append(f"      {team}: {data['price']:.2f} ({prob:.1%}) - {data['bookmaker']}")
                
                # Best totals odds
                best_totals = self.find_best_odds(match, 'totals')
                if best_totals:
                    report.append(f"   ⚽ Over/Under Goals (Best Odds):")
                    for outcome, data in best_totals.items():
                        prob = self.calculate_implied_probability(data['price'])
                        report.append(f"      {outcome}: {data['price']:.2f} ({prob:.1%}) - {data['bookmaker']}")
                
                report.append("")
        
        return "\n".join(report)


def manual_scraping_example():
    """
    Example of manual scraping without API (for reference).
    Note: Most betting sites block scrapers - use API instead.
    """
    print("⚠️  Manual scraping tips:")
    print("1. Most betting sites use JavaScript rendering - need Selenium")
    print("2. Many sites block automated access (bot detection)")
    print("3. Terms of Service usually prohibit scraping")
    print("4. Use official APIs when available")
    print("\nRecommended: Use The Odds API (free tier: 500 requests/month)")
    print("Sign up: https://the-odds-api.com/")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Scrape football betting odds')
    parser.add_argument('--api-key', type=str, help='Odds API key (get free at odds-api.com)')
    parser.add_argument('--league', type=str, help='Specific league to scrape')
    parser.add_argument('--all-leagues', action='store_true', help='Scrape all supported leagues')
    parser.add_argument('--days', type=int, default=7, help='Days ahead to scrape (default: 7)')
    parser.add_argument('--output', type=str, help='Output file (JSON format)')
    parser.add_argument('--demo', action='store_true', help='Show demo/setup instructions')
    
    args = parser.parse_args()
    
    if args.demo:
        print("\n" + "="*100)
        print("🎯 ODDS SCRAPER SETUP")
        print("="*100)
        print("\n1. Get Free API Key:")
        print("   - Visit: https://the-odds-api.com/")
        print("   - Sign up for free account")
        print("   - Free tier: 500 requests/month")
        print("   - Supports 90+ sports including football")
        
        print("\n2. Usage Examples:")
        print("   # Scrape all leagues")
        print("   python3 odds_scraper.py --api-key YOUR_KEY --all-leagues")
        print("")
        print("   # Scrape specific league")
        print("   python3 odds_scraper.py --api-key YOUR_KEY --league 'Premier League'")
        print("")
        print("   # Save to JSON file")
        print("   python3 odds_scraper.py --api-key YOUR_KEY --all-leagues --output odds.json")
        print("")
        print("   # Get next 14 days")
        print("   python3 odds_scraper.py --api-key YOUR_KEY --all-leagues --days 14")
        
        print("\n3. Supported Markets:")
        print("   - Match Winner (H2H)")
        print("   - Over/Under Goals (Totals)")
        print("   - Asian Handicap (Spreads)")
        
        print("\n4. Alternative Sources:")
        print("   - Oddsportal.com (requires manual extraction)")
        print("   - Betfair API (requires account)")
        print("   - Smarkets API (requires account)")
        
        print("\n" + "="*100)
        return
    
    if not args.api_key:
        print("❌ API key required!")
        print("\nGet free API key: https://the-odds-api.com/")
        print("Then run: python3 odds_scraper.py --api-key YOUR_KEY --all-leagues")
        print("\nOr run: python3 odds_scraper.py --demo for setup instructions")
        sys.exit(1)
    
    # Initialize scraper
    scraper = OddsScraper(api_key=args.api_key)
    
    # Scrape odds
    if args.all_leagues:
        odds_data = scraper.scrape_all_leagues(days_ahead=args.days)
    else:
        print("❌ Please specify --all-leagues or --league")
        sys.exit(1)
    
    # Generate report
    if odds_data:
        report = scraper.format_odds_report(odds_data)
        print(report)
        
        # Save to file if requested
        if args.output:
            # Save JSON
            with open(args.output, 'w', encoding='utf-8') as f:
                json.dump(odds_data, f, indent=2, ensure_ascii=False)
            print(f"\n💾 Saved to: {args.output}")
            
            # Also save readable report
            report_file = args.output.replace('.json', '_report.txt')
            with open(report_file, 'w', encoding='utf-8') as f:
                f.write(report)
            print(f"📄 Report saved to: {report_file}")
    else:
        print("\n⚠️  No odds data retrieved")


if __name__ == '__main__':
    main()
