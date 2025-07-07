import streamlit as st
import sqlite3
from streamlit_option_menu import option_menu
from Controllers.players_controller import get_player_info
from Manage_Modules.manage_leagues import manage_leagues
from Manage_Modules.manage_teams import manage_teams
from Manage_Modules.manage_matches import manage_matches
from Manage_Modules.manage_tournment import manage_tournment
DB_PATH = "Others/game_database.db"



def render(player_id):

    player_name = get_player_info(player_id)['username']
    st.title(f"👋 Welcome, {player_name}")

    show_tabs = [
        "Manage Leagues", 
        "Manage Teams", 
        "Manage Matches", 
        "Manage Predictions", 
        "Manage Tournament"
    ]
    icons = ["trophy", "people", "calendar-week", "pencil-square", "bullseye"]

    selected_tab = option_menu(
        menu_title=None,
        options=show_tabs,
        icons=icons,
        orientation="horizontal",
        styles={
            "container": {
                "padding": "10px",
                "background-color": "#ffffff",
                "border-radius": "10px",
                "box-shadow": "0 4px 12px rgba(0, 0, 0, 0.1)"
            },
            "nav-link": {
                "font-size": "18px",
                "font-weight": "600",
                "text-align": "center",
                "color": "#1f2937",
                "margin": "0px 10px",
                "border-radius": "8px",
                "transition": "all 0.3s ease",
                "padding": "10px 18px",
            },
            "nav-link-selected": {
                "background": "linear-gradient(135deg, #3b82f6, #60a5fa)",
                "color": "white",
                "font-weight": "bold",
                "box-shadow": "0 0 10px rgba(59, 130, 246, 0.4)",
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
        st.header("📝 Manage Predictions")
        st.info("Review or evaluate player predictions.")

    elif selected_tab == "Manage Tournament":
        st.header("🎯 Manage Tournament")
        st.info("Handle rounds, knockout stages, and rules.")
        manage_tournment()
