# Data Models

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class OddsData:
    """Represents odds for a single match from a bookmaker"""
    bookmaker: str
    match_name: str
    home_team: str
    away_team: str
    home_odds: float
    draw_odds: Optional[float]
    away_odds: float
    timestamp: str
    url: str
    league: Optional[str] = None
    
    def to_dict(self) -> dict:
        """Convert to dictionary for database storage"""
        return {
            'bookmaker': self.bookmaker,
            'match_name': self.match_name,
            'home_team': self.home_team,
            'away_team': self.away_team,
            'home_odds': self.home_odds,
            'draw_odds': self.draw_odds,
            'away_odds': self.away_odds,
            'timestamp': self.timestamp,
            'url': self.url,
            'league': self.league
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'OddsData':
        """Create OddsData from dictionary"""
        return cls(**data)
    
    def get_best_odds(self) -> tuple:
        """Returns (best_odds_value, best_odds_type)"""
        odds = {
            'home': self.home_odds,
            'draw': self.draw_odds if self.draw_odds else 0,
            'away': self.away_odds
        }
        best = max(odds.items(), key=lambda x: x[1])
        return best[1], best[0]


@dataclass
class Match:
    """Represents a match across multiple bookmakers"""
    match_name: str
    home_team: str
    away_team: str
    league: Optional[str]
    odds: list  # List of OddsData from different bookmakers
    
    def get_best_home_odds(self) -> OddsData:
        """Returns best home odds across all bookmakers"""
        return max(self.odds, key=lambda x: x.home_odds)
    
    def get_best_away_odds(self) -> OddsData:
        """Returns best away odds across all bookmakers"""
        return max(self.odds, key=lambda x: x.away_odds)
    
    def get_best_draw_odds(self) -> Optional[OddsData]:
        """Returns best draw odds across all bookmakers"""
        draw_odds = [o for o in self.odds if o.draw_odds]
        if draw_odds:
            return max(draw_odds, key=lambda x: x.draw_odds)
        return None
    
    def get_arbitrage_opportunity(self) -> Optional[dict]:
        """Check if arbitrage opportunity exists"""
        best_home = self.get_best_home_odds()
        best_away = self.get_best_away_odds()
        best_draw = self.get_best_draw_odds()
        
        # Calculate implied probabilities
        inv_home = 1 / best_home.home_odds
        inv_away = 1 / best_away.away_odds
        
        if best_draw:
            inv_draw = 1 / best_draw.draw_odds
            total = inv_home + inv_away + inv_draw
        else:
            total = inv_home + inv_away
        
        # If total < 1, arbitrage exists
        if total < 1:
            return {
                'profit_margin': (1 - total) * 100,
                'best_home': best_home,
                'best_draw': best_draw,
                'best_away': best_away
            }
        return None
