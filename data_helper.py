"""
Data helper module for reading and processing CSV files.
Handles CSV data loading for Fantacalcio statistics files.
Supports files named: Statistiche_Fantacalcio_Stagione_[Year].csv
"""

import os
import pandas as pd
from typing import List, Dict, Any, Tuple


# Use os.path for serverless environment compatibility
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(CURRENT_DIR, "data")
FANTACALCIO_PREFIX = "Statistiche_Fantacalcio_Stagione_"


def get_all_csv_files() -> List[Tuple[str, str]]:
    """
    Scan the data directory and return all Fantacalcio CSV files.
    Returns: List of (file_path, season) tuples sorted by season.
    
    Example: ('/path/to/data/Statistiche_Fantacalcio_Stagione_2023_24.csv', '2023-24')
    """
    if not os.path.exists(DATA_DIR):
        return []
    
    files_with_seasons = []
    
    try:
        for filename in sorted(os.listdir(DATA_DIR)):
            if filename.startswith(FANTACALCIO_PREFIX) and filename.endswith(".csv"):
                season = extract_season_from_filename(filename)
                if season:
                    file_path = os.path.join(DATA_DIR, filename)
                    files_with_seasons.append((file_path, season))
    except OSError as e:
        print(f"Error reading data directory: {e}")
    
    return files_with_seasons


def extract_season_from_filename(filename: str) -> str:
    """
    Extract season from Fantacalcio filename and format with a dash.
    E.g., 'Statistiche_Fantacalcio_Stagione_2023_24.csv' -> '2023-24'
    """
    if not filename.startswith(FANTACALCIO_PREFIX) or not filename.endswith(".csv"):
        return None
    
    season = filename[len(FANTACALCIO_PREFIX):-4]
    return season.replace("_", "-") if season else None


def load_csv_data(file_path: str) -> pd.DataFrame:
    """
    Load CSV file and clean the player name column.
    Handles CSV files with a title row that needs to be skipped.
    Uses "Nome" column for player names.
    """
    try:
        # Skip first row (title row in Fantacalcio files)
        df = pd.read_csv(file_path, skiprows=1)
        
        # Clean player names: strip whitespace
        if "Nome" in df.columns:
            df["Nome"] = df["Nome"].astype(str).str.strip()
        
        return df
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        return None


def get_all_player_names() -> List[str]:
    """
    Scan all Fantacalcio CSV files and return a unique, sorted list of player names.
    Uses the "Nome" column from the CSV files.
    """
    player_names = set()
    files_with_seasons = get_all_csv_files()
    
    for csv_file, season in files_with_seasons:
        df = load_csv_data(csv_file)
        if df is None or "Nome" not in df.columns:
            continue
        
        # Add all non-null player names
        names = df["Nome"].dropna().unique().tolist()
        player_names.update(names)
    
    return sorted(list(player_names))


def search_player_names(query: str) -> List[str]:
    """
    Search for player names matching the query (case-insensitive, partial match).
    """
    all_names = get_all_player_names()
    query_lower = query.lower().strip()
    
    if not query_lower:
        return []
    
    # Return names that contain the query string
    return [name for name in all_names if query_lower in name.lower()]


def get_player_statistics(player_name: str) -> Dict[str, Any]:
    """
    Aggregate specific statistics for a player across all Fantacalcio CSV files.
    
    Returns: {
        'player_name': str,
        'columns': ['Stagione', 'Pv', 'Mv', 'Fm', 'Gf', 'Amm', 'Esp', 'R'],
        'rows': [list of dicts with only the requested columns]
    }
    """
    all_rows = []
    files_with_seasons = get_all_csv_files()
    
    for csv_file, season in files_with_seasons:
        df = load_csv_data(csv_file)
        if df is None or "Nome" not in df.columns:
            continue
        
        # Filter for this player (case-insensitive match)
        player_df = df[df["Nome"].str.lower() == player_name.lower()].copy()
        
        if player_df.empty:
            continue
        
        # Add season column at the beginning
        player_df.insert(0, "Stagione", season)
        
        # Convert to list of dicts
        rows = player_df.to_dict(orient="records")
        all_rows.extend(rows)
    
    # Define the exact columns and order requested by the user
    columns = ["Stagione", "Pv", "Mv", "Fm", "Gf", "Amm", "Esp", "R"]
    
    # Filter the rows to keep only the requested columns
    filtered_rows = []
    for row in all_rows:
        filtered_row = {col: row.get(col, None) for col in columns}
        filtered_rows.append(filtered_row)
    
    return {
        "player_name": player_name,
        "columns": columns,
        "rows": filtered_rows,
    }