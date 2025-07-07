from datetime import datetime, timedelta
from Controllers.db_controller import get_connection
from Controllers.utils import fetch_all, execute_query, fetch_one
from config import API_TOKEN, BASE_URL
import requests
import os
import json

HEADERS = {'X-Auth-Token': API_TOKEN}
# Popular Competitions: code -> readable name
COMPETITIONS = {
    "CL": "Champions League",
    "PL": "Premier League",
    "PD": "La Liga",
    "SA": "Serie A",
    "BL1": "Bundesliga",
    "FL1": "Ligue 1",
    "EL": "Europa League",
    "PPL": "Primeira Liga",
    "CAFCL": "CAF Champions League",        # Add if supported
    "EGYPL": "Egyptian Premier League"      # Add if supported
}
STATUS_MAP = {
    "SCHEDULED": "upcoming",
    "FINISHED": "completed",
    "IN_PLAY": "live"
}

def fetch_api(url):
    response = requests.get(url, headers=HEADERS)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"API error {response.status_code}: {response.text}")
        return None
    
def get_or_create_round_by_week(conn, match_datetime):
    weekday = match_datetime.weekday()  # Monday=0, Sunday=6
    days_to_friday = (weekday - 4) % 7
    start_date = match_datetime - timedelta(days=days_to_friday)
    start_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
    end_date = start_date + timedelta(days=6, hours=23, minutes=59)

    cur = conn.cursor()
    cur.execute("SELECT id FROM rounds WHERE start_date = ? AND end_date = ?", (start_date.date(), end_date.date()))
    row = cur.fetchone()
    if row:
        return row[0]

    cur.execute("SELECT MAX(round_number) FROM rounds")
    max_round = cur.fetchone()[0] or 0
    round_number = max_round + 1
    name = f"Round {round_number}"
    deadline = match_datetime - timedelta(hours=2)

    cur.execute("""
        INSERT INTO rounds (name, round_number, start_date, end_date, prediction_deadline)
        VALUES (?, ?, ?, ?, ?)
    """, (name, round_number, start_date.date(), end_date.date(), deadline.isoformat()))
    conn.commit()
    return cur.lastrowid

def get_league_id_by_code(conn, code):
    cur = conn.cursor()
    cur.execute("SELECT id FROM leagues WHERE code = ?", (code,))
    row = cur.fetchone()
    return row[0] if row else None

def insert_match(conn, match, league_id):
    cur = conn.cursor()

    # 1. Parse match date and skip past matches
    dt = datetime.fromisoformat(match['utcDate'].replace("Z", ""))
    if dt <= datetime.now():
        return False  # Skip past matches

    # 2. Team details
    home_id = match['homeTeam']['id']
    away_id = match['awayTeam']['id']
    api_match_id = match['id']
    matchday = match.get('matchday', 0)

    # 3. Round
    round_id = get_or_create_round_by_week(conn, dt)

    # 4. Skip if duplicate
    cur.execute("""
        SELECT id FROM matches
        WHERE home_team_id = ? AND away_team_id = ? AND match_datetime = ?
    """, (home_id, away_id, dt.isoformat()))
    if cur.fetchone():
        return False  # Match already exists

    # 5. Stage (insert if missing)
    stage_name = match.get('stage', 'REGULAR_SEASON').upper()
    stage_id = None
    cur.execute("SELECT id FROM stages WHERE name = ? AND league_id = ?", (stage_name, league_id))
    row = cur.fetchone()
    if row:
        stage_id = row[0]
    else:
        cur.execute("INSERT INTO stages (name, league_id) VALUES (?, ?)", (stage_name, league_id))
        stage_id = cur.lastrowid
        conn.commit()

    # 6. Status mapping
    status = STATUS_MAP.get(match.get('status'), 'upcoming')

    # 7. Get venue name from home team
    cur.execute("SELECT Venue_name FROM teams WHERE id = ?", (home_id,))
    venue_row = cur.fetchone()
    venue_name = venue_row[0] if venue_row and venue_row[0] else 'Unknown'

    # 8. Determine is_predictable
    is_predictable = int(
        league_id == 2021 or
        home_id in (81, 86) or
        away_id in (81, 86)
    )

    # 9. Final insert
    cur.execute("""
        INSERT INTO matches (
            round_id, league_id, home_team_id, away_team_id,
            match_datetime, status, matchday, api_match_id, stage_id, is_predictable, Venue_name
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        round_id, league_id, home_id, away_id,
        dt.isoformat(), status, matchday, api_match_id, stage_id, is_predictable, venue_name
    ))

    conn.commit()
    return True


def fetch_and_insert_matches(matchday_from=1, matchday_to=7):
    conn = get_connection()
    report = []  # (league_name, success_count, skipped_count, message)

    # === Prepare log folder & file ===
    os.makedirs("Logs", exist_ok=True)
    log_file = f"Logs/match_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"

    with open(log_file, "w", encoding="utf-8") as log:
        log.write(f"🔍 Match Fetch Log - {datetime.now()}\n")
        log.write(f"Matchday Range: {matchday_from} to {matchday_to}\n")
        log.write("=" * 60 + "\n\n")

        for code, name in COMPETITIONS.items():
            success = 0
            skipped = 0
            message = ""

            try:
                data = fetch_api(f"{BASE_URL}/competitions/{code}/matches")
            except Exception as e:
                message = f"❌ API call failed: {str(e)}"
                report.append((name, 0, 0, message))
                log.write(f"{name} ({code}): {message}\n\n")
                continue

            if not data or 'matches' not in data:
                message = "❌ Invalid competition code or empty response."
                report.append((name, 0, 0, message))
                log.write(f"{name} ({code}): {message}\n\n")
                continue

            # Save API response
            json_filename = f"Logs/{code}_matches_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(json_filename, "w", encoding="utf-8") as jf:
                json.dump(data, jf, indent=2)

            matches = data['matches']
            if not matches:
                message = "⚠️ No matches found in API."
                report.append((name, 0, 0, message))
                log.write(f"{name} ({code}): {message}\n\n")
                continue

            league_id = get_league_id_by_code(conn, code)
            if not league_id:
                message = "❗ League not found in database."
                report.append((name, 0, 0, message))
                log.write(f"{name} ({code}): {message}\n\n")
                continue

            filtered_matches = [
                match for match in matches
                if match.get('matchday') and matchday_from <= match['matchday'] <= matchday_to
            ]

            if not filtered_matches:
                message = f"⚠️ No matches in range ({matchday_from}-{matchday_to})."
                report.append((name, 0, 0, message))
                log.write(f"{name} ({code}): {message}\n\n")
                continue

            for match in filtered_matches:
                inserted = insert_match(conn, match, league_id)
                if inserted:
                    success += 1
                else:
                    skipped += 1

            if success == 0 and skipped > 0:
                message = "⚠️ All matches skipped (likely past dates or duplicates)."

            report.append((name, success, skipped, message))
            log.write(f"✅ {name} ({code}): {success} added, {skipped} skipped. {message}\n\n")

        log.write("=" * 60 + "\n")
        log.write("📄 End of log.\n")

    conn.close()
    return report

def delete_all_matches():
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("SELECT COUNT(*) FROM matches")
        count = cur.fetchone()[0]
        cur.execute("DELETE FROM matches")
        conn.commit()
        return count
    finally:
        cur.close()
        conn.close()

# Get all leagues that have at least one match
def get_leagues_with_matches():
    query = """
        SELECT DISTINCT l.id, l.name
        FROM leagues l
        JOIN matches m ON m.league_id = l.id
        ORDER BY l.name
    """
    return fetch_all(query)

# Get all rounds that contain matches for a specific league
def get_rounds_by_league(league_id):
    query = """
        SELECT r.id, r.name, r.start_date, r.end_date, COUNT(m.id) AS match_count
        FROM rounds r
        JOIN matches m ON m.round_id = r.id
        WHERE m.league_id = ?
        GROUP BY r.id, r.name, r.start_date, r.end_date
        ORDER BY r.start_date
    """
    return fetch_all(query, (league_id,))


# Get all matches in a specific round
def get_matches_by_round(round_id, league_id):
    query = """
        SELECT m.id, ht.name AS home_team, at.name AS away_team, m.match_datetime, m.status, m.is_predictable, m.Venue_name, m.matchday, m.home_score, m.away_score
        FROM matches m
        JOIN teams ht ON m.home_team_id = ht.id
        JOIN teams at ON m.away_team_id = at.id
        WHERE m.round_id = ? AND m.league_id = ?
        ORDER BY m.match_datetime
    """
    return fetch_all(query, (round_id, league_id))


# Delete all matches for a specific round
def delete_matches_by_round(round_id):
    query = "DELETE FROM matches WHERE round_id = ?"
    return execute_query(query, (round_id,))

# Delete the round itself and all matches in it
def delete_round(round_id):
    delete_matches_by_round(round_id)
    query = "DELETE FROM rounds WHERE id = ?"
    return execute_query(query, (round_id,))

# Delete all matches for a given league
def delete_matches_by_league(league_id):
    query = "DELETE FROM matches WHERE league_id = ?"
    return execute_query(query, (league_id,))

def update_match(match_id: int, field_values: dict):
    """
    Updates specified fields of a match by ID.
    :param match_id: ID of the match to update.
    :param field_values: Dictionary of fields to update and their new values.
    """
    fields = ', '.join([f"{key} = ?" for key in field_values.keys()])
    values = list(field_values.values()) + [match_id]
    
    query = f"""
    UPDATE matches
    SET {fields}, updated_at = CURRENT_TIMESTAMP
    WHERE id = ?
    """
    execute_query(query, values)


def delete_match(match_id: int):
    """
    Deletes a match by ID.
    :param match_id: ID of the match to delete.
    """
    query = "DELETE FROM matches WHERE id = ?"
    execute_query(query, [match_id])
    
def get_league_by_id(league_id):
    query = "SELECT id, name, country FROM leagues WHERE id = ?"
    return fetch_one(query, (league_id,))

def get_league_by_id(league_id):
    query = "SELECT * FROM leagues WHERE id = ?"
    return fetch_one(query, (league_id,))

def get_team_venue(team_id):
    query = "SELECT Venue_name FROM teams WHERE id = ?"
    result = fetch_one(query, (team_id,))
    return result["Venue_name"] if result and result["Venue_name"] else None

def get_or_create_stage(stage_name, league_id):
    query = "SELECT id FROM stages WHERE name = ? AND league_id = ?"
    row = fetch_one(query, (stage_name.upper(), league_id))
    if row:
        return row["id"]
    insert_query = "INSERT INTO stages (name, league_id) VALUES (?, ?)"
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(insert_query, (stage_name.upper(), league_id))
    conn.commit()
    return cur.lastrowid

def get_or_create_round_by_week(conn, match_datetime):
    date_str = match_datetime.date().isoformat()
    cur = conn.cursor()
    cur.execute("SELECT id FROM rounds WHERE ? BETWEEN start_date AND end_date", (date_str,))
    row = cur.fetchone()
    if row:
        return row[0]
    
    # If no round found, create a new one (for this week)
    start_date = match_datetime.date()
    end_date = start_date
    name = f"Matchweek {start_date.strftime('%Y-%m-%d')}"
    cur.execute("INSERT INTO rounds (name, start_date, end_date) VALUES (?, ?, ?)", (name, start_date, end_date))
    conn.commit()
    return cur.lastrowid

def delete_match_by_id(match_id: int):
    """Delete a match by its ID."""
    query = "DELETE FROM matches WHERE id = ?"
    execute_query(query, (match_id,))