import requests
from Controllers.db_controller import get_connection
from Controllers.utils import fetch_all, execute_query
import os

from config import API_TOKEN, BASE_URL

HEADERS = {'X-Auth-Token': API_TOKEN}


def get_all_leagues():
    query = "SELECT id, name, country, logo_path, Trade_Name, start_date, end_date FROM leagues ORDER BY country ASC"
    return fetch_all(query)



def delete_league(league_id):
    query = "DELETE FROM leagues WHERE id = ?"
    execute_query(query, (league_id,))

def update_league_details(league_id, name, country, type_value, is_active, logo_path, trade_name, start_date, end_date):
    query = """
        UPDATE leagues
        SET name = ?, country = ?, type = ?, is_active = ?, logo_path = ?, Trade_Name = ?, start_date = ?, end_date = ?
        WHERE id = ?
    """
    execute_query(query, (
        name,
        country,
        type_value,
        is_active,
        logo_path,
        trade_name,
        start_date.isoformat() if start_date else None,
        end_date.isoformat() if end_date else None,
        league_id  # ✅ Now at the end
    ))




def insert_league(league_data):
    logo_filename = league_data.get("emblem", "").split("/")[-1]  # e.g., 'pl.png'
    code = logo_filename.split(".")[0].upper()  # Extract 'pl' → 'PL'

    # Extract start and end dates from season
    season = league_data.get("season", {})
    start_date = season.get("startDate", None)
    end_date = season.get("endDate", None)

    query = """
        INSERT OR IGNORE INTO leagues (id, name, country, logo_path, code, start_date, end_date)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """
    execute_query(query, (
        league_data["id"],
        league_data["name"],
        league_data.get("area", {}).get("name", "Unknown"),
        logo_filename,
        code,
        start_date,
        end_date
    ))



def fetch_leagues_from_api():
    url = f"{BASE_URL}/competitions"
    response = requests.get(url, headers=HEADERS)
    if response.status_code == 200:
        return response.json().get("competitions", [])
    return []

def delete_all_leagues():
    query = "DELETE FROM leagues"
    execute_query(query)

def get_stages_by_league(league_id):
    query = """
        SELECT id, name, is_two_legged, allows_draw, has_penalties
        FROM stages
        WHERE league_id = ?
        ORDER BY id ASC
    """
    return fetch_all(query, (league_id,))

def update_stage(stage_id, name, is_two_legged, allows_draw, has_penalties):
    query = """
        UPDATE stages
        SET name = ?, is_two_legged = ?, allows_draw = ?, has_penalties = ?
        WHERE id = ?
    """
    execute_query(query, (name, is_two_legged, allows_draw, has_penalties, stage_id))


def delete_stage(stage_id):
    query = "DELETE FROM stages WHERE id = ?"
    execute_query(query, (stage_id,))


def insert_stage(name, league_id):
    query = """
        INSERT OR IGNORE INTO stages (name, league_id)
        VALUES (?, ?)
    """
    execute_query(query, (name, league_id))


def get_league_logo_path(logo_filename):
    logo_dir = "Assets/Leagues"
    full_path = os.path.join(logo_dir, logo_filename)
    if os.path.exists(full_path):
        return full_path
    return None

def add_league(name, country, type_value, is_active, logo_path, code, trade_name, start_date, end_date):
    query = """
        INSERT INTO leagues (name, country, type, is_active, logo_path, code, Trade_Name, start_date, end_date)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """
    execute_query(query, (name, country, type_value, is_active, logo_path, code, trade_name, start_date, end_date))