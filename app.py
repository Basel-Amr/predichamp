import streamlit as st
from streamlit_option_menu import option_menu
from Authentications import auth
from Modules import profile, predictions, leaderboard, achievement, manage, cup, fixtures, teams, leagues
from Controllers.players_controller import get_player_id_by_username
from streamlit_autorefresh import st_autorefresh
from datetime import datetime, timedelta
# Page Configuration
st.set_page_config(
    page_title="Football Cup Predictor",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="expanded"
)
st.markdown(
    """
    <style>
        [data-testid="stSidebarNav"] {
            display: none;
        }
    </style>
    """,
    unsafe_allow_html=True
)

# 💡 Custom Font & Styling
st.markdown("""
    <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@500&display=swap" rel="stylesheet">
    <style>
        html, body, [class*="css"] {
            font-family: 'Poppins', sans-serif;
        }
        .block-container {
            padding-top: 1rem;
            padding-left: 3rem;
            padding-right: 3rem;
        }
    </style>
""", unsafe_allow_html=True)
#https://media1.giphy.com/media/v1.Y2lkPTc5MGI3NjExMG5kNG8wOGlzNnhvYjEyMWlhc3dkcmlmeTN6MG91cTJmMWRvbDFmYyZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/3ohA2TEUVTPWlzSD28/giphy.gif
# 🎞️ Football Animation
def show_animation():
    st.markdown(
        """
        <div style="text-align:center; margin-bottom: 25px;">
            <img src="https://media3.giphy.com/media/v1.Y2lkPTc5MGI3NjExYjFnbTd5Ymo0OG5va3d6cDI4OHl6ZnZtZTJjZ3U0aWVjbWliank0ayZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/dKdtyye7l5f44/giphy.gif" alt="Football Animation" width="300" />
        </div>
        """,
        unsafe_allow_html=True,
    )

# 🔐 Session State
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "username" not in st.session_state:
    st.session_state.username = ""
if "role" not in st.session_state:
    st.session_state.role = "player"

# Main Dashboard (Tabs)
def main_page():
    # ✅ Inject CSS for horizontal scroll + hover and click animations
    st.markdown("""
        <style>
        /* Make nav scrollable */
        .horizontal-scroll-container {
            overflow-x: auto;
            white-space: nowrap;
            padding-bottom: 10px;
        }
        .horizontal-scroll-container ul {
            display: inline-flex !important;
            flex-wrap: nowrap !important;
        }

        /* Add hover & active animations */
        .nav-link {
            transition: transform 0.2s ease, box-shadow 0.2s ease;
        }
        .nav-link:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 15px rgba(0, 0, 0, 0.15);
        }
        .nav-link:active {
            transform: scale(0.97);
        }
        </style>
    """, unsafe_allow_html=True)
    # 🔍 SEARCH SECTION
    search_query = st.text_input(
        label="",
        value="",
        placeholder="🔍 Search Teams, Players, or Leagues",
        key="search_input"
    )

    st.markdown("""
        <style>
            .stTextInput input {
                background-color: #1f2937;
                border: 2px solid #3b82f6;
                border-radius: 12px;
                padding: 12px 16px;
                font-size: 16px;
                color: #f9fafb;
                transition: all 0.3s ease;
            }
            .stTextInput input::placeholder {
                color: #9ca3af;
            }
            .stTextInput input:focus {
                border-color: #2563eb;
                box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.3);
            }
        </style>
    """, unsafe_allow_html=True)

    if search_query.strip():
        st.markdown("### 🔎 Search Results")
        # # You can call a search function here based on your DB
        # results = search_database(search_query.strip())  # <-- You write this function

        # if results:
        #     for res in results:
        #         st.markdown(f"- **{res['type']}**: {res['name']} ({res.get('extra', '')})")
        # else:
        #     st.warning("No matching results found.")

    # 🔖 Define visible tabs and icons
    show_tabs = ["Profile", "Predictions", "Fixtures", "Leaderboard", "Achievement", "Cup", "Teams", "Leagues"]
    icons = ["person-circle", "lightning", "calendar-event", "trophy", "award", "trophy", "people", "flag"]

    # 🔧 Add 'Manage' for admin users
    if st.session_state.role == "admin":
        show_tabs.append("Manage")
        icons.append("gear")

    # 📱 Render the horizontal menu inside scroll container
    with st.container():
        st.markdown('<div class="horizontal-scroll-container">', unsafe_allow_html=True)

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
                    "font-size": "16px",
                    "font-weight": "600",
                    "text-align": "center",
                    "color": "#1f2937",
                    "margin": "0px 10px",
                    "border-radius": "8px",
                    "transition": "all 0.3s ease",
                    "padding": "8px 16px",
                    "white-space": "nowrap"
                },
                "nav-link-selected": {
                    "background": "linear-gradient(135deg, #3b82f6, #60a5fa)",
                    "color": "white",
                    "font-weight": "bold",
                    "box-shadow": "0 0 10px rgba(59, 130, 246, 0.4)",
                }
            },
            key="main_tabs"
        )

        st.markdown('</div>', unsafe_allow_html=True)

    # 🧠 Get player ID from username
    player_id = get_player_id_by_username(st.session_state.username)

    # 🔄 Conditional rendering per tab
    if selected_tab == "Profile":
        profile.render(player_id)
    elif selected_tab == "Predictions":
        st_autorefresh(interval=3000, limit=None, key="refresh")
        predictions.render(player_id)
    elif selected_tab == "Fixtures":
        st.markdown("""
            <div style='padding: 15px; background-color: #fff3cd; border-radius: 10px; margin-top:10px;'>
                <h3 style='color:#b36b00;'>📅 Upcoming Fixtures</h3>
                <p style='margin:0; font-size:15px; color:#444;'>Review and control upcoming matches grouped by league and round.</p>
            </div>
        """, unsafe_allow_html=True)
        st_autorefresh(interval=3000, limit=None, key="refresh")
        fixtures.render_fixtures()
    elif selected_tab == "Leaderboard":
        leaderboard.render(player_id)
    elif selected_tab == "Achievement":
        achievement.render(player_id)
    elif selected_tab == "Cup":
        cup.render(player_id)
    elif selected_tab == "Teams":
        teams.render()
    elif selected_tab == "Leagues":
        #st_autorefresh(interval=5000, limit=None, key="refresh")
        leagues.render()
    elif selected_tab == "Manage":
        manage.render(player_id)


# App Execution
show_animation()

if not st.session_state.logged_in:
    nav_auth = option_menu(
        menu_title=None,
        options=["🔐 Login", "📝 Sign Up"],
        icons=["box-arrow-in-right", "person-plus"],
        default_index=0,
        orientation="horizontal",
        styles={
            "container": {
                "padding": "10px",
                "background-color": "#ffffff",
                "border-radius": "10px",
                "box-shadow": "0 4px 12px rgba(0, 0, 0, 0.1)"
            },
            "nav-link": {
                "font-size": "20px",
                "font-weight": "600",
                "text-align": "center",
                "color": "#1f2937",
                "margin": "0px 15px",
                "border-radius": "8px",
                "transition": "all 0.3s ease",
                "padding": "12px 20px",
            },
            "nav-link-selected": {
                "background": "linear-gradient(135deg, #3b82f6, #60a5fa)",
                "color": "white",
                "font-weight": "bold",
                "box-shadow": "0 0 10px rgba(59, 130, 246, 0.4)",
            }
        }
    )

    if nav_auth == "🔐 Login":
        auth.login()
    else:
        auth.signup()
else:
    main_page()
