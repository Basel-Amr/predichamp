# auth.py
import os
import streamlit as st
from dotenv import load_dotenv
from Controllers.utils import execute_query, fetch_one, hash_password, verify_password
import datetime
from pytz import all_timezones

load_dotenv()
ADMIN_SECRET_CODE = os.getenv("ADMIN_SECRET_CODE", "")

def get_user_by_username(username):
    query = "SELECT * FROM players WHERE username = ?"  # ✅ Correct
    return fetch_one(query, (username,))



def create_user(username, email, password, role="player", timezone="Africa/Cairo"):
    hashed = hash_password(password)
    query = """
        INSERT INTO players (username, email, password_hash, role, timezone)
        VALUES (?, ?, ?, ?, ?)
    """
    execute_query(query, (username, email, hashed, role, timezone))
    return True

def update_last_login(username):
    now = datetime.datetime.now().isoformat(timespec='seconds')
    query = "UPDATE players SET last_login_at =? WHERE username = ?"
    execute_query(query, (now, username))
    
def login():
    st.markdown("<h1 style='text-align: center;'>🔐 Login</h1>", unsafe_allow_html=True)
    st.markdown("---")
    
    st.markdown("👤 **Enter your credentials to access the Football Cup App**")

    username = st.text_input("🧑 Username")
    password = st.text_input("🔒 Password", type="password")

    if st.button("🚀 Login"):
        with st.spinner("Verifying credentials..."):
            user = get_user_by_username(username)
            if user:
                stored_hash = user[3]
                if verify_password(password, stored_hash):
                    # Update last_login_at
                    update_last_login(username)
                    
                    st.success(f"✅ Welcome back, **{username}**! ⚽")
                    st.session_state.logged_in = True
                    st.session_state.username = username
                    st.session_state.role = user[5]
                    st.balloons()
                    st.rerun()
                else:
                    st.error("❌ Incorrect password. Please try again.")
            else:
                st.error("❌ User not found. Please sign up first.")

def signup():
    st.markdown("<h1 style='text-align: center;'>📝 Sign Up</h1>", unsafe_allow_html=True)
    st.markdown("----")
    st.markdown("✍️ **Fill in the details to join PrediChamp!**")

    with st.form("signup_form"):
        username = st.text_input("🧑 Username", help="Pick a unique name you'll be identified by.")
        email = st.text_input("📧 Email", help="We'll send notifications and results here.")
        password = st.text_input("🔑 Password", type="password")
        password_confirm = st.text_input("🔁 Confirm Password", type="password")

        # 🌍 Timezone selection
        timezones = sorted(all_timezones)
        default_tz = "Africa/Cairo"
        timezone = st.selectbox("🌍 Your Timezone", options=timezones, index=timezones.index(default_tz), help="Used to show match times in your local zone")

        # 🛡️ Admin role code (optional)
        admin_code_input = st.text_input("🛡️ Admin Code", type="password", help="Only fill if you're authorized to be admin (optional)")

        submitted = st.form_submit_button("🎯 Register")

    if submitted:
        if not username or not email or not password or not password_confirm:
            st.warning("⚠️ All fields except admin code are required.")
            return

        if password != password_confirm:
            st.error("❌ Passwords do not match!")
            return

        if get_user_by_username(username):
            st.error("⚠️ Username already taken. Try a different one.")
            return

        if fetch_one("SELECT 1 FROM players WHERE email = ?", (email,)):
            st.error("📧 Email already registered. Try logging in instead.")
            return

        role = "admin" if admin_code_input == ADMIN_SECRET_CODE else "player"

        with st.spinner("Creating your account..."):
            create_user(username, email, password, role, timezone)

        st.success(f"🎉 Welcome aboard **{username}**! Your account has been created as a **{role}**.")
        st.balloons()


def logout():
    st.session_state.logged_in = False
    st.session_state.username = ""
    st.session_state.role = "player"
    st.rerun()