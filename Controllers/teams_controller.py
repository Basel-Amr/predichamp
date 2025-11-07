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

def get_team_id_by_name(team_name):
    """
    Fetch the team ID by its name (case-insensitive).

    Args:
        team_name (str): The name of the team.

    Returns:
        int | None: The team's ID if found, otherwise None.
    """
    if not team_name:
        return None

    query = f"""
        SELECT id
        FROM teams
        WHERE LOWER(name) = LOWER('{team_name}')
        LIMIT 1
    """
    result = fetch_one(query)
    return result["id"] if result else None

def get_match_full_info(match_id):
    """
    Fetch all related info for a given match_id:
    - Teams (names + IDs)
    - Round, Stage, and League info
    - Match rules (allows_draw, has_penalties, is_two_legged)
    Returns a clean dictionary ready for render_prediction_form().
    """

    query = """
        SELECT 
            m.id AS match_id,
            m.home_team_id,
            m.away_team_id,
            th.name AS home_team,
            ta.name AS away_team,
            m.match_datetime,
            r.id AS round_id,
            r.name AS round_name,
            s.id AS stage_id,
            s.name AS stage_name,
            s.is_two_legged,
            s.allows_draw,
            s.has_penalties,
            l.id AS league_id,
            l.name AS league_name
        FROM matches m
        LEFT JOIN teams th ON th.id = m.home_team_id
        LEFT JOIN teams ta ON ta.id = m.away_team_id
        LEFT JOIN rounds r ON r.id = m.round_id
        LEFT JOIN stages s ON s.id = m.stage_id
        LEFT JOIN leagues l ON l.id = s.league_id
        WHERE m.id = ?
    """

    row = fetch_one(query, (match_id,))
    if not row:
        raise ValueError(f"❌ No match found with id {match_id}")

    # Build the dict
    match_info = {
        "id": row["match_id"],
        "home_team_id": row["home_team_id"],
        "away_team_id": row["away_team_id"],
        "home_team": row["home_team"],
        "away_team": row["away_team"],
        "match_datetime": row["match_datetime"],
        "allows_draw": row["allows_draw"],
        "has_penalties": row["has_penalties"],
        "is_two_legged": row["is_two_legged"],
        "round_id": row["round_id"],
        "round_name": row["round_name"],
        "stage_id": row["stage_id"],
        "stage_name": row["stage_name"],
        "league_id": row["league_id"],
        "league_name": row["league_name"]
    }

    return match_info

