# Scrapling Odds - Frontend

A modern, responsive web interface for comparing bookmaker odds - styled like Oddschecker.

## Features

- 📊 **Odds Comparison Table** - Side-by-side comparison of multiple bookmakers
- 🎯 **Best Odds Highlighting** - Green highlighting for the best odds
- 🔍 **Search & Filter** - Find matches by team, league, or bookmaker
- 📱 **Responsive Design** - Works on desktop, tablet, and mobile
- ⚡ **Real-time Updates** - Auto-refresh every 60 seconds
- 💎 **Arbitrage Detection** - Identifies profit opportunities
- 🎨 **Modern UI** - Clean, professional design with smooth animations

## Quick Start

### Option 1: Open Directly (Simplest)

```bash
cd frontend
# Open index.html in your browser
# On macOS:
open index.html
# On Linux:
xdg-open index.html
# On Windows:
start index.html
```

### Option 2: Use a Local Server (Recommended)

```bash
cd frontend

# Using Python
python3 -m http.server 8080

# Using Node.js (if you have npx)
npx serve

# Using PHP
php -S localhost:8080
```

Then open: http://localhost:8080

## Project Structure

```
frontend/
├── index.html          # Main HTML file
├── css/
│   └── style.css       # All styles (12,000+ lines)
├── js/
│   └── app.js          # JavaScript logic (400+ lines)
├── images/             # Bookmaker logos, icons
└── README.md           # This file
```

## Configuration

### Connect to Real Data

Currently, the frontend uses **mock data** for demonstration. To connect to your actual scraped odds:

**Option 1: Simple JSON File**
```javascript
// In js/app.js, replace MOCK_ODDS_DATA with:
const response = await fetch('./data/odds.json');
const data = await response.json();
```

**Option 2: API Endpoint**
```javascript
// If you have a backend API
const CONFIG = {
    API_URL: 'http://localhost:5000/api/odds'
};
```

**Option 3: WebSocket (Real-time)**
```javascript
// For real-time updates
const ws = new WebSocket('ws://localhost:8080');
ws.onmessage = (event) => {
    const odds = JSON.parse(event.data);
    updateDisplay(odds);
};
```

### Data Format

The frontend expects odds data in this format:

```json
{
    "id": 1,
    "league": "Austrian Bundesliga",
    "homeTeam": "Red Bull Salzburg",
    "awayTeam": "Austria Wien",
    "kickoffTime": "2026-02-23T18:00:00",
    "bookmakers": {
        "tipico": { "home": 1.45, "draw": 4.50, "away": 6.00 },
        "rabona": { "home": 1.48, "draw": 4.40, "away": 5.80 }
    }
}
```

## Customization

### Add More Bookmakers

1. Update the filter dropdown in `index.html`:
```html
<select id="bookmakerFilter">
    <option value="all">All Bookmakers</option>
    <option value="tipico">Tipico</option>
    <option value="rabona">Rabona</option>
    <option value="bet365">Bet365</option>  <!-- Add this -->
</select>
```

2. Add bookmaker colors in `css/style.css`:
```css
.bookmaker-bet365 {
    background: #007B5F;
    color: white;
}
```

### Change Colors

Edit CSS variables in `css/style.css`:

```css
:root {
    --primary: #1a73e8;        /* Main brand color */
    --secondary: #34a853;      /* Best odds green */
    --accent: #fbbc04;         /* Highlight yellow */
    --danger: #ea4335;         /* Error red */
}
```

### Add New Sports

1. Update navigation in `index.html`:
```html
<nav class="main-nav">
    <a href="#" class="active">Football</a>
    <a href="#">Basketball</a>
    <a href="#">Tennis</a>
    <a href="#">Ice Hockey</a>
    <a href="#">Baseball</a>  <!-- Add this -->
</nav>
```

## Features Explained

### Best Odds Detection

The app automatically highlights the highest odds for each outcome (1, X, 2) with:
- Green background
- Star badge (★)
- Border highlight

### Arbitrage Detection

When you click on a match, the modal calculates if there's an arbitrage opportunity:
- Combines best odds from different bookmakers
- Shows profit margin if > 0%
- Formula: `1/home + 1/draw + 1/away < 1`

### Filters

- **League Filter**: Show only specific leagues
- **Bookmaker Filter**: Compare specific bookmakers
- **Search**: Find teams or matches
- **Sort**: By time, best odds, or popularity

## Browser Support

- ✅ Chrome 90+
- ✅ Firefox 88+
- ✅ Safari 14+
- ✅ Edge 90+

## Performance

- Lightweight: ~15KB CSS + ~15KB JS (gzipped)
- Fast rendering: Uses CSS Grid and Flexbox
- Minimal dependencies: Only Font Awesome icons
- Smooth animations: CSS transitions and keyframes

## Keyboard Shortcuts

- `Ctrl + R` - Refresh odds
- `ESC` - Close modal
- `/` - Focus search box (add this feature)

## API Integration Example

```python
# Flask backend example
from flask import Flask, jsonify
import sqlite3

app = Flask(__name__)

@app.route('/api/odds')
def get_odds():
    conn = sqlite3.connect('../odds.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM odds ORDER BY timestamp DESC LIMIT 50')
    rows = cursor.fetchall()
    
    # Convert to JSON format expected by frontend
    odds = []
    for row in rows:
        odds.append({
            'id': row[0],
            'bookmaker': row[1],
            'match_name': row[2],
            'home_odds': row[5],
            'draw_odds': row[6],
            'away_odds': row[7],
            'timestamp': row[8]
        })
    
    return jsonify(odds)

if __name__ == '__main__':
    app.run(debug=True, port=5000)
```

## Deployment

### Static Hosting (GitHub Pages, Netlify, Vercel)

1. Upload `frontend/` folder
2. Configure domain (optional)
3. Done!

### With Backend

```bash
# Example: Deploy with Flask
cd frontend
# Build production assets (if using a build tool)
# Or just serve static files

# Backend serves frontend
from flask import Flask, send_from_directory

app = Flask(__name__)

@app.route('/')
def index():
    return send_from_directory('frontend', 'index.html')

@app.route('/<path:path>')
def static_files(path):
    return send_from_directory('frontend', path)
```

## Troubleshooting

### Odds Not Loading
- Check browser console for errors
- Verify data format matches expected structure
- Ensure CORS is enabled if using separate API

### Styles Not Applied
- Check that `css/style.css` path is correct
- Clear browser cache
- Verify Font Awesome CDN is loading

### Modal Not Opening
- Check that `js/app.js` is loaded
- Verify no JavaScript errors in console

## Future Enhancements

- [ ] User authentication
- [ ] Favorite matches
- [ ] Odds history charts
- [ ] Email alerts for arbitrage
- [ ] Mobile app (PWA)
- [ ] Dark mode
- [ ] Multi-language support
- [ ] Live match tracking
- [ ] Betting calculator
- [ ] Export to Excel/CSV

## Credits

- Design inspired by [Oddschecker](https://www.oddschecker.com)
- Icons by [Font Awesome](https://fontawesome.com)
- Fonts by [Google Fonts](https://fonts.google.com)

## License

MIT License - See main project LICENSE
