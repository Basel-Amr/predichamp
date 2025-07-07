import os
import base64
import streamlit as st
from Controllers.teams_controller import get_team_full_info, get_league_info_for_team, get_team_squad, get_participated_league
import pytz
from datetime import datetime
from tzlocal import get_localzone
from datetime import datetime
from Renders.render_helpers import render_league_banner
from Controllers import fixtures_controller as ctrl
from Renders.render_leagues_helper import render_table, render_rules

LEAGUE_COLORS = {
    "Premier League": "#1e1f57,#932790",        # Deep navy & royal purple (lion mane)
    "Primera Division": "#ff3a20,#ffd700",      # Red & yellow (Spanish flag tone)
    "Serie A": "#005daa,#00e0ca",               # Classic blue + teal accent
    "Bundesliga": "#e30613,#ffffff",            # Pure red & white (official)
    "Ligue 1": "#001c3d,#ffdc00",               # Navy blue & yellow (Hexagoal theme)
    "Champions League": "#0a0a23,#4c8eda",      # Deep night blue & light star blue
    "Europa League": "#ff7c00,#121212",         # Bright orange & dark gray/black
}

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

# Phase 1: Top Club Header
def render_team_header(team, coach):
    logo_src = render_team_logo_img(os.path.join("Assets", "Teams", team['logo_path']))

    def safe(val, default="Unknown"):
        return val if val else default

    # Shirt colors parsing
    shirt_colors = safe(team['club_colors'])
    color_list = [c.strip().lower() for c in shirt_colors.split('/') if c.strip()]

    def css_safe_color(c):
        mapping = {
            'navy blue': 'navy',
            'sky blue': 'skyblue',
            'dark red': 'darkred'
        }
        return mapping.get(c, c)

    shirt_colors_html = ''.join(
        f'<span style="background-color:{css_safe_color(color)};width:16px;height:16px;display:inline-block;border-radius:50%;margin-right:4px;border:1px solid white;"></span>'
        for color in color_list
    ) if shirt_colors != "Unknown" else 'Unknown'

    website = safe(team['website'], '#')
    website_display = team['website'] if team['website'] else 'Unknown'

    import pycountry
    def country_flag(name):
        try:
            country = pycountry.countries.get(name=name)
            if country:
                return chr(127397 + ord(country.alpha_2[0])) + chr(127397 + ord(country.alpha_2[1]))
        except:
            pass
        return ""

    flag_emoji = country_flag(safe(coach['nationality']))

    st.markdown(f"""
        <style>
            .team-header {{
                background: linear-gradient(135deg, #1e293b, #0f172a);
                padding: 24px;
                border-radius: 20px;
                margin-bottom: 24px;
                color: #f9fafb;
                display: flex;
                flex-direction: column;
                gap: 24px;
                box-shadow: 0 0 10px rgba(255,255,255,0.05);
            }}

            .team-main-info {{
                display: flex;
                align-items: center;
                gap: 20px;
                flex-wrap: wrap;
            }}

            .team-logo {{
                width: 95px;
                height: 95px;
                border-radius: 16px;
                object-fit: contain;
                background-color: #fff;
                padding: 8px;
                box-shadow: 0 0 12px rgba(255, 255, 255, 0.1);
                transition: transform 0.3s ease;
            }}

            .team-logo:hover {{
                transform: scale(1.08);
                box-shadow: 0 0 12px rgba(255,255,255,0.3);
            }}

            .club-name {{
                font-size: 28px;
                font-weight: 800;
                margin-bottom: 6px;
            }}

            .coach-info {{
                display: flex;
                align-items: center;
                gap: 14px;
                font-size: 15px;
                color: #d1d5db;
            }}

            .coach-img {{
                width: 42px;
                height: 42px;
                border-radius: 50%;
                object-fit: cover;
                box-shadow: 0 0 6px rgba(255,255,255,0.1);
                transition: transform 0.3s ease;
            }}

            .coach-img:hover {{
                transform: scale(1.1);
            }}

            .details-table {{
                border-collapse: collapse;
                width: 100%;
            }}

            .details-table td {{
                padding: 8px 12px;
                font-size: 14px;
                vertical-align: top;
                color: #e5e7eb;
                border-bottom: 1px solid #1f2937;
            }}

            .details-table tr:hover td {{
                background-color: #1f2937;
            }}
        </style>
        <div class="team-header">
            <div class="team-main-info">
                <img src="{logo_src}" class="team-logo">
                <div>
                    <div class="club-name">{safe(team['official_name'])}</div>
                    <div class="coach-info">
                        <img src="https://cdn-icons-png.flaticon.com/512/3135/3135715.png" class="coach-img">
                        <div>{safe(coach['name'])}<br><small>{flag_emoji} {safe(coach['nationality'])}</small></div>
                    </div>
                </div>
            </div>
            <table class="details-table">
                <tr><td>🌍 Nationality</td><td>{safe(team['nationality'])}</td></tr>
                <tr><td>🏟️ Venue</td><td>{safe(team['Venue_name'])} ({safe(team['venue_location'])})</td></tr>
                <tr><td>👥 Capacity</td><td>{safe(team['venue_capacity'])}</td></tr>
                <tr><td>🎽 Club Colors</td><td>{shirt_colors_html}</td></tr>
                <tr><td>📅 Founded</td><td>{safe(team['founded'])}</td></tr>
                <tr><td>🌐 Website</td><td><a href="{website}" target="_blank" style="color:#60a5fa;">{website_display}</a></td></tr>
                <tr><td>📍 Address</td><td>{safe(team['address'])}</td></tr>
            </table>
        </div>
    """, unsafe_allow_html=True)


    
def render_team_matches(team_id):
    team_data = get_team_full_info(team_id)
    team_info = team_data['team']
    matches = team_data['matches'] if team_data and 'matches' in team_data else []

    col1, col2 = st.columns([1, 1])

    with col1:
        st.markdown("""
            <style>
                .matches-panel {
                    background-color: #111827;
                    padding: 20px;
                    border-radius: 18px;
                    color: white;
                    width: 100%;
                }

                .match-row {
                    display: flex;
                    align-items: center;
                    justify-content: space-between;
                    padding: 10px 15px;
                    border-bottom: 1px solid #1f2937;
                }

                .match-left {
                    display: flex;
                    flex-direction: column;
                    gap: 4px;
                }

                .match-competition {
                    font-size: 13px;
                    color: #9ca3af;
                }

                .match-date {
                    font-size: 12px;
                    color: #6b7280;
                }

                .match-center {
                    font-size: 14px;
                    font-weight: 600;
                    text-align: center;
                }

                .match-status {
                    background-color: #10b981;
                    font-size: 12px;
                    color: white;
                    padding: 2px 8px;
                    border-radius: 9999px;
                }
                .team-logo-small {
                    width: 20px;
                    height: 20px;
                    object-fit: contain;
                    background-color: white;
                    border-radius: 4px;
                    margin: 0 6px;
                    vertical-align: middle;
                    box-shadow: 0 0 4px rgba(255,255,255,0.1);
                }
            </style>

            <div class="matches-panel">
                <h4 style="text-align:center; color:#f9fafb;">📅 Recent Matches</h4>
        """, unsafe_allow_html=True)

        for match in matches[:22]:  # Limit to recent 5
            home = match['home_team_name']
            away = match['away_team_name']
            
            home_logo_path = os.path.join("Assets", "Teams", match['home_team_logo'])
            away_logo_path = os.path.join("Assets", "Teams", match['away_team_logo'])
            home_logo_src = render_team_logo_img(home_logo_path)
            away_logo_src = render_team_logo_img(away_logo_path)
            # Convert UTC to local
            utc_dt = datetime.fromisoformat(match['match_datetime'].replace("Z", ""))
            local_dt = pytz.utc.localize(utc_dt).astimezone(get_localzone())
            time_str = local_dt.strftime('%I:%M %p')
            date_friendly = local_dt.strftime('%a %d %b %Y')
            comp = match['league_name']
            score = f"{match['home_score']} - {match['away_score']}" if match['status'] == 'finished' else "vs"

            st.markdown(f"""
            <div class="match-row">
                <div class="match-left">
                    <div class="match-competition">{comp}</div>
                    <div class="match-date">{date_friendly} | {time_str}</div>
                </div>
                <div class="match-center">
                    <img src="{home_logo_src}" class="team-logo-small"> {home} 
                    {score} 
                    {away} <img src="{away_logo_src}" class="team-logo-small">
                </div>
                <div class="match-status">{match['status'].capitalize()}</div>
            </div>
        """, unsafe_allow_html=True)
    
    with col2:
        league = get_league_info_for_team(team_id)
        render_league_banner(league['name'], ctrl.get_logo_path_from_league(league['name']))
        render_table(league['id'], league['country'], league['name'],team_info['name'])
        render_rules(league['name'])

def calculate_age(birthdate_str):
    try:
        birthdate = datetime.strptime(birthdate_str, "%Y-%m-%d")
        today = datetime.today()
        return today.year - birthdate.year - ((today.month, today.day) < (birthdate.month, birthdate.day))
    except:
        return None

def render_team_squad(team_id):
    squad = get_team_squad(team_id)
    if not squad:
        st.info("No squad data available.")
        return

    position_colors = {
        "Goalkeeper": "#f59e0b",
        "Defence": "#3b82f6",
        "Midfield": "#10b981",
        "Offence": "#ef4444",
    }

    position_icons = {
        "Goalkeeper": "🧤",
        "Defence": "🛡️",
        "Midfield": "🎯",
        "Offence": "⚔️"
    }

    grouped = {}
    for player in squad:
        pos = player['position'] or "Unknown"
        if pos not in grouped:
            grouped[pos] = []
        grouped[pos].append(player)

    st.markdown("""
        <style>
            .full-width-container {
                width: 100%;
                margin: 0 auto;
                background-color: #1f2937;
                padding: 20px;
                border-radius: 16px;
                box-shadow: 0 0 10px rgba(255,255,255,0.05);
            }

            .position-title {
                font-size: 20px;
                font-weight: 700;
                margin: 24px 0 14px;
            }

            .player-row {
                display: flex;
                justify-content: space-between;
                align-items: center;
                padding: 8px 0;
                border-bottom: 1px solid #374151;
            }

            .player-row:last-child {
                border-bottom: none;
            }

            .player-number {
                font-size: 14px;
                color: #9ca3af;
                margin-right: 8px;
                width: 32px;
                text-align: center;
            }

            .player-info {
                flex-grow: 1;
                max-width: 280px;
                text-align: right;
                margin-right: 12px;
            }

            .player-name {
                font-weight: bold;
                color: white;
            }

            .player-meta {
                color: #9ca3af;
                font-size: 13px;
            }

            .position-icon {
                font-size: 18px;
                padding-left: 4px;
            }
        </style>
        <div class="full-width-container">
    """, unsafe_allow_html=True)

    for position, players in grouped.items():
        color = position_colors.get(position, "#9ca3af")
        icon = position_icons.get(position, "❓")
        st.markdown(f"""<div class="position-title" style="color:{color};">{icon} {position}</div>""", unsafe_allow_html=True)

        for p in players:
            age = calculate_age(p['date_of_birth']) or "-"
            st.markdown(f"""
                <div class="player-row">
                    <div class="player-number">{p['shirt_number'] or '-'}</div>
                    <div class="player-info">
                        <div class="player-name">{p['name']}</div>
                        <div class="player-meta">{age} yrs | {p['nationality']}</div>
                    </div>
                    <div class="position-icon">{icon}</div>
                </div>
            """, unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)

def render_participated_leagues(team_id):
    leagues = get_participated_league(team_id)

    if not leagues:
        st.info("No league participation history found.")
        return

    st.markdown("""
        <style>
            .leagues-container {
                background-color: #111827;
                padding: 24px;
                border-radius: 18px;
                margin-top: 26px;
                box-shadow: 0 0 14px rgba(255,255,255,0.04);
                color: #f9fafb;
            }

            .leagues-title {
                font-size: 22px;
                font-weight: 800;
                margin-bottom: 22px;
                text-align: center;
                color: #facc15;
                letter-spacing: 0.5px;
            }

            .league-name {
                font-weight: 700;
                font-size: 24px;
                flex-grow: 1;
            }

            .season-range {
                color: #f9fafb;
                font-size: 13px;
                text-align: right;
            }

            .team-logo-small {
                width: 72px;
                height: 72px;
                object-fit: contain;
                background-color: transparent;
                border-radius: 10px;
                margin-right: 14px;
                box-shadow: 0 0 6px rgba(255,255,255,0.15);
            }
        </style>
        <div class="leagues-container">
            <div class="leagues-title">🏆 League Participation History</div>
    """, unsafe_allow_html=True)

    for league in leagues:
        league_path = os.path.join("Assets", "Leagues", league['logo_path'])
        league_path_src = render_team_logo_img(league_path)

        # Get league colors or fallback
        color_pair = LEAGUE_COLORS.get(league['league_name'], "#374151,#1f2937")
        bg_color, hover_color = color_pair.split(",")

        st.markdown(f"""
            <div class="league-row" style="
                display: flex;
                align-items: center;
                margin-bottom: 14px;
                font-size: 16px;
                padding: 12px 16px;
                border-radius: 12px;
                background-color: {bg_color};
                transition: transform 0.3s ease, box-shadow 0.3s ease;
                box-shadow: 0 0 10px rgba(0,0,0,0.2);"
                onmouseover="this.style.boxShadow='0 0 16px {hover_color}'; this.style.transform='scale(1.02)'"
                onmouseout="this.style.boxShadow='0 0 10px rgba(0,0,0,0.2)'; this.style.transform='scale(1)'"
            >
                <img src="{league_path_src}" class="team-logo-small" style="width:72px; height:72px;">
                <div class="league-name">{league['league_name']}</div>
                <div class="season-range">{league['season_start']} ➜ {league['season_end']}</div>
            </div>
        """, unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)



def render_team_gallery(teams):
    query_params = st.query_params

    if query_params.get("scroll_to") == "details":
        st.markdown("""
            <script>
                setTimeout(function() {
                    const el = document.getElementById("team-details");
                    if (el) el.scrollIntoView({ behavior: "smooth", block: "start" });
                }, 500);
            </script>
        """, unsafe_allow_html=True)
        query_params.clear()  # Optional: reset after scroll

    st.markdown("""
        <style>
            .team-card {
                position: relative;
                width: 140px;
                height: 140px;
                border-radius: 50%;
                background-color: #1f2937;
                margin: 30px auto;
                box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
                cursor: pointer;
                overflow: hidden;
                transition: transform 0.25s ease, box-shadow 0.25s ease;
                display: flex;
                align-items: center;
                justify-content: center;
                text-align: center;
            }
            .team-card:hover {
                transform: scale(1.1);
                box-shadow: 0 6px 20px rgba(255,255,255,0.2);
            }
            .team-card-content {
                z-index: 1;
                display: flex;
                flex-direction: column;
                align-items: center;
                justify-content: center;
            }
            .team-logo {
                width: 90px;
                height: 90px;
                object-fit: contain;
                border-radius: 50%;
                box-shadow: 0 0 6px rgba(255, 255, 255, 0.2);
                margin-bottom: 6px;
            }
            .team-name {
                font-size: 13px;
                font-weight: 600;
                color: #f9fafb;
                margin-bottom: 2px;
                text-shadow: 0 0 4px rgba(0, 0, 0, 0.5);
            }
            .team-nation {
                font-size: 11px;
                color: #d1d5db;
            }
            .fallback-icon {
                font-size: 36px;
                color: white;
                margin-bottom: 6px;
                text-shadow: 0 0 6px rgba(0, 0, 0, 0.6);
            }
            .click-form button {
                all: unset;
                width: 100%;
                height: 100%;
                position: absolute;
                top: 0;
                left: 0;
                z-index: 2;
                cursor: pointer;
            }
        </style>
        <h3 style='text-align:center; color:#10b981; font-size: 30px;'>🏟️ Club Gallery</h3>
        <p style='text-align:center; color:#9ca3af; font-size: 16px;'>Click a team to view its details</p>
        <br>
    """, unsafe_allow_html=True)

    cols = st.columns(3)

    for idx, team in enumerate(teams):
        team_id = team["id"]
        name = team["name"]
        nationality = team["nationality"]
        color = team["color"]
        logo_src = render_team_logo_img(os.path.join("Assets", "Teams", team['logo_path']))

        with cols[idx % 3]:
            with st.form(f"form_{team_id}", clear_on_submit=True):
                clicked = st.form_submit_button(label="", help=f"Click to select {name}")

                card_content = f"""
                    <div class="team-card" style="background: {color};">
                        <div class="click-form"><button type="submit"></button></div>
                        <div class="team-card-content">
                            {f'<img src="{logo_src}" class="team-logo">' if logo_src else '<div class="fallback-icon">❓</div>'}
                            <div class="team-name">{name}</div>
                            <div class="team-nation">{nationality}</div>
                        </div>
                    </div>
                """

                st.markdown(card_content, unsafe_allow_html=True)

                if clicked:
                    st.session_state["selected_team_id"] = team_id
                    st.session_state["selected_team_name"] = name
                    st.toast(f"✅ You selected {name} (ID: {team_id})")
                    st.markdown("""
                        <script>
                            window.location.search = '?scroll_to=details';
                        </script>
                    """, unsafe_allow_html=True)
                    # 👇 Add query param and rerun to trigger scroll next time
                    st.query_params["scroll_to"] = "details"
                    #st.rerun()

    if "selected_team_id" in st.session_state:
        st.markdown('<div id="team-details"></div>', unsafe_allow_html=True)
        st.markdown("---")
        st.success(f"🎯 Selected Team: **{st.session_state['selected_team_name']}** (ID: `{st.session_state['selected_team_id']}`)")
        team_data = get_team_full_info(st.session_state['selected_team_id'])
        if team_data:
            render_team_header(team_data["team"], team_data["coach"])
            render_participated_leagues(st.session_state['selected_team_id'])
            render_team_matches(st.session_state['selected_team_id'])
            #render_team_squad(team_data["team"]['id'])
            render_team_squad(st.session_state['selected_team_id'])  # 👥 Show squad



