"""
Tipico Scraper
Scrapes odds from Tipico (Austria/Germany) using actual site selectors
"""

import asyncio
from typing import List, Optional
from scrapling.fetchers import StealthyFetcher
from scrapers.base import BaseBookmakerScraper
from models.odds import OddsData
from datetime import datetime
import logging
import re

logger = logging.getLogger(__name__)


class TipicoScraper(BaseBookmakerScraper):
    """
    Scraper for Tipico bookmaker
    Now using real selectors from site investigation
    """
    
    def __init__(self):
        super().__init__(
            name="Tipico",
            base_url="https://sports.tipico.at",
            country="AT"
        )
        
        # League URLs based on your investigation
        self.league_urls = {
            "Austrian Bundesliga": "/de/alle/fussball/oesterreich/bundesliga",
            "Austrian 2. Liga": "/de/alle/fussball/oesterreich/2-liga",
        }
    
    async def get_match_urls(self) -> List[str]:
        """
        Get match URLs from Tipico league pages
        Uses the EventRow container selector you found
        """
        all_match_urls = []
        
        for league_name, league_path in self.league_urls.items():
            try:
                league_url = f"{self.base_url}{league_path}"
                logger.info(f"[{self.name}] Scraping {league_name}: {league_url}")
                
                # Fetch league page - run sync fetcher in separate thread
                # This avoids "Sync API inside asyncio loop" error
                page = await asyncio.to_thread(
                    StealthyFetcher.fetch,
                    league_url,
                    solve_cloudflare=True,
                    network_idle=True
                )
                
                # Use the selector you found: class="EventRow-styles-module-event-row"
                # The <a> tag contains the href to the match
                match_links = page.css('a.EventRow-styles-module-event-row::attr(href)').getall()
                
                # Alternative selectors if the above doesn't work
                if not match_links:
                    alternative_selectors = [
                        '[data-gtmid="eventRowContainer"]::attr(href)',
                        'a[href*="/event/"]::attr(href)',
                        'a[aria-label*="event"]::attr(href)',
                    ]
                    
                    for selector in alternative_selectors:
                        match_links = page.css(selector).getall()
                        if match_links:
                            logger.info(f"[{self.name}] Found links using: {selector}")
                            break
                
                if not match_links:
                    logger.warning(f"[{self.name}] No match links found for {league_name}")
                    continue
                
                # Process URLs
                for link in match_links:
                    # Ensure full URL
                    if link.startswith('/'):
                        full_url = f"{self.base_url}{link}"
                    elif link.startswith('http'):
                        full_url = link
                    else:
                        continue
                    
                    # Only include URLs with /event/
                    if '/event/' in full_url:
                        all_match_urls.append({
                            'url': full_url,
                            'league': league_name
                        })
                
                logger.info(f"[{self.name}] Found {len(match_links)} matches in {league_name}")
                
            except Exception as e:
                logger.error(f"[{self.name}] Error scraping {league_name}: {e}")
        
        # Remove duplicates while preserving order
        seen = set()
        unique_urls = []
        for item in all_match_urls:
            if item['url'] not in seen:
                seen.add(item['url'])
                unique_urls.append(item)
        
        logger.info(f"[{self.name}] Total unique matches: {len(unique_urls)}")
        return unique_urls[:15]  # Limit to 15 matches
    
    async def scrape_match(self, url: str) -> Optional[OddsData]:
        """
        Override scrape_match to use StealthyFetcher with asyncio.to_thread
        """
        max_retries = 3
        
        for attempt in range(max_retries):
            try:
                logger.info(f"[{self.name}] Scraping: {url} (attempt {attempt + 1})")
                
                # Fetch page using StealthyFetcher in thread
                page = await asyncio.to_thread(
                    StealthyFetcher.fetch,
                    url,
                    network_idle=True
                )
                
                if not page:
                    logger.warning(f"[{self.name}] Failed to fetch page: {url}")
                    return None
                
                # Parse odds
                odds = self.parse_odds(page, url)
                
                if odds:
                    logger.info(f"[{self.name}] Successfully scraped: {odds.match_name}")
                    return odds
                else:
                    logger.warning(f"[{self.name}] Failed to parse odds from {url}")
                    return None
                    
            except Exception as e:
                logger.error(f"[{self.name}] Error scraping {url}: {e}")
                
                if attempt < max_retries - 1:
                    wait_time = (attempt + 1) * 5
                    logger.info(f"[{self.name}] Retrying in {wait_time}s...")
                    await asyncio.sleep(wait_time)
                else:
                    logger.error(f"[{self.name}] Max retries exceeded for {url}")
                    return None
        
        return None
    
    def parse_odds(self, page, url: str) -> Optional[OddsData]:
        """
        Parse odds from a Tipico match page
        """
        # Extract league from URL
        league = "Unknown"
        if 'bundesliga' in url.lower():
            league = "Austrian Bundesliga"
        elif '2-liga' in url.lower():
            league = "Austrian 2. Liga"
        
        try:
            if not page:
                logger.warning(f"[{self.name}] No page provided for {url}")
                return None
            
            # Extract team names from aria-label or page content
            team_names = self._extract_team_names(page)
            
            if not team_names:
                logger.warning(f"[{self.name}] Could not extract team names from {url}")
                return None
            
            home_team, away_team = team_names
            match_name = f"{home_team} vs {away_team}"
            
            # Extract odds using the selector pattern from your sheet
            # Pattern: .OddResult-styles-module-value-cell span
            odds_selectors = [
                '.OddResult-styles-module-value-cell span::text',
                '[class*="OddResult"] span::text',
                'button[class*="odd"] span[class*="value"]::text',
                '.odd-button .odd-value::text',
            ]
            
            odds_values = []
            for selector in odds_selectors:
                raw_values = page.css(selector).getall()
                # Filter valid odds (numeric, reasonable range)
                odds_values = [v.strip() for v in raw_values if self._is_valid_odd_value(v)]
                if len(odds_values) >= 3:
                    logger.debug(f"[{self.name}] Found odds with selector: {selector}")
                    break
            
            if len(odds_values) < 3:
                logger.warning(f"[{self.name}] Insufficient odds values ({len(odds_values)}) from {url}")
                return None
            
            # First 3 values are typically 1X2 (Home, Draw, Away)
            home_odds = self.normalize_odds(odds_values[0])
            draw_odds = self.normalize_odds(odds_values[1])
            away_odds = self.normalize_odds(odds_values[2])
            
            # Validate odds
            if home_odds < 1.01 or away_odds < 1.01:
                logger.warning(f"[{self.name}] Invalid odds: home={home_odds}, away={away_odds}")
                return None
            
            logger.info(f"[{self.name}] Parsed: {match_name} | {home_odds} / {draw_odds} / {away_odds}")
            
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
            logger.error(f"[{self.name}] Error parsing odds from {url}: {e}", exc_info=True)
            return None
    
    def _extract_team_names(self, page) -> Optional[tuple]:
        """
        Extract home and away team names from the match page
        Tries multiple methods
        """
        # Method 1: From page title (usually "Team A vs Team B - Tipico")
        title = page.css('title::text').get()
        if title and 'vs' in title.lower():
            parts = title.lower().split('vs')
            if len(parts) >= 2:
                # Clean up - remove " - Tipico" or similar
                home = parts[0].strip().title()
                away = parts[1].split('-')[0].strip().title()
                return (home, away)
        
        # Method 2: From team name containers
        team_selectors = [
            '.SoccerPreLive-styles-module-team div::text',
            '[class*="team"]:not([class*="team-right"]) div::text',
            '.home-team::text',
            '.event-team:first-child::text',
        ]
        
        for selector in team_selectors:
            elements = page.css(selector).getall()
            elements = [e.strip() for e in elements if e.strip()]
            if len(elements) >= 2:
                return (elements[0], elements[1])
        
        # Method 3: From aria-label on the page
        aria_label = page.css('[aria-label*="vs"]::attr(aria-label)').get()
        if aria_label and 'vs' in aria_label.lower():
            # Format: "Team A vs Team B event"
            match = re.search(r'(.+?)\s+vs\s+(.+?)\s+event', aria_label, re.IGNORECASE)
            if match:
                return (match.group(1).strip(), match.group(2).strip())
        
        return None
    
    def _is_valid_odd_value(self, value: str) -> bool:
        """Check if a string is a valid decimal odd value"""
        if not value:
            return False
        try:
            # Clean the value
            cleaned = value.strip().replace(',', '.')
            val = float(cleaned)
            # Valid odds are typically between 1.01 and 500
            return 1.01 <= val <= 500
        except (ValueError, TypeError):
            return False
    
    async def scrape_all(self, max_matches: int = 10) -> List[OddsData]:
        """
        Override scrape_all to handle the match_data dict structure
        """
        results = []
        
        try:
            # Get match URLs with league info
            matches_data = await self.get_match_urls()
            logger.info(f"[{self.name}] Found {len(matches_data)} total matches")
            
            # Limit matches
            matches_data = matches_data[:max_matches]
            
            # Scrape each match
            for match_data in matches_data:
                odds = await self.scrape_match(match_data['url'])
                
                if odds:
                    results.append(odds)
                
                # Be nice - add delay between requests
                await asyncio.sleep(random.uniform(3, 6))
            
            logger.info(f"[{self.name}] Successfully scraped {len(results)}/{len(matches_data)} matches")
            
        except Exception as e:
            logger.error(f"[{self.name}] Error in scrape_all: {e}")
        
        return results
