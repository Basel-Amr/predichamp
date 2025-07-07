import streamlit as st
import base64
from pathlib import Path
from datetime import datetime, timedelta
from tzlocal import get_localzone
import pytz
import os
from Controllers.fixtures_controller import get_league_dates, calculate_league_progress
import uuid
# 🎨 Optional: Unique colors per league
LEAGUE_COLORS = {
    "Premier League": "#1e1f57,#932790",         # Deep navy & royal purple (lion mane)
    "La Liga": "#ff3a20,#ffd700",               # Red & yellow (Spanish flag tone)
    "Serie A": "#005daa,#00e0ca",               # Classic blue + teal accent
    "Bundesliga": "#e30613,#ffffff",            # Pure red & white (official)
    "Ligue 1": "#001c3d,#ffdc00",               # Navy blue & yellow (Hexagoal theme)
    "Champions League": "#0a0a23,#4c8eda",      # Deep night blue & light star blue
    "Europa League": "#ff7c00,#121212",         # Bright orange & dark gray/black
}

def convert_img_to_base64(path):
    """
    Converts an image file to a base64 string for HTML embedding.
    
    Parameters:
        path (str): The full path to the image file.
    
    Returns:
        str: Base64-encoded image string or None if file not found or error.
    """
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


    
def render_league_banner(league_name, logo_path=None):
    import re
    from datetime import datetime

    gradient = LEAGUE_COLORS.get(league_name, "#003366,#004080")
    class_id = re.sub(r'\W+', '', league_name.lower())
    banner_class = f"league-banner-{class_id}"
    logo_class = f"league-logo-circle-{class_id}"
    float_anim = f"float-logo-{class_id}"

    logo_html = ""
    logo_b64 = convert_img_to_base64(logo_path) if logo_path else None
    if logo_b64:
        data_uri = f"data:image/png;base64,{logo_b64}"
        logo_html = f"""
        <div class="{logo_class}">
            <img src="{data_uri}" class="league-logo-img" alt="{league_name} logo" />
        </div>
        """

    start_date, end_date = get_league_dates(league_name)
    if not start_date or not end_date:
        st.warning(f"⚠️ Missing dates for {league_name}")
        return

    # Ensure dates are in date format
    if isinstance(start_date, str):
        start_date = datetime.strptime(start_date, "%Y-%m-%d").date()
    if isinstance(end_date, str):
        end_date = datetime.strptime(end_date, "%Y-%m-%d").date()

    progress, start_fmt, end_fmt = calculate_league_progress(str(start_date), str(end_date))
    if progress is None:
        st.warning(f"⚠️ Unable to calculate progress for {league_name}")
        return

    color = "#4CAF50" if progress >= 66 else "#FFD700" if progress >= 33 else "#FF4C4C"
    now = datetime.now().date()
    season_note = ""

    if progress <= 0 and now < start_date:
        days_to_start = (start_date - now).days
        season_note = f"""
        <div class="season-note upcoming">🚨 <strong>Season hasn't started yet</strong> – Kicks off in <strong>{days_to_start} days</strong>! Stay tuned ⚽</div>
        """
    elif progress >= 100 and now > end_date:
        season_note = f"""
        <div class="season-note ended">🏁 <strong>Season Completed</strong> – Thanks for watching! See you next season 👋</div>
        """

    st.markdown(f"""
        <style>
            .{banner_class} {{
                background: linear-gradient(90deg, {gradient});
                border-radius: 14px;
                padding: 20px 30px;
                margin-top: 25px;
                margin-bottom: 5px;
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
                height: 90px;
                width: 90px;
                display: flex;
                justify-content: center;
                align-items: center;
                animation: {float_anim} 2.5s infinite ease-in-out;
            }}
            .league-logo-img {{
                height: 60px;
                width: 60px;
                object-fit: contain;
                border-radius: 12px;
            }}
            .league-progress {{
                margin-top: 16px;
                padding: 10px 16px 20px;
                animation: fadeInUp 0.8s ease-in-out;
            }}
            .season-note {{
                background: #330033;
                color: #ffc;
                padding: 12px 20px;
                border-radius: 12px;
                text-align: center;
                margin-top: 12px;
                font-weight: bold;
                font-size: 1.05rem;
                box-shadow: 0 4px 12px rgba(0,0,0,0.3);
            }}
            .season-note.ended {{
                background: #003300;
                color: #aaffaa;
            }}
            .season-note.upcoming {{
                background: #331100;
                color: #ffe680;
            }}
            @keyframes fadeInUp {{
                0% {{ opacity: 0; transform: translateY(10px); }}
                100% {{ opacity: 1; transform: translateY(0); }}
            }}
            @keyframes {float_anim} {{
                0% {{ transform: translateY(0px); }}
                50% {{ transform: translateY(-5px); }}
                100% {{ transform: translateY(0px); }}
            }}
            .progress-bar-outer {{
                background: #222;
                height: 24px;
                border-radius: 14px;
                box-shadow: inset 0 0 5px rgba(0, 0, 0, 0.4);
                overflow: hidden;
            }}
            .progress-bar-inner {{
                height: 100%;
                width: {progress:.1f}%;
                background: linear-gradient(90deg, {color}, #00ffff);
                transition: width 2s ease-in-out;
                border-radius: 14px;
                box-shadow: 0 0 12px {color};
            }}
            .progress-bar-inner:hover {{
                filter: brightness(1.2);
                box-shadow: 0 0 18px {color};
            }}
            .progress-dates {{
                display: flex;
                justify-content: space-between;
                font-size: 0.9rem;
                font-weight: 600;
                color: #ddd;
                margin-top: 6px;
            }}
            .progress-dates span:hover {{
                transform: scale(1.05);
                color: #fff;
            }}
        </style>

        <div class="{banner_class}">
            <div>🏆 {league_name}</div>
            {logo_html}
        </div>
        <div class="league-progress">
            <div class="progress-bar-outer">
                <div class="progress-bar-inner" title="Progress: {progress:.1f}%"></div>
            </div>
            <div class="progress-dates">
                <span>📅 {start_fmt}</span>
                <span><b>{progress:.1f}%</b></span>
                <span>📅 {end_fmt}</span>
            </div>
            {season_note}
        </div>
    """, unsafe_allow_html=True)
    
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

def render_team_logo_img(logo_path):
    try:
        logo_b64 = convert_img_to_base64(logo_path)
        return f"data:image/png;base64,{logo_b64}"
    except FileNotFoundError:
        return None


def convert_img_to_base64(path):
    """
    Converts an image file to a base64 string for HTML embedding.
    
    Parameters:
        path (str): The full path to the image file.
    
    Returns:
        str: Base64-encoded image string or None if file not found or error.
    """
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

def render_team_logos(home, away, home_logo_src, away_logo_src, home_score, away_score,
                      status, home_color="#c8102e", away_color="#111", time_str="20:00", unique_id=None):
    if unique_id is None:
        unique_id = str(uuid.uuid4()).replace("-", "")

    banner_class = f"match-banner-{unique_id}"
    time_class = f"center-time-{unique_id}"

    # Determine what to show in the center
    center_content = f"{home_score} - {away_score}" if home_score is not None and away_score is not None else time_str

    return f"""
    <style>
        .{banner_class} {{
            display: flex;
            position: relative;
            border-radius: 16px 16px 0 0;
            overflow: hidden;
            height: 140px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.3);
            font-family: 'Segoe UI', sans-serif;
            z-index: 2; /* 🔥 Ensure it's above match-info-card */
        }}

        .{banner_class} .team-half {{
            flex: 1;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            color: white;
            position: relative;
        }}

        .{banner_class} .team-half.left {{
            background: linear-gradient(135deg, {home_color}, #00000055);
            clip-path: polygon(0 0, 100% 0, 85% 100%, 0% 100%);
        }}

        .{banner_class} .team-half.right {{
            background: linear-gradient(135deg, {away_color}, #00000055);
            clip-path: polygon(15% 0, 100% 0, 100% 100%, 0% 100%);
        }}

        .{banner_class} .team-half img {{
            width: 90px;
            height: 90px;
            object-fit: contain;
            border-radius: 50%;
            background: transparent;
            padding: 0px;
            box-shadow: transperent;
            transition: transform 0.3s ease-in-out;
        }}

        .{banner_class} .team-half img:hover {{
            transform: scale(1.1);
        }}

        .{banner_class} .team-name {{
            margin-top: 10px;
            font-size: 1.5rem;
            font-weight: 700;
            text-shadow: 0 1px 3px rgba(0,0,0,0.6);
        }}

        .{banner_class} .{time_class} {{
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            background: #2e003e;
            padding: 12px 24px;
            border-radius: 14px;
            font-size: 1.4rem;
            font-weight: 700;
            color: white;
            z-index: 2;
            box-shadow: 0 0 10px rgba(255,255,255,0.3);
            text-align: center;
        }}
    </style>

    <div class="{banner_class}">
        <div class="team-half left">
            <img src="{home_logo_src}" alt="{home} logo" />
            <div class="team-name">{home}</div>
        </div>
        <div class="{time_class}">{center_content}</div>
        <div class="team-half right">
            <img src="{away_logo_src}" alt="{away} logo" />
            <div class="team-name">{away}</div>
        </div>
    </div>
    """

def render_match_info_section(date_friendly, match):
    league = match.get("league_name", "Unknown League")
    venue = match["Venue_Name"]
    home_team = match["home_team"]
    away_team = match["away_team"]
    matchday = match["matchday"]
    season = "2025/2026"

    return f"""
    <style>
        .match-info-card {{
            background: linear-gradient(180deg, #240046 0%, #3c096c 100%);
            padding: 40px 30px 25px;
            border-radius: 0 0 18px 18px;
            color: #f1f1f1;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            text-align: center;
            box-shadow: 0 4px 12px rgba(0,0,0,0.3);
            position: relative;
            z-index: 1;
        }}

        .match-info-card::before {{
            content: '';
            position: absolute;
            top: -1px;
            left: 50%;
            transform: translateX(-50%);
            width: 110px;
            height: 50px;
            background-color: #240046;
            border-bottom-left-radius: 55px;
            border-bottom-right-radius: 55px;
            z-index: 4;
        }}

        .match-info-card * {{
            position: relative;
            z-index: 2;
        }}

        .match-info-card .match-details {{
            margin-top: 11px;
            font-size: 0.95rem;
            color: #ddd;
        }}

        .match-info-card strong {{
            color: #fff;
        }}
    </style>

    <div class="match-info-card">
        <div><strong>Matchweek {matchday}</strong></div>
        <div style="margin-top: 6px;">📅 <strong>{date_friendly}</strong> &nbsp;•&nbsp; 🏟️ <strong>{venue}</strong></div>
        <div class="match-details">
            {home_team} vs {away_team} |  {league} {season} | {league}
        </div>
    </div>
    """






def render_status_result(status):
    status_display = {
        "upcoming": ("🕒 Upcoming", "upcoming-status"),
        "live": ("🟢 Live Now", "live-status"),
        "finished": ("✅ Finished", "finished-status"),
        "cancelled": ("❌ Cancelled", "cancelled-status")
    }

    label, css_class = status_display.get(status.lower(), ("❓ Unknown", "unknown-status"))

    return f"""
    <style>
        .status-row {{
            margin-top: 18px;
            display: flex;
            justify-content: center;
            align-items: center;
        }}
        .badge {{
            padding: 10px 28px;
            border-radius: 999px;
            font-size: 1.1rem;
            font-weight: 600;
            display: inline-block;
            text-align: center;
            box-shadow: 0 6px 15px rgba(0, 0, 0, 0.35);
            animation: fadeInBadge 0.6s ease-out;
            text-transform: uppercase;
            letter-spacing: 1px;
            background-size: 200% 200%;
            transition: all 0.3s ease-in-out;
            border: 1px solid rgba(255,255,255,0.2);
        }}
        .badge:hover {{
            transform: scale(1.06);
            box-shadow: 0 8px 22px rgba(0, 0, 0, 0.4);
        }}

        .upcoming-status {{
            background: linear-gradient(135deg, #fdd835, #fbc02d);
            color: #1a1a1a;
        }}
        .live-status {{
            background: linear-gradient(135deg, #00e676, #00c853);
            color: #002200;
            animation: pulseGlow 1.6s infinite;
        }}
        .finished-status {{
            background: linear-gradient(135deg, #9e9e9e, #cfd8dc);
            color: #111;
        }}
        .cancelled-status {{
            background: linear-gradient(135deg, #e53935, #b71c1c);
            color: white;
        }}
        .unknown-status {{
            background: linear-gradient(135deg, #78909c, #90a4ae);
            color: #222;
        }}

        @keyframes fadeInBadge {{
            0% {{ opacity: 0; transform: translateY(10px); }}
            100% {{ opacity: 1; transform: translateY(0); }}
        }}

        @keyframes pulseGlow {{
            0% {{ box-shadow: 0 0 6px rgba(0, 255, 128, 0.5); }}
            50% {{ box-shadow: 0 0 18px rgba(0, 255, 128, 0.8); }}
            100% {{ box-shadow: 0 0 6px rgba(0, 255, 128, 0.5); }}
        }}
    </style>

    <div class="status-row">
        <span class="badge {css_class}">{label}</span>
    </div>
    """





def render_countdown_block(local_dt):
    status, countdown = calculate_countdown(local_dt)

    base_style = """
    <style>
        .countdown-wrapper {
            display: flex;
            justify-content: center;
            margin-top: 20px;
            animation: fadeInUp 0.6s ease;
        }
        .countdown {
            padding: 14px 28px;
            background: linear-gradient(to right, #202020, #333333);
            border-radius: 16px;
            font-size: 1.35rem;
            font-weight: 600;
            color: #ffffff;
            box-shadow: 0 6px 18px rgba(0, 0, 0, 0.35);
            font-family: 'Segoe UI', sans-serif;
            text-align: center;
            white-space: nowrap;
            min-width: 260px;
        }

        @keyframes fadeInUp {
            0% { transform: translateY(10px); opacity: 0; }
            100% { transform: translateY(0); opacity: 1; }
        }
    </style>
    """

    if status == "upcoming" and countdown:
        days, hours, minutes, seconds = countdown
        time_parts = []
        if days: time_parts.append(f"{days}d")
        if hours: time_parts.append(f"{hours}h")
        if minutes: time_parts.append(f"{minutes}m")
        if seconds: time_parts.append(f"{seconds}s")

        countdown_text = "⏳ Kick-off in " + " ".join(time_parts)
        return f"{base_style}<div class='countdown-wrapper'><div class='countdown'>{countdown_text}</div></div>", status

    elif status == "live":
        return f"""{base_style}<div class='countdown-wrapper'><div class='countdown'>🟢 The match is Live!</div></div>""", status

    elif status == "finished":
        return f"""{base_style}<div class='countdown-wrapper'><div class='countdown'>✅ Match Finished</div></div>""", status

    else:
        return "", status




def render_match_card(match: dict):
    # Extract info
    home = match['home_team']
    away = match['away_team']
    home_score = match.get("home_score","-")
    away_score = match.get("away_score","-")
    home_color = match.get("home_color","-")
    away_color = match.get("away_color","-")
    # Convert UTC to local
    utc_dt = datetime.fromisoformat(match['match_datetime'].replace("Z", ""))
    local_dt = pytz.utc.localize(utc_dt).astimezone(get_localzone())
    date_friendly = local_dt.strftime('%a %d %b %Y')
    time_str = local_dt.strftime('%I:%M %p') 
    # Countdown block & status
    countdown_html, status = render_countdown_block(local_dt)
    status =match.get("status")
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
    teams_html = render_team_logos(home, away, home_logo_src, away_logo_src, 
                                   home_score, away_score, status, home_color=home_color,
                                   away_color=away_color,
                                   time_str = time_str,
                                   unique_id=match['match_id']
                                   )
    status_html = render_status_result(status)
    match_html = render_match_info_section(date_friendly, match)

    st.markdown(f"""
    <style>
    .match-card {{
        background: linear-gradient(to right, #1a1a1a, #2b2b2b);
        color: #f0f0f0;
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
    .team-name-ribbon {{
        display: inline-block;
        margin-top: 10px;
        padding: 6px 22px;
        font-weight: bold;
        font-size: 1rem;
        color: white;
        background: linear-gradient(to right, #445566, #2c3e50);
        border-radius: 999px;
        box-shadow: 0 2px 6px rgba(0,0,0,0.4);
        position: relative;
        z-index: 1;
    }}
    .vs {{
        font-size: 2.8rem;
        font-weight: bold;
        color: #dddddd;
    }}
    .meta {{
        font-size: 0.95rem;
        margin-bottom: 5px;
    }}
    .countdown {{
        margin-top: 15px;
        padding: 10px;
        background-color: #202020;
        border-radius: 10px;
        font-size: 1.3rem;
        font-weight: bold;
        color: #e0e0e0;
        box-shadow: 0 2px 10px rgba(0,0,0,0.2);
    }}
    .status-row {{
        margin-top: 18px;
        display: flex;
        justify-content: center;
        gap: 10px;
    }}
    .badge {{
        padding: 10px 20px;
        border-radius: 50px;
        font-size: 1.1rem;
        font-weight: bold;
        display: inline-block;
        text-align: center;
        box-shadow: 0 4px 10px rgba(0, 0, 0, 0.2);
        animation: popIn 0.4s ease-out;
        text-transform: uppercase;
        letter-spacing: 1px;
    }}
    .upcoming-status {{
        background: linear-gradient(to right, #ffe066, #ffc300);
        color: #222;
    }}
    .live-status {{
        background: linear-gradient(to right, #00e676, #1de9b6);
        color: #003300
        animation: pulseGlow 1.5s infinite;
    }}
    .finished-status {{
        background: linear-gradient(to right, #999999, #cccccc);
        color: #111;
    }}
    .cancelled-status {{
        background: linear-gradient(to right, #ff4d4d, #cc0000);
        color: white;
    }}
    .result {{
        background-color: #00bfff;
        color: white;
    }}
    .match-header-block {{
        background: linear-gradient(to right, #252525, #3a3a3a);
        padding: 14px 20px;
        border-radius: 14px;
        margin-bottom: 18px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.4);
        font-family: 'Segoe UI', sans-serif;
        color: #ffffff;
        text-align: center;
        letter-spacing: 0.4px;
        animation: fadeInUp 0.6s ease-out;
    }}
    .header-top, .header-bottom {{
        font-size: 1.05rem;
        font-weight: 500;
        text-shadow: 0 1px 2px rgba(0, 0, 0, 0.4);
        margin: 2px 0;
    }}
    .match-header-block strong {{
        font-weight: 700;
        color: #f2f2f2;
    }}

    /* Animations */
    @keyframes popIn {{
        0% {{ transform: scale(0.8); opacity: 0; }}
        100% {{ transform: scale(1); opacity: 1; }}
    }}

    @keyframes pulseGlow {{
        0% {{ box-shadow: 0 0 8px rgba(0, 255, 128, 0.5); }}
        50% {{ box-shadow: 0 0 18px rgba(0, 255, 128, 0.9); }}
        100% {{ box-shadow: 0 0 8px rgba(0, 255, 128, 0.5); }}
    }}

    @keyframes fadeInUp {{
        0% {{ transform: translateY(10px); opacity: 0; }}
        100% {{ transform: translateY(0); opacity: 1; }}
    }}
    </style>
""", unsafe_allow_html=True)
    with st.container():
        st.markdown('<div class="match-card">', unsafe_allow_html=True)
        st.markdown(teams_html, unsafe_allow_html=True)
        st.markdown(match_html, unsafe_allow_html=True)
        st.markdown(status_html, unsafe_allow_html=True)
        st.markdown(countdown_html, unsafe_allow_html=True)

