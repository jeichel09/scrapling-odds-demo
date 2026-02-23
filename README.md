# Scrapling Odds Demo

A demo project for scraping live odds from European bookmakers using Scrapling framework.

## Supported Bookmakers

- ✅ **Tipico** (Austria/Germany)
- ✅ **Rabona** (Crypto sportsbook)

## Features

- 🕷️ **Scrapling-powered** - Bypasses anti-bot protection
- 🔄 **Async scraping** - Concurrent requests for speed
- 💾 **SQLite storage** - Local database for odds history
- 📊 **Odds comparison** - Compare across bookmakers
- 🛡️ **Stealth mode** - Avoid detection with proxy rotation

## Installation

```bash
# Clone repository
git clone https://github.com/jeichel09/scrapling-odds-demo.git
cd scrapling-odds-demo

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install Scrapling browsers (one-time setup)
scrapling install
```

## Usage

### Scrape Single Bookmaker

```python
from scrapers.tipico import TipicoScraper
import asyncio

async def main():
    scraper = TipicoScraper()
    odds = await scraper.scrape_all()
    
    for odd in odds:
        print(f"{odd.match_name}: {odd.home_odds} / {odd.draw_odds} / {odd.away_odds}")

asyncio.run(main())
```

### Scrape Multiple Bookmakers

```python
from scrapers.tipico import TipicoScraper
from scrapers.rabona import RabonaScraper
from storage.database import OddsDatabase
import asyncio

async def main():
    scrapers = [TipicoScraper(), RabonaScraper()]
    db = OddsDatabase()
    
    for scraper in scrapers:
        print(f"Scraping {scraper.name}...")
        odds = await scraper.scrape_all()
        db.save_odds(odds)
        print(f"Saved {len(odds)} odds from {scraper.name}")

asyncio.run(main())
```

### Run Demo

```bash
# Scrape both bookmakers and save to database
python main.py

# View saved odds
python -c "from storage.database import OddsDatabase; db = OddsDatabase(); db.print_latest_odds()"
```

## Project Structure

```
scrapling-odds-demo/
├── scrapers/
│   ├── __init__.py
│   ├── base.py           # Base scraper class
│   ├── tipico.py         # Tipico scraper
│   └── rabona.py         # Rabona scraper
├── models/
│   ├── __init__.py
│   └── odds.py           # Data models
├── storage/
│   ├── __init__.py
│   └── database.py       # SQLite database
├── config/
│   └── settings.py       # Configuration
├── tests/
│   └── test_scrapers.py  # Unit tests
├── requirements.txt      # Dependencies
├── main.py              # Demo script
└── README.md            # This file
```

## Configuration

Edit `config/settings.py` to customize:

```python
# Proxy settings (recommended for production)
PROXIES = [
    "http://user:pass@proxy1:8080",
    "http://user:pass@proxy2:8080",
]

# Rate limiting
REQUEST_DELAY = (2, 5)  # Random delay between 2-5 seconds
MAX_CONCURRENT = 3      # Max concurrent scrapers

# Database
DATABASE_PATH = "odds.db"
```

## Legal Notice

⚠️ **IMPORTANT**: This project is for **educational purposes only**.

- Always check bookmaker Terms of Service before scraping
- Respect robots.txt files
- Use reasonable rate limiting to avoid overloading servers
- Consider using official APIs when available
- The authors are not responsible for any misuse of this software

## License

MIT License - See LICENSE file

## Author

Created for educational demonstration of Scrapling framework.
