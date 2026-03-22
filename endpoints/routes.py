from flask import Blueprint, jsonify, request
from data_helper import search_player_names, get_player_statistics


api_bp = Blueprint("api", __name__)


@api_bp.get("/api/search")
def search_players():
    """
    Search for players by name (Fantacalcio statistics).
    
    Query parameter: q (search query string)
    Returns: {"suggestions": [list of matching player names]}
    """
    query = request.args.get("q", "").strip()
    
    if not query or len(query) < 1:
        return jsonify({"suggestions": []})
    
    suggestions = search_player_names(query)
    return jsonify({"suggestions": suggestions})


@api_bp.get("/api/player/<player_name>")
def get_player_stats(player_name: str):
    """
    Get all statistics for a player across all Fantacalcio CSV files.
    
    Returns: {
        "player_name": str,
        "columns": [list of column names, including "Stagione"],
        "rows": [list of data dicts with "Stagione" column added]
    }
    
    Note: Different seasons may have different columns. Missing values are None.
    """
    stats = get_player_statistics(player_name)
    return jsonify(stats)


