import streamlit as st
import base64
from pathlib import Path
from datetime import datetime, timedelta
from tzlocal import get_localzone
import pytz
import os

# 🎨 Optional: Unique colors per league
LEAGUE_COLORS = {
    "Premier League": "#38003c,#7515a9",
    "La Liga": "#cc1f2f,#ff5e5b",
    "Serie A": "#0056a3,#00bfff",
    "Bundesliga": "#d00027,#ff8080",
    "Ligue 1": "#132257,#2c4bc9",
    "Champions League": "#090979,#00d4ff",
    "Europa League": "#ff7c00,#f83600"
}

import re

def render_league_banner(league_name, logo_path=None):
    """
    Render a stunning, league-specific banner with a custom gradient and floating logo.
    Ensures CSS classes are unique per league.
    """
    # Gradient colors
    gradient = LEAGUE_COLORS.get(league_name, "#003366,#004080")

    # Generate unique, safe CSS class
    class_id = re.sub(r'\W+', '', league_name.lower())
    banner_class = f"league-banner-{class_id}"
    logo_class = f"circle-logo-{class_id}"
    float_logo = f"float-logo-{class_id}"

    # Image as base64
    logo_html = ""
    if logo_path:
        logo_b64 = convert_img_to_base64(logo_path)
        logo_html = f"""
        <div class="{logo_class}">
            <img src="data:image/png;base64,{logo_b64}" class="league-logo" alt="logo" />
        </div>
        """

    st.markdown(f"""
        <style>
            .{banner_class} {{
                background: linear-gradient(90deg, {gradient});
                border-radius: 14px;
                padding: 20px 30px;
                margin-top: 25px;
                margin-bottom: 15px;
                color: white;
                font-size: 2rem;
                font-weight: 900;
                display: flex;
                justify-content: space-between;
                align-items: center;
                box-shadow: 0 8px 16px rgba(0,0,0,0.25);
                transition: transform 0.2s ease, box-shadow 0.2s ease;
            }}
            .{banner_class}:hover {{
                transform: scale(1.02);
                box-shadow: 0 12px 24px rgba(0,0,0,0.35);
            }}
            .{logo_class} {{
                border: 4px solid white;
                border-radius: 50%;
                padding: 8px;
                height: 70px;
                width: 70px;
                display: flex;
                justify-content: center;
                align-items: center;
                background-color: white;
                animation: {float_logo} 2.5s infinite ease-in-out;
            }}
            .league-logo {{
                height: 40px;
                width: 40px;
                border-radius: 50%;
            }}
            @keyframes {float_logo} {{
                0% {{ transform: translateY(0px); }}
                50% {{ transform: translateY(-5px); }}
                100% {{ transform: translateY(0px); }}
            }}
        </style>

        <div class="{banner_class}">
            <div>🏆 {league_name}</div>
            {logo_html}
        </div>
    """, unsafe_allow_html=True)



def convert_img_to_base64(path):
    try:
        with open(path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode("utf-8")
    except FileNotFoundError:
        return None
    
def calculate_countdown(local_dt):
    now = datetime.now(get_localzone())

    if now < local_dt:
        # Match hasn't started yet
        diff = local_dt - now
        days = diff.days
        hours = diff.seconds // 3600
        minutes = (diff.seconds % 3600) // 60
        seconds = diff.seconds % 60
        return "upcoming", (days, hours, minutes, seconds)

    elif now < local_dt + timedelta(hours=2):
        # Match is live
        return "live", None

    else:
        # Match has finished
        return "finished", None

def render_deadline(days, hours, minutes, seconds):
    return f"""
    <div style="
        margin-top: 20px;
        font-family: 'Segoe UI', sans-serif;
        text-align: center;
        color: #fff;
        font-weight: 600;
        font-size: 2.2rem;
        text-shadow: 0 0 8px rgba(255, 100, 100, 0.8);
        letter-spacing: 2px;
        animation: pulseGlow 2s infinite;
    ">
        ⏳ {days} <span style="color:#ffcccc; font-size:1.2rem;">d</span> 
        {hours:02} <span style="color:#ff9999; font-size:1.2rem;">h</span> 
        {minutes:02} <span style="color:#ff6666; font-size:1.2rem;">m</span> 
        {seconds:02} <span style="color:#ff3333; font-size:1.2rem;">s</span>
    </div>

    <style>
    @keyframes pulseGlow {{
        0% {{ text-shadow: 0 0 8px rgba(255, 80, 80, 0.7); }}
        50% {{ text-shadow: 0 0 18px rgba(255, 0, 0, 0.9); }}
        100% {{ text-shadow: 0 0 8px rgba(255, 80, 80, 0.7); }}
    }}
    </style>
    """



def render_team_logo_img(logo_path):
    try:
        logo_b64 = convert_img_to_base64(logo_path)
        return f"data:image/png;base64,{logo_b64}"
    except FileNotFoundError:
        return None

def render_match_summary_line(match):
    league = match.get("league_name", "Unknown League")
    nation = match.get("nationality", "Unknown Country")
    stage = match.get("stage_name", "Unknown Stage")
    matchday = match.get("matchday", "-")
    return f"{nation}, {league}, {stage}, Matchday {matchday}"


def render_match_header(date_friendly, time_str, venue, nation, league, stage, matchday):
    return f"""
    <div class="meta">
        <span style="margin-right: 15px;">📆 <strong>{date_friendly}</strong></span>
        <span style="margin-right: 15px;">⌚ <strong>{time_str}</strong></span>
        <span>🏟️ <strong>{venue}</strong></span>
        <div style="margin-top: 5px;">
            <span style="margin-right: 15px;"><strong>{nation}, </strong></span>
            <span style="margin-right: 15px;"><strong>{league}, </strong></span>
            <span style="margin-right: 15px;"><strong>{stage}, </strong></span>
            <span>Matchday <strong>{matchday}</strong></span>
        </div>
    </div>
    """


def render_team_logos(home, away, home_logo_src, away_logo_src):
    return f"""
    <div class="teams">
        <div class="team">
            <img src="{home_logo_src}" alt="{home} logo"><br>
            <strong>{home}</strong>
        </div>
        <div class="vs">VS</div>
        <div class="team">
            <img src="{away_logo_src}" alt="{away} logo"><br>
            <strong>{away}</strong>
        </div>
    </div>
    """


def render_status_result(status, result):
    return f"""
    <div class="status-row">
        <span class="badge status">🎯 {status}</span>
        <span class="badge result">{result}</span>
    </div>
    """


def render_countdown_block(local_dt):
    status, countdown = calculate_countdown(local_dt)

    if status == "upcoming" and countdown:
        days, hours, minutes, seconds = countdown
        countdown_html = render_deadline(days, hours, minutes, seconds)
        return countdown_html, status  # ✅ No wrapping here

    elif status == "live":
        return "<div class='countdown'>🟢 The match is Live!</div>", status

    elif status == "finished":
        return "<div class='countdown'>✅ Match Finished</div>", status

    else:
        return "", status



def render_match_card(match: dict):
    # Extract info
    home = match['home_team']
    away = match['away_team']
    venue = match.get('Venue_Name', 'N/A')
    league = match.get("league_name", "Unknown League")
    nation = match.get("nationality", "Unknown Country")
    stage = match.get("stage_name", "Unknown Stage")
    matchday = match.get("matchday", "-")
    home_score = match.get("home_score","-")
    away_score = match.get("away_score","-")
    #print(f"Home score = {home_score} and Away_score = {away_score}")
    # Convert UTC to local
    utc_dt = datetime.fromisoformat(match['match_datetime'].replace("Z", ""))
    local_dt = pytz.utc.localize(utc_dt).astimezone(get_localzone())
    time_str = local_dt.strftime('%I:%M %p')
    date_friendly = local_dt.strftime('%a %d %b %Y')

    # Countdown block & status
    countdown_html, status = render_countdown_block(local_dt)

    # Logos
    home_logo_src = render_team_logo_img(os.path.join("Assets", "Teams", match['home_logo']))
    away_logo_src = render_team_logo_img(os.path.join("Assets", "Teams", match['away_logo']))

    # Result
    result = (
        f"{match['home_score']} - {match['away_score']}"
        if match.get('home_score') is not None and match.get('away_score') is not None
        else "⏳ Not started yet"
    )

    # Assembling card
    header_html = render_match_header(date_friendly, time_str, venue, nation, league, stage, matchday)
    teams_html = render_team_logos(home, away, home_logo_src, away_logo_src)
    status_html = render_status_result(status, result)

    st.markdown(f"""
    <style>
    .match-card {{
        background: linear-gradient(to right, #8a0303, #b00d23);
        color: white;
        border-radius: 18px;
        padding: 20px;
        margin-bottom: 15px;
        box-shadow: 0 5px 15px rgba(0,0,0,0.2);
        text-align: center;
        font-family: 'Segoe UI', sans-serif;
        transition: transform 0.3s ease;
    }}
    .match-card:hover {{
        transform: scale(1.03);
        box-shadow: 0 8px 20px rgba(0,0,0,0.3);
    }}
    .teams {{
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-top: 20px;
    }}
    .team {{
        width: 40%;
        text-align: center;
    }}
    .team img {{
        width: 70px;
        height: 70px;
        border-radius: 50%;
        border: 2px solid #fff;
        object-fit: cover;
    }}
    .vs {{
        font-size: 2.8rem;
        font-weight: bold;
    }}
    .meta {{
        font-size: 0.95rem;
        margin-bottom: 5px;
    }}
    .countdown {{
        margin-top: 15px;
        padding: 10px;
        background-color: #660000;
        border-radius: 10px;
        font-size: 1.3rem;
        font-weight: bold;
        color: #ffb3b3;
        box-shadow: 0 2px 10px rgba(0,0,0,0.2);
    }}
    .status-row {{
        margin-top: 15px;
        display: flex;
        justify-content: center;
        gap: 15px;
        flex-wrap: wrap;
    }}
    .badge {{
        padding: 8px 16px;
        border-radius: 30px;
        font-weight: bold;
        font-size: 1rem;
        display: inline-block;
        box-shadow: 0 2px 6px rgba(0,0,0,0.2);
    }}
    .status {{
        background-color: #ffcc00;
        color: #333;
    }}
    .result {{
        background-color: #00bfff;
        color: white;
    }}
    </style>

    <div class="match-card">
        {header_html}
        {teams_html}
        {status_html}
        {countdown_html}
    </div>
    """, unsafe_allow_html=True)


# def render_match_card(match: dict):
#     home = match['home_team']
#     away = match['away_team']
#     venue = match.get('Venue_Name', 'N/A')
    
#     league = match.get("league_name", "Unknown League")
#     nation = match.get("nationality", "Unknown Country")
#     stage = match.get("stage_name", "Unknown Stage")
#     matchday = match.get("matchday", "-")

#     # Convert UTC to local time
#     utc_dt = datetime.fromisoformat(match['match_datetime'].replace("Z", ""))
#     local_tz = get_localzone()
#     local_dt = pytz.utc.localize(utc_dt).astimezone(local_tz)

#     time_str = local_dt.strftime('%I:%M %p')
#     date_friendly = local_dt.strftime('%a %d %b %Y')
#     status = match.get('status', '').capitalize()
#     print(status)
#     # Countdown
#     status, countdown = calculate_countdown(local_dt)
#     countdown_html = ""
#     if status == "upcoming" and countdown:
#         days, hours, minutes, seconds = countdown
#         countdown_html = render_deadline(days, hours, minutes, seconds)
#     elif status == "live":
#         countdown_html = "<h4 style='color:#28a745; text-align:center;'>🟢 The match is Live!</h4>"
#     elif status == "finished":
#         countdown_html = "<h4 style='color:#888; text-align:center;'>✅ Match Finished</h4>"
#     else:
#         countdown_html = "<h4 style='color:#999;'>Unknown status</h4>"


#     # Logos
#     home_logo_path = os.path.join("Assets", "Teams", match['home_logo'])
#     away_logo_path = os.path.join("Assets", "Teams", match['away_logo'])
#     home_logo_src = render_team_logo_img(home_logo_path)
#     away_logo_src = render_team_logo_img(away_logo_path)

#     result = (
#         f"{match['home_score']} - {match['away_score']}"
#         if match.get('home_score') is not None and match.get('away_score') is not None
#         else "⏳ Not started yet"
#     )

#     st.markdown(f"""
#     <style>
#     .match-card {{
#         background: linear-gradient(to right, #8a0303, #b00d23);
#         color: white;
#         border-radius: 18px;
#         padding: 20px;
#         margin-bottom: 15px;
#         box-shadow: 0 5px 15px rgba(0,0,0,0.2);
#         text-align: center;
#         font-family: 'Segoe UI', sans-serif;
#         transition: transform 0.3s ease;
#     }}
#     .match-card:hover {{
#         transform: scale(1.03);
#         box-shadow: 0 8px 20px rgba(0,0,0,0.3);
#     }}
#     .teams {{
#         display: flex;
#         justify-content: space-between;
#         align-items: center;
#         margin-top: 20px;
#     }}
#     .team {{
#         width: 40%;
#         text-align: center;
#     }}
#     .team img {{
#         width: 70px;
#         height: 70px;
#         border-radius: 50%;
#         border: 2px solid #fff;
#         object-fit: cover;
#     }}
#     .vs {{
#         font-size: 2.8rem;
#         font-weight: bold;
#     }}
#     .meta {{
#         font-size: 0.95rem;
#         margin-bottom: 5px;
#     }}
#     .countdown {{
#         margin-top: 15px;
#         padding: 10px;
#         background-color: #660000;
#         border-radius: 10px;
#         font-size: 1.3rem;
#         font-weight: bold;
#         color: #ffb3b3;
#         box-shadow: 0 2px 10px rgba(0,0,0,0.2);
#     }}
#     .status-row{{
#         margin-top: 15px;
#         display: flex;
#         justify-content: center;
#         gap: 15px;
#         flex-wrap: wrap;  
#     }}
#     .badge {{
#         padding: 8px 16px;
#         border-radius: 30px;
#         font-weight: bold;
#         font-size: 1rem;
#         display: inline-block;
#         box-shadow: 0 2px 6px rgba(0,0,0,0.2);
#     }}
#     .status {{
#         background-color: #ffcc00;
#         color: #333;
#     }}
#     .result{{
#         background-color: #00bfff;
#         color: white;  
#     }}
#     </style>

#     <div class="match-card">
#         <div class="meta">
#             <span style="margin-right: 15px;">📆 <strong>{date_friendly}</strong></span>
#             <span style="margin-right: 15px;">⌚ <strong>{time_str}</strong></span>
#             <span>🏟️ <strong>{venue}</strong></span>
#         <div style="margin-top: 5px;">
#             <span style="margin-right: 15px;"><strong>{nation}, </strong></span>
#             <span style="margin-right: 15px;"><strong>{league}, </strong></span>
#             <span style="margin-right: 15px;"><strong>{stage}, </strong></span>
#             <span>Matchday <strong>{matchday}</strong></span>
#         </div>
#         </div>
#         <div class="teams">
#             <div class="team">
#                 <img src="{home_logo_src}" alt="{home} logo"><br>
#                 <strong>{home}</strong>
#             </div>
#             <div class="vs">VS</div>
#             <div class="team">
#                 <img src="{away_logo_src}" alt="{away} logo"><br>
#                 <strong>{away}</strong>
#             </div>
#         </div>
#         <div style="margin-top: 15px;">
#             <div class="status-row">
#                 <span class="badge status">🎯 {status}</span>
#                 <span class="badge result">{result}</span>
#             </div>  
#         </div>
#         {f'<div class="countdown">Starts in:<br>{countdown_html}</div>' if countdown_html else ""}
#     </div>
#     """, unsafe_allow_html=True)

# def render_time_info(match):
#     utc_dt = datetime.fromisoformat(match['match_datetime'].replace("Z", ""))
#     local_tz = get_localzone()
#     local_dt = pytz.utc.localize(utc_dt).astimezone(local_tz)

#     time_str = local_dt.strftime('%I:%M %p')
#     date_friendly = local_dt.strftime('%a %d %b %Y')
#     countdown = calculate_countdown(local_dt)

#     countdown_html = ""
#     if countdown:
#         days, hours, minutes = countdown
#         countdown_html = render_deadline(days, hours, minutes)

#     return date_friendly, time_str, countdown_html

# def render_team_info(match):
#     home_logo_path = os.path.join("Assets", "Teams", match['home_logo'])
#     away_logo_path = os.path.join("Assets", "Teams", match['away_logo'])
#     home_logo_src = render_team_logo_img(home_logo_path)
#     away_logo_src = render_team_logo_img(away_logo_path)
#     return home_logo_src, away_logo_src

# def render_result(match):
#     if match.get('home_score') is not None and match.get('away_score') is not None:
#         return f"{match['home_score']} - {match['away_score']}"
#     return "⏳ Not started yet"

# def render_status_badges(match):
#     status = match.get('status', '').capitalize()
#     result = render_result(match)
#     return f'''
#     <div class="status-row">
#         <span class="badge status">🎯 {status}</span>
#         <span class="badge result">{result}</span>
#     </div>'''

# def render_match_meta(match):
#     venue = match.get('Venue_Name', 'N/A')
#     league = match.get("league_name", "Unknown League")
#     nation = match.get("nationality", "Unknown Country")
#     stage = match.get("stage_name", "Unknown Stage")
#     matchday = match.get("matchday", "-")

#     return f'''
#     <div class="meta">
#         <div>
#             <span style="margin-right: 15px;">📅 <strong>{match['formatted_date']}</strong></span>
#             <span style="margin-right: 15px;">⌚ <strong>{match['formatted_time']}</strong></span>
#             <span>🏟️ <strong>{venue}</strong></span>
#         </div>
#         <div style="margin-top: 5px;">
#             <span style="margin-right: 15px;"><strong>{nation}, </strong></span>
#             <span style="margin-right: 15px;"><strong>{league}, </strong></span>
#             <span style="margin-right: 15px;"><strong>{stage}, </strong></span>
#             <span>Matchday <strong>{matchday}</strong></span>
#         </div>
#     </div>
#     '''


# def render_match_summary_line(match):
#     league = match.get("league_name", "Unknown League")
#     nation = match.get("nationality", "Unknown Country")
#     stage = match.get("stage_name", "Unknown Stage")
#     matchday = match.get("matchday", "-")
#     return f"{nation}, {league}, {stage}, Matchday {matchday}"

# def render_match_card(match: dict):
#     date_friendly, time_str, countdown_html = render_time_info(match)
#     home_logo_src, away_logo_src = render_team_info(match)
#     home = match['home_team']
#     away = match['away_team']
#     match['formatted_date'] = date_friendly
#     match['formatted_time'] = time_str

#     meta_html = render_match_meta(match)
#     status_html = render_status_badges(match)

#     st.markdown(f"""
#     <style>
#     .match-card {{
#         background: linear-gradient(to right, #8a0303, #b00d23);
#         color: white;
#         border-radius: 18px;
#         padding: 20px;
#         margin-bottom: 15px;
#         box-shadow: 0 5px 15px rgba(0,0,0,0.2);
#         text-align: center;
#         font-family: 'Segoe UI', sans-serif;
#         transition: transform 0.3s ease;
#     }}
#     .match-card:hover {{
#         transform: scale(1.03);
#         box-shadow: 0 8px 20px rgba(0,0,0,0.3);
#     }}
#     .teams {{
#         display: flex;
#         justify-content: space-between;
#         align-items: center;
#         margin-top: 20px;
#     }}
#     .team {{
#         width: 40%;
#         text-align: center;
#     }}
#     .team img {{
#         width: 70px;
#         height: 70px;
#         border-radius: 50%;
#         border: 2px solid #fff;
#         object-fit: cover;
#     }}
#     .vs {{
#         font-size: 2.8rem;
#         font-weight: bold;
#     }}
#     .meta {{
#         font-size: 0.95rem;
#         margin-bottom: 5px;
#     }}
#     .countdown {{
#         margin-top: 15px;
#         padding: 10px;
#         background-color: #660000;
#         border-radius: 10px;
#         font-size: 1.3rem;
#         font-weight: bold;
#         color: #ffb3b3;
#         box-shadow: 0 2px 10px rgba(0,0,0,0.2);
#     }}
#     .status-row{{
#         margin-top: 15px;
#         display: flex;
#         justify-content: center;
#         gap: 15px;
#         flex-wrap: wrap;  
#     }}
#     .badge {{
#         padding: 8px 16px;
#         border-radius: 30px;
#         font-weight: bold;
#         font-size: 1rem;
#         display: inline-block;
#         box-shadow: 0 2px 6px rgba(0,0,0,0.2);
#     }}
#     .status {{
#         background-color: #ffcc00;
#         color: #333;
#     }}
#     .result{{
#         background-color: #00bfff;
#         color: white;  
#     }}
#     </style>

#     <div class="match-card">
#         {meta_html}
#         <div class="teams">
#             <div class="team">
#                 <img src="{home_logo_src}" alt="{home} logo"><br>
#                 <strong>{home}</strong>
#             </div>
#             <div class="vs">VS</div>
#             <div class="team">
#                 <img src="{away_logo_src}" alt="{away} logo"><br>
#                 <strong>{away}</strong>
#             </div>
#         </div>
#         {status_html}
#         {f'<div class="countdown">Starts in:<br>{countdown_html}</div>' if countdown_html else ""}
#     </div>
#     """, unsafe_allow_html=True)
    
