#!/usr/bin/env python3
"""
Main script for Scrapling Odds Demo
Scrapes odds from Tipico and Rabona
"""

import asyncio
import logging
import sys
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('scraper.log')
    ]
)
logger = logging.getLogger(__name__)

# Import scrapers
from scrapers.tipico import TipicoScraper
from scrapers.rabona import RabonaScraper
from storage.database import OddsDatabase


async def scrape_bookmaker(scraper, db):
    """Scrape a single bookmaker and save to database"""
    try:
        logger.info(f"\n{'='*60}")
        logger.info(f"Starting scraper: {scraper.name}")
        logger.info(f"{'='*60}\n")
        
        # Scrape odds
        odds = await scraper.scrape_all(max_matches=10)
        
        if odds:
            # Save to database
            db.save_odds(odds)
            
            # Print summary
            logger.info(f"\n{'='*60}")
            logger.info(f"{scraper.name} Summary:")
            logger.info(f"{'='*60}")
            logger.info(f"Matches scraped: {len(odds)}")
            
            for odd in odds[:5]:  # Show first 5
                draw_str = f" / {odd.draw_odds:.2f}" if odd.draw_odds else ""
                logger.info(f"  {odd.match_name:40s} | {odd.home_odds:.2f}{draw_str} / {odd.away_odds:.2f}")
            
            if len(odds) > 5:
                logger.info(f"  ... and {len(odds) - 5} more matches")
            
            logger.info(f"{'='*60}\n")
        else:
            logger.warning(f"No odds found for {scraper.name}")
        
        return len(odds)
        
    except Exception as e:
        logger.error(f"Error scraping {scraper.name}: {e}", exc_info=True)
        return 0


async def main():
    """Main entry point"""
    print("\n" + "="*80)
    print(" ".center(80))
    print("SCRAPLING ODDS DEMO".center(80))
    print("Scrape live odds from European bookmakers".center(80))
    print(" ".center(80))
    print("="*80 + "\n")
    
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("\nBookmakers:")
    print("  - Tipico (Austria/Germany)")
    print("  - Rabona (Crypto sportsbook)")
    print("\n" + "-"*80 + "\n")
    
    # Initialize database
    db = OddsDatabase()
    
    # Initialize scrapers
    scrapers = [
        TipicoScraper(),
        RabonaScraper()
    ]
    
    # Scrape each bookmaker
    total_odds = 0
    for scraper in scrapers:
        count = await scrape_bookmaker(scraper, db)
        total_odds += count
        
        # Wait between scrapers
        if scraper != scrapers[-1]:
            logger.info("Waiting 10 seconds before next scraper...")
            await asyncio.sleep(10)
    
    # Print final statistics
    print("\n" + "="*80)
    print("FINAL STATISTICS".center(80))
    print("="*80)
    
    stats = db.get_statistics()
    print(f"\nTotal odds in database: {stats['total_odds']}")
    print(f"Bookmakers: {stats['total_bookmakers']}")
    print(f"Unique matches: {stats['total_matches']}")
    print(f"Odds added today: {stats['odds_today']}")
    
    print("\n" + "-"*80)
    print("\nLatest odds from database:")
    db.print_latest_odds()
    
    print(f"\nFinished at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("\n" + "="*80)
    print("Thank you for using Scrapling Odds Demo!".center(80))
    print("="*80 + "\n")
    
    return total_odds


if __name__ == "__main__":
    try:
        total = asyncio.run(main())
        
        if total > 0:
            print(f"\n✅ Successfully scraped {total} odds!")
            sys.exit(0)
        else:
            print("\n⚠️  No odds were scraped. Check the logs for errors.")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n\n🛑 Scraper stopped by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        sys.exit(1)
