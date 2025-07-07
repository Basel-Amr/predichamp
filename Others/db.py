# db.py
import os
import sqlite3
from dotenv import load_dotenv

load_dotenv()

DB_FILE = os.getenv("DB_FILE", "game_database.db")
DB_PASSWORD = os.getenv("DB_PASSWORD", None)  # we won't use it in sqlite for now

def get_connection():
    conn = sqlite3.connect(DB_FILE, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn
