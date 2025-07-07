# auto_push_db.py
import os
import subprocess
from datetime import datetime
from zoneinfo import ZoneInfo
import streamlit as st

def auto_push_db():
    try:
        # Timezone setup for Cairo
        local_tz = ZoneInfo("Africa/Cairo")

        GITHUB_TOKEN = os.getenv("GH_TOKEN") or st.secrets["GH_TOKEN"]
        GITHUB_USER = "Basel-Amr"
        GITHUB_REPO = "predichamp"
        DB_FILE = "Others\game_database.db"

        if not os.path.exists(DB_FILE):
            st.error("❌ Database file not found.")
            return

        # Git config
        subprocess.run(["git", "config", "--global", "user.email", "auto@streamlit.io"])
        subprocess.run(["git", "config", "--global", "user.name", "Streamlit Auto Bot"])

        # Add, commit and push
        subprocess.run(["git", "add", DB_FILE])

        now = datetime.now(local_tz).strftime("%Y-%m-%d %H:%M:%S")  # Cairo local time
        subprocess.run(["git", "commit", "-m", f"Auto update DB: {now}"])

        repo_url = f"https://{GITHUB_USER}:{GITHUB_TOKEN}@github.com/{GITHUB_USER}/{GITHUB_REPO}.git"
        subprocess.run(["git", "push", repo_url])

        st.success("✅ Database pushed to GitHub successfully!")
    except Exception as e:
        st.error(f"❌ Failed to push DB: {e}")
