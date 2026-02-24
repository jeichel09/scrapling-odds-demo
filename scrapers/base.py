from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Optional
from datetime import datetime
import asyncio
import random
import logging

from scrapling.fetchers import StealthyFetcher, StealthySession
from models.odds import OddsData

logger = logging.getLogger(__name__)


class BaseBookmakerScraper(ABC):
    """Base class for all bookmaker scrapers"""
    
    def __init__(self, name: str, base_url: str, country: str = "EU"):
        self.name = name
        self.base_url = base_url
        self.country = country
        self.session = None
        self._init_session()
    
    def _init_session(self):
        """Initialize Scrapling session with stealth settings"""
        try:
            self.session = StealthySession(
                headless=True,  # Run browser in headless mode
                human_like_delays=True,  # Add random delays
            )
            logger.info(f"Initialized session for {self.name}")
        except Exception as e:
            logger.error(f"Failed to initialize session for {self.name}: {e}")
            self.session = None
    
    @abstractmethod
    async def get_match_urls(self) -> List[str]:
        """
        Get list of match URLs to scrape
        Should return list of full URLs
        """
        pass
    
    @abstractmethod
    def parse_odds(self, page, url: str) -> Optional[OddsData]:
        """
        Extract odds from a page
        Returns OddsData object or None if parsing fails
        """
        pass
    
    async def scrape_match(self, url: str) -> Optional[OddsData]:
        """
        Scrape a single match
        Includes retry logic and error handling
        """
        max_retries = 3
        
        for attempt in range(max_retries):
            try:
                logger.info(f"[{self.name}] Scraping: {url} (attempt {attempt + 1})")
                
                # Fetch page with network idle wait
                page = await self.session.fetch(url, network_idle=True)
                
                # Random delay to look human
                await asyncio.sleep(random.uniform(2, 4))
                
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
                    wait_time = (attempt + 1) * 5  # Exponential backoff
                    logger.info(f"[{self.name}] Retrying in {wait_time}s...")
                    await asyncio.sleep(wait_time)
                else:
                    logger.error(f"[{self.name}] Max retries exceeded for {url}")
                    return None
        
        return None
    
    async def scrape_all(self, max_matches: int = 10) -> List[OddsData]:
        """
        Scrape all matches from this bookmaker
        
        Args:
            max_matches: Maximum number of matches to scrape (default 10)
        
        Returns:
            List of OddsData objects
        """
        results = []
        
        try:
            # Get match URLs
            urls = await self.get_match_urls()
            logger.info(f"[{self.name}] Found {len(urls)} matches")
            
            # Limit to max_matches
            urls = urls[:max_matches]
            
            # Scrape each match
            for url in urls:
                odds = await self.scrape_match(url)
                
                if odds:
                    results.append(odds)
                
                # Be nice - add delay between requests
                await asyncio.sleep(random.uniform(3, 6))
            
            logger.info(f"[{self.name}] Successfully scraped {len(results)}/{len(urls)} matches")
            
        except Exception as e:
            logger.error(f"[{self.name}] Error in scrape_all: {e}")
        
        return results
    
    def normalize_odds(self, odds_text: str) -> float:
        """
        Convert various odds formats to decimal
        
        Supports:
        - Decimal: "2.50" -> 2.50
        - European: "2,60" -> 2.60 (comma as decimal separator)
        - Fractional: "5/2" -> 3.50
        - American: "+150" -> 2.50, "-200" -> 1.50
        """
        if not odds_text:
            return 0.0
        
        odds_text = str(odds_text).strip()
        
        # Handle European format (comma as decimal separator)
        # e.g., "2,60" -> "2.60"
        odds_text = odds_text.replace(',', '.')
        
        try:
            # Fractional format (e.g., "5/2")
            if '/' in odds_text:
                num, den = odds_text.split('/')
                return (float(num) / float(den)) + 1
            
            # American format (e.g., "+150" or "-200")
            if odds_text.startswith('+'):
                return (float(odds_text[1:]) / 100) + 1
            elif odds_text.startswith('-'):
                return (100 / float(odds_text[1:])) + 1
            
            # Decimal format (e.g., "2.50")
            return float(odds_text)
            
        except (ValueError, ZeroDivisionError) as e:
            logger.warning(f"Failed to parse odds: {odds_text} - {e}")
            return 0.0
    
    def __del__(self):
        """Cleanup session on deletion"""
        if self.session:
            try:
                asyncio.create_task(self.session.close())
            except:
                pass
