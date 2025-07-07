import streamlit as st
import os
import base64
from collections import defaultdict
from datetime import datetime
from Renders.render_helpers import render_league_banner, render_match_card
from Controllers import fixtures_controller as ctrl
import pandas as pd

from Controllers.leagues_controller import (
    get_active_leagues,
    get_league_by_id,
    get_fixtures_by_league,
    get_league_table
)

ASSET_LOGO_FOLDER = "Assets/Leagues"
ASSET_TEAM_FOLDER = "Assets/Teams"






def convert_img_to_base64(path):
    try:
        with open(path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode("utf-8")
    except FileNotFoundError:
        return None

def render():
    st.header("🏆 Leagues")

    leagues = get_active_leagues()
    if not leagues:
        st.warning("No active leagues found.")
        return

    selected_league_id = st.session_state.get("selected_league_id")

    render_leagues(leagues)

    if selected_league_id:
        league = get_league_by_id(selected_league_id)
        print(league)
        st.subheader(f"🏆 {league['name']} | {league['country']}")

        tab1, tab2 = st.tabs(["📅 Fixtures", "📊 Table"])

        with tab1:
            render_fixtures(selected_league_id)
        with tab2:
            render_league_banner(league['name'], ctrl.get_logo_path_from_league(league['name']))
            render_table(selected_league_id, league['country'], league['name'])
            render_rules(league['name'])

def render_leagues(leagues):
    selected_league_id = st.session_state.get("selected_league_id")

    with st.expander("⚽ Select a League", expanded=False):
        st.markdown("""
            <style>
            .league-grid {
                display: grid;
                grid-template-columns: repeat(3, 1fr);
                gap: 20px;
                margin-top: 20px;
            }
            .league-card {
                background-color: #ffffff;
                border: 2px solid transparent;
                border-radius: 16px;
                box-shadow: 0 8px 20px rgba(0, 0, 0, 0.1);
                text-align: center;
                padding: 25px 15px;
                transition: all 0.3s ease;
                cursor: pointer;
            }
            .league-card:hover {
                transform: translateY(-5px);
                box-shadow: 0 12px 24px rgba(0, 0, 0, 0.2);
            }
            .league-card.active {
                border-color: #007acc;
                background-color: #eaf6ff;
            }
            .league-logo-big {
                width: 80px;
                height: 80px;
                object-fit: contain;
                border-radius: 50%;
                margin-bottom: 15px;
            }
            .league-name {
                font-size: 18px;
                font-weight: 700;
                color: #333;
            }
            </style>
        """, unsafe_allow_html=True)

        st.markdown('<div class="league-grid">', unsafe_allow_html=True)

        for league in leagues:
            logo_path = os.path.join(ASSET_LOGO_FOLDER, league['logo_path'])
            logo_b64 = convert_img_to_base64(logo_path)
            logo_img = f"data:image/png;base64,{logo_b64}" if logo_b64 else "https://via.placeholder.com/80"

            is_active = (selected_league_id == league['id'])
            active_class = "active" if is_active else ""

            with st.form(key=f"form_league_{league['id']}"):
                st.markdown(f"""
                    <div class="league-card {active_class}">
                        <img src="{logo_img}" class="league-logo-big" />
                        <div class="league-name">{league['name']}</div>
                        <input type="hidden" name="selected_league_id" value="{league['id']}" />
                        <button type="submit" style="display:none;"></button>
                    </div>
                """, unsafe_allow_html=True)
                submitted = st.form_submit_button("")
                if submitted:
                    st.session_state.selected_league_id = league['id']

        st.markdown('</div>', unsafe_allow_html=True)




def render_fixtures(league_id):
    fixtures = get_fixtures_by_league(league_id)
    if not fixtures:
        st.info("No fixtures found for this league.")
        return

    # Group fixtures by date
    grouped_fixtures = defaultdict(list)
    for match in sorted(fixtures, key=lambda m: m['match_datetime']):
        date_str = datetime.fromisoformat(match['match_datetime']).strftime("%A, %d %B %Y")
        grouped_fixtures[date_str].append(match)

    # CSS styling
    st.markdown("""
        <style>
        .day-header {
            background: linear-gradient(90deg, #007acc, #00c6ff);
            color: white;
            padding: 10px 20px;
            border-radius: 8px;
            margin-top: 30px;
            margin-bottom: 10px;
            font-size: 20px;
            font-weight: 600;
            text-align: center;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        }
        </style>
    """, unsafe_allow_html=True)

    # Render fixtures grouped by date
    for day, matches in grouped_fixtures.items():
        st.markdown(f"<div class='day-header'>📅 {day}</div>", unsafe_allow_html=True)
        for match in matches:
            render_match_card(match)


# Table Part    
LEAGUE_RULES = {
    "Premier League": {
        "Champions League": list(range(1, 6)),
        "Europa League": [6],
        "Conference League": [7],
        "Relegation": list(range(18, 21))
    },
    "Serie A": {
        "Champions League": list(range(1, 5)),
        "Europa League": [5],
        "Conference League": [6],
        "Relegation": list(range(18, 21))
    },
    "Bundesliga": {
        "Champions League": list(range(1, 5)),
        "Europa League": [5],
        "Conference League": [6],
        "Relegation Playoffs": [16],
        "Relegation": [17, 18]
    },
    "Primera Division": {
        "Champions League": list(range(1, 6)),
        "Europa League": [6, 7],
        "Conference League": [8],
        "Relegation": list(range(18, 21))
    },
    "Ligue 1": {
        "Champions League": list(range(1, 5)),
        "Europa League": [5],
        "Conference League": [6],
        "Relegation Playoffs": [16],
        "Relegation": [17, 18]
    }
}

CATEGORY_COLORS = {
    "Champions League": "#4CAF50",       # Green
    "Europa League": "#001F7F",          # Dark Blue
    "Conference League": "#40E0D0",      # Turquoise
    "Relegation Playoffs": "#FFD700",    # Yellow
    "Relegation": "#FF0000",             # Red
}


def get_category_for_position(league, pos):
    rules = LEAGUE_RULES.get(league, {})
    for category, positions in rules.items():
        if pos in positions:
            return category
    return None

def color_circle(cat):
    if not cat:
        return ""
    color = CATEGORY_COLORS.get(cat, "#ccc")
    # Using a colored ● emoji with color span
    return f'<span style="color:{color}; font-size:20px;">●</span>'

# Replace rank number with colored circle + number inside dataframe styling
def rank_with_circle(row):
    cat = row['Category']
    pos = row['#']
    circle = color_circle(cat)
    # Position number with circle prefix
    return f'{circle} {pos}'

   # Style dataframe with hover & custom CSS
def highlight_row(x):
    return ['background-color: #d6e4ff' if x.name == 0 else '' for _ in x]
    
def rank_with_circle(row):
    cat = row['Category']
    pos = row['#']
    if not cat:
        return str(pos)
    color = CATEGORY_COLORS.get(cat, "#ccc")
    # Colored circle + rank number as HTML
    return f'<span style="color:{color}; font-size:20px;">●</span> {pos}'

def highlight_row(x):
    # Highlight the first row (top team) with light blue background
    return ['background-color: #d6e4ff' if x.name == 0 else '' for _ in x]

def render_table(league_id, country, league_name, highlight_team: str = None):
    table = get_league_table(league_id, country)
    if not table:
        st.info("No table data available.")
        return

    df = pd.DataFrame(table)
    df['GD'] = df['goals_for'] - df['goals_against']

    df_display = df[['team_name', 'played', 'wins', 'draws', 'losses',
                     'goals_for', 'goals_against', 'GD', 'points']]
    df_display.columns = ['Team', 'P', 'W', 'D', 'L', 'GF', 'GA', 'GD', 'Pts']

    df_display.insert(0, '#', range(1, len(df_display) + 1))
    df_display['Category'] = df_display['#'].apply(lambda pos: get_category_for_position(league_name, pos))

    def format_rank(row):
        color = CATEGORY_COLORS.get(row['Category'], "#999")
        number = row['#']
        tooltip = row['Category']
        return f"""
        <div title="{tooltip}" style='
            background-color:{color};
            color:white;
            width:32px;
            height:32px;
            border-radius:50%;
            display:flex;
            align-items:center;
            justify-content:center;
            font-weight:bold;
            font-size:14px;
            margin:auto;
        '>{number}</div>
        """

    df_display['#'] = df_display.apply(format_rank, axis=1)
    df_display = df_display.drop(columns=['Category'])
    df_display.reset_index(drop=True, inplace=True)

    # Highlight specific team if provided
    def highlight_row(row):
        if highlight_team and row['Team'].lower() == highlight_team.lower():
            return ['background-color: #2563eb; color: white; font-weight: bold;'] * len(row)
        return [''] * len(row)

    styled_df = df_display.style \
        .set_table_attributes("style='margin-left:auto;margin-right:auto;border-collapse:collapse;width:90%;'") \
        .set_properties(**{
            'text-align': 'center',
            'font-family': 'Segoe UI, sans-serif',
            'font-size': '16px',
            'padding': '8px',
            'border': '1px solid #444',
            'background-color': '#1e1e1e',
            'color': '#eee'
        }) \
        .set_table_styles([
            {'selector': 'th', 'props': [
                ('background-color', '#333'),
                ('color', 'white'),
                ('font-size', '18px'),
                ('padding', '10px'),
                ('text-align', 'center'),
                ('border', '1px solid #444')
            ]},
            {'selector': 'td', 'props': [
                ('border', '1px solid #444')
            ]},
            {'selector': 'tbody tr:hover', 'props': [
                ('background-color', '#292929')
            ]}
        ], overwrite=False) \
        .apply(highlight_row, axis=1)

    st.markdown(f"<h3 style='text-align:center;'>🏆 {league_name} League Table</h3>", unsafe_allow_html=True)
    st.write(styled_df.to_html(escape=False, index=False), unsafe_allow_html=True)



def render_rules(league_name):
    rules = LEAGUE_RULES.get(league_name)
    if not rules:
        st.info("No rules available for this league.")
        return

    # Inject CSS once
    st.markdown("""
        <style>
        .rule-badge {
            display: inline-flex;
            align-items: center;
            gap: 10px;
            padding: 8px 14px;
            margin: 6px 4px;
            border-radius: 12px;
            background: #1f1f1f;
            color: white;
            font-size: 16px;
            font-weight: 600;
            box-shadow: 0 3px 6px rgba(0,0,0,0.25);
            transition: transform 0.2s ease, box-shadow 0.2s ease;
        }

        .rule-badge:hover {
            transform: scale(1.05);
            box-shadow: 0 5px 12px rgba(0,0,0,0.4);
        }

        .circle-dot {
            font-size: 22px;
            display: inline-block;
            line-height: 1;
            user-select: none;
        }
        </style>
    """, unsafe_allow_html=True)

    with st.expander("📜 Rules"):
        st.subheader("Qualification and Relegation")

        for category in rules:
            color = CATEGORY_COLORS.get(category, "#999")
            st.markdown(
                f"""
                <div class="rule-badge">
                    <span class="circle-dot" style="color:{color};">●</span>
                    <span>{category}</span>
                </div>
                """,
                unsafe_allow_html=True
            )

        st.markdown("---")
        st.markdown("#### ⚖️ Tie-Breaker Rules")
        st.markdown("""
        In the event that two (or more) teams have an equal number of points, the following rules break the tie:
        1. **Head-to-head** results (if all tied teams have played each other)
        2. **Goal difference** across the league
        3. **Goals scored** during the season
        """)

















