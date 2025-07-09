import streamlit as st
from datetime import datetime
from Controllers import fixtures_controller as ctrl
from Renders.render_helpers import render_league_banner, render_match_card

def render_fixtures(player_id):
    # 🌟 Title
    st.markdown("""
        <div style="text-align: center; padding: 15px 0; margin-bottom: 20px;">
            <h1 style="color: #003566; font-size: 2.5rem; font-weight: bold;">
                🎯 Matchday Live
            </h1>
            <p style="color: #6c757d; font-size: 1.1rem;">Track every kick — gameweek by gameweek!</p>
        </div>
    """, unsafe_allow_html=True)

    # 📥 Fetch fixtures
    fixtures_by_date = ctrl.get_upcoming_fixtures_grouped()
    if not fixtures_by_date:
        st.info("No fixtures available.")
        return

    available_dates = sorted(fixtures_by_date.keys())
    today_str = datetime.today().strftime('%Y-%m-%d')

    # 🧠 Select default: first date on or after today
    default_index = next((i for i, d in enumerate(available_dates) if d >= today_str), 0)

    # 📆 Show all available dates with Gameweek labels
    gameweek_labels = [f"Matchday {i+1} — {date}" for i, date in enumerate(available_dates)]

    selected_label = st.selectbox("🔘 Select Matchday", options=gameweek_labels, index=default_index)
    selected_date = selected_label.split(" — ")[-1]

    st.divider()

    if selected_date not in fixtures_by_date:
        st.warning(f"📭 No matches scheduled for **{selected_date}**. Take the day off 😎!")
        return

    # 📅 Display Matches for Selected Date
    st.subheader(f"🗓️ Fixtures on {selected_date}")
    for league_name, matches in fixtures_by_date[selected_date].items():
        render_league_banner(league_name, ctrl.get_logo_path_from_league(league_name))
        for match in matches:
            render_match_card(match, player_id)
