/**
 * Scrapling Odds - Frontend with API Integration
 * Fetches odds from Flask API on-demand
 */

// API Configuration
const API_BASE_URL = 'http://localhost:5000/api';
const CACHE_DURATION = 5 * 60 * 1000; // 5 minutes in milliseconds

// State
let state = {
    matches: [],
    cachedMatches: [],
    cachedTimestamp: null,
    selectedLeague: 'all',
    selectedBookmaker: 'all',
    searchQuery: '',
    sortBy: 'time',
    isLoading: false
};

/**
 * Initialize the application
 */
document.addEventListener('DOMContentLoaded', () => {
    initializeApp();
});

function initializeApp() {
    setupEventListeners();
    loadOdds(); // Load on startup
}

/**
 * Fetch odds from API
 */
async function fetchOddsFromAPI(bookmakers = ['tipico'], forceRefresh = false) {
    const bookmakersParam = bookmakers.join(',');
    const url = `${API_BASE_URL}/odds?bookmakers=${bookmakersParam}${forceRefresh ? '&force_refresh=true' : ''}`;
    
    try {
        showLoading();
        const response = await fetch(url);
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const result = await response.json();
        
        if (result.data && result.data.odds) {
            return {
                odds: result.data.odds,
                cached: result.cached,
                timestamp: result.timestamp
            };
        }
        
        throw new Error('Invalid data format');
        
    } catch (error) {
        console.error('Error fetching odds:', error);
        throw error;
    }
}

/**
 * Load odds (with caching check)
 */
async function loadOdds(forceRefresh = false) {
    // Check if we have recent cached data
    if (!forceRefresh && state.cachedMatches.length > 0) {
        const now = Date.now();
        const cacheAge = now - state.cachedTimestamp;
        
        if (cacheAge < CACHE_DURATION) {
            console.log('Using cached data');
            state.matches = state.cachedMatches;
            applyFilters();
            renderMatches();
            showCacheInfo(true, Math.round((CACHE_DURATION - cacheAge) / 1000));
            return;
        }
    }
    
    // Fetch fresh data
    try {
        const result = await fetchOddsFromAPI(['tipico'], forceRefresh);
        
        // Process and group odds by match
        state.matches = groupOddsByMatch(result.odds);
        state.cachedMatches = state.matches;
        state.cachedTimestamp = Date.now();
        
        applyFilters();
        renderMatches();
        showCacheInfo(result.cached, CACHE_DURATION / 1000);
        
    } catch (error) {
        console.error('Failed to load odds:', error);
        showError('Failed to load odds. Is the API server running?');
    }
}

/**
 * Group odds by match for display
 */
function groupOddsByMatch(oddsList) {
    const matches = {};
    
    oddsList.forEach(odd => {
        const key = `${odd.home_team} vs ${odd.away_team}`;
        
        if (!matches[key]) {
            matches[key] = {
                id: key,
                match_name: odd.match_name,
                home_team: odd.home_team,
                away_team: odd.away_team,
                league: odd.league,
                kickoffTime: odd.timestamp, // Using timestamp as placeholder
                bookmakers: {}
            };
        }
        
        matches[key].bookmakers[odd.bookmaker] = {
            home: odd.home_odds,
            draw: odd.draw_odds,
            away: odd.away_odds,
            timestamp: odd.timestamp
        };
    });
    
    return Object.values(matches);
}

/**
 * Show loading state
 */
function showLoading() {
    state.isLoading = true;
    const container = document.getElementById('matchesContainer');
    container.innerHTML = `
        <div class="loading">
            <i class="fas fa-spinner fa-spin"></i>
            <p>Loading odds from bookmakers...</p>
            <p style="font-size: 0.9rem; color: var(--text-muted);">This may take 10-30 seconds</p>
        </div>
    `;
}

/**
 * Show cache info
 */
function showCacheInfo(isCached, secondsRemaining) {
    const refreshBtn = document.querySelector('.btn-refresh');
    if (refreshBtn) {
        if (isCached) {
            refreshBtn.innerHTML = `<i class="fas fa-sync-alt"></i> Refresh (${Math.round(secondsRemaining/60)}m left)`;
            refreshBtn.style.background = 'var(--secondary)';
        } else {
            refreshBtn.innerHTML = '<i class="fas fa-sync-alt"></i> Refresh';
            refreshBtn.style.background = 'var(--accent)';
        }
    }
}

/**
 * Refresh odds (force new fetch)
 */
async function refreshOdds() {
    const btn = document.querySelector('.btn-refresh');
    btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Fetching...';
    btn.disabled = true;
    
    try {
        await loadOdds(true); // Force refresh
    } finally {
        btn.disabled = false;
        btn.innerHTML = '<i class="fas fa-sync-alt"></i> Refresh';
    }
}

// ... (keep existing functions: applyFilters, renderMatches, createMatchCard, etc.)
// But update createMatchCard to work with new data structure

/**
 * Create HTML for a match card
 */
function createMatchCard(match) {
    const bookmakers = Object.entries(match.bookmakers);
    
    // Calculate best odds
    const bestHome = Math.max(...bookmakers.map(([, odds]) => odds.home || 0));
    const bestDraw = Math.max(...bookmakers.map(([, odds]) => odds.draw || 0));
    const bestAway = Math.max(...bookmakers.map(([, odds]) => odds.away || 0));
    
    return `
        <div class="match-card" onclick="showMatchDetails('${match.id}')">
            <div class="match-info">
                <div class="match-league">${match.league || 'Unknown'}</div>
                <div class="match-teams">
                    <div class="team">
                        <div class="team-logo">${match.home_team.charAt(0)}</div>
                        <span>${match.home_team}</span>
                    </div>
                    <div class="team">
                        <div class="team-logo">${match.away_team.charAt(0)}</div>
                        <span>${match.away_team}</span>
                    </div>
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
 * Create HTML for outcome odds
 */
function createOutcomeOdds(match, outcome, bestOdds) {
    const bookmakers = Object.entries(match.bookmakers);
    
    return `
        <div class="bookmaker-odds">
            <div class="outcome-label">${outcome === 'home' ? '1' : outcome === 'draw' ? 'X' : '2'}</div>
            ${bookmakers.map(([name, odds]) => {
                const value = odds[outcome] || '-';
                const isBest = odds[outcome] === bestOdds && bookmakers.length > 1;
                return `
                    <div class="odds-row">
                        <div class="odd-cell ${isBest ? 'best-odds' : ''}">
                            ${typeof value === 'number' ? value.toFixed(2) : value}
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
async function showMatchDetails(matchId) {
    const match = state.matches.find(m => m.id === matchId);
    if (!match) return;
    
    // Fetch comparison across all bookmakers
    try {
        const response = await fetch(`${API_BASE_URL}/compare/${encodeURIComponent(match.match_name)}`);
        const result = await response.json();
        
        const modal = document.getElementById('matchModal');
        const title = document.getElementById('modalMatchTitle');
        const details = document.getElementById('modalOddsDetails');
        
        title.textContent = match.match_name;
        
        // Build detailed comparison
        details.innerHTML = `
            <div class="match-detail-section">
                <h3>Best Odds by Bookmaker</h3>
                ${createOddsComparisonTable(result.odds || [])}
            </div>
        `;
        
        modal.classList.add('active');
        
    } catch (error) {
        console.error('Error fetching match details:', error);
    }
}

/**
 * Create odds comparison table
 */
function createOddsComparisonTable(odds) {
    if (!odds || odds.length === 0) {
        return '<p>No odds data available</p>';
    }
    
    return `
        <table class="odds-comparison-table">
            <thead>
                <tr>
                    <th>Bookmaker</th>
                    <th>1</th>
                    <th>X</th>
                    <th>2</th>
                </tr>
            </thead>
            <tbody>
                ${odds.map(odd => `
                    <tr>
                        <td>${odd.bookmaker}</td>
                        <td>${odd.home_odds?.toFixed(2) || '-'}</td>
                        <td>${odd.draw_odds?.toFixed(2) || '-'}</td>
                        <td>${odd.away_odds?.toFixed(2) || '-'}</td>
                    </tr>
                `).join('')}
            </tbody>
        </table>
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
    // Search input
    const searchInput = document.getElementById('searchInput');
    searchInput.addEventListener('input', (e) => {
        state.searchQuery = e.target.value;
        applyFilters();
        renderMatches();
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
        // Reload with new bookmaker
        loadOdds();
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
}

/**
 * Apply filters and sorting
 */
function applyFilters() {
    let filtered = [...state.matches];
    
    // Filter by search
    if (state.searchQuery) {
        const query = state.searchQuery.toLowerCase();
        filtered = filtered.filter(m =>
            m.home_team.toLowerCase().includes(query) ||
            m.away_team.toLowerCase().includes(query) ||
            m.league.toLowerCase().includes(query)
        );
    }
    
    // Sort
    filtered = sortMatches(filtered);
    
    state.filteredMatches = filtered;
}

function sortMatches(matches) {
    switch (state.sortBy) {
        case 'time':
            return matches; // Keep original order
        case 'best-odds':
            return matches.sort((a, b) => {
                const aBest = Math.max(...Object.values(a.bookmakers).map(o => o.home));
                const bBest = Math.max(...Object.values(b.bookmakers).map(o => o.home));
                return bBest - aBest;
            });
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
    
    if (!state.filteredMatches || state.filteredMatches.length === 0) {
        container.innerHTML = '';
        noResults.style.display = 'flex';
        return;
    }
    
    noResults.style.display = 'none';
    container.innerHTML = state.filteredMatches.map(match => createMatchCard(match)).join('');
}

function showError(message) {
    const container = document.getElementById('matchesContainer');
    container.innerHTML = `
        <div class="no-results">
            <i class="fas fa-exclamation-circle" style="color: var(--danger);"></i>
            <p>${message}</p>
            <button onclick="loadOdds()" style="margin-top: 1rem;">Try Again</button>
        </div>
    `;
}

// Export functions for global access
window.refreshOdds = refreshOdds;
window.showMatchDetails = showMatchDetails;
window.closeModal = closeModal;
