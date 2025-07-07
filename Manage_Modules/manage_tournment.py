import streamlit as st
from Controllers.send_email import send_reminder_email_to_all
from Controllers.utils_prediction import update_scores_for_match
from Controllers.utils import fetch_all
from Controllers.predictions_controller import get_next_round_info
from Controllers.api_controller import update_all_teams, update_all_players, fetch_all_target_leagues
import Manage_Controllers.manage_tournment_controller as manage
from auto_push_db import auto_push_db

def manage_tournment():
    # 💠 Header
    st.markdown("""
        <style>
        .main-title {
            text-align:center;
            color:#1f2937;
            font-size:40px;
            font-weight:800;
            margin-bottom: 0;
        }
        .subtitle {
            text-align:center;
            color:#6b7280;
            font-size:18px;
            margin-top:0;
            margin-bottom: 30px;
        }
        .stButton>button {
            border-radius: 10px;
            transition: all 0.2s ease-in-out;
        }
        .stButton>button:hover {
            transform: scale(1.03);
            border: 2px solid #3b82f6;
        }
        </style>
        <p class='main-title'>⚙️ Admin Tournament Control Panel</p>
        <p class='subtitle'>Manage tournament workflows and data operations efficiently</p>
        <hr style="border: 1px solid #ddd; margin-bottom: 2rem;">
    """, unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    # 🔄 Tournament Operations
    with col1:
        with st.expander("🛠️ Tournament Actions", expanded=True):
            st.markdown("Use these tools to control the tournament lifecycle.")

            if st.button("🧹 Reset Tournament", help="Reset all tournament data (Disabled for now)", type='secondary'):
                manage.reset_season()
                st.toast("⚠️ Reset Tournament is not active yet", icon="⚠️")

            if st.button("🛑 End Tournament", help="Permanently end the current tournament", type='secondary'):
                #manage.end_season()
                #manage.send_tournament_end_emails()
                st.toast("⛔ End Tournament is not active yet", icon="⛔")

            if st.button("🏆 Start the Cup", help="Start the tournament knockout cup", type='secondary'):
                st.toast("⚠️ Start Cup is not active yet", icon="⚠️")

    # 📡 Data Management
    with col2:
        with st.expander("📡 Data Management", expanded=True):
            st.markdown("Push updates, calculate scores, and notify players.")

            if st.button("📤 Push Data to DB", help="Sync latest data with the database", type="primary"):
                with st.spinner("🔄 Syncing with database..."):
                    auto_push_db()  # Uncomment when implemented
                    st.success("✅ Data pushed to database successfully!")

            if st.button("📧 Send Reminder Emails", help="Notify users of upcoming rounds", type="primary"):
                with st.spinner("📨 Sending email reminders..."):
                    info = get_next_round_info()
                    if info:
                        send_reminder_email_to_all(
                            round_id=info['round_id'],
                            round_name=info['round_name'],
                            deadline=info['deadline'],
                            match_time=info['first_match_time'],
                            match_count=info['match_count'],
                            level="test"
                        )
                        st.success("✅ Reminder emails sent successfully!")
                    else:
                        st.warning("⚠️ No upcoming round found.")

            if st.button("📊 Calculate Match Points", help="Recalculate scores for all matches", type="primary"):
                with st.spinner("🧮 Calculating points..."):
                    try:
                        matches = fetch_all("SELECT id FROM matches")
                        for match in matches:
                            update_scores_for_match(match["id"])
                        st.success(f"✅ Points updated for {len(matches)} matches.")
                    except Exception as e:
                        st.error(f"❌ Error: {e}")

    st.markdown("""---""")

    col3, col4 = st.columns(2)

    with col3:
        if st.button("🧠 Update Team Info", help="Fetch and refresh all team data", type="primary"):
            with st.spinner("🔄 Updating team information..."):
                update_all_teams()
            st.success("✅ Team information updated!")

    with col4:
        if st.button("👟 Update Player Info", help="Fetch and refresh player data", type="primary"):
            with st.spinner("🔄 Updating player information..."):
                update_all_players()
            st.success("✅ Player information updated!")

    st.markdown("---")

    # 📅 Fetch Matches
    league_map = {
        "WC": "FIFA World Cup",
        "CL": "UEFA Champions League",
        "BL1": "Bundesliga",
        "DED": "Eredivisie",
        "BSA": "Brasileirão",
        "PD": "La Liga",
        "FL1": "Ligue 1",
        "ELC": "Championship",
        "PPL": "Primeira Liga",
        "EC": "European Championship",
        "SA": "Serie A",
        "PL": "Premier League"
    }

    st.markdown("### 🗂️ League Match Fetcher")
    selected_leagues = st.multiselect(
        "📋 Select leagues to download matches for:",
        options=list(league_map.keys()),
        format_func=lambda x: league_map[x]
    )

    if st.button("📅 Fetch Matches & Scores", type="primary", help="Download schedules and scores for selected leagues"):
        if selected_leagues:
            with st.spinner("🔄 Fetching match data..."):
                fetch_all_target_leagues(selected_leagues)
                st.success("✅ Match data fetched successfully!")
        else:
            st.warning("⚠️ Please select at least one league.")
