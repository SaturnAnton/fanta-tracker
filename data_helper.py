"""
Data helper module for reading and processing CSV files.
Handles CSV data loading for Fantacalcio statistics files.
Supports files named: Statistiche_Fantacalcio_Stagione_[Year].csv
"""

import os
import pandas as pd
from typing import List, Dict, Any, Tuple
import urllib.parse


# Use os.path for serverless environment compatibility
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(CURRENT_DIR, "data")
FANTACALCIO_PREFIX = "Statistiche_Fantacalcio_Stagione_"

# Mappa dei codici ruolo (colonna "R") alla dicitura estesa
ROLE_NAMES = {
    "P": "Portiere",
    "D": "Difensore",
    "C": "Centrocampista",
    "A": "Attaccante",
}


def get_all_csv_files() -> List[Tuple[str, str]]:
    """
    Scan the data directory and return all Fantacalcio CSV files.
    Returns: List of (file_path, season) tuples sorted by season.
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
    """
    try:
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
    """
    player_names = set()
    files_with_seasons = get_all_csv_files()
    
    for csv_file, _ in files_with_seasons:
        df = load_csv_data(csv_file)
        if df is None or "Nome" not in df.columns:
            continue
        
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
    
    return [name for name in all_names if query_lower in name.lower()]


def _find_player_id_by_name(player_name: str) -> int:
    """
    Helper function to find the unique ID of a player given their name.
    Scans from the most recent file backwards to get the latest valid ID.
    """
    player_name = urllib.parse.unquote(player_name)
    files_with_seasons = reversed(get_all_csv_files()) # Partiamo dai file più recenti
    
    for csv_file, _ in files_with_seasons:
        df = load_csv_data(csv_file)
        if df is None or "Nome" not in df.columns or "Id" not in df.columns:
            continue
        
        # Cerca il match del nome
        match = df[df["Nome"].str.lower() == player_name.lower()]
        if not match.empty:
            return int(match.iloc[0]["Id"])
            
    return None


def get_player_statistics(player_name: str) -> Dict[str, Any]:
    """
    Aggregate specific statistics for a player across all files using their unique ID.
    Dynamically adjusts columns for Goalkeepers (P) vs Outfield players.
    """
    player_name = urllib.parse.unquote(player_name)
    player_id = _find_player_id_by_name(player_name)
    
    if player_id is None:
        return {
            "player_name": player_name,
            "role": "",
            "role_extended": "",
            "team": None,
            "columns": ["Stagione", "Squadra", "R", "Pv", "Mv", "Fm", "Gf", "Ass", "Amm", "Esp"],
            "rows": [],
        }
        
    all_rows = []
    files_with_seasons = get_all_csv_files()
    
    # 2. Cerca in tutti i file usando l'ID invece del nome
    for csv_file, season in files_with_seasons:
        df = load_csv_data(csv_file)
        if df is None or "Id" not in df.columns:
            continue
        
        # Filtro per ID (sicuro al 100% anche se ha cambiato nome nel file)
        player_df = df[df["Id"] == player_id].copy()
        
        if player_df.empty:
            continue
        
        # Aggiungi colonna Stagione
        player_df.insert(0, "Stagione", season)
        
        rows = player_df.to_dict(orient="records")
        all_rows.extend(rows)
    
    # 3. Determina ruolo e squadra attuale basandoti sull'ultima riga trovata (stagione più recente)
    player_role = all_rows[-1].get("R", "").upper() if all_rows else ""
    player_team = all_rows[-1].get("Squadra") if all_rows else None

    # 4. Imposta le colonne mirate richieste (con l'aggiunta degli assist)
    if player_role == "P":
        columns = ["Stagione", "Squadra", "R", "Pv", "Mv", "Fm", "Gs", "Rp", "Ass", "Amm", "Esp"]
    else:
        columns = ["Stagione", "Squadra", "R", "Pv", "Mv", "Fm", "Gf", "Ass", "Amm", "Esp"]
    
    # 5. Filtra i dati finali
    filtered_rows = []
    for row in all_rows:
        filtered_row = {col: row.get(col, None) for col in columns}
        filtered_rows.append(filtered_row)
    
    return {
        "player_name": player_name,
        "role": player_role,
        "role_extended": ROLE_NAMES.get(player_role, player_role),
        "team": player_team,
        "columns": columns,
        "rows": filtered_rows,
    }