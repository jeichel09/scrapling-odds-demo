"""
SQLite Database for storing odds
"""

import sqlite3
import json
from datetime import datetime, timedelta
from typing import List, Optional
from models.odds import OddsData
import logging

logger = logging.getLogger(__name__)


class OddsDatabase:
    """SQLite database for odds storage"""
    
    def __init__(self, db_path: str = "odds.db"):
        self.db_path = db_path
        self._init_db()
    
    def _init_db(self):
        """Initialize database with tables"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Create odds table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS odds (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    bookmaker TEXT NOT NULL,
                    match_name TEXT NOT NULL,
                    home_team TEXT NOT NULL,
                    away_team TEXT NOT NULL,
                    home_odds REAL NOT NULL,
                    draw_odds REAL,
                    away_odds REAL NOT NULL,
                    timestamp TEXT NOT NULL,
                    url TEXT NOT NULL,
                    league TEXT
                )
            ''')
            
            # Create index for faster queries
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_bookmaker 
                ON odds(bookmaker)
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_timestamp 
                ON odds(timestamp)
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_match 
                ON odds(match_name)
            ''')
            
            conn.commit()
            logger.info(f"Database initialized: {self.db_path}")
    
    def save_odds(self, odds_list: List[OddsData]):
        """Save list of odds to database"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            for odds in odds_list:
                cursor.execute('''
                    INSERT INTO odds 
                    (bookmaker, match_name, home_team, away_team, 
                     home_odds, draw_odds, away_odds, timestamp, url, league)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    odds.bookmaker,
                    odds.match_name,
                    odds.home_team,
                    odds.away_team,
                    odds.home_odds,
                    odds.draw_odds,
                    odds.away_odds,
                    odds.timestamp,
                    odds.url,
                    odds.league
                ))
            
            conn.commit()
            logger.info(f"Saved {len(odds_list)} odds to database")
    
    def get_latest_odds(self, bookmaker: Optional[str] = None, 
                       hours: int = 24) -> List[OddsData]:
        """Get latest odds from last N hours"""
        cutoff = (datetime.now() - timedelta(hours=hours)).isoformat()
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            if bookmaker:
                cursor.execute('''
                    SELECT * FROM odds 
                    WHERE bookmaker = ? AND timestamp > ?
                    ORDER BY timestamp DESC
                ''', (bookmaker, cutoff))
            else:
                cursor.execute('''
                    SELECT * FROM odds 
                    WHERE timestamp > ?
                    ORDER BY timestamp DESC
                ''', (cutoff,))
            
            rows = cursor.fetchall()
            
            # Convert rows to OddsData objects
            odds_list = []
            for row in rows:
                odds_list.append(OddsData(
                    bookmaker=row[1],
                    match_name=row[2],
                    home_team=row[3],
                    away_team=row[4],
                    home_odds=row[5],
                    draw_odds=row[6],
                    away_odds=row[7],
                    timestamp=row[8],
                    url=row[9],
                    league=row[10]
                ))
            
            return odds_list
    
    def get_match_comparison(self, match_name: str) -> List[OddsData]:
        """Get all odds for a specific match across bookmakers"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT * FROM odds 
                WHERE match_name LIKE ?
                ORDER BY timestamp DESC
            ''', (f'%{match_name}%',))
            
            rows = cursor.fetchall()
            
            odds_list = []
            for row in rows:
                odds_list.append(OddsData(
                    bookmaker=row[1],
                    match_name=row[2],
                    home_team=row[3],
                    away_team=row[4],
                    home_odds=row[5],
                    draw_odds=row[6],
                    away_odds=row[7],
                    timestamp=row[8],
                    url=row[9],
                    league=row[10]
                ))
            
            return odds_list
    
    def print_latest_odds(self, bookmaker: Optional[str] = None):
        """Print latest odds to console"""
        odds = self.get_latest_odds(bookmaker)
        
        if not odds:
            print("No odds found in database")
            return
        
        print(f"\n{'='*80}")
        print(f"LATEST ODDS ({len(odds)} matches)")
        print(f"{'='*80}")
        
        current_bookmaker = None
        for odd in odds:
            if odd.bookmaker != current_bookmaker:
                current_bookmaker = odd.bookmaker
                print(f"\n📊 {current_bookmaker}")
                print("-" * 80)
            
            draw_str = f" / {odd.draw_odds:.2f}" if odd.draw_odds else ""
            print(f"  {odd.match_name:40s} | {odd.home_odds:.2f}{draw_str} / {odd.away_odds:.2f}")
        
        print(f"\n{'='*80}\n")
    
    def get_statistics(self) -> dict:
        """Get database statistics"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Total odds
            cursor.execute('SELECT COUNT(*) FROM odds')
            total_odds = cursor.fetchone()[0]
            
            # Unique bookmakers
            cursor.execute('SELECT COUNT(DISTINCT bookmaker) FROM odds')
            total_bookmakers = cursor.fetchone()[0]
            
            # Unique matches
            cursor.execute('SELECT COUNT(DISTINCT match_name) FROM odds')
            total_matches = cursor.fetchone()[0]
            
            # Odds today
            today = datetime.now().strftime('%Y-%m-%d')
            cursor.execute('''
                SELECT COUNT(*) FROM odds 
                WHERE timestamp LIKE ?
            ''', (f'{today}%',))
            odds_today = cursor.fetchone()[0]
            
            return {
                'total_odds': total_odds,
                'total_bookmakers': total_bookmakers,
                'total_matches': total_matches,
                'odds_today': odds_today
            }
