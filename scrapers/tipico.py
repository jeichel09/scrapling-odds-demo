"""
Tipico Scraper
Scrapes odds from Tipico (Austria/Germany)
"""

from typing import List
from scrapling.fetchers import StealthyFetcher
from scrapers.base import BaseBookmakerScraper
from models.odds import OddsData
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class TipicoScraper(BaseBookmakerScraper):
    """
    Scraper for Tipico bookmaker
    Target: Austrian Bundesliga and major European leagues
    """
    
    def __init__(self):
        super().__init__(
            name="Tipico",
            base_url="https://www.tipico.at",
            country="AT"
        )
    
    async def get_match_urls(self) -> List[str]:
        """
        Get match URLs from Tipico football page
        Returns list of match URLs
        """
        try:
            # Tipico main football page
            main_url = f"{self.base_url}/de/online-sportwetten/fussball"
            
            logger.info(f"[{self.name}] Fetching main page: {main_url}")
            
            page = await StealthyFetcher.fetch(
                main_url,
                solve_cloudflare=True,  # Bypass Cloudflare if present
                network_idle=True
            )
            
            # Tipico uses data attributes and classes for match links
            # Look for match links - these selectors are examples
            # You'll need to inspect the actual site to get exact selectors
            
            # Try different possible selectors
            selectors = [
                'a[href*="/de/online-sportwetten/fussball/"]',
                '.EventSelectionLink',
                '[data-testid="event-link"]',
                '.event-title a'
            ]
            
            urls = []
            for selector in selectors:
                links = page.css(f'{selector}::attr(href)').getall()
                if links:
                    for link in links:
                        if '/fussball/' in link and '/live/' not in link:
                            full_url = link if link.startswith('http') else f"{self.base_url}{link}"
                            urls.append(full_url)
                    if urls:
                        break
            
            # Remove duplicates while preserving order
            seen = set()
            unique_urls = []
            for url in urls:
                if url not in seen:
                    seen.add(url)
                    unique_urls.append(url)
            
            logger.info(f"[{self.name}] Found {len(unique_urls)} match URLs")
            return unique_urls[:15]  # Limit to 15 matches
            
        except Exception as e:
            logger.error(f"[{self.name}] Error getting match URLs: {e}")
            return []
    
    def parse_odds(self, page, url: str) -> OddsData:
        """
        Parse odds from a Tipico match page
        """
        try:
            # Extract team names
            # Tipico typically uses these selectors
            team_selectors = [
                '.EventHeaderTitle',
                '[data-testid="event-title"]',
                '.event-participant',
                '.team-name'
            ]
            
            teams = []
            for selector in team_selectors:
                teams = page.css(f'{selector}::text').getall()
                if len(teams) >= 2:
                    break
            
            if len(teams) < 2:
                logger.warning(f"[{self.name}] Could not find team names")
                return None
            
            home_team = teams[0].strip()
            away_team = teams[1].strip()
            match_name = f"{home_team} vs {away_team}"
            
            # Extract league if available
            league = page.css('.BreadcrumbItem::text').get() or "Unknown"
            
            # Extract odds
            # Tipico typically displays 1X2 odds in order: Home, Draw, Away
            odds_selectors = [
                '.OddsButton .OddsValue',
                '[data-testid="odd-value"]',
                '.odd-button .value',
                '.selection-odd'
            ]
            
            odds_values = []
            for selector in odds_selectors:
                odds_values = page.css(f'{selector}::text').getall()
                if len(odds_values) >= 2:
                    break
            
            if len(odds_values) < 2:
                logger.warning(f"[{self.name}] Could not find odds values")
                return None
            
            # Parse odds (assume 1X2 format)
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
