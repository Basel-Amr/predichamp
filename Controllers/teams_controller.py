from Controllers.utils import fetch_all, fetch_one

def get_all_teams():
    query = """
        SELECT *
        FROM teams
        ORDER BY name
    """
    return fetch_all(query)


def get_team_full_info(team_id):
    team = fetch_one(f"""
        SELECT *
        FROM teams
        WHERE id = {team_id}
    """)

    coach = fetch_one(f"""
        SELECT *
        FROM coaches
        WHERE team_id = {team_id}
    """)

    players = fetch_all(f"""
        SELECT *
        FROM football_player
        WHERE team_id = {team_id}
        ORDER BY shirt_number
    """)

    matches = fetch_all(f"""
        SELECT 
            DATE(m.match_datetime) AS match_date,
            l.name AS league_name,
            l.country AS nationality,
            s.name AS stage_name,
            m.matchday,
            m.match_datetime,
            m.status,
            m.api_match_id AS match_id,
            m.home_score,
            m.away_score,
            m.Venue_name,
            ht.name AS home_team_name,
            at.name AS away_team_name,
            ht.logo_path AS home_team_logo,
            at.logo_path AS away_team_logo,
            ht.color AS home_color,
            at.color AS away_color,
            ht.logo_path AS home_logo,
            at.logo_path AS away_logo
        FROM matches m
        JOIN leagues l ON m.league_id = l.id
        JOIN teams ht ON m.home_team_id = ht.id
        JOIN teams at ON m.away_team_id = at.id
        LEFT JOIN stages s ON m.stage_id = s.id
        WHERE m.home_team_id = {team_id} OR m.away_team_id = {team_id}
        ORDER BY m.match_datetime ASC
    """)

    competitions = fetch_all(f"""
        SELECT tc.*, l.name AS league_name
        FROM team_competitions tc
        JOIN leagues l ON tc.league_id = l.id
        WHERE tc.team_id = {team_id}
        ORDER BY tc.season_start DESC
    """)

    return {
        "team": team,
        "coach": coach,
        "players": players,
        "matches": matches,
        "competitions": competitions
    }
    
def get_league_info_for_team(team_id):
    # Step 1: Get the team's nationality
    team = fetch_one(f"""
        SELECT nationality, name
        FROM teams
        WHERE id = {team_id}
    """)
    if not team or not team['nationality']:
        return None

    nationality = team['nationality']

    # Step 2: Find the league whose country matches the team's nationality
    league = fetch_one(f"""
        SELECT *
        FROM leagues
        WHERE country = '{nationality}'
        LIMIT 1
    """)
    if not league:
        print(f"⚠️ No league found for team '{team['name']}' with nationality '{nationality}'")
        return None

    return league

def get_team_squad(team_id):
    query = f"""
        SELECT 
            id,
            name,
            first_name,
            last_name,
            date_of_birth,
            nationality,
            section,
            position,
            shirt_number,
            team_id,
            team_name,
            team_crest,
            contract_start,
            contract_until
        FROM football_player
        WHERE team_id = {team_id}
        ORDER BY 
            CASE 
                WHEN position = 'Goalkeeper' THEN 1
                WHEN position = 'Defence' THEN 2
                WHEN position = 'Midfield' THEN 3
                WHEN position = 'Offence' THEN 4
                ELSE 5
            END,
            shirt_number ASC
    """
    return fetch_all(query)

def get_participated_league(team_id):
    query = f"""
        SELECT 
        l.id AS league_id,
        l.name AS league_name,
        l.logo_path,
        l.country,
        tc.season_start,
        tc.season_end
    FROM team_competitions tc
    JOIN leagues l ON tc.league_id = l.id
    WHERE tc.team_id = {team_id}
    ORDER BY tc.season_start DESC;
    """
    return fetch_all(query)