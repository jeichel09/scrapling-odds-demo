"""
Rabona Scraper
Scrapes odds from Rabona (Crypto sportsbook)
"""

from typing import List
from scrapling.fetchers import StealthyFetcher
from scrapers.base import BaseBookmakerScraper
from models.odds import OddsData
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class RabonaScraper(BaseBookmakerScraper):
    """
    Scraper for Rabona crypto sportsbook
    Target: Major European football leagues
    """
    
    def __init__(self):
        super().__init__(
            name="Rabona",
            base_url="https://rabona.com",
            country="Crypto"
        )
    
    async def get_match_urls(self) -> List[str]:
        """
        Get match URLs from Rabona football/sports page
        """
        try:
            # Rabona sports page
            main_url = f"{self.base_url}/en/sports/football"
            
            logger.info(f"[{self.name}] Fetching main page: {main_url}")
            
            page = await StealthyFetcher.fetch(
                main_url,
                solve_cloudflare=True,
                network_idle=True
            )
            
            # Rabona selectors (crypto sites often use different patterns)
            selectors = [
                'a[href*="/sports/event/"]',
                '.event-link',
                '[data-testid="match-link"]',
                '.match-row a'
            ]
            
            urls = []
            for selector in selectors:
                links = page.css(f'{selector}::attr(href)').getall()
                if links:
                    for link in links:
                        if '/event/' in link or '/match/' in link:
                            full_url = link if link.startswith('http') else f"{self.base_url}{link}"
                            urls.append(full_url)
                    if urls:
                        break
            
            # Alternative: Try to find match IDs and construct URLs
            if not urls:
                match_ids = page.css('[data-match-id]::attr(data-match-id)').getall()
                for match_id in match_ids[:15]:
                    urls.append(f"{self.base_url}/en/sports/event/{match_id}")
            
            # Remove duplicates
            seen = set()
            unique_urls = []
            for url in urls:
                if url not in seen:
                    seen.add(url)
                    unique_urls.append(url)
            
            logger.info(f"[{self.name}] Found {len(unique_urls)} match URLs")
            return unique_urls[:15]
            
        except Exception as e:
            logger.error(f"[{self.name}] Error getting match URLs: {e}")
            return []
    
    def parse_odds(self, page, url: str) -> OddsData:
        """
        Parse odds from a Rabona match page
        """
        try:
            # Extract team names
            team_selectors = [
                '.event-teams .team-name',
                '.match-teams .team',
                '[data-testid="team-name"]',
                '.participant-name'
            ]
            
            teams = []
            for selector in team_selectors:
                teams = page.css(f'{selector}::text').getall()
                if len(teams) >= 2:
                    break
            
            if len(teams) < 2:
                # Try alternative: look for team names in title
                title = page.css('title::text').get()
                if title and 'vs' in title:
                    teams = title.split('vs')[:2]
            
            if len(teams) < 2:
                logger.warning(f"[{self.name}] Could not find team names")
                return None
            
            home_team = teams[0].strip()
            away_team = teams[1].strip()
            match_name = f"{home_team} vs {away_team}"
            
            # Extract league
            league = page.css('.sport-league::text').get() or "Unknown"
            
            # Extract odds
            odds_selectors = [
                '.odd-value',
                '.market-odds .value',
                '[data-testid="odd-button"]',
                '.selection-odd-value'
            ]
            
            odds_values = []
            for selector in odds_selectors:
                odds_values = page.css(f'{selector}::text').getall()
                if len(odds_values) >= 2:
                    break
            
            if len(odds_values) < 2:
                logger.warning(f"[{self.name}] Could not find odds values")
                return None
            
            # Parse odds
            home_odds = self.normalize_odds(odds_values[0])
            draw_odds = self.normalize_odds(odds_values[1]) if len(odds_values) > 2 else None
            away_odds = self.normalize_odds(odds_values[-1])
            
            if home_odds == 0.0 or away_odds == 0.0:
                logger.warning(f"[{self.name}] Invalid odds values")
                return None
            
            return OddsData(
                bookmaker=self.name,
                match_name=match_name,
                home_team=home_team,
                away_team=away_team,
                home_odds=home_odds,
                draw_odds=draw_odds,
                away_odds=away_odds,
                timestamp=datetime.now().isoformat(),
                url=url,
                league=league
            )
            
        except Exception as e:
            logger.error(f"[{self.name}] Error parsing odds from {url}: {e}")
            return None
