from datetime import datetime, timedelta
from Controllers.db_controller import get_connection
from Controllers.utils import fetch_all, execute_query, fetch_one
from config import API_TOKEN, BASE_URL
import requests
import os
import json

import bcrypt

# ------------------- Password Utilities ------------------- #

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode('utf-8')

def verify_password(password: str, hashed: str) -> bool:
    if isinstance(hashed, str):
        hashed = hashed.encode('utf-8')
    return bcrypt.checkpw(password.encode(), hashed)


# 📥 Get all players
def get_all_players():
    query = """
        SELECT id, username, email, role, score, bonous, total_leagues_won, total_cups_won,
               created_at, updated_at, last_login_at, is_confirmed, timezone
        FROM players
        ORDER BY created_at DESC
    """
    return fetch_all(query)

# 🔍 Get player by ID
def get_player_by_id(player_id):
    player_query = "SELECT * FROM players WHERE id = ?"
    player = fetch_one(player_query, (player_id,))

    if not player:
        return None

    score_query = "SELECT SUM(score) as total FROM predictions WHERE player_id = ?"
    score_row = fetch_one(score_query, (player_id,))
    total_prediction_score = score_row["total"] if score_row and score_row["total"] is not None else 0

    # Convert to dict if needed
    player = dict(player)
    player["total_prediction_score"] = total_prediction_score

    return player

# ✏️ Update player info (email, role, confirmed, timezone, bonous)
def update_player(player_id, email, role, is_confirmed, timezone, bonous):
    query = """
        UPDATE players
        SET email = ?, role = ?, is_confirmed = ?, timezone = ?, bonous = ?, updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
    """
    execute_query(query, (email, role, is_confirmed, timezone, bonous, player_id))

# 🔑 Reset player password
def reset_player_password(player_id, new_password):
    hashed = hash_password(new_password)
    query = "UPDATE players SET password_hash = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?"
    execute_query(query, (hashed, player_id))

# 📊 Count predictions per player
def get_prediction_count(player_id):
    query = "SELECT COUNT(*) as total FROM predictions WHERE player_id = ?"
    row = fetch_one(query, (player_id,))
    return row['total'] if row else 0

def get_player_prediction_count(player_id):
    """
    Returns the number of predictions made by a specific player.
    """
    query = "SELECT COUNT(*) as count FROM predictions WHERE player_id = ?"
    row = fetch_one(query, (player_id,))
    return row["count"] if row else 0

def get_player_round_prediction_stats(player_id):
    """
    Returns a list of rounds with counts of predicted and unpredicted matches for a given player.
    """
    query = """
        SELECT 
            r.id AS round_id,
            r.name AS round_name,
            COUNT(m.id) AS total_matches,
            COUNT(p.id) AS predicted_matches,
            COUNT(m.id) - COUNT(p.id) AS unpredicted_matches
        FROM rounds r
        JOIN matches m ON m.round_id = r.id
        LEFT JOIN predictions p ON p.match_id = m.id AND p.player_id = ?
        GROUP BY r.id
        ORDER BY r.round_number ASC
    """
    return fetch_all(query, (player_id,))

def get_all_player_predictions(player_id):
    """
    Returns all predictions made by a player along with match info, scores, and teams.
    """
    query = """
        SELECT 
            p.id AS prediction_id,
            p.predicted_home_score,
            p.predicted_away_score,
            p.score AS earned_points,
            m.match_datetime,
            t1.name AS home_team,
            t2.name AS away_team,
            m.home_score AS actual_home_score,
            m.away_score AS actual_away_score,
            r.name AS round_name,
            l.name AS league_name
        FROM predictions p
        JOIN matches m ON m.id = p.match_id
        JOIN teams t1 ON t1.id = m.home_team_id
        JOIN teams t2 ON t2.id = m.away_team_id
        JOIN rounds r ON r.id = m.round_id
        JOIN leagues l ON l.id = m.league_id
        WHERE p.player_id = ? AND m.is_predictable = 1
        ORDER BY m.match_datetime DESC
    """
    return fetch_all(query, (player_id,))

def get_next_round():
    query = """
        SELECT * FROM rounds
        WHERE prediction_deadline > CURRENT_TIMESTAMP
        ORDER BY prediction_deadline ASC
        LIMIT 1
    """
    round_info = fetch_one(query)

    if not round_info:
        return None

    # Convert sqlite3.Row to a mutable dictionary
    round_info = dict(round_info)

    # Get matches for this round
    matches = fetch_all("""
        SELECT 
            m.id,
            m.home_team_id, ht.name as home_team_name,
            m.away_team_id, at.name as away_team_name,
            m.match_datetime,
            m.home_score,
            m.away_score
        FROM matches m
        JOIN teams ht ON m.home_team_id = ht.id
        JOIN teams at ON m.away_team_id = at.id
        WHERE m.round_id = ? AND m.is_predictable = 1
        ORDER BY m.match_datetime
    """, (round_info["id"],))

    round_info["matches"] = matches
    return round_info


def get_player_predictions_for_round(player_id, round_id):
    """
    Fetches all predictions made by a player for matches in a specific round.

    Returns a list of dictionaries with:
        - prediction_id
        - match_id
        - home_team_name
        - away_team_name
        - predicted_home_score
        - predicted_away_score
        - match_datetime
        - actual_home_score
        - actual_away_score
        - stage_name
    """
    query = """
        SELECT 
            p.id AS prediction_id,
            p.match_id,
            ht.name AS home_team_name,
            at.name AS away_team_name,
            p.predicted_home_score,
            p.predicted_away_score,
            m.match_datetime,
            m.home_score AS actual_home_score,
            m.away_score AS actual_away_score,
            s.name AS stage_name
        FROM predictions p
        JOIN matches m ON p.match_id = m.id
        JOIN teams ht ON m.home_team_id = ht.id
        JOIN teams at ON m.away_team_id = at.id
        JOIN rounds r ON m.round_id = r.id
        LEFT JOIN stages s ON m.stage_id = s.id
        WHERE p.player_id = ? AND r.id = ? AND m.is_predictable = 1
        ORDER BY m.match_datetime
    """
    return fetch_all(query, (player_id, round_id))

def save_predictions_for_player(player_id, predictions: dict):
    """
    Saves predictions for a given player.

    Parameters:
    - player_id: int — The ID of the player making predictions.
    - predictions: dict — Keys are match_ids, values are {"home": int, "away": int}.

    Returns:
    - True if successful (any predictions processed), False otherwise.
    """
    saved_any = False

    for match_id, scores in predictions.items():
        home = scores.get("home")
        away = scores.get("away")

        if home is None or away is None or not str(home).isdigit() or not str(away).isdigit():
            continue

        home = int(home)
        away = int(away)

        existing = fetch_one(
            "SELECT id FROM predictions WHERE player_id = ? AND match_id = ?",
            (player_id, match_id)
        )

        if existing:
            execute_query(
                "UPDATE predictions SET predicted_home_score = ?, predicted_away_score = ?, created_at = CURRENT_TIMESTAMP WHERE id = ?",
                (home, away, existing["id"])
            )
        else:
            execute_query(
                """
                INSERT INTO predictions (player_id, match_id, predicted_home_score, predicted_away_score)
                VALUES (?, ?, ?, ?)
                """,
                (player_id, match_id, home, away)
            )
        saved_any = True  # Flag at least one successful operation

    return saved_any

def update_player_info(player):
    """
    Updates the player info in the database.
    Accepts a dict with keys: id, username, email, timezone, avatar_name, bonous, role, (optional) new_password
    Also updates the score field by summing predictions.
    """
    if not player or "id" not in player:
        return False

    # Update basic fields
    query = """
        UPDATE players
        SET username = ?, email = ?, timezone = ?, avatar_name = ?, bonous = ?, role = ?, updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
    """
    execute_query(query, (
        player['username'],
        player['email'],
        player['timezone'],
        player['avatar_name'],
        player['bonous'],
        player['role'],
        player['id']
    ))

    # If new_password is provided → hash and update
    new_password = player.get("new_password", "").strip()
    if new_password:
        hashed_pw = hash_password(new_password)
        execute_query("UPDATE players SET password_hash = ? WHERE id = ?", (hashed_pw, player['id']))

    # Recalculate total score from predictions
    score_result = fetch_one("SELECT SUM(score) as total FROM predictions WHERE player_id = ?", (player['id'],))
    total_score = score_result["total"] if score_result["total"] is not None else 0
    execute_query("UPDATE players SET score = ? WHERE id = ?", (total_score, player['id']))

    return True

def delete_player(player_id):
    try:
        execute_query("DELETE FROM players WHERE id = ?", (player_id,))
        return True
    except Exception as e:
        print(f"Error deleting player: {e}")
        return False