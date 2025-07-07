import streamlit as st
import Manage_Controllers.manage_matches_controller as ctrl

import streamlit as st
import Manage_Controllers.manage_matches_controller as ctrl
from datetime import datetime
from Controllers.utils_prediction import update_scores_for_match

def manage_matches():
    st.header("📋 Manage Matches")

    # === MATCH FETCH FORM ===
    with st.form("match_range_form"):
        col1, col2 = st.columns(2)
        with col1:
            from_day = st.number_input("From Matchday", min_value=1, max_value=50, value=1)
        with col2:
            to_day = st.number_input("To Matchday", min_value=1, max_value=50, value=7)

        if st.form_submit_button("📥 Fetch Matches"):
            report = ctrl.fetch_and_insert_matches(from_day, to_day)
            for name, added, skipped, msg in report:
                st.success(f"✅ {name}: {added} added, {skipped} skipped. {msg}")

    st.markdown("---")
    st.subheader("⚙️ View & Manage Matches by League")

    leagues = ctrl.get_leagues_with_matches()
    if not leagues:
        st.info("No leagues found with matches.")
        return

    league_names = {f"{l['name']} (ID: {l['id']})": l['id'] for l in leagues}
    selected_league = st.selectbox("Select League", options=list(league_names.keys()))
    league_id = league_names[selected_league]

    if st.button("🗑️ Delete All Matches for This League"):
        ctrl.delete_matches_by_league(league_id)
        st.warning(f"All matches deleted for league: {selected_league}")
        st.rerun()

    # === ADD MATCH SECTION ===
    with st.expander("➕ Add New Match"):
        from Controllers.utils import fetch_all, execute_query
        from Controllers.db_controller import get_connection
        from datetime import datetime

        conn = get_connection()
        league = ctrl.get_league_by_id(league_id)
        nationality = league['country']

        if nationality.lower() == "europe":
            team_query = "SELECT id, name FROM teams WHERE continent = 'Europe'"
            teams = fetch_all(team_query)
        else:
            team_query = "SELECT id, name FROM teams WHERE nationality = ?"
            teams = fetch_all(team_query, (nationality,))

        team_options = {t['name']: t['id'] for t in teams}

        col1, col2 = st.columns(2)
        with col1:
            home_team = st.selectbox(f"🏠 Home Team", options=list(team_options.keys()))
        with col2:
            away_team = st.selectbox("🚩 Away Team", options=[t for t in team_options.keys() if t != home_team])

        col1, col2 = st.columns(2)
        with col1:
            match_date = st.date_input("📅 Match Date")
        with col2:
            match_time = st.time_input("⏰ Match Time")

        match_datetime = datetime.combine(match_date, match_time)
        matchday = st.number_input("🔢 Matchday", min_value=1, max_value=50, value=1)
        status = st.selectbox("🎯 Status", ['upcoming', 'live', 'finished', 'cancelled'])
        is_predictable = st.checkbox("📊 Is Predictable", value=False)

        if st.button("✅ Add Match"):
            home_id = team_options[home_team]
            away_id = team_options[away_team]
            round_id = ctrl.get_or_create_round_by_week(conn, match_datetime)
            stage_id = ctrl.get_or_create_stage("REGULAR_SEASON", league_id)
            venue = ctrl.get_team_venue(home_id) or "Unknown"

            query = """
                INSERT INTO matches (
                    round_id, league_id, home_team_id, away_team_id,
                    match_datetime, status, matchday, stage_id, is_predictable, Venue_Name
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            values = (
                round_id, league_id, home_id, away_id,
                match_datetime.isoformat(), status, matchday,
                stage_id, int(is_predictable), venue
            )

            execute_query(query, values)
            st.success("✅ Match added successfully!")
            st.rerun()
            
    rounds = ctrl.get_rounds_by_league(league_id)
    if not rounds:
        st.info("No rounds found for this league.")
        return

    for r in rounds:
        match_count = r["match_count"]
        with st.expander(f"📆 {r['name']} ({match_count} matches) – {r['start_date']} → {r['end_date']}"):
            matches = ctrl.get_matches_by_round(r['id'], league_id)
            if not matches:
                st.info("No matches found in this round for the selected league.")
            else:
                for match in matches:
                    with st.container():
                        st.markdown("---")
                        col1, col2 = st.columns([3, 1])

                        with col1:
                            st.markdown(f"#### ⚽ {match['home_team']} vs {match['away_team']}")

                            if f"edit_mode_{match['id']}" not in st.session_state:
                                st.session_state[f"edit_mode_{match['id']}"] = False

                            if not st.session_state[f"edit_mode_{match['id']}"]:
                                st.markdown(f"""
                                    🗓️ **Date:** {match['match_datetime'] or 'N/A'}  
                                    🏟️ **Venue:** {match['Venue_Name'] or 'N/A'}  
                                    🔢 **Matchday:** {match['matchday'] or 'N/A'}  
                                    🎯 **Status:** {match['status'].capitalize() if match['status'] else 'N/A'}  
                                    📊 **Predictable:** {'✅ Yes' if match['is_predictable'] else '❌ No'}  
                                    🏁 **Score:** {match['home_score']} - {match['away_score'] if match['away_score'] is not None else ''}
                                """)
                                col_btn1, col_btn2 = st.columns([1, 1])
                                with col_btn1:
                                    if st.button("✏️ Edit", key=f"edit_button_{match['id']}"):
                                        st.session_state[f"edit_mode_{match['id']}"] = True
                                with col_btn2:
                                    if st.button("🗑️ Delete", key=f"delete_{match['id']}"):
                                        ctrl.delete_match_by_id(match['id'])
                                        st.error(f"Match {match['home_team']} vs {match['away_team']} deleted.")
                                        st.rerun()
                            else:
                                with st.form(f"edit_match_{match['id']}"):
                                    home_score = st.number_input("Home Score", value=match['home_score'] or 0, step=1)
                                    away_score = st.number_input("Away Score", value=match['away_score'] or 0, step=1)
                                    status = st.selectbox("Status", ['upcoming', 'live', 'finished', 'cancelled'], index=['upcoming', 'live', 'finished', 'cancelled'].index(match['status']))
                                    matchday = st.number_input("Matchday", min_value=1, max_value=50, value=match['matchday'])
                                    venue = st.text_input("Venue", value=match['Venue_Name'] or "")
                                    is_predictable = st.checkbox("Is Predictable", value=bool(match['is_predictable']))

                                    col_form1, col_form2 = st.columns([1, 1])
                                    with col_form1:
                                        if st.form_submit_button("💾 Save Changes"):
                                            from Controllers.db_controller import get_connection
                                            from Controllers.utils import execute_query
                                            query = """
                                                UPDATE matches
                                                SET home_score = ?, away_score = ?, status = ?, matchday = ?, Venue_Name = ?, is_predictable = ?, updated_at = CURRENT_TIMESTAMP
                                                WHERE id = ?
                                            """
                                            values = (home_score, away_score, status, matchday, venue, int(is_predictable), match['id'])
                                            execute_query(query, values)
                                            update_scores_for_match(match['id'])
                                            st.success("✅ Match updated successfully!")
                                            st.session_state[f"edit_mode_{match['id']}"] = False
                                            st.rerun()
                                    with col_form2:
                                        if st.form_submit_button("❌ Cancel"):
                                            st.session_state[f"edit_mode_{match['id']}"] = False
                                            st.rerun()

            col1, col2 = st.columns(2)
            with col1:
                if st.button(f"🗑️ Delete Matches in {r['name']}", key=f"del_matches_{r['id']}"):
                    ctrl.delete_matches_by_round(r['id'])
                    st.warning(f"Matches deleted for round: {r['name']}")
                    st.rerun()

            with col2:
                if st.button(f"❌ Delete Round '{r['name']}'", key=f"del_round_{r['id']}"):
                    ctrl.delete_round(r['id'])
                    st.error(f"Round '{r['name']}' deleted.")
                    st.rerun()


