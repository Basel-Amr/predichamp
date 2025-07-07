# auth.py
import os
import streamlit as st
from dotenv import load_dotenv
from utils import execute_query, fetch_one, hash_password, verify_password
import datetime

load_dotenv()
ADMIN_SECRET_CODE = os.getenv("ADMIN_SECRET_CODE", "")

def get_user_by_username(username):
    query = "SELECT * FROM players WHERE username = ?"
    return fetch_one(query, (username,))


def create_user(username, email, password, role="player"):
    hashed = hash_password(password)
    query = "INSERT INTO players (username, email, password_hash, role) VALUES (?, ?, ?, ?)"
    execute_query(query, (username, email, hashed, role))
    return True

def update_last_login(username):
    now = datetime.datetime.now().isoformat(timespec='seconds')
    query = "UPDATE players SET last_login_at = ? WHERE username = ?"
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
    st.markdown("---")
    
    st.markdown("✍️ **Fill the form below to create a new account**")

    username = st.text_input("🧑 Username", key="signup_username")
    email = st.text_input("📧 Email", key="signup_email")
    password = st.text_input("🔑 Password", type="password", key="signup_password")
    password_confirm = st.text_input("🔁 Confirm Password", type="password", key="signup_confirm_password")
    admin_code_input = st.text_input("🛡️ Admin Code (optional)", type="password", key="admin_code")

    if st.button("🎯 Register"):
        if not username or not email or not password or not password_confirm:
            st.warning("⚠️ All fields except admin code are required.")
            return

        if password != password_confirm:
            st.error("🔁 Passwords do not match!")
            return

        if get_user_by_username(username):
            st.error("⚠️ Username already exists. Try something else.")
            return

        if fetch_one("SELECT 1 FROM players WHERE email = ?", (email,)):
            st.error("📧 Email already registered. Please log in.")
            return

        role = "admin" if admin_code_input and admin_code_input == ADMIN_SECRET_CODE else "player"

        with st.spinner("Creating your account..."):
            create_user(username, email, password, role)

        st.success(f"🎉 Account created successfully as **{role}**! You can now log in.")
        st.balloons()


def logout():
    st.session_state.logged_in = False
    st.session_state.username = ""
    st.session_state.role = "player"
    st.rerun()