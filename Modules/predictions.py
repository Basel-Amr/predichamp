from Modules import under_update
import streamlit as st
from datetime import datetime
from Controllers import predictions_controller as ctrl
from Renders.render_predictions_helper import render_league_banner, render_match_card
from dateutil import tz
import pytz

# def render(player_id):
#     under_update.under_update_view()

def render(player_id):
    # 🌍 Get user's local timezone
    local_tz = ctrl.get_localzone_for_player(player_id)
    print("Player timezone:", local_tz.zone)  # Optional debug
    now_local = datetime.now(local_tz)

    # 🌟 Title
    st.markdown("""
    <div style="
        text-align: center; 
        padding: 30px 20px; 
        margin-bottom: 30px; 
        background: linear-gradient(90deg, #003566, #00509e);
        border-radius: 12px;
        box-shadow: 0 4px 15px rgba(0, 53, 102, 0.3);
        color: white;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    ">
        <h1 style="
            font-size: 3rem; 
            font-weight: 900; 
            letter-spacing: 2px; 
            margin-bottom: 10px;
        ">
            Predict & Conquer<br>Round by Round!
        </h1>
        <p style="
            font-size: 1.3rem; 
            font-weight: 500; 
            opacity: 0.85;
            max-width: 600px;
            margin: 0 auto;
            line-height: 1.4;
        ">
            Stay ahead of the game with real-time predictions, <br>
            challenge yourself each matchday, and track your score progress!
        </p>
    </div>
    """, unsafe_allow_html=True)

    # 📥 Fetch fixtures grouped by round
    rounds = ctrl.get_upcoming_predictable_fixtures_grouped_by_round()
    if not rounds:
        st.info("No upcoming rounds with predictable fixtures.")
        return

    # Sort rounds by deadline (UTC)
    sorted_rounds = sorted(rounds.items(), key=lambda x: x[1]["deadline"])

    # Build selectbox options
    options = []
    for round_id, info in sorted_rounds:
        deadline_utc = datetime.fromisoformat(info["deadline"]).replace(tzinfo=pytz.UTC)
        deadline_local = deadline_utc.astimezone(local_tz)
        options.append({
            "label": f"{info['round_name']} — Deadline: {deadline_local.strftime('%b %d, %Y %I:%M %p')}",
            "round_id": round_id,
            "deadline_local": deadline_local
        })

    # 🎯 Select default round
    now_local = datetime.now(local_tz)
    default_index = next(
        (i for i, opt in enumerate(options) if opt["deadline_local"] > now_local),
        len(options) - 1
    )

    # 🎯 Select round from dropdown
    selected_label = st.selectbox("🔘 Select Gameweek", options=[opt["label"] for opt in options], index=default_index)
    selected_index = next(i for i, opt in enumerate(options) if opt["label"] == selected_label)
    selected_round_id = options[selected_index]["round_id"]
    selected_round = rounds[selected_round_id]

    # 🧮 Match stats
    predicted, unpredicted = ctrl.get_prediction_stats_for_player(player_id, selected_round_id)
    match_count = selected_round.get("match_count", len(selected_round["matches"]))
    deadline_local = options[selected_index]["deadline_local"]
    time_left = deadline_local - now_local
    can_predict = now_local < deadline_local

    # ✨ Style for completion animation (must be injected separately before HTML)
    confetti_animation = """
    <style>
    @keyframes pop {
        0% { transform: scale(0.8); opacity: 0.2; }
        50% { transform: scale(1.05); opacity: 1; }
        100% { transform: scale(1); }
    }
    .prediction-done {
        animation: pop 0.8s ease-in-out;
        color: #0a4700;
        font-weight: 800;
        font-size: 1.2rem;
        background: linear-gradient(90deg, #ccffcc, #b2f2bb);
        padding: 16px 24px;
        border-radius: 12px;
        margin-top: 18px;
        margin-bottom: 10px;
        box-shadow: 0 0 20px rgba(0, 128, 0, 0.25);
        text-align: center;
        letter-spacing: 0.5px;
    }
    </style>
    """

    # Render confetti style early if needed
    if can_predict and unpredicted == 0:
        st.markdown(confetti_animation, unsafe_allow_html=True)

    # 🔔 Prediction status block
    prediction_status_html = f"""
        <div style="text-align: center; margin-top: 10px;">
            <p style="font-size: 1rem; color: #333; font-weight: 600; margin-bottom: 0;">
                ✅ <b>{predicted}</b> predicted &nbsp;&nbsp;|&nbsp;&nbsp; ⏳ <b>{unpredicted}</b> remaining
            </p>
    """

    # 🧾 Round header info
    header_html = f"""
        <div style="margin-top: 10px; margin-bottom: 20px; padding: 14px 20px; border-radius: 12px;
                    background: linear-gradient(90deg, #edf2fb, #e2eafc);
                    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08); text-align: center;">
            <h2 style="color: #003566; font-size: 1.7rem; margin-bottom: 8px;">
                🗓️ Fixtures for <span style="color: #003566;">{selected_round['round_name']}</span>
            </h2>
            <p style="font-size: 1rem; color: #495057; font-weight: 500;">
                <span style="background-color: #dbeafe; color: #1d4ed8; padding: 4px 10px;
                            border-radius: 20px; font-weight: 600;">
                    {match_count} match{'es' if match_count != 1 else ''}
                </span>
                <br><br>
                {"⏳ Prediction closes: <b>" + deadline_local.strftime('%b %d, %Y %I:%M %p %Z') + "</b><br>🕒 Time left: <b>" + str(time_left).split('.')[0] + "</b>" if can_predict else "❌ <b>Prediction deadline passed!</b>"}
            </p>
            {prediction_status_html}
        </div>
    """

    st.markdown(header_html, unsafe_allow_html=True)

    # 📊 Group matches by league
    grouped_by_league = {}
    for match in selected_round["matches"]:
        league = match["league_name"]
        grouped_by_league.setdefault(league, []).append(match)

    # 🧾 Render league banners and matches
    for league_name, league_matches in grouped_by_league.items():
        render_league_banner(league_name, ctrl.get_logo_path_from_league(league_name))
        for match in league_matches:
            render_match_card(match, player_id, can_predict=can_predict)
