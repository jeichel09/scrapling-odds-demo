# League Configuration for Scrapling Odds Demo
# Only scrape odds for these specific football tournaments

TARGET_LEAGUES = [
    # Austria
    "Austrian Bundesliga",           # Österreichische Bundesliga
    "Austrian 2. Liga",              # 2. Liga
    
    # Germany
    "German Bundesliga",             # 1. Bundesliga
    "German 2. Bundesliga",          # 2. Bundesliga
    
    # England
    "Premier League",                # English Premier League
    "Championship",                  # EFL Championship
    "League One",                    # EFL League One
    "League Two",                    # EFL League Two
    
    # Spain
    "La Liga",                       # Primera División
    "La Liga 2",                     # Segunda División
    "Segunda División",              # Alternative name
    
    # Italy
    "Serie A",                       # Italian Serie A
    "Serie B",                       # Italian Serie B
    
    # France
    "Ligue 1",                       # French Ligue 1
    "Ligue 2",                       # French Ligue 2
    
    # European Competitions
    "UEFA Champions League",         # UCL
    "Champions League",              # Alternative name
    "UEFA Europa League",            # League Europe
    "Europa League",                 # Alternative name
    "UEFA Nations League",           # Nations League
    "Nations League",                # Alternative name
]

# Alternative names that bookmakers might use (for matching)
LEAGUE_ALIASES = {
    # Austria
    "Österreichische Bundesliga": "Austrian Bundesliga",
    "ÖBL": "Austrian Bundesliga",
    "2. Liga": "Austrian 2. Liga",
    
    # Germany
    "1. Bundesliga": "German Bundesliga",
    "Bundesliga": "German Bundesliga",
    "2. Bundesliga": "German 2. Bundesliga",
    
    # England
    "EPL": "Premier League",
    "English Premier League": "Premier League",
    "EFL Championship": "Championship",
    "EFL League One": "League One",
    "EFL League Two": "League Two",
    
    # Spain
    "Primera División": "La Liga",
    "LaLiga": "La Liga",
    "LaLiga Santander": "La Liga",
    "Segunda División": "La Liga 2",
    "LaLiga SmartBank": "La Liga 2",
    
    # Italy
    "Serie A TIM": "Serie A",
    "Serie BKT": "Serie B",
    
    # France
    "Ligue 1 Uber Eats": "Ligue 1",
    "Ligue 2 BKT": "Ligue 2",
    
    # Europe
    "UCL": "UEFA Champions League",
    "Champions": "UEFA Champions League",
    "UEL": "UEFA Europa League",
    "Europa": "UEFA Europa League",
    "UNL": "UEFA Nations League",
}

# League priorities (for ordering)
LEAGUE_PRIORITY = {
    "UEFA Champions League": 1,
    "UEFA Europa League": 2,
    "UEFA Nations League": 3,
    "Premier League": 4,
    "German Bundesliga": 5,
    "La Liga": 6,
    "Serie A": 7,
    "Ligue 1": 8,
    "Austrian Bundesliga": 9,
    "Championship": 10,
    "German 2. Bundesliga": 11,
    "La Liga 2": 12,
    "Serie B": 13,
    "Ligue 2": 14,
    "Austrian 2. Liga": 15,
    "League One": 16,
    "League Two": 17,
}

# URL patterns for specific leagues (for direct navigation)
LEAGUE_URLS = {
    "tipico": {
        "Austrian Bundesliga": "/de/online-sportwetten/fussball/oesterreich/bundesliga",
        "German Bundesliga": "/de/online-sportwetten/fussball/deutschland/bundesliga",
        "Premier League": "/de/online-sportwetten/fussball/england/premier-league",
        "La Liga": "/de/online-sportwetten/fussball/spanien/laliga",
        "Serie A": "/de/online-sportwetten/fussball/italien/serie-a",
        "Ligue 1": "/de/online-sportwetten/fussball/frankreich/ligue-1",
        "UEFA Champions League": "/de/online-sportwetten/fussball/international/champions-league",
        "UEFA Europa League": "/de/online-sportwetten/fussball/international/europa-league",
    },
    "rabona": {
        # To be filled in after investigation
    }
}

# Countries for filtering
TARGET_COUNTRIES = [
    "Austria",
    "Germany",
    "England",
    "Spain",
    "Italy",
    "France",
    "International",  # For UCL, Europa, Nations League
]
