from Modules import under_update
from Controllers import leaderboard_controller as ctrl
import streamlit as st
import os
import base64
# def render(player_id):
#     under_update.under_update_view()

def convert_img_to_base64(path):
    if not os.path.exists(path):
        print(f"[⚠️ File not found]: {path}")
        return None
    try:
        with open(path, "rb") as img_file:
            encoded = base64.b64encode(img_file.read()).decode("utf-8")
        return encoded
    except Exception as e:
        print(f"[❌ Error reading file]: {path} → {e}")
        return None

def render_team_logo_img(logo_path):
    logo_b64 = convert_img_to_base64(logo_path)
    return f"data:image/png;base64,{logo_b64}" if logo_b64 else None

def render(player_id):
    player = ctrl.get_player_info(player_id)
    if not player:
        st.warning("Player not found")
        return

    st.markdown(f"""
        <div style="background-color:#1f2937; padding:30px; border-radius:16px; margin-top:24px; box-shadow: 0 0 12px rgba(255,255,255,0.04);">
            <h2 style="color:#facc15; text-align:center;">🏅 Player Profile</h2>
            <div style="text-align:center;">
                <img src="{render_team_logo_img(os.path.join('Assets', 'Avatars', player['avatar_path']))}" style="width:80px; height:80px; border-radius:50%; box-shadow:0 0 6px rgba(255,255,255,0.2); margin-bottom:10px;">
                <h3 style="color:#f9fafb;">{player['username']}</h3>
                <p style="color:#9ca3af; font-size:13px;">📧 {player['email']} • 🕓 Joined: {player['created_at'][:10]}</p>
                <div style="margin-top:12px; color:#facc15; font-size:16px;">
                    <strong>🏆 Rank #{player['rank']} | 💯 {player['total_points']} pts</strong>
                </div>
                <div style="margin-top:8px; font-size:14px; color:#9ca3af;">
                    Leagues Won: <b>{player['total_leagues_won']}</b> • Cups Won: <b>{player['total_cups_won']}</b>
                </div>
            </div>
        </div>
    """, unsafe_allow_html=True)
    leaderboard = ctrl.fetch_all("""
        SELECT p.id, p.username, p.avatar_name,
               COALESCE((SELECT SUM(score) FROM predictions WHERE player_id = p.id), 0) + COALESCE(p.bonous, 0) AS total_points,
               p.total_leagues_won, p.total_cups_won
        FROM players p
        ORDER BY total_points DESC, p.username ASC
    """)

    st.markdown("""
        <style>
            .card-list {
                display: flex;
                flex-direction: column;
                gap: 16px;
                margin-top: 30px;
                justify-content: center;
            }
            .card {
                background-color: #111827;
                border-radius: 12px;
                padding: 16px 24px;
                width: 100%;
                box-shadow: 0 0 8px rgba(255,255,255,0.05);
                transition: transform 0.2s ease, box-shadow 0.2s ease;
                display: flex;
                align-items: center;
                justify-content: space-between;
            }
            .card:hover {
                transform: scale(1.01);
                box-shadow: 0 0 12px rgba(255,255,255,0.08);
            }
            .card.highlight {
                border: 2px solid #facc15;
            }
            .avatar-small {
                width: 64px;
                height: 64px;
                border-radius: 50%;
                object-fit: cover;
                box-shadow: 0 0 4px rgba(255,255,255,0.1);
                margin-right: 16px;
            }
            .player-info {
                flex-grow: 1;
                text-align: left;
            }
            .username {
                color: #f9fafb;
                font-size: 16px;
                font-weight: 600;
                margin-bottom: 4px;
            }
            .meta {
                color: #9ca3af;
                font-size: 13px;
            }
            .rank-points {
                text-align: right;
                color: #facc15;
                font-weight: bold;
                font-size: 15px;
                white-space: nowrap;
            }
        </style>
        <div class="card-list">
    """, unsafe_allow_html=True)

    for idx, row in enumerate(leaderboard):
        pid, username, avatar, total, leagues, cups = row
        avatar_src = render_team_logo_img(os.path.join("Assets", "Avatars", avatar)) if avatar else ""
        highlight_class = "highlight" if pid == player_id else ""

        st.markdown(f"""
            <div class="card {highlight_class}">
                <img src="{avatar_src}" class="avatar-small">
                <div class="player-info">
                    <div class="username">{username}</div>
                    <div class="meta">Leagues: {leagues} • Cups: {cups}</div>
                </div>
                <div class="rank-points">#{idx + 1}<br>{total} pts</div>
            </div>
        """, unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)