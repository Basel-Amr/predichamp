import os
import json
import requests
from Controllers.utils import fetch_all, fetch_one, execute_query
from Controllers.db_controller import get_connection
from config import API_TOKEN, BASE_URL
from time import sleep
import streamlit as st
import base64
import requests
from datetime import datetime
from requests.exceptions import RequestException, Timeout, ConnectionError
from datetime import datetime, timedelta

HEADERS = {'X-Auth-Token': API_TOKEN}
TEAMS_DIR = os.path.join("Assets", "Teams")
PLAYERS_DIR = os.path.join("Assets", "Players")
LOG_DIR = os.path.join("logs")
MATCHES_DIR = os.path.join("Assets", "Matches")
LOG_FILE = os.path.join(MATCHES_DIR, "fetch_log.txt")
FAILED_LOG_PATH = os.path.join(LOG_DIR, "failed_players.log")
os.makedirs(TEAMS_DIR, exist_ok=True)
os.makedirs(PLAYERS_DIR, exist_ok=True)
os.makedirs(LOG_DIR, exist_ok=True)
os.makedirs(MATCHES_DIR, exist_ok=True)

def get_logo_base64(path):
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode()
    
def update_team_info(team_id, counters):
    team_url = f"{BASE_URL}/teams/{team_id}"
    response = requests.get(team_url, headers=HEADERS)
    if response.status_code != 200:
        print(f"❌ Failed to fetch team info for team {team_id}. Status code: {response.status_code}")
        counters['failed_teams'] += 1
        return

    team_data = response.json()

    # Save JSON
    json_path = os.path.join(TEAMS_DIR, f"{team_id}.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(team_data, f, ensure_ascii=False, indent=4)

    # Download logo
    logo_url = team_data.get("crest")
    logo_path = os.path.join(TEAMS_DIR, f"{team_id}.png")
    logo_name = f"{team_id}.png"
    if logo_url:
        try:
            img_data = requests.get(logo_url).content
            with open(logo_path, 'wb') as handler:
                handler.write(img_data)
        except Exception as e:
            print(f"⚠️ Could not download logo for team {team_id}: {e}")
            logo_path = None

    # Insert or update area
    area = team_data.get("area", {})
    area_id = area.get("id")
    area_name = area.get("name")
    area_code = area.get("code")
    area_flag = area.get("flag")
    if area_id and area_name:
        execute_query("""
            INSERT INTO areas (id, name, code, flag_url)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET name=excluded.name, code=excluded.code, flag_url=excluded.flag_url
        """, (area_id, area_name, area_code, area_flag))

    # Update teams
    values = (
        team_data.get("tla"),
        team_data.get("shortName"),
        logo_name,
        area_name,
        team_data.get("venue"),
        team_data.get("clubColors"),
        team_data.get("founded"),
        team_data.get("website"),
        team_data.get("address"),
        team_id
    )
    execute_query("""
        UPDATE teams SET
            tla = ?, official_name = ?, logo_path = ?, nationality = ?,
            Venue_name = ?, club_colors = ?, founded = ?, website = ?, address = ?
        WHERE id = ?
    """, values)
    counters['updated_teams'] += 1

    # Insert or update competitions
    competitions = team_data.get("runningCompetitions", [])
    for comp in competitions:
        comp_id = comp.get("id")
        comp_name = comp.get("name")
        comp_code = comp.get("code")
        comp_type = comp.get("type", "LEAGUE")
        if comp_type == 'SUPER_CUP':
            comp_type = 'CUP'
        comp_emblem = comp.get("emblem") or ""

        if not comp_id or not comp_name:
            continue

        # Insert or update league
        execute_query("""
            INSERT INTO leagues (id, name, code, type, logo_path)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET name=excluded.name, code=excluded.code, type=excluded.type, logo_path=excluded.logo_path
        """, (comp_id, comp_name, comp_code, comp_type, comp_emblem))
        counters['inserted_leagues'] += 1

        league_info = fetch_one("SELECT start_date, end_date FROM leagues WHERE id = ?", (comp_id,))
        start_date, end_date = league_info if league_info else (None, None)

        execute_query("""
            INSERT OR IGNORE INTO team_competitions (team_id, league_id, season_start, season_end)
            VALUES (?, ?, ?, ?)
        """, (team_id, comp_id, start_date, end_date))
        counters['inserted_team_comps'] += 1

    # Insert or update players
    squad = team_data.get("squad", [])
    for player in squad:
        player_id = player.get("id")
        name = player.get("name")
        position = player.get("position")
        dob = player.get("dateOfBirth")
        nationality = player.get("nationality")
        execute_query("""
            INSERT INTO football_player (id, name, position, date_of_birth, nationality)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET name=excluded.name, position=excluded.position, date_of_birth=excluded.date_of_birth, nationality=excluded.nationality
        """, (player_id, name, position, dob, nationality))
        counters['inserted_players'] += 1

    # Insert or update coach
    coach = team_data.get("coach", {})
    if coach:
        coach_id = coach.get("id")
        if coach_id:
            execute_query("""
                INSERT INTO coaches (id, team_id, name, first_name, last_name, date_of_birth, nationality, contract_start, contract_until)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET team_id=excluded.team_id, name=excluded.name, first_name=excluded.first_name,
                last_name=excluded.last_name, date_of_birth=excluded.date_of_birth, nationality=excluded.nationality,
                contract_start=excluded.contract_start, contract_until=excluded.contract_until
            """, (
                coach_id, team_id, coach.get("name"), coach.get("firstName"), coach.get("lastName"),
                coach.get("dateOfBirth"), coach.get("nationality"),
                coach.get("contract", {}).get("start"), coach.get("contract", {}).get("until")
            ))
            counters['inserted_coaches'] += 1

    print(f"✅ Team {team_id} updated successfully.")
    
def update_all_teams():
    conn = get_connection()
    teams = fetch_all("SELECT id FROM teams")
    if not teams:
        print("No teams found in the database.")
        return

    counters = {
        'updated_teams': 0,
        'failed_teams': 0,
        'inserted_leagues': 0,
        'inserted_team_comps': 0,
        'inserted_players': 0,
        'inserted_coaches': 0
    }

    for (team_id,) in teams:
        update_team_info(team_id, counters)
        sleep(5)

    print("\n📊 Update Summary:")
    print(f"  ✔️ Teams updated: {counters['updated_teams']}")
    print(f"  ❌ Teams failed: {counters['failed_teams']}")
    print(f"  🏆 Leagues inserted/updated: {counters['inserted_leagues']}")
    print(f"  🔗 Team-Competition links inserted: {counters['inserted_team_comps']}")
    print(f"  👟 Players inserted/updated: {counters['inserted_players']}")
    print(f"  🎓 Coaches inserted/updated: {counters['inserted_coaches']}")

def log_failed_player(player_id, player_name=None, reason=None):
    with open(FAILED_LOG_PATH, "a", encoding="utf-8") as log_file:
        timestamp = datetime.now().strftime("[%Y-%m-%d %H:%M:%S]")
        name_display = player_name or f"ID: {player_id}"
        message = f"{timestamp} ❌ Failed: {name_display}"
        if reason:
            message += f" - Reason: {reason}"
        log_file.write(message + "\n")

def update_football_player_info(player_id, counters):
    player_url = f"{BASE_URL}/persons/{player_id}"

    try:
        res = requests.get(player_url, headers=HEADERS, timeout=10)
        res.raise_for_status()
    except (Timeout, ConnectionError, RequestException) as e:
        log_failed_player(player_id, reason=str(e))
        return

    try:
        player_data = res.json()
        player_name = player_data.get("name", "Unknown")
    except Exception as e:
        log_failed_player(player_id, reason=f"Invalid JSON - {e}")
        return

    # Save JSON
    try:
        player_path = os.path.join(PLAYERS_DIR, f"{player_id}.json")
        with open(player_path, "w", encoding="utf-8") as f:
            json.dump(player_data, f, ensure_ascii=False, indent=4)
    except Exception as e:
        log_failed_player(player_id, player_name, reason=f"JSON save failed - {e}")
        return

    current_team = player_data.get("currentTeam", {})
    current_area = current_team.get("area", {}) if current_team else {}
    contract_start = current_team.get("contract", {}).get("start")
    contract_until = current_team.get("contract", {}).get("until")

    try:
        execute_query("""
            INSERT INTO football_player (
                id, name, first_name, last_name, date_of_birth, nationality,
                section, position, shirt_number, team_id,
                area_id, team_name, team_crest, contract_start, contract_until
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                name=excluded.name, first_name=excluded.first_name, last_name=excluded.last_name,
                date_of_birth=excluded.date_of_birth, nationality=excluded.nationality,
                section=excluded.section, position=excluded.position, shirt_number=excluded.shirt_number,
                team_id=excluded.team_id, area_id=excluded.area_id,
                team_name=excluded.team_name, team_crest=excluded.team_crest,
                contract_start=excluded.contract_start, contract_until=excluded.contract_until
        """, (
            player_data.get("id"),
            player_data.get("name"),
            player_data.get("firstName"),
            player_data.get("lastName"),
            player_data.get("dateOfBirth"),
            player_data.get("nationality"),
            player_data.get("section"),
            player_data.get("position"),
            player_data.get("shirtNumber"),
            current_team.get("id"),
            current_area.get("id"),
            current_team.get("name"),
            current_team.get("crest"),
            contract_start,
            contract_until
        ))
        counters['inserted_players'] += 1
    except Exception as e:
        log_failed_player(player_id, player_name, reason=f"DB insert failed - {e}")

def update_all_players():
    all_players = fetch_all("SELECT DISTINCT id FROM football_player")
    total = len(all_players)
    counters = {'inserted_players': 0}

    if total == 0:
        st.warning("⚠️ No players found in the database.")
        return

    st.markdown("### 👟 Updating Football Players")
    progress_bar = st.progress(0)
    status_text = st.empty()

    for idx, (player_id,) in enumerate(all_players, 1):
        sleep(6)
        update_football_player_info(player_id, counters)

        percent = int((idx / total) * 100)
        progress_bar.progress(percent)
        status_text.text(f"Updating player {idx}/{total} (ID: {player_id})...")

    st.success(f"✅ Finished updating all players. Total players updated: {counters['inserted_players']}")

# Matches Part
STATUS_MAP = {
    "SCHEDULED": "upcoming",
    "FINISHED": "completed",
    "IN_PLAY": "live"
}

# === Round Helper ===
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

# === Match Insert ===
def insert_match_with_score(conn, match, league_id):
    cur = conn.cursor()
    dt = datetime.fromisoformat(match['utcDate'].replace("Z", ""))

    # Check duplicate
    cur.execute("""
        SELECT id FROM matches
        WHERE home_team_id = ? AND away_team_id = ? AND match_datetime = ?
    """, (match['homeTeam']['id'], match['awayTeam']['id'], dt.isoformat()))
    if cur.fetchone():
        return False

    # Round link
    round_id = get_or_create_round_by_week(conn, dt)

    # Stage
    stage_name = match.get('stage', 'REGULAR_SEASON').upper()
    cur.execute("SELECT id FROM stages WHERE name = ? AND league_id = ?", (stage_name, league_id))
    row = cur.fetchone()
    if row:
        stage_id = row[0]
    else:
        cur.execute("INSERT INTO stages (name, league_id) VALUES (?, ?)", (stage_name, league_id))
        stage_id = cur.lastrowid
        conn.commit()

    # Venue
    cur.execute("SELECT Venue_name FROM teams WHERE id = ?", (match['homeTeam']['id'],))
    venue_row = cur.fetchone()
    venue_name = venue_row[0] if venue_row and venue_row[0] else 'Unknown'

    # Match status
    status = STATUS_MAP.get(match.get("status"), "upcoming")
    is_predictable = int(
        league_id == 2021 or
        match['homeTeam']['id'] in (81, 86) or
        match['awayTeam']['id'] in (81, 86)
    )

    # Scores
    full_time = match.get("score", {}).get("fullTime", {})
    home_score = full_time.get("home")
    away_score = full_time.get("away")

    # Insert match
    cur.execute("""
        INSERT INTO matches (
            round_id, league_id, home_team_id, away_team_id,
            match_datetime, status, matchday, api_match_id,
            stage_id, is_predictable, Venue_name,
            home_score, away_score
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        round_id, league_id,
        match['homeTeam']['id'], match['awayTeam']['id'],
        dt.isoformat(), status, match.get("matchday", 0), match.get("id"),
        stage_id, is_predictable, venue_name,
        home_score, away_score
    ))

    conn.commit()
    return True

def log_message(msg):
    log_file = os.path.join(MATCHES_DIR, "match_fetch_log.txt")
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {msg}\n")
    print(msg)

# === Fetch One League ===
def fetch_league_matches(league_code, counters, total):
    url = f"{BASE_URL}/competitions/{league_code}/matches?season=2025"
    try:
        res = requests.get(url, headers=HEADERS, timeout=20)
        res.raise_for_status()
        data = res.json()

        # Save raw JSON
        raw_path = os.path.join(MATCHES_DIR, f"{league_code}_raw.json")
        with open(raw_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)

        # Process matches
        conn = get_connection()
        league_id = fetch_one("SELECT id FROM leagues WHERE code = ?", (league_code,))['id']
        inserted_matches = []

        for m in data.get("matches", []):
            match_obj = {
                "id": m.get("id"),
                "matchday": m.get("matchday"),
                "utcDate": m.get("utcDate"),
                "status": m.get("status"),
                "stage": m.get("stage"),
                "homeTeam": m["homeTeam"],
                "awayTeam": m["awayTeam"],
                "score": m.get("score")
            }
            inserted = insert_match_with_score(conn, match_obj, league_id)
            if inserted:
                inserted_matches.append(match_obj)

        conn.close()

        # Save simplified JSON
        simplified_path = os.path.join(MATCHES_DIR, f"{league_code}_matches.json")
        with open(simplified_path, "w", encoding="utf-8") as f:
            json.dump(inserted_matches, f, indent=4)

        counters['success'] += 1
        log_message(f"✅ {league_code}: {len(inserted_matches)} matches inserted.")

    except RequestException as e:
        counters['failed'] += 1
        log_message(f"❌ Failed {league_code} - {e}")

# === Fetch All Selected Leagues ===
def fetch_all_target_leagues(target_league_codes):
    total = len(target_league_codes)
    counters = {"success": 0, "failed": 0}
    progress_text = st.empty()
    progress_bar = st.progress(0)

    for idx, code in enumerate(target_league_codes):
        fetch_league_matches(code, counters, total)
        progress = (idx + 1) / total
        progress_bar.progress(progress)
        progress_text.markdown(f"⚽ `{code}`: {idx + 1}/{total} completed")
        sleep(1.5)

    st.success(f"✅ Done! {counters['success']} leagues inserted. ❌ {counters['failed']} failed.")
    st.balloons()
    log_message("🎯 All leagues fetched and saved.")