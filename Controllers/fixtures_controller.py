import os
from Controllers.utils import fetch_one, fetch_all, execute_query 
import datetime
from datetime import datetime
from Controllers.db_controller import get_connection
import logging

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
        
def get_upcoming_fixtures_grouped():
    query = """
        SELECT 
            DATE(m.match_datetime) AS match_date,
            l.name AS league_name,
            l.country AS nationality,
            s.name AS stage_name,
            m.matchday,
            m.match_datetime,
            m.status,
            m.api_match_id AS match_id,
            m.home_score,
            m.away_score,
            m.Venue_name,
            ht.name AS home_team,
            at.name AS away_team,
            ht.color AS home_color,
            at.color AS away_color,
            ht.logo_path AS home_logo,
            at.logo_path AS away_logo
        FROM matches m
        JOIN leagues l ON m.league_id = l.id
        JOIN teams ht ON m.home_team_id = ht.id
        JOIN teams at ON m.away_team_id = at.id
        LEFT JOIN stages s ON m.stage_id = s.id
        ORDER BY match_date ASC, l.name ASC, m.match_datetime ASC
    """
    rows = fetch_all(query)

    grouped = {}
    for row in rows:
        match_date = row["match_date"]
        league = row["league_name"]

        if match_date not in grouped:
            grouped[match_date] = {}

        if league not in grouped[match_date]:
            grouped[match_date][league] = []

        grouped[match_date][league].append(dict(row))

    return grouped

def get_league_dates(league_name):
    query = """
        SELECT start_date, end_date
        FROM leagues
        WHERE name = ?
        LIMIT 1
    """
    row = fetch_one(query, (league_name,))
    return (row['start_date'], row['end_date']) if row else (None, None)


def calculate_league_progress(start_date, end_date):
    """
    Calculates the percentage of the league completed based on the start and end dates.

    Parameters:
        start_date (str): Start date in 'YYYY-MM-DD' format.
        end_date (str): End date in 'YYYY-MM-DD' format.

    Returns:
        tuple: (progress_percent: float, start_fmt: str, end_fmt: str)
               or (0.0, formatted_start, formatted_end) if today is before start.
    """
    try:
        start = datetime.strptime(start_date, "%Y-%m-%d").date()
        end = datetime.strptime(end_date, "%Y-%m-%d").date()
        today = datetime.now().date()

        if start >= end:
            logging.warning(f"Invalid date range: start={start}, end={end}")
            return 0.0, start.strftime("%d %b"), end.strftime("%d %b")

        total_days = (end - start).days
        elapsed = (today - start).days

        # Cap elapsed at [0, total_days]
        elapsed = max(0, min(elapsed, total_days))

        progress = (elapsed / total_days) * 100

        return round(progress, 2), start.strftime("%d %b"), end.strftime("%d %b")

    except ValueError as ve:
        logging.error(f"ValueError in calculate_league_progress: {ve}")
    except Exception as e:
        logging.error(f"Unhandled error in calculate_league_progress: {e}")

    # Fallback
    return 0.0, "N/A", "N/A"