/**
 * Search autocomplete functionality using Fetch API
 * Dynamically fetches player suggestions as user types
 */

const searchInput = document.getElementById('searchInput');
const suggestionsDropdown = document.getElementById('suggestionsDropdown');
const noResults = document.getElementById('noResults');

// Debounce timer
let debounceTimer;

/**
 * Fetch and display player suggestions
 */
async function fetchSuggestions(query) {
    if (!query || query.trim().length === 0) {
        suggestionsDropdown.classList.add('hidden');
        suggestionsDropdown.innerHTML = '';
        return;
    }

    try {
        const response = await fetch(`/api/search?q=${encodeURIComponent(query)}`);
        const data = await response.json();
        
        displaySuggestions(data.suggestions, query);
    } catch (error) {
        console.error('Error fetching suggestions:', error);
        suggestionsDropdown.classList.add('hidden');
    }
}

/**
 * Display suggestions in dropdown
 */
function displaySuggestions(suggestions, query) {
    suggestionsDropdown.innerHTML = '';
    
    if (suggestions.length === 0) {
        suggestionsDropdown.classList.add('hidden');
        return;
    }

    suggestionsDropdown.classList.remove('hidden');
    
    suggestions.forEach(name => {
        const li = document.createElement('div');
        li.className = 'suggestion-item';
        
        // Highlight the matched query part
        const regex = new RegExp(`(${query})`, 'gi');
        const highlightedName = name.replace(regex, '<strong>$1</strong>');
        
        li.innerHTML = highlightedName;
        li.addEventListener('click', () => selectSuggestion(name));
        suggestionsDropdown.appendChild(li);
    });
}

/**
 * Handle suggestion selection
 */
function selectSuggestion(playerName) {
    // Navigate to player details page
    window.location.href = `/player/${encodeURIComponent(playerName)}`;
}

/**
 * Debounced search handler
 */
function handleSearchInput(event) {
    const query = event.target.value;
    
    // Clear previous timer
    clearTimeout(debounceTimer);
    
    // Set new timer for debounced search (300ms)
    debounceTimer = setTimeout(() => {
        fetchSuggestions(query);
    }, 300);
}

/**
 * Handle Enter key press
 */
function handleSearchKeydown(event) {
    if (event.key === 'Enter') {
        event.preventDefault();
        
        const query = searchInput.value.trim();
        if (query) {
            // If there's exactly one suggestion, select it
            const items = suggestionsDropdown.querySelectorAll('.suggestion-item');
            if (items.length === 1) {
                items[0].click();
            }
        }
    }
}

/**
 * Close dropdown when clicking outside
 */
function handleClickOutside(event) {
    if (!event.target.closest('.search-box-wrapper')) {
        suggestionsDropdown.classList.add('hidden');
    }
}

// Event listeners
searchInput.addEventListener('input', handleSearchInput);
searchInput.addEventListener('keydown', handleSearchKeydown);
document.addEventListener('click', handleClickOutside);
