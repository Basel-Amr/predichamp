import streamlit as st
import sqlite3
from streamlit_option_menu import option_menu
from Controllers.players_controller import get_player_info
from Manage_Modules.manage_leagues import manage_leagues
from Manage_Modules.manage_teams import manage_teams
from Manage_Modules.manage_matches import manage_matches
from Manage_Modules.manage_tournment import manage_tournment
from Manage_Modules.manage_players import manage_players 
DB_PATH = "Others/game_database.db"



def render(player_id):
    player_name = get_player_info(player_id)['username']
    
    st.markdown(f"""
        <div style='
            text-align: center;
            padding: 30px 10px;
            background: linear-gradient(90deg, #1e3a8a, #3b82f6);
            border-radius: 12px;
            margin-bottom: 25px;
            box-shadow: 0 8px 24px rgba(0,0,0,0.15);
        '>
            <h1 style='color: white; font-size: 2.5rem; margin-bottom: 0;'>👋 Welcome, {player_name}!</h1>
            <p style='color: #e0e7ff; font-size: 1.2rem;'>Administrator Control Panel — Manage your football universe</p>
        </div>
    """, unsafe_allow_html=True)

    show_tabs = [
        "Manage Players",
        "Manage Predictions", 
        "Manage Leagues", 
        "Manage Teams", 
        "Manage Matches", 
        "Manage Tournament"
    ]
    icons = ["person-lines-fill", "pencil-square", "trophy", "people", "calendar-week", "bullseye"]

    selected_tab = option_menu(
        menu_title=None,
        options=show_tabs,
        icons=icons,
        orientation="horizontal",
        styles={
            "container": {
                "padding": "12px",
                "background-color": "#ffffff",
                "border-radius": "12px",
                "box-shadow": "0 6px 18px rgba(0, 0, 0, 0.08)"
            },
            "nav-link": {
                "font-size": "16.5px",
                "font-weight": "600",
                "color": "#1e293b",
                "text-align": "center",
                "margin": "0px 6px",
                "border-radius": "8px",
                "transition": "all 0.3s ease",
                "padding": "10px 16px",
            },
            "nav-link-selected": {
                "background": "linear-gradient(135deg, #3b82f6, #60a5fa)",
                "color": "white",
                "font-weight": "bold",
                "box-shadow": "0 0 12px rgba(59, 130, 246, 0.5)",
            }
        }
    )

    if selected_tab == "Manage Leagues":
        manage_leagues()

    elif selected_tab == "Manage Teams":
        manage_teams()

    elif selected_tab == "Manage Matches":
        manage_matches()

    elif selected_tab == "Manage Predictions":
        st.markdown("### 📝 Manage Player Predictions")
        st.info("Review, update, or evaluate match predictions submitted by players. Filter by round, accuracy, or time.")

    elif selected_tab == "Manage Tournament":
        st.markdown("### 🏆 Manage Tournament Structure")
        manage_tournment()

    elif selected_tab == "Manage Players":
        st.markdown("### 👤 Manage Registered Players")
        st.info("Edit player roles, reset passwords, view stats, and deactivate accounts.")
        manage_players()
