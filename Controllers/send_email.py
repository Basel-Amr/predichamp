import os
import smtplib
import sqlite3
from datetime import datetime, timedelta
from dotenv import load_dotenv, find_dotenv
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from Controllers.utils import fetch_all
from Controllers.predictions_controller import get_predicted_matches_for_player, get_next_round_info, get_matches_for_round, get_player_id_by_username
from datetime import datetime, timezone

# Load environment variables
load_dotenv(find_dotenv(), override=True)  # override=True forces reloading and overwriting existing env vars


SMTP_SERVER = os.getenv('SMTP_SERVER')
SMTP_PORT = int(os.getenv('SMTP_PORT'))
SENDER_EMAIL = os.getenv('SENDER_EMAIL')
SENDER_PASSWORD = os.getenv('SENDER_PASSWORD')

def get_all_player_emails():
    """Returns a list of all player emails and usernames."""
    query = "SELECT username, email FROM players"
    rows = fetch_all(query)
    return [(row["username"], row["email"]) for row in rows]





def send_reminder_email_to_all(round_id, round_name, deadline, match_time, match_count, level='test'):
    """
    Send personalized reminder emails, showing prediction status per player.
    Converts deadline and match_time to datetime if they are strings.
    """

    # Helper to parse datetime string or pass-through if datetime
    def parse_datetime(value, name):
        if isinstance(value, datetime):
            return value
        try:
            return datetime.fromisoformat(value)
        except Exception:
            raise ValueError(f"Invalid datetime format for {name}: {value}")

    try:
        deadline = parse_datetime(deadline, "deadline")
        match_time = parse_datetime(match_time, "match_time")
        # Ensure these are timezone-aware in UTC (important for timedelta)
        if deadline.tzinfo is None:
            deadline = deadline.replace(tzinfo=timezone.utc)
        if match_time.tzinfo is None:
            match_time = match_time.replace(tzinfo=timezone.utc)
    except ValueError as e:
        print(f"❌ Date parsing error: {e}")
        return

    now_utc = datetime.utcnow().replace(tzinfo=timezone.utc)
    time_left = deadline - now_utc
    days = time_left.days
    hours = time_left.seconds // 3600
    minutes = (time_left.seconds % 3600) // 60
    time_left_str = f"{days} days, {hours} hours, {minutes} minutes"

    # Get all players
    recipients = get_all_player_emails()  # [(username, email)]

    # Get all matches for the round once (list of dicts with id, home_team, away_team)
    all_matches = get_matches_for_round(round_id)

    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SENDER_EMAIL, SENDER_PASSWORD)

            for username, email in recipients:
                player_id = get_player_id_by_username(username)  # You need to implement or replace this

                # Get this player's predicted matches for this round
                player_predictions = get_predicted_matches_for_player(player_id, round_id)
                predicted_match_ids = {p['match_id'] for p in player_predictions}

                # Prepare predicted matches text
                predicted_matches_text = "\n".join(
                    [f"- {p['home_team']} vs {p['away_team']}" for p in player_predictions]
                ) or "None yet!"

                # Prepare unpredicted matches text
                unpredicted_matches = [
                    m for m in all_matches if m['id'] not in predicted_match_ids
                ]
                unpredicted_matches_text = "\n".join(
                    [f"- {m['home_team']} vs {m['away_team']}" for m in unpredicted_matches]
                ) or "All predicted! 🎉"

                predicted_count = len(player_predictions)

                # Define subject and body templates based on level
                if level == "2days":
                    subject = f"⏳ Just 2 Days Left – Get Ready for {round_name}!"
                    body_template = f"""
Hi {username} ⚽,

The excitement is building! The round **{round_name}** kicks off soon.

🗓 Match Time: {match_time.strftime('%Y-%m-%d %H:%M')} (UTC)
⏰ Deadline to Predict: {deadline.strftime('%Y-%m-%d %H:%M')} (UTC) — that's {time_left_str} left
📊 Number of Matches: {match_count}

✅ You've predicted {predicted_count} matches:
{predicted_matches_text}

⚠️ You still need to predict these matches:
{unpredicted_matches_text}

You've still got **2 full days** to make your predictions. Don’t miss out – the leaderboard is waiting!

🔥 Show us your football wisdom!
"""
                elif level == "1day":
                    subject = f"⏰ Only 1 Day Left to Predict – {round_name} Awaits!"
                    body_template = f"""
Hey {username} ⚽,

Only **1 day left** until the deadline for round **{round_name}**.

🗓 Match Time: {match_time.strftime('%Y-%m-%d %H:%M')} (UTC)
⏰ Prediction Deadline: {deadline.strftime('%Y-%m-%d %H:%M')} (UTC) — that's {time_left_str} left
📊 Matches in Round: {match_count}

✅ You've predicted {predicted_count} matches:
{predicted_matches_text}

⚠️ You still need to predict these matches:
{unpredicted_matches_text}

Your next big move could change the game. Submit your predictions now and stay ahead of the pack!

💪 Let’s make it count!
"""
                elif level == "2hours":
                    subject = f"🚨 FINAL CALL, {round_name} Starts Soon!"
                    body_template = f"""
Hi {username},

⏰ Time's almost up! This is your **FINAL REMINDER** to submit predictions for **{round_name}**.

Deadline: {deadline.strftime('%Y-%m-%d %H:%M')} (UTC) — that's {time_left_str} left

✅ You've predicted {predicted_count} matches:
{predicted_matches_text}

⚠️ You still need to predict these matches:
{unpredicted_matches_text}

⚠️ If you've already predicted – you're awesome. If not, now's your last chance!

🏁 Let's kick off in style!
"""
                elif level == "test":
                    subject = f"🧪 Test Reminder for {round_name}"
                    body_template = f"""
Hi {username},

This is a **test email** for round **{round_name}** reminder system.

🗓 Match Time: {match_time.strftime('%Y-%m-%d %H:%M')} (UTC)
⏰ Prediction Deadline: {deadline.strftime('%Y-%m-%d %H:%M')} (UTC) — that's {time_left_str} left
📊 Number of Matches: {match_count}

✅ You have predicted {predicted_count} matches:
{predicted_matches_text}

⚠️ Matches left to predict:
{unpredicted_matches_text}

Thanks for being part of the prediction game!

Best,
The Match Predictor Team
"""
                else:
                    print("⚠️ Invalid reminder level provided.")
                    return

                message = MIMEMultipart()
                message["From"] = SENDER_EMAIL
                message["To"] = email
                message["Subject"] = subject
                message.attach(MIMEText(body_template, "plain"))

                server.sendmail(SENDER_EMAIL, email, message.as_string())

        print(f"✅ {level.upper()} reminder sent to {len(recipients)} players.")

    except Exception as e:
        print(f"❌ Failed to send {level.upper()} reminder:", e)








if __name__ == "__main__":
    round_name, deadline, match_time, match_count = get_next_round_info()
    now = datetime.now()

    if now.date() == (deadline - timedelta(days=2)).date():
        send_reminder_email_to_all(round_name, deadline, match_time, match_count, "2days")
    elif now.date() == (deadline - timedelta(days=1)).date():
        send_reminder_email_to_all(round_name, deadline, match_time, match_count, "1day")
    elif now.strftime("%Y-%m-%d %H:%M") == deadline.strftime("%Y-%m-%d %H:%M"):
        send_reminder_email_to_all(round_name, deadline, match_time, match_count, "2hours")
    else:
        print("Notjing happens")
        send_reminder_email_to_all(round_name, deadline, match_time, match_count, "2days")