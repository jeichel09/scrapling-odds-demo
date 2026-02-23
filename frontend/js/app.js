/**
 * Scrapling Odds Comparison - Frontend App
 * Handles data loading, filtering, sorting, and UI interactions
 */

// Configuration
const CONFIG = {
    // API endpoint - in production this would be your backend API
    // For now, we'll use mock data or localStorage
    API_URL: '../api/odds', // Placeholder for future backend
    REFRESH_INTERVAL: 60000, // 60 seconds
    DEBOUNCE_DELAY: 300
};

// State
let state = {
    matches: [],
    filteredMatches: [],
    selectedLeague: 'all',
    selectedBookmaker: 'all',
    searchQuery: '',
    sortBy: 'time'
};

// Mock Data for demonstration (replace with actual API call)
const MOCK_ODDS_DATA = [
    {
        id: 1,
        league: "Austrian Bundesliga",
        homeTeam: "Red Bull Salzburg",
        awayTeam: "Austria Wien",
        kickoffTime: "2026-02-23T18:00:00",
        bookmakers: {
            tipico: { home: 1.45, draw: 4.50, away: 6.00 },
            rabona: { home: 1.48, draw: 4.40, away: 5.80 }
        }
    },
    {
        id: 2,
        league: "German Bundesliga",
        homeTeam: "Bayern München",
        awayTeam: "Borussia Dortmund",
        kickoffTime: "2026-02-23T20:30:00",
        bookmakers: {
            tipico: { home: 1.65, draw: 4.20, away: 4.50 },
            rabona: { home: 1.68, draw: 4.10, away: 4.40 }
        }
    },
    {
        id: 3,
        league: "Premier League",
        homeTeam: "Manchester City",
        awayTeam: "Liverpool",
        kickoffTime: "2026-02-24T17:30:00",
        bookmakers: {
            tipico: { home: 1.85, draw: 3.60, away: 3.80 },
            rabona: { home: 1.88, draw: 3.55, away: 3.75 }
        }
    },
    {
        id: 4,
        league: "La Liga",
        homeTeam: "Real Madrid",
        awayTeam: "Barcelona",
        kickoffTime: "2026-02-24T21:00:00",
        bookmakers: {
            tipico: { home: 2.10, draw: 3.40, away: 3.20 },
            rabona: { home: 2.15, draw: 3.35, away: 3.15 }
        }
    },
    {
        id: 5,
        league: "Serie A",
        homeTeam: "Juventus",
        awayTeam: "AC Milan",
        kickoffTime: "2026-02-25T20:45:00",
        bookmakers: {
            tipico: { home: 2.30, draw: 3.20, away: 2.90 },
            rabona: { home: 2.35, draw: 3.15, away: 2.85 }
        }
    }
];

/**
 * Initialize the application
 */
document.addEventListener('DOMContentLoaded', () => {
    initializeApp();
});

function initializeApp() {
    loadOdds();
    setupEventListeners();
    startAutoRefresh();
}

/**
 * Load odds data
 */
async function loadOdds() {
    showLoading();
    
    try {
        // In production, fetch from your API:
        // const response = await fetch(CONFIG.API_URL);
        // const data = await response.json();
        
        // For demo, use mock data
        await new Promise(resolve => setTimeout(resolve, 1000)); // Simulate network delay
        state.matches = MOCK_ODDS_DATA;
        
        applyFilters();
        renderMatches();
    } catch (error) {
        console.error('Error loading odds:', error);
        showError('Failed to load odds. Please try again.');
    }
}

/**
 * Show loading state
 */
function showLoading() {
    const container = document.getElementById('matchesContainer');
    container.innerHTML = `
        <div class="loading">
            <i class="fas fa-spinner fa-spin"></i>
            <p>Loading odds...</p>
        </div>
    `;
}

/**
 * Show error message
 */
function showError(message) {
    const container = document.getElementById('matchesContainer');
    container.innerHTML = `
        <div class="no-results">
            <i class="fas fa-exclamation-circle"></i>
            <p>${message}</p>
        </div>
    `;
}

/**
 * Apply filters and sorting
 */
function applyFilters() {
    let filtered = [...state.matches];
    
    // Filter by league
    if (state.selectedLeague !== 'all') {
        const leagueMap = {
            'bundesliga': 'Austrian Bundesliga',
            'premier': 'Premier League',
            'laliga': 'La Liga',
            'seriea': 'Serie A'
        };
        filtered = filtered.filter(m => 
            m.league.toLowerCase().includes(leagueMap[state.selectedLeague]?.toLowerCase() || '')
        );
    }
    
    // Filter by search query
    if (state.searchQuery) {
        const query = state.searchQuery.toLowerCase();
        filtered = filtered.filter(m =>
            m.homeTeam.toLowerCase().includes(query) ||
            m.awayTeam.toLowerCase().includes(query) ||
            m.league.toLowerCase().includes(query)
        );
    }
    
    // Sort
    filtered = sortMatches(filtered);
    
    state.filteredMatches = filtered;
}

/**
 * Sort matches
 */
function sortMatches(matches) {
    switch (state.sortBy) {
        case 'time':
            return matches.sort((a, b) => new Date(a.kickoffTime) - new Date(b.kickoffTime));
        case 'best-odds':
            return matches.sort((a, b) => {
                const aBest = Math.max(...Object.values(a.bookmakers).map(b => b.home));
                const bBest = Math.max(...Object.values(b.bookmakers).map(b => b.home));
                return bBest - aBest;
            });
        case 'popularity':
            // For demo, just keep original order
            return matches;
        default:
            return matches;
    }
}

/**
 * Render matches to the DOM
 */
function renderMatches() {
    const container = document.getElementById('matchesContainer');
    const noResults = document.getElementById('noResults');
    
    if (state.filteredMatches.length === 0) {
        container.innerHTML = '';
        noResults.style.display = 'flex';
        return;
    }
    
    noResults.style.display = 'none';
    
    container.innerHTML = state.filteredMatches.map(match => createMatchCard(match)).join('');
}

/**
 * Create HTML for a match card
 */
function createMatchCard(match) {
    const kickoff = new Date(match.kickoffTime);
    const timeStr = kickoff.toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit' });
    const dateStr = kickoff.toLocaleDateString('en-GB', { day: 'numeric', month: 'short' });
    
    // Calculate best odds
    const bookmakerList = Object.entries(match.bookmakers);
    const bestHome = Math.max(...bookmakerList.map(([, odds]) => odds.home));
    const bestDraw = Math.max(...bookmakerList.map(([, odds]) => odds.draw));
    const bestAway = Math.max(...bookmakerList.map(([, odds]) => odds.away));
    
    return `
        <div class="match-card" onclick="showMatchDetails(${match.id})">
            <div class="match-info">
                <div class="match-league">${match.league}</div>
                <div class="match-teams">
                    <div class="team">
                        <div class="team-logo">${match.homeTeam.charAt(0)}</div>
                        <span>${match.homeTeam}</span>
                    </div>
                    <div class="team">
                        <div class="team-logo">${match.awayTeam.charAt(0)}</div>
                        <span>${match.awayTeam}</span>
                    </div>
                </div>
                <div class="match-time">
                    <i class="far fa-clock"></i> ${dateStr}, ${timeStr}
                </div>
            </div>
            <div class="odds-grid">
                ${createOutcomeOdds(match, 'home', bestHome)}
                ${createOutcomeOdds(match, 'draw', bestDraw)}
                ${createOutcomeOdds(match, 'away', bestAway)}
            </div>
        </div>
    `;
}

/**
 * Create HTML for outcome odds (1, X, or 2)
 */
function createOutcomeOdds(match, outcome, bestOdds) {
    const bookmakerList = Object.entries(match.bookmakers);
    
    // Filter by selected bookmaker
    let filteredBookmakers = bookmakerList;
    if (state.selectedBookmaker !== 'all') {
        filteredBookmakers = bookmakerList.filter(([name]) => 
            name.toLowerCase() === state.selectedBookmaker.toLowerCase()
        );
    }
    
    return `
        <div class="bookmaker-odds">
            <div class="outcome-label">${outcome === 'home' ? '1' : outcome === 'draw' ? 'X' : '2'}</div>
            ${filteredBookmakers.map(([name, odds]) => {
                const isBest = odds[outcome] === bestOdds && filteredBookmakers.length > 1;
                return `
                    <div class="odds-row">
                        <div class="odd-cell ${isBest ? 'best-odds' : ''}">
                            ${odds[outcome].toFixed(2)}
                        </div>
                        <div class="bookmaker-name">${name}</div>
                    </div>
                `;
            }).join('')}
        </div>
    `;
}

/**
 * Show match details modal
 */
function showMatchDetails(matchId) {
    const match = state.matches.find(m => m.id === matchId);
    if (!match) return;
    
    const modal = document.getElementById('matchModal');
    const title = document.getElementById('modalMatchTitle');
    const details = document.getElementById('modalOddsDetails');
    
    title.textContent = `${match.homeTeam} vs ${match.awayTeam}`;
    
    details.innerHTML = `
        <div class="match-detail-section">
            <h3>Match Information</h3>
            <p><strong>League:</strong> ${match.league}</p>
            <p><strong>Kickoff:</strong> ${new Date(match.kickoffTime).toLocaleString()}</p>
        </div>
        <div class="match-detail-section">
            <h3>Odds Comparison</h3>
            <table class="odds-comparison-table">
                <thead>
                    <tr>
                        <th>Bookmaker</th>
                        <th>1 (${match.homeTeam})</th>
                        <th>X (Draw)</th>
                        <th>2 (${match.awayTeam})</th>
                    </tr>
                </thead>
                <tbody>
                    ${Object.entries(match.bookmakers).map(([name, odds]) => `
                        <tr>
                            <td>${name}</td>
                            <td>${odds.home.toFixed(2)}</td>
                            <td>${odds.draw.toFixed(2)}</td>
                            <td>${odds.away.toFixed(2)}</td>
                        </tr>
                    `).join('')}
                </tbody>
            </table>
        </div>
        <div class="match-detail-section">
            <h3>Best Odds</h3>
            <div class="best-odds-summary">
                ${calculateBestOdds(match)}
            </div>
        </div>
    `;
    
    modal.classList.add('active');
}

/**
 * Calculate and display best odds
 */
function calculateBestOdds(match) {
    const bookmakers = Object.entries(match.bookmakers);
    
    const bestHome = bookmakers.reduce((best, [name, odds]) => 
        odds.home > best.odds ? { name, odds: odds.home } : best
    , { name: '', odds: 0 });
    
    const bestDraw = bookmakers.reduce((best, [name, odds]) => 
        odds.draw > best.odds ? { name, odds: odds.draw } : best
    , { name: '', odds: 0 });
    
    const bestAway = bookmakers.reduce((best, [name, odds]) => 
        odds.away > best.odds ? { name, odds: odds.away } : best
    , { name: '', odds: 0 });
    
    // Calculate arbitrage
    const margin = (1 / bestHome.odds) + (1 / bestDraw.odds) + (1 / bestAway.odds);
    const arbitrage = margin < 1 ? ((1 - margin) * 100).toFixed(2) : null;
    
    return `
        <div class="best-odds-grid">
            <div class="best-odd-item">
                <span class="label">1 (Home)</span>
                <span class="value">${bestHome.odds.toFixed(2)}</span>
                <span class="bookmaker">${bestHome.name}</span>
            </div>
            <div class="best-odd-item">
                <span class="label">X (Draw)</span>
                <span class="value">${bestDraw.odds.toFixed(2)}</span>
                <span class="bookmaker">${bestDraw.name}</span>
            </div>
            <div class="best-odd-item">
                <span class="label">2 (Away)</span>
                <span class="value">${bestAway.odds.toFixed(2)}</span>
                <span class="bookmaker">${bestAway.name}</span>
            </div>
        </div>
        ${arbitrage ? `
            <div class="arbitrage-alert">
                <i class="fas fa-exclamation-triangle"></i>
                Arbitrage opportunity: ${arbitrage}% profit margin
            </div>
        ` : ''}
    `;
}

/**
 * Close modal
 */
function closeModal() {
    const modal = document.getElementById('matchModal');
    modal.classList.remove('active');
}

/**
 * Setup event listeners
 */
function setupEventListeners() {
    // Search input with debounce
    const searchInput = document.getElementById('searchInput');
    let searchTimeout;
    searchInput.addEventListener('input', (e) => {
        clearTimeout(searchTimeout);
        searchTimeout = setTimeout(() => {
            state.searchQuery = e.target.value;
            applyFilters();
            renderMatches();
        }, CONFIG.DEBOUNCE_DELAY);
    });
    
    // League filters
    document.querySelectorAll('.league-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            document.querySelectorAll('.league-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            state.selectedLeague = btn.dataset.league;
            applyFilters();
            renderMatches();
        });
    });
    
    // Bookmaker filter
    document.getElementById('bookmakerFilter').addEventListener('change', (e) => {
        state.selectedBookmaker = e.target.value;
        applyFilters();
        renderMatches();
    });
    
    // Sort by
    document.getElementById('sortBy').addEventListener('change', (e) => {
        state.sortBy = e.target.value;
        applyFilters();
        renderMatches();
    });
    
    // Close modal on outside click
    document.getElementById('matchModal').addEventListener('click', (e) => {
        if (e.target.id === 'matchModal') {
            closeModal();
        }
    });
    
    // Keyboard shortcuts
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
            closeModal();
        }
        if (e.key === 'r' && e.ctrlKey) {
            e.preventDefault();
            refreshOdds();
        }
    });
}

/**
 * Refresh odds manually
 */
async function refreshOdds() {
    const btn = document.querySelector('.btn-refresh');
    btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Refreshing...';
    btn.disabled = true;
    
    await loadOdds();
    
    btn.innerHTML = '<i class="fas fa-sync-alt"></i> Refresh';
    btn.disabled = false;
}

/**
 * Auto-refresh odds periodically
 */
function startAutoRefresh() {
    setInterval(() => {
        loadOdds();
    }, CONFIG.REFRESH_INTERVAL);
}

// Export functions for global access
window.refreshOdds = refreshOdds;
window.showMatchDetails = showMatchDetails;
window.closeModal = closeModal;
