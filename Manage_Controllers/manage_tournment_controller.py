from Controllers.db_controller import get_connection
from Controllers.utils import fetch_all, fetch_one
import os
import smtplib
import os
from dotenv import load_dotenv, find_dotenv
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from Controllers.utils import fetch_all

# Load environment
load_dotenv(find_dotenv(), override=True)
SMTP_SERVER = os.getenv("SMTP_SERVER")
SMTP_PORT = int(os.getenv("SMTP_PORT"))
SENDER_EMAIL = os.getenv("SENDER_EMAIL")
SENDER_PASSWORD = os.getenv("SENDER_PASSWORD")

def send_tournament_end_emails():
    # 1. Get leaderboard (winner is rank 1)
    leaderboard = fetch_all("""
        SELECT p.id, p.username, p.email,
               COALESCE((SELECT SUM(score) FROM predictions WHERE player_id = p.id), 0) + COALESCE(p.bonous, 0) AS total_points
        FROM players p
        ORDER BY total_points DESC, username ASC
    """)

    if not leaderboard:
        return

    winner = leaderboard[0]
    winner_name = winner["username"]
    winner_score = winner["total_points"]

    # 2. Loop over all players
    for player in leaderboard:
        name = player["username"]
        email = player["email"]
        rank = leaderboard.index(player) + 1
        points = player["total_points"]

        subject = "🏁 Tournament Ended — See the Winner and Your Final Stats!"
        body = f"""
        <html>
        <body style="font-family:Arial, sans-serif; background-color:#f9fafb; padding:20px; color:#111827;">
            <h2>🏆 What a Tournament!</h2>
            <p>Hi <b>{name}</b>,</p>
            <p>The tournament has officially <strong>ended</strong> — and it was thrilling from start to finish!</p>

            <h3 style="color:#3b82f6;">🥇 Winner: <span style="color:#111827;">{winner_name}</span> with <b>{winner_score} pts</b></h3>

            <hr>
            <p><b>Your Final Stats:</b><br>
               • Rank: <b>#{rank}</b><br>
               • Total Points: <b>{points}</b></p>

            <p>Thank you for being part of this amazing journey. More tournaments are coming soon. Stay sharp! ⚽🔥</p>

            <p style="margin-top:24px;">Cheers,<br><b>The Tournament Team</b></p>
        </body>
        </html>
        """

        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = SENDER_EMAIL
        msg["To"] = email
        msg.attach(MIMEText(body, "html"))

        try:
            with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
                server.starttls()
                server.login(SENDER_EMAIL, SENDER_PASSWORD)
                server.send_message(msg)
                print(f"✅ Sent to {email}")
        except Exception as e:
            print(f"❌ Failed to send email to {email}: {e}")

def end_season():
    conn = get_connection()
    cur = conn.cursor()

    # Determine the winner based on prediction scores + bonous
    cur.execute("""
        SELECT p.id
        FROM players p
        LEFT JOIN (
            SELECT player_id, SUM(score) AS pred_score
            FROM predictions
            GROUP BY player_id
        ) pr ON p.id = pr.player_id
        ORDER BY COALESCE(pred_score, 0) + COALESCE(p.bonous, 0) DESC
        LIMIT 1
    """)
    
    winner = cur.fetchone()
    if winner:
        winner_id = winner[0]
        cur.execute("""
            UPDATE players 
            SET total_leagues_won = total_leagues_won + 1 
            WHERE id = ?
        """, (winner_id,))

    # Clear tables
    cur.execute("DELETE FROM predictions")
    cur.execute("DELETE FROM matches")
    cur.execute("DELETE FROM rounds")
    cur.execute("DELETE FROM two_legged_table")

    # Reset players' scores and bonous
    cur.execute("UPDATE players SET score = 0, bonous = 0")

    conn.commit()
    conn.close()
