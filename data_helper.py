"""
Data helper module for reading and processing CSV files.
Handles CSV data loading for Fantacalcio statistics files.
Supports files named: Statistiche_Fantacalcio_Stagione_[Year].csv
"""

import os
import re
import unicodedata
import pandas as pd
from typing import List, Dict, Any, Tuple, Optional
import urllib.parse


# Use os.path for serverless environment compatibility
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(CURRENT_DIR, "data")
FANTACALCIO_PREFIX = "Statistiche_Fantacalcio_Stagione_"
XG_PREFIX = "stats_"

# Mappa dei codici ruolo (colonna "R") alla dicitura estesa
ROLE_NAMES = {
    "P": "Portiere",
    "D": "Difensore",
    "C": "Centrocampista",
    "A": "Attaccante",
}

# Cache in memoria dei dati xG/xA per stagione, per evitare di rileggere il CSV ad ogni richiesta
_xg_season_cache: Dict[str, Optional[pd.DataFrame]] = {}


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


def _normalize_text(value: str) -> str:
    """
    Rimuove accenti, punteggiatura e maiuscole per confronti "fuzzy" tra nomi/squadre
    provenienti da fonti diverse (es. 'Martínez' -> 'martinez').
    """
    if not value:
        return ""
    text = str(value).strip()
    text = "".join(c for c in unicodedata.normalize("NFKD", text) if not unicodedata.combining(c))
    text = text.lower()
    text = re.sub(r"[^a-z0-9\s\-']", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _split_fantacalcio_name(nome: str) -> Tuple[str, str]:
    """
    Il campo "Nome" del Fantacalcio contiene di solito il solo cognome, a volte
    seguito da un'iniziale (una o più lettere) per distinguere gli omonimi,
    nel formato "Cognome X." (es. "Martinez L." per Lautaro, "Hernandez Th."
    per Theo). Restituisce (cognome_normalizzato, iniziale_minuscola).
    Se non è presente un'iniziale, l'iniziale restituita è "".
    """
    raw = str(nome).strip()
    match = re.match(r"^(.*?)\s+([A-Za-z]{1,3})\.$", raw)
    if match:
        surname_part, initial_part = match.groups()
        return _normalize_text(surname_part), initial_part.lower()
    return _normalize_text(raw), ""


def extract_season_from_xg_filename(filename: str) -> str:
    """
    Estrae la stagione da un file di statistiche xG/xA e la converte nello
    stesso formato usato dal Fantacalcio.
    E.g., 'stats_2020-2021.csv' -> '2020-21'
    """
    match = re.match(r"^stats_(\d{4})-(\d{4})\.csv$", filename)
    if not match:
        return None
    year_start, year_end = match.groups()
    return f"{year_start}-{year_end[2:]}"


def get_all_xg_files() -> List[Tuple[str, str]]:
    """
    Scansiona la cartella data e restituisce tutti i file di statistiche xG/xA.
    Returns: List of (file_path, season) tuples.
    """
    if not os.path.exists(DATA_DIR):
        return []

    files_with_seasons = []

    try:
        for filename in sorted(os.listdir(DATA_DIR)):
            if filename.startswith(XG_PREFIX) and filename.endswith(".csv"):
                season = extract_season_from_xg_filename(filename)
                if season:
                    files_with_seasons.append((os.path.join(DATA_DIR, filename), season))
    except OSError as e:
        print(f"Error reading data directory: {e}")

    return files_with_seasons


def _load_xg_dataframe(file_path: str) -> pd.DataFrame:
    """
    Legge un file di statistiche xG/xA (delimitato da ';', con eventuale BOM)
    e pre-calcola le colonne normalizzate usate per il matching dei nomi.
    """
    try:
        df = pd.read_csv(file_path, sep=";", encoding="utf-8-sig")
        df["player"] = df["player"].astype(str).str.strip()
        df["team"] = df["team"].astype(str).str.strip()
        df["_norm_player"] = df["player"].apply(_normalize_text)
        df["_surname"] = df["_norm_player"].apply(lambda n: n.split(" ")[-1] if n else "")
        return df
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        return None


def _get_xg_dataframe_for_season(season: str) -> Optional[pd.DataFrame]:
    """Restituisce (con cache) il dataframe xG/xA per una data stagione, se esiste."""
    if season in _xg_season_cache:
        return _xg_season_cache[season]

    df = None
    for file_path, file_season in get_all_xg_files():
        if file_season == season:
            df = _load_xg_dataframe(file_path)
            break

    _xg_season_cache[season] = df
    return df


def _teams_match(team_a: str, team_b: str) -> bool:
    """Confronto tollerante tra nomi squadra (es. 'AC Milan' contiene 'Milan')."""
    a, b = _normalize_text(team_a), _normalize_text(team_b)
    if not a or not b:
        return False
    return a in b or b in a


def _first_name_matches_initial(norm_player: str, surname: str, initial: str) -> bool:
    """
    Verifica se il "nome" (la parte di norm_player che precede il cognome)
    inizia con l'iniziale indicata dal Fantacalcio.
    Es. norm_player="lautaro martinez", surname="martinez", initial="l" -> True
        norm_player="theo hernandez", surname="hernandez", initial="th" -> True
    """
    if not initial:
        return True

    first_name_part = norm_player
    if surname and norm_player.endswith(surname):
        first_name_part = norm_player[: -len(surname)].strip()

    if not first_name_part:
        # Nessun nome davanti al cognome (es. mononimi): confronta l'intero
        # nome normalizzato, per non escludere per errore i match validi.
        first_name_part = norm_player

    return first_name_part.startswith(initial)


def get_xg_xa_for_player(player_name: str, team: str, season: str) -> Dict[str, Any]:
    """
    Cerca xG e xA di un giocatore di movimento per una data stagione, abbinando
    i dati per cognome, poi restringendo con l'iniziale del nome (quando
    presente nel Fantacalcio, es. "Martinez L.") e infine con la squadra in
    caso di residua ambiguità. Se il match resta ambiguo o non trovato,
    restituisce valori nulli invece di rischiare un abbinamento sbagliato.
    """
    df = _get_xg_dataframe_for_season(season)
    if df is None or df.empty:
        return {"Xg": None, "Xa": None}

    surname, initial = _split_fantacalcio_name(player_name)
    if not surname:
        return {"Xg": None, "Xa": None}

    candidates = df[
        (df["_norm_player"] == surname)
        | (df["_surname"] == surname)
        | df["_norm_player"].str.contains(re.escape(surname), na=False)
    ]

    if candidates.empty:
        return {"Xg": None, "Xa": None}

    if len(candidates) > 1 and initial:
        initial_filtered = candidates[
            candidates["_norm_player"].apply(lambda n: _first_name_matches_initial(n, surname, initial))
        ]
        if not initial_filtered.empty:
            candidates = initial_filtered

    if len(candidates) > 1 and team:
        team_filtered = candidates[candidates["team"].apply(lambda t: _teams_match(t, team))]
        if not team_filtered.empty:
            candidates = team_filtered

    if len(candidates) != 1:
        # Ambiguità non risolta (es. due omonimi nella stessa squadra con la
        # stessa iniziale): meglio non mostrare il dato piuttosto che
        # abbinarlo al giocatore sbagliato.
        return {"Xg": None, "Xa": None}

    row = candidates.iloc[0]
    return {"Xg": float(row["xG"]), "Xa": float(row["xA"])}


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
            "columns": ["Stagione", "Squadra", "R", "Pv", "Mv", "Fm", "Gf", "Ass", "Xg", "Xa", "Amm", "Esp"],
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

    # 3. Aggiungi xG/xA ad ogni stagione, solo per i giocatori di movimento (non portieri)
    for row in all_rows:
        row_role = str(row.get("R", "")).upper()
        if row_role != "P":
            xg_xa = get_xg_xa_for_player(row.get("Nome", player_name), row.get("Squadra"), row.get("Stagione"))
            row["Xg"] = xg_xa["Xg"]
            row["Xa"] = xg_xa["Xa"]

    # 4. Determina ruolo e squadra attuale basandoti sull'ultima riga trovata (stagione più recente)
    player_role = all_rows[-1].get("R", "").upper() if all_rows else ""
    player_team = all_rows[-1].get("Squadra") if all_rows else None

    # 5. Imposta le colonne mirate richieste (con l'aggiunta di assist, xG e xA)
    if player_role == "P":
        columns = ["Stagione", "Squadra", "R", "Pv", "Mv", "Fm", "Gs", "Rp", "Ass", "Amm", "Esp"]
    else:
        columns = ["Stagione", "Squadra", "R", "Pv", "Mv", "Fm", "Gf", "Ass", "Xg", "Xa", "Amm", "Esp"]
    
    # 6. Filtra i dati finali
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