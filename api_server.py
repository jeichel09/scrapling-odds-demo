"""
Flask API for Scrapling Odds Demo
On-demand odds scraping with caching
"""

from flask import Flask, jsonify, request
from flask_cors import CORS
import asyncio
import json
import os
from datetime import datetime, timedelta
from functools import wraps
from typing import Dict, List, Optional

# Import scrapers
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from scrapers.tipico import TipicoScraper
from scrapers.rabona import RabonaScraper
from models.odds import OddsData
from storage.database import OddsDatabase

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend

# Simple in-memory cache
cache = {}
CACHE_DURATION = 300  # 5 minutes

def get_cached(key: str) -> Optional[Dict]:
    """Get cached data if not expired"""
    if key in cache:
        data, timestamp = cache[key]
        if datetime.now() - timestamp < timedelta(seconds=CACHE_DURATION):
            return data
        else:
            del cache[key]
    return None

def set_cache(key: str, data: Dict):
    """Store data in cache"""
    cache[key] = (data, datetime.now())

# Initialize scrapers
scrapers = {
    'tipico': TipicoScraper(),
    'rabona': RabonaScraper()
}

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'ok',
        'timestamp': datetime.now().isoformat(),
        'scrapers': list(scrapers.keys())
    })

@app.route('/api/leagues', methods=['GET'])
def get_leagues():
    """Get list of available leagues"""
    leagues = [
        {"id": "bundesliga", "name": "Austrian Bundesliga", "country": "AT"},
        {"id": "2-liga", "name": "Austrian 2. Liga", "country": "AT"},
        {"id": "bundesliga-de", "name": "German Bundesliga", "country": "DE"},
        {"id": "premier-league", "name": "Premier League", "country": "EN"},
        {"id": "la-liga", "name": "La Liga", "country": "ES"},
        {"id": "serie-a", "name": "Serie A", "country": "IT"},
        {"id": "ligue-1", "name": "Ligue 1", "country": "FR"},
    ]
    return jsonify(leagues)

@app.route('/api/odds', methods=['GET'])
def get_odds():
    """
    Get odds for specified bookmakers and leagues
    Query params:
    - bookmakers: comma-separated list (e.g., "tipico,rabona")
    - leagues: comma-separated list (e.g., "bundesliga,2-liga")
    - force_refresh: bool (bypass cache)
    """
    bookmakers_param = request.args.get('bookmakers', 'tipico')
    leagues_param = request.args.get('leagues', '')
    force_refresh = request.args.get('force_refresh', 'false').lower() == 'true'
    
    # Parse parameters
    requested_bookmakers = [b.strip() for b in bookmakers_param.split(',') if b.strip()]
    requested_leagues = [l.strip() for l in leagues_param.split(',') if l.strip()]
    
    # Create cache key
    cache_key = f"odds:{bookmakers_param}:{leagues_param}"
    
    # Check cache
    if not force_refresh:
        cached_data = get_cached(cache_key)
        if cached_data:
            print(f"[API] Serving cached data for {cache_key}")
            return jsonify({
                'data': cached_data,
                'cached': True,
                'timestamp': datetime.now().isoformat()
            })
    
    # Scrape on-demand
    print(f"[API] Scraping fresh data for {requested_bookmakers}")
    
    all_odds = []
    errors = []
    
    for bookmaker_name in requested_bookmakers:
        if bookmaker_name not in scrapers:
            errors.append(f"Unknown bookmaker: {bookmaker_name}")
            continue
        
        scraper = scrapers[bookmaker_name]
        
        try:
            # Run async scraper in sync Flask context
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            odds = loop.run_until_complete(scraper.scrape_all(max_matches=5))
            loop.close()
            
            # Convert to dict
            for odd in odds:
                all_odds.append({
                    'bookmaker': odd.bookmaker,
                    'match_name': odd.match_name,
                    'home_team': odd.home_team,
                    'away_team': odd.away_team,
                    'home_odds': odd.home_odds,
                    'draw_odds': odd.draw_odds,
                    'away_odds': odd.away_odds,
                    'league': odd.league,
                    'timestamp': odd.timestamp,
                    'url': odd.url
                })
            
        except Exception as e:
            errors.append(f"{bookmaker_name}: {str(e)}")
            print(f"[API] Error scraping {bookmaker_name}: {e}")
    
    # Cache results
    result_data = {
        'odds': all_odds,
        'count': len(all_odds),
        'bookmakers': requested_bookmakers,
        'errors': errors if errors else None
    }
    
    set_cache(cache_key, result_data)
    
    return jsonify({
        'data': result_data,
        'cached': False,
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/odds/<bookmaker>', methods=['GET'])
def get_bookmaker_odds(bookmaker):
    """Get odds from a specific bookmaker"""
    if bookmaker not in scrapers:
        return jsonify({'error': f'Bookmaker not found: {bookmaker}'}), 404
    
    cache_key = f"odds:{bookmaker}"
    
    # Check cache
    cached_data = get_cached(cache_key)
    if cached_data:
        return jsonify({
            'data': cached_data,
            'cached': True,
            'timestamp': datetime.now().isoformat()
        })
    
    # Scrape
    scraper = scrapers[bookmaker]
    
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        odds = loop.run_until_complete(scraper.scrape_all(max_matches=10))
        loop.close()
        
        result_data = {
            'odds': [odd.to_dict() for odd in odds],
            'count': len(odds),
            'bookmaker': bookmaker
        }
        
        set_cache(cache_key, result_data)
        
        return jsonify({
            'data': result_data,
            'cached': False,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/compare/<match_name>', methods=['GET'])
def compare_match(match_name):
    """Compare odds across all bookmakers for a specific match"""
    all_odds = []
    
    for name, scraper in scrapers.items():
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            odds = loop.run_until_complete(scraper.scrape_all(max_matches=20))
            loop.close()
            
            # Filter for match
            for odd in odds:
                if match_name.lower() in odd.match_name.lower():
                    all_odds.append(odd.to_dict())
                    
        except Exception as e:
            print(f"[API] Error with {name}: {e}")
    
    return jsonify({
        'match': match_name,
        'odds': all_odds,
        'count': len(all_odds),
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/cache/clear', methods=['POST'])
def clear_cache():
    """Clear the cache (admin endpoint)"""
    global cache
    cache = {}
    return jsonify({'status': 'Cache cleared'})

@app.route('/api/cache/stats', methods=['GET'])
def cache_stats():
    """Get cache statistics"""
    return jsonify({
        'cache_size': len(cache),
        'cached_keys': list(cache.keys()),
        'cache_duration': CACHE_DURATION
    })

if __name__ == '__main__':
    print("="*60)
    print("Scrapling Odds API Server")
    print("="*60)
    print("\nEndpoints:")
    print("  GET  /api/health          - Health check")
    print("  GET  /api/leagues         - List available leagues")
    print("  GET  /api/odds            - Get odds (use ?bookmakers=tipico,rabona)")
    print("  GET  /api/odds/<name>     - Get specific bookmaker")
    print("  GET  /api/compare/<match> - Compare match across bookmakers")
    print("  POST /api/cache/clear     - Clear cache")
    print("\nExamples:")
    print('  curl "http://localhost:5000/api/odds?bookmakers=tipico"')
    print('  curl "http://localhost:5000/api/odds?bookmakers=tipico,rabona&force_refresh=true"')
    print("="*60)
    
    app.run(debug=True, host='0.0.0.0', port=5000)
