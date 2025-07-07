import os
import bcrypt
from PIL import Image
from Controllers.utils import fetch_one, fetch_all, execute_query 
import datetime
from datetime import datetime

# ------------------- Player Retrieval ------------------- #

def get_player_info(player_id):
    # Get the current player's basic info and total points
    row = fetch_one("""
        SELECT 
            id, username, email, avatar_name, created_at,
            total_leagues_won, total_cups_won, 
            (SELECT COALESCE(SUM(score), 0) FROM predictions WHERE player_id = players.id) AS total_points
        FROM players 
        WHERE id = ?
    """, (player_id,))
    
    if not row:
        return None

    player_points = row[7]

    # Get leaderboard (all players with total points, sorted descending)
    leaderboard = fetch_all("""
        SELECT id, 
               (SELECT COALESCE(SUM(score), 0) FROM predictions WHERE player_id = players.id) AS total_points
        FROM players
        ORDER BY total_points DESC
    """)

    # Find the rank of the player (1-based index)
    rank = next((index + 1 for index, entry in enumerate(leaderboard) if entry[0] == player_id), None)

    # Return complete player info with rank
    return {
        "id": row[0],
        "username": row[1],
        "email": row[2],
        "avatar_name": row[3],
        "created_at": row[4],
        "total_leagues_won": row[5],
        "total_cups_won": row[6],
        "total_points": player_points,
        "rank": rank
    }

# ------------------- Player Update ------------------- #

def update_player_info(player_id, username, email, password, avatar_name):
    try:
        now = datetime.now().isoformat(timespec="seconds")

        if password:
            password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            query = """
                UPDATE players 
                SET username=?, email=?, password_hash=?, avatar_name=?, updated_at=?
                WHERE id=?
            """
            execute_query(query, (username, email, password_hash, avatar_name, now, player_id))
        else:
            query = """
                UPDATE players 
                SET username=?, email=?, avatar_name=?, updated_at=?
                WHERE id=?
            """
            execute_query(query, (username, email, avatar_name, now, player_id))

        return True

    except Exception as e:
        print("❌ Error updating player:", e)
        return False

# ------------------- Player Deletion ------------------- #

def delete_player(player_id):
    avatar_row = fetch_one("SELECT avatar_path FROM players WHERE id = ?", (player_id,))
    avatar_path = avatar_row[0] if avatar_row else None

    conn, cur = execute_query("", ())
    try:
        cur.execute("DELETE FROM players WHERE id = ?", (player_id,))
        conn.commit()

        if avatar_path:
            normalized_path = os.path.normpath(avatar_path)
            if os.path.exists(normalized_path):
                os.remove(normalized_path)
                print(f"✅ Deleted avatar: {normalized_path}")
            else:
                print(f"⚠️ Avatar path does not exist: {normalized_path}")
        return True
    except Exception as e:
        print("❌ Error deleting player:", e)
        #conn.rollback()
        #return False
    finally:
        cur.close()
        conn.close()

# ------------------- Player ID Lookup ------------------- #

def get_player_id_by_username(username):
    row = fetch_one("SELECT id FROM players WHERE username =?", (username,))
    return row[0] if row else None

# ------------------- Avatar Upload & Save ------------------- #

def save_avatar_image(player_id, image):
    """
    Save avatar image to 'assets/avatars/{player_id}.png' and update avatar_path in DB.
    Returns: relative path to saved avatar.
    """
    avatars_dir = os.path.join("assets", "avatars")
    os.makedirs(avatars_dir, exist_ok=True)
    save_path = os.path.join(avatars_dir, f"{player_id}.png")

    if isinstance(image, Image.Image):
        image.save(save_path, format="PNG")
    elif hasattr(image, "getbuffer"):  # Streamlit's UploadedFile
        with open(save_path, "wb") as f:
            f.write(image.getbuffer())
    elif isinstance(image, bytes):
        with open(save_path, "wb") as f:
            f.write(image)
    else:
        raise ValueError("Unsupported image type")

    normalized_path = save_path.replace("\\", "/")

    conn, cur = execute_query("", ())
    try:
        cur.execute("UPDATE players SET avatar_path = ? WHERE id = ?", (normalized_path, player_id))
        conn.commit()
    finally:
        cur.close()
        conn.close()

    return normalized_path
