import os
import bcrypt
from PIL import Image
from Controllers.utils import fetch_one, fetch_all, execute_query 
import datetime
from datetime import datetime
import pytz
from tzlocal import get_localzone_name
from Controllers.db_controller import get_connection

def get_localzone_for_player(player_id: int):
    """
    Returns the player's timezone as a pytz.timezone object
    based on the `timezone` field in the `players` table.
    
    Raises:
        RuntimeError: if timezone is not found or invalid.
    """
    row = fetch_one("SELECT timezone FROM players WHERE id = ?", (player_id,))
    
    if not row or not row["timezone"]:
        raise RuntimeError("⚠️ Timezone not found for this player in the database.")

    try:
        return pytz.timezone(row["timezone"])
    except pytz.UnknownTimeZoneError:
        raise RuntimeError(f"❌ Invalid timezone: {row['timezone']}")
    

def get_upcoming_predictable_fixtures_grouped_by_round():
    query = """
        SELECT 
            r.id AS round_id,
            r.name AS round_name,
            r.round_number,
            r.prediction_deadline,
            DATE(m.match_datetime) AS match_date,
            l.name AS league_name,
            l.country AS nationality,
            s.name AS stage_name,
            m.matchday,
            m.match_datetime,
            m.status,
            m.home_score,
            m.away_score,
            m.Venue_name,
            m.id,
            ht.name AS home_team,
            at.name AS away_team,
            ht.color AS home_color,
            at.color AS away_color,
            ht.logo_path AS home_logo,
            at.logo_path AS away_logo
        FROM matches m
        JOIN rounds r ON m.round_id = r.id
        JOIN leagues l ON m.league_id = l.id
        JOIN teams ht ON m.home_team_id = ht.id
        JOIN teams at ON m.away_team_id = at.id
        LEFT JOIN stages s ON m.stage_id = s.id
        WHERE m.is_predictable = 1
        ORDER BY r.round_number ASC, m.match_datetime ASC
    """
    rows = fetch_all(query)

    grouped = {}
    for row in rows:
        round_id = row["round_id"]

        if round_id not in grouped:
            grouped[round_id] = {
                "round_id": round_id,
                "round_name": row["round_name"],
                "round_number": row["round_number"],
                "deadline": row["prediction_deadline"],
                "matches": [],
                "match_count": 0 
            }

        grouped[round_id]["matches"].append(dict(row))
        grouped[round_id]["match_count"] += 1

    return grouped




def get_round_deadline(round_id):
    query = "SELECT prediction_deadline FROM rounds WHERE id = ?"
    result = fetch_one(query, (round_id,))
    return result['prediction_deadline'] if result else None


def get_local_deadline(utc_deadline_str):
    """
    Convert a UTC datetime string from the DB to the user's local timezone.

    Args:
        utc_deadline_str (str): UTC datetime in ISO format, e.g., '2025-07-10T18:00:00Z' or '2025-07-10 18:00:00'

    Returns:
        datetime: Local timezone-aware datetime object
    """
    # Handle both 'Z' format and space-separated format
    try:
        # Try parsing ISO 8601 with Z
        if utc_deadline_str.endswith('Z'):
            utc_dt = datetime.strptime(utc_deadline_str, '%Y-%m-%dT%H:%M:%SZ')
        else:
            utc_dt = datetime.fromisoformat(utc_deadline_str)
    except Exception as e:
        raise ValueError(f"Invalid UTC datetime format: {utc_deadline_str}") from e

    # Set timezone to UTC explicitly
    utc_zone = pytz.utc
    utc_dt = utc_zone.localize(utc_dt)

    # Convert to user's local timezone
    local_tz = get_localzone()
    local_dt = utc_dt.astimezone(local_tz)

    return local_dt

def get_logo_path_from_league(league_name: str) -> str:
    """
    Given a league name, return the relative logo path if it exists.
    The image is assumed to be stored in Assets/Leagues/ with the filename matching 'logo_path' in the DB.

    Args:
        league_name (str): The name of the league.

    Returns:
        str: The relative path to the logo image, or an empty string if not found.
    """
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT logo_path FROM leagues WHERE name = ?", (league_name,))
        row = cur.fetchone()
        if row and row[0]:
            filename = row[0]
            file_path = os.path.join("Assets", "Leagues", filename)
            if os.path.exists(file_path):
                return file_path.replace("\\", "/")  # Ensure compatibility for web use
        return ""
    finally:
        conn.close()
        
def get_league_dates(league_name):
    query = """
        SELECT start_date, end_date
        FROM leagues
        WHERE name = ?
        LIMIT 1
    """
    row = fetch_one(query, (league_name,))
    return (row['start_date'], row['end_date']) if row else (None, None)


def calculate_league_progress(start_date_str, end_date_str):
    try:
        start = datetime.strptime(start_date_str, "%Y-%m-%d")
        end = datetime.strptime(end_date_str, "%Y-%m-%d")
        today = datetime.today()

        if today < start:
            return 0, start.strftime("%b %d, %Y"), end.strftime("%b %d, %Y")

        total_days = (end - start).days
        passed_days = (today - start).days
        progress = min(100, (passed_days / total_days) * 100)

        return progress, start.strftime("%b %d, %Y"), end.strftime("%b %d, %Y")
    except Exception as e:
        return None, None, None
    
    
# Prediction Part
def save_prediction(player_id, match_id, home_score, away_score, penalty_winner_id=None):
    """
    Inserts or updates a prediction for a specific player and match.
    Ensures uniqueness via (player_id, match_id).
    """
    # First check if a prediction already exists
    check_query = """
        SELECT id FROM predictions WHERE player_id = ? AND match_id = ?
    """
    existing = fetch_one(check_query, (player_id, match_id))

    if existing:
        # Update existing prediction
        update_query = """
            UPDATE predictions
            SET predicted_home_score = ?, predicted_away_score = ?, predicted_penalty_winner_id = ?
            WHERE player_id = ? AND match_id = ?
        """
        execute_query(update_query, (
            home_score,
            away_score,
            penalty_winner_id,
            player_id,
            match_id
        ))
    else:
        # Insert new prediction
        insert_query = """
            INSERT INTO predictions (player_id, match_id, predicted_home_score, predicted_away_score, predicted_penalty_winner_id)
            VALUES (?, ?, ?, ?, ?)
        """
        execute_query(insert_query, (
            player_id,
            match_id,
            home_score,
            away_score,
            penalty_winner_id
        ))
        
def get_existing_prediction(player_id, match_id):
    query = """
        SELECT 
            p.id AS prediction_id,
            p.player_id,
            p.match_id,
            p.predicted_home_score,
            p.predicted_away_score,
            p.predicted_penalty_winner_id,
            p.score,
            p.created_at AS prediction_created_at,
            
            m.round_id,
            m.league_id,
            m.home_team_id,
            m.away_team_id,
            m.match_datetime,
            m.status,
            m.home_score,
            m.away_score,
            m.stage_id,
            m.penalty_winner,
            m.is_predictable,
            m.created_at AS match_created_at,
            m.updated_at AS match_updated_at,
            m.matchday,
            m.Venue_Name,
            m.api_match_id,
            
            ht.name AS home_team,
            at.name AS away_team,
            ht.color AS home_color,
            at.color AS away_color
            
        FROM predictions p
        JOIN matches m ON p.match_id = m.id
        JOIN teams ht ON m.home_team_id = ht.id
        JOIN teams at ON m.away_team_id = at.id
        WHERE p.player_id = ? AND p.match_id = ?
    """
    return fetch_one(query, (player_id, match_id))



def get_prediction_type(match_id):
    """
    Returns a simplified label for the prediction type:
    - DRAW_SINGLE
    - DRAW_SINGLE_PEN
    - DRAW_TWO_LEG_PEN
    """
    query = """
        SELECT
            COALESCE(s.allows_draw, 1) AS allows_draw,
            COALESCE(s.has_penalties, 0) AS has_penalties,
            COALESCE(s.is_two_legged, 0) AS is_two_legged
        FROM matches m
        LEFT JOIN stages s ON m.stage_id = s.id
        WHERE m.id = ?
    """
    row = fetch_one(query, (match_id,))
    if not row:
        return None  # Or raise an exception or return "UNKNOWN"

    allows_draw = bool(row["allows_draw"])
    has_penalties = bool(row["has_penalties"])
    is_two_legged = bool(row["is_two_legged"])

    if allows_draw and not has_penalties and not is_two_legged:
        return "DRAW_SINGLE"
    elif allows_draw and has_penalties and not is_two_legged:
        return "DRAW_SINGLE_PEN"
    elif allows_draw and has_penalties and is_two_legged:
        return "DRAW_TWO_LEG_PEN"

    return None  # You may want to handle this as "NOT_ALLOWED"


# Email Reminder
def get_next_round_info():
    now_str = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")  # UTC now as string

    # Get next round info where prediction deadline > now
    round_query = """
        SELECT id, name, prediction_deadline
        FROM rounds
        WHERE prediction_deadline > ?
        ORDER BY prediction_deadline ASC
        LIMIT 1
    """
    next_round = fetch_one(round_query, (now_str,))
    if not next_round:
        return None

    round_id = next_round['id']
    round_name = next_round['name']
    deadline = next_round['prediction_deadline']

    # Convert deadline to datetime object if needed
    if isinstance(deadline, str):
        try:
            deadline = datetime.fromisoformat(deadline)
        except Exception:
            deadline = datetime.strptime(deadline, "%Y-%m-%d %H:%M:%S")

    # Get first match datetime of only predictable matches in that round
    match_time_query = """
        SELECT MIN(match_datetime) AS first_match_time
        FROM matches
        WHERE round_id = ? AND is_predictable = 1
    """
    match_time_row = fetch_one(match_time_query, (round_id,))
    first_match_time = match_time_row['first_match_time'] if match_time_row else None

    if isinstance(first_match_time, str):
        try:
            first_match_time = datetime.fromisoformat(first_match_time)
        except Exception:
            first_match_time = datetime.strptime(first_match_time, "%Y-%m-%d %H:%M:%S")

    # Count only predictable matches in this round
    count_query = """
        SELECT COUNT(*) AS match_count
        FROM matches
        WHERE round_id = ? AND is_predictable = 1
    """
    count_row = fetch_one(count_query, (round_id,))
    match_count = count_row['match_count'] if count_row else 0

    return {
        "round_id": round_id,
        "round_name": round_name,
        "deadline": deadline,
        "first_match_time": first_match_time,
        "match_count": match_count
    }


def get_matches_for_round(round_id):
    query = """
        SELECT m.id, ht.name AS home_team, at.name AS away_team
        FROM matches m
        JOIN teams ht ON m.home_team_id = ht.id
        JOIN teams at ON m.away_team_id = at.id
        WHERE m.round_id = ? AND m.is_predictable = 1
        ORDER BY m.match_datetime ASC
    """
    return fetch_all(query, (round_id,))


def get_predicted_matches_for_player(player_id, round_id):
    query = """
        SELECT p.match_id, ht.name AS home_team, at.name AS away_team
        FROM predictions p
        JOIN matches m ON p.match_id = m.id
        JOIN teams ht ON m.home_team_id = ht.id
        JOIN teams at ON m.away_team_id = at.id
        WHERE p.player_id = ? AND m.round_id = ? AND m.is_predictable = 1
    """
    result = fetch_all(query, (player_id, round_id))
    return result

def get_prediction_stats_for_player(player_id, round_id):
    """
    Returns the count of predicted and unpredicted matches for a player in a given round.
    
    Parameters:
        player_id (int): The ID of the player.
        round_id (int): The ID of the round.
    
    Returns:
        tuple: (predicted_count, unpredicted_count)
    """
    # Count predicted matches
    predicted_query = """
        SELECT COUNT(*) 
        FROM predictions p
        JOIN matches m ON p.match_id = m.id
        WHERE p.player_id = ? AND m.round_id = ? AND m.is_predictable = 1
    """
    
    # Count total predictable matches for the round
    total_query = """
        SELECT COUNT(*) 
        FROM matches 
        WHERE round_id = ? AND is_predictable = 1
    """

    predicted_count = fetch_one(predicted_query, (player_id, round_id))[0]
    total_predictable = fetch_one(total_query, (round_id,))[0]

    unpredicted_count = total_predictable - predicted_count

    return predicted_count, unpredicted_count


def get_player_id_by_username(username: str) -> int | None:
    """
    Returns the player ID for a given username.
    Returns None if the username does not exist.
    """
    query = "SELECT id FROM players WHERE username = ? LIMIT 1"
    row = fetch_one(query, (username,))
    if row:
        return row['id']
    return None