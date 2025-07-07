# utils.py
import bcrypt
from Controllers.db_controller import get_connection

# ------------------- Password Utilities ------------------- #

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode('utf-8')

def verify_password(password: str, hashed: str) -> bool:
    if isinstance(hashed, str):
        hashed = hashed.encode('utf-8')
    return bcrypt.checkpw(password.encode(), hashed)

# ------------------- Database Utilities ------------------- #

def execute_query(query, params=(), dict_cursor=False):
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute(query, params)
        conn.commit() 
        return conn, cur
    finally:
        cur.close()
        conn.close()


def fetch_one(query: str, params: tuple = (), dict_cursor=False):
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute(query, params)
        return cur.fetchone()
    finally:
        cur.close()
        conn.close()

def fetch_all(query: str, params: tuple = (), dict_cursor=False):
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute(query, params)
        return cur.fetchall()
    finally:
        cur.close()
        conn.close()



# ------------------- Helper Functions ------------------- #

def get_team_id_by_name(teams: list, team_name: str):
    return next((team['id'] for team in teams if team['name'] == team_name), None)
