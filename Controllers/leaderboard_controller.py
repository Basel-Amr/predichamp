from Controllers.db_controller import get_connection
from Controllers.utils import fetch_all, fetch_one
import os

def get_player_info(player_id):
    conn = get_connection()
    cur = conn.cursor()

    # Fetch player info directly from the players table
    cur.execute("""
        SELECT 
            id, 
            username, 
            email, 
            avatar_name, 
            created_at,
            COALESCE(score + bonous, 0) AS total_points,
            total_leagues_won,
            total_cups_won
        FROM players
        WHERE id = ?
    """, (player_id,))
    
    row = cur.fetchone()
    conn.close()

    if not row:
        return None

    # Fetch leaderboard to calculate rank
    leaderboard = fetch_all("""
        SELECT id, COALESCE(score + bonous, 0) AS total_points
        FROM players
        ORDER BY total_points DESC
    """)

    rank = next((index + 1 for index, entry in enumerate(leaderboard) if entry[0] == player_id), None)

    return {
        "id": row[0],
        "username": row[1],
        "email": row[2],
        "avatar_path": row[3],
        "created_at": row[4],
        "total_points": row[5],
        "total_leagues_won": row[6],
        "total_cups_won": row[7],
        "rank": rank
    }
