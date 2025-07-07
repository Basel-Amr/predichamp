import requests
from Controllers.utils import fetch_all, execute_query, fetch_one
import os
from Controllers.db_controller import get_connection

from config import API_TOKEN, BASE_URL

HEADERS = {'X-Auth-Token': API_TOKEN}
    
# Popular Competitions: code -> readable name
COMPETITIONS = {
    "CL": "Champions League",
    "PL": "Premier League",
    "PD": "La Liga",
    "SA": "Serie A",
    "BL1": "Bundesliga",
    "FL1": "Ligue 1",
#    "WC": "World Cup",
#    "EC": "Euro Cup",
    "EL": "Europa League",
    "PPL": "Primeira Liga",
    "CAFCL": "CAF Champions League",        # Add if supported
    "EGYPL": "Egyptian Premier League"      # Add if supported
#    "DED": "Eredivisie",
#    "BSA": "Brasileirão",
#    "MLS": "Major League Soccer"
}

def get_all_leagues():
    return fetch_all("SELECT id, name, code FROM leagues ORDER BY name")

def get_teams_by_league(league_id):
    return fetch_all("SELECT id, name, tla, logo_path FROM teams WHERE id = ? ORDER BY name", (league_id,))

def get_nationalities():
    query = "SELECT DISTINCT nationality FROM teams ORDER BY nationality ASC"
    result = fetch_all(query)
    return [row["nationality"] for row in result if row["nationality"]]

def get_teams_by_nationality(selected_nationality):
    """
    Fetch all teams filtered by nationality.
    
    Args:
        selected_nationality (str): The nationality to filter teams by.

    Returns:
        List[Dict]: A list of teams with that nationality.
    """
    query = """
        SELECT id, name, official_name, tla, logo_path, nationality, Venue_name, color,venue_location,venue_capacity, color
        FROM teams
        WHERE nationality = ?
        ORDER BY name ASC
    """
    rows = fetch_all(query, (selected_nationality,))
    
    # Convert sqlite3.Row → dict manually
    return [dict(row) for row in rows]

    

def delete_teams_for_league(league_id):
    execute_query("DELETE FROM teams WHERE id = ?", (league_id,))

def delete_team(team_id):
    execute_query("DELETE FROM teams WHERE id = ?", (team_id,))

def update_team(team_id, name, tla):
    execute_query("UPDATE teams SET name = ?, tla = ? WHERE id = ?", (name, tla, team_id))

def insert_team_manual(name, official_name, tla, logo_path, nationality, venue_name="no_data"):
    conn = get_connection()
    cur = conn.cursor()
    try:
        # Get the next available ID
        cur.execute("SELECT MAX(id) FROM teams")
        last_id = cur.fetchone()[0]
        next_id = (last_id or 0) + 1

        cur.execute("""
            INSERT INTO teams (id, name, official_name, tla, logo_path, nationality, Venue_name)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (next_id, name, official_name, tla, logo_path, nationality, venue_name))
        
        conn.commit()
    finally:
        cur.close()
        conn.close()



def fetch_and_insert_teams(league_id):
    comp_code = fetch_one("SELECT code FROM leagues WHERE id = ?", (league_id,))[0]
    url = f"{BASE_URL}/competitions/{comp_code}/teams"
    resp = requests.get(url, headers=HEADERS)
    if resp.status_code != 200:
        return 0
    teams = resp.json().get("teams", [])
    count = 0
    for t in teams:
        execute_query("""
            INSERT OR IGNORE INTO teams (id, id, name, official_name, tla, logo_path, nationality)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            t['id'], league_id,
            t.get('shortName') or t['name'],
            t['name'],
            t.get('tla'),
            t.get('crest', '').split("/")[-1],
            t.get('area', {}).get('name')
        ))
        count += 1
    return count

def get_team_logo_path(filename):
    path = os.path.join("Assets", "Teams", filename)
    return path if os.path.exists(path) else None

def get_nationalities_with_team_counts():
    query = """
        SELECT nationality, COUNT(*) as count
        FROM teams
        GROUP BY nationality
        ORDER BY nationality ASC
    """
    rows = fetch_all(query)
    return {row['nationality']: row['count'] for row in rows}


def update_team_full(team_id, name, official_name, tla, logo_path, nationality, venue_name,color='#833535',venue_location='no_data',venue_capacity='no_data'):
    query = """
        UPDATE teams
        SET name = ?, official_name = ?, tla = ?, logo_path = ?, nationality = ?, Venue_name = ?, color = ?, venue_location = ?, venue_capacity = ?
        WHERE id = ?
    """
    execute_query(query, (name, official_name, tla, logo_path, nationality, venue_name,color, venue_location,venue_capacity  ,team_id))


def insert_team(conn, team):
    c = conn.cursor()
    team_id = team['id']
    
    # ✅ Check if the team with same id already exists
    c.execute("SELECT id FROM teams WHERE id = ?", (team_id,))
    row = c.fetchone()
    if row:
        return 0  # Already exists by ID

    # ✅ Check if the team with same name already exists (due to UNIQUE constraint)
    short_name = team.get('shortName', team['name'])
    official_name = team['name']
    c.execute("SELECT id FROM teams WHERE name = ?", (short_name,))
    row = c.fetchone()
    if row:
        return 0  # Already exists by name

    tla = team.get('tla')
    logo_name = team.get('crest', '').split("/")[-1]
    nationality = team.get('area', {}).get('name', 'Unknown')

    c.execute("""
        INSERT INTO teams (id, name, official_name, tla, logo_path, nationality)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (team_id, short_name, official_name, tla, logo_name, nationality))
    
    conn.commit()
    return 1  # Inserted


def fetch_api(url):
    response = requests.get(url, headers=HEADERS)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"API error {response.status_code}: {response.text}")
        return None


def fetch_all_teams_from_api():
    total_inserted = 0
    conn = get_connection()
    for code, name in COMPETITIONS.items():
        print(f"📥 Fetching teams for {name} ({code})...")
        data = fetch_api(f"{BASE_URL}/competitions/{code}/teams")
        if data:
            for team in data.get('teams', []):
                total_inserted += insert_team(conn, team)
    conn.close()
    return total_inserted


def delete_all_teams():
    query = "DELETE FROM teams"
    execute_query(query)

def delete_teams_by_nationality(nationality: str) -> int:
    """
    Deletes all teams from the database that belong to a given nationality.

    Args:
        nationality (str): The nationality to filter teams by.

    Returns:
        int: The number of teams deleted.
    """
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("SELECT COUNT(*) FROM teams WHERE nationality = ?", (nationality,))
        count = cur.fetchone()[0]

        cur.execute("DELETE FROM teams WHERE nationality = ?", (nationality,))
        conn.commit()
        return count
    finally:
        cur.close()
        conn.close()
        
