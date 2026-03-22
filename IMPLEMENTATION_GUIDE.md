# Fantacalcio Player Statistics App - Complete Documentation

## Overview

A Flask-based web application for searching and viewing Italian Fantacalcio player statistics across multiple seasons. The app dynamically aggregates data from multiple CSV files with varying column structures.

---

## Project Structure

```
fanta-tracker/
├── main.py                          # Flask application entry point
├── data_helper.py                   # CSV parsing and data aggregation logic
├── endpoints/
│   ├── __init__.py
│   └── routes.py                    # API endpoints
├── templates/                       # Jinja2 HTML templates
│   ├── base.html                    # Base template with navbar and footer
│   ├── index.html                   # Search page
│   └── player.html                  # Player details page with dynamic table
├── static/
│   ├── css/
│   │   └── style.css               # Responsive styling
│   └── js/
│       └── search.js               # Autocomplete search functionality
├── data/                            # CSV data files
│   └── Statistiche_Fantacalcio_Stagione_*.csv
├── requirements.txt                 # Python dependencies
├── pyproject.toml                   # Project metadata
├── vercel.json                      # Vercel deployment config
└── README.md
```

---

## Key Features

### 1. **Intelligent CSV Parsing**
- **Location**: `data_helper.py`
- **Handles**:
  - Files matching pattern: `Statistiche_Fantacalcio_Stagione_[Year].csv`
  - Skips title row (first row) automatically
  - Extracts season from filename (e.g., `2023_24` from `Statistiche_Fantacalcio_Stagione_2023_24.csv`)
  - Cleans player names (strips whitespace)
  - Uses "Nome" column for player identification

### 2. **Dynamic Column Handling**
- Different seasons may have different columns
- Backend automatically merges dataframes
- Missing values displayed as "-" in frontend
- Columns are dynamically generated based on CSV headers

### 3. **Search & Autocomplete**
- **Endpoint**: `/api/search?q=<query>`
- Real-time search as user types
- Case-insensitive partial matching
- Returns unique player names across all seasons

### 4. **Player Statistics Aggregation**
- **Endpoint**: `/api/player/<player_name>`
- Aggregates data across all seasons for a player
- Adds "Stagione" column to each record
- Returns JSON with columns and row data

---

## API Reference

### Search Endpoint
```
GET /api/search?q=<query>
```

**Response:**
```json
{
  "suggestions": [
    "Buffon",
    "Buffon G."
  ]
}
```

### Player Stats Endpoint
```
GET /api/player/<player_name>
```

**Response:**
```json
{
  "player_name": "Buffon",
  "columns": [
    "Stagione",
    "Amm",
    "Ass",
    "Au",
    "Esp",
    "Fm",
    "Gf",
    "Gs",
    ...
  ],
  "rows": [
    {
      "Stagione": "2015_16",
      "Amm": 1,
      "Ass": 0,
      "Au": 0,
      "Esp": 0,
      "Fm": 5.8,
      "Gf": 0,
      "Gs": 17,
      ...
    },
    ...
  ]
}
```

---

## Frontend Implementation

### Search Page (`templates/index.html`)
- Clean search box with placeholder text in Italian
- Dynamic dropdown with autocomplete suggestions
- Highlights matching text
- Click on suggestion navigates to player details

### Player Details Page (`templates/player.html`)
- Displays player name as heading
- Dynamically generates table based on returned columns
- First column is always "Stagione"
- Loads data via Fetch API from `/api/player/<name>` endpoint
- Shows loading message during data fetch

### JavaScript (`static/js/search.js`)
- **Debounced search**: 300ms delay to minimize API calls
- **Fetch API**: Makes HTTP requests to backend
- **Event handling**: Keyboard navigation, click outside to close dropdown
- **Highlights**: Bolds matching text in suggestions

### Styling (`static/css/style.css`)
- **Responsive design**: Mobile-first approach
- **CSS Variables**: Theming with CSS custom properties
- **Accessible colors**: Good contrast ratios
- **Smooth transitions**: Visual feedback for interactions
- **Flexbox/Grid**: Modern layout techniques

---

## Data Flow

```
1. User types in search box
   ↓
2. JavaScript debounces input (300ms)
   ↓
3. Fetch API calls GET /api/search?q=<query>
   ↓
4. Backend searches all loaded player names
   ↓
5. Returns matching suggestions
   ↓
6. JavaScript renders dropdown with highlights
   ↓
7. User clicks suggestion
   ↓
8. Navigate to /player/<name>
   ↓
9. HTML template loaded, Fetch API calls /api/player/<name>
   ↓
10. Backend fetches data from ALL CSV files for that player
    ↓
11. Dynamically merges columns and adds "Stagione" column
    ↓
12. Returns JSON with columns and rows
    ↓
13. JavaScript generates table dynamically
    ↓
14. Display aggregated statistics across all seasons
```

---

## Important Functions

### `data_helper.py`

```python
extract_season_from_filename(filename: str) -> str
# Extracts season from filename
# Example: "Statistiche_Fantacalcio_Stagione_2023_24.csv" -> "2023_24"

get_all_csv_files() -> List[Tuple[Path, str]]
# Returns list of (file_path, season) tuples

load_csv_data(file_path: Path) -> pd.DataFrame
# Loads CSV, skips header row, cleans player names

get_all_player_names() -> List[str]
# Returns unique player names across all seasons

search_player_names(query: str) -> List[str]
# Case-insensitive partial match search

get_player_statistics(player_name: str) -> Dict[str, Any]
# Aggregates all seasons for a player, returns columns and rows
```

### `endpoints/routes.py`

```python
@api_bp.get("/api/search")
# Handles autocomplete search requests

@api_bp.get("/api/player/<player_name>")
# Retrieves aggregated statistics for a player
```

---

## Deployment on Vercel

### Configuration (`vercel.json`)
```json
{
  "version": 2,
  "builds": [
    {
      "src": "main.py",
      "use": "@vercel/python"
    }
  ],
  "routes": [
    {
      "src": "/public/(.*)",
      "dest": "/public/$1"
    },
    {
      "src": "/(.*)",
      "dest": "main.py"
    }
  ]
}
```

### Environment Setup
1. Install dependencies: `pip install -r requirements.txt`
2. Place CSV files in `data/` directory
3. Deploy to Vercel: `vercel deploy`

---

## CSV File Format Expected

- **Naming Pattern**: `Statistiche_Fantacalcio_Stagione_YYYY_YY.csv`
- **First Row**: Title row (automatically skipped)
- **Second Row**: Column headers
- **Player Column**: "Nome"
- **Data Rows**: Start from row 3

### Example Structure:
```
Statistiche Fantacalcio Stagione 2023 24
Id,R,Rm,Nome,Squadra,Pv,Mv,Fm,Gf,Gs,Rp,Rc,R+,R-,Ass,Amm,Esp,Au
282,P,Por,Buffon,Juventus,35,6.21,5.8,0,17,1,0,0,0,0,1,0,0
...
```

---

## Testing

Run tests to verify data parsing:
```bash
python3 << 'EOF'
from data_helper import get_all_csv_files, get_all_player_names, search_player_names, get_player_statistics

# Get all files
files = get_all_csv_files()
print(f"Found {len(files)} seasons")

# Get players
players = get_all_player_names()
print(f"Found {len(players)} unique players")

# Search
results = search_player_names("buffon")
print(f"Search results: {results}")

# Get stats
stats = get_player_statistics("Buffon")
print(f"Found {len(stats['rows'])} season records for Buffon")
EOF
```

Start Flask dev server:
```bash
python -m flask --app main run --port 5000
```

Then test endpoints:
- Search: `http://localhost:5000/api/search?q=buffon`
- Player stats: `http://localhost:5000/api/player/Buffon`
- Home page: `http://localhost:5000/`

---

## Vercel Serverless Considerations

- **Cold starts**: First request may take 5-10 seconds as CSV files are loaded
- **Caching**: Consider implementing caching for player name lists
- **File size**: Keep total CSV data under Vercel's 50MB limit
- **Timeout**: Default 60s timeout is sufficient for data operations

---

## Future Enhancements

1. **Caching**: Add Redis caching for player lists and stats
2. **Pagination**: Paginate large result sets
3. **Filtering**: Add filters by position, season, stats threshold
4. **Export**: Add CSV/PDF export of player stats
5. **Comparison**: Compare multiple players side-by-side
6. **History**: Save search history for users

---

## Troubleshooting

### No players found
- Verify CSV files are in `data/` folder
- Check CSV filename matches pattern: `Statistiche_Fantacalcio_Stagione_*.csv`
- Verify "Nome" column exists in CSV
- Check for whitespace issues in filenames

### Search not working
- Ensure `data_helper.py` is in root directory
- Verify `get_all_player_names()` returns non-empty list
- Check browser console for JavaScript errors

### Table not displaying
- Verify API response has `columns` and `rows` arrays
- Check browser network tab for failed requests
- Ensure player name matches exactly (case-insensitive)

---

## License & Credits

Built with:
- **Backend**: Flask, Pandas
- **Frontend**: HTML5, CSS3, Vanilla JavaScript
- **Deployment**: Vercel
- **Python Version**: 3.9+
