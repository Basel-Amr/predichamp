import streamlit as st
from streamlit_extras.switch_page_button import switch_page
import streamlit.components.v1 as components
from datetime import datetime
import pytz
import time
import streamlit_antd_components as sac

import Manage_Controllers.manage_players_controller as ctrl


def manage_players():
    st.markdown("""
        <style>
        .glass-box {
            background: linear-gradient(145deg, rgba(240, 248, 255, 0.7), rgba(255, 255, 255, 0.4));
            box-shadow: 0 12px 24px rgba(0, 0, 0, 0.15);
            backdrop-filter: blur(8px);
            border-radius: 16px;
            padding: 20px 25px;
            margin-bottom: 25px;
            transition: all 0.3s ease-in-out;
        }
        .glass-box:hover {
            transform: scale(1.01);
            box-shadow: 0 16px 32px rgba(0, 0, 0, 0.2);
        }
        .section-title {
            font-size: 32px;
            font-weight: 800;
            text-align: center;
            margin: 40px 0 30px;
            color: #0f172a;
            background: -webkit-linear-gradient(45deg, #3b82f6, #06b6d4);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        .player-info {
            font-size: 18px;
            line-height: 1.6;
            color: #1f2937;
            margin-top: 12px;
        }
        </style>
    """, unsafe_allow_html=True)

    st.markdown("<div class='section-title'>👥 Manage Players</div>", unsafe_allow_html=True)

    players = ctrl.get_all_players()
    if not players:
        st.warning("No players found.")
        return

    for p in players:
        with st.expander(f"🧑 {p['username']} — ID: {p['id']}"):
            player = dict(ctrl.get_player_by_id(p['id']))
            predictions_count = ctrl.get_player_prediction_count(p['id'])
            col1, col2 = st.columns(2)
            with col1:
                player['username'] = st.text_input("Username", value=player['username'], key=f"usr_{p['id']}")
                player['email'] = st.text_input("Email", value=player['email'], key=f"email_{p['id']}")
                player['timezone'] = st.text_input("Timezone", value=player['timezone'], key=f"tz_{p['id']}")
                player['avatar_name'] = st.text_input("Avatar Path", value=player['avatar_name'], key=f"ava_{p['id']}")
                player['new_password'] = st.text_input("🔑 New Password", value="", type="password", key=f"pw_{p['id']}")
            with col2:
                player['bonous'] = st.number_input("Bonus Points", value=player['bonous'], key=f"bonus_{p['id']}")
                player['role'] = st.selectbox("Role", ["player", "admin"], index=0 if player['role'] == "player" else 1, key=f"role_{p['id']}")
                st.markdown(f"<span class='player-info'><b>Total Predictions:</b> {predictions_count}</span>", unsafe_allow_html=True)
                st.markdown(f"<span class='player-info'><b>Created At:</b> {player['created_at']}</span>", unsafe_allow_html=True)
                st.markdown(f"<span class='player-info'><b>Last Login:</b> {player['last_login_at'] or 'Never'}</span>", unsafe_allow_html=True)
                st.markdown(f"<span class='player-info'><b>Score from Predictions:</b> {player['total_prediction_score']}</span>", unsafe_allow_html=True)


            if st.button("💾 Save Info", key=f"save_info_{p['id']}"):
                updated = ctrl.update_player_info(player)
                if updated:
                    st.success("✅ Player info updated!")
                else:
                    st.warning("⚠️ No changes or update failed.")
            if st.button(f"🗑️ Delete Player", key=f"delete_{p['id']}"):
                confirmed = st.warning("Are you sure you want to delete this player? This action cannot be undone.")
                if st.button(f"✅ Confirm Delete {p['id']}", key=f"confirm_delete_{p['id']}"):
                    deleted = ctrl.delete_player(p['id'])
                    if deleted:
                        st.success(f"✅ Player {p['username']} deleted successfully.")
                        st.experimental_rerun()
                    else:
                        st.error("❌ Failed to delete the player.")

            st.markdown("""<hr style='margin:20px 0;'>""", unsafe_allow_html=True)
            st.markdown("<div class='section-title'>📅 Predictions (Next Round)</div>", unsafe_allow_html=True)

            next_round = ctrl.get_next_round()
            if not next_round:
                st.info("No upcoming round found.")
                return

            predictions = ctrl.get_player_predictions_for_round(p['id'], next_round['id'])
            predictions_dict = {
                pred['match_id']: {
                    'home': pred['predicted_home_score'],
                    'away': pred['predicted_away_score']
                }
                for pred in predictions
            }

            matches = next_round['matches']
            for match in matches:
                match_id = match['id']
                home = match['home_team_name']
                away = match['away_team_name']
                prev = predictions_dict.get(match_id, {"home": 0, "away": 0})
                # Convert UTC time to player timezone in 12-hour format
                utc_dt = datetime.fromisoformat(match['match_datetime'])  # assuming this is in ISO format and UTC
                player_tz = pytz.timezone(player['timezone'] or "Africa/Cairo")
                localized_dt = pytz.utc.localize(utc_dt).astimezone(player_tz)
                formatted_time = localized_dt.strftime("%Y-%m-%d • %I:%M %p")  # e.g., "2025-07-06 • 08:30 PM"

                with st.container():
                    st.markdown(f"""
                        <div class='glass-box'>
                            <b>{home} vs {away}</b><br>
                            <small style='color:gray;'>Kickoff: {formatted_time} ({player['timezone']})</small>
                    """, unsafe_allow_html=True)

                    col1, col2, col3 = st.columns([2, 2, 1])
                    with col1:
                        home_score = st.number_input(f"{home} goals", min_value=0, value=prev['home'], key=f"ph_{p['id']}_{match_id}")
                    with col2:
                        away_score = st.number_input(f"{away} goals", min_value=0, value=prev['away'], key=f"pa_{p['id']}_{match_id}")
                    with col3:
                        if st.button("💾 Save", key=f"save_pred_{p['id']}_{match_id}"):
                            saved = ctrl.save_predictions_for_player(p['id'], {
                                match_id: {
                                    "home": home_score,
                                    "away": away_score
                                }
                            })
                            if saved:
                                st.success("✅ Prediction saved!")
                            else:
                                st.warning("⚠️ No valid prediction or already saved.")
                    st.markdown("</div>", unsafe_allow_html=True)
