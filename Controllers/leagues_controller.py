from Controllers.db_controller import get_connection
from Controllers.utils import fetch_all, fetch_one

# 1. Get all active leagues with type 'LEAGUE'
def get_active_leagues():
    query = """
        SELECT id, name, logo_path
        FROM leagues
        WHERE is_active = 1 AND type = 'LEAGUE'
        ORDER BY name
    """
    return fetch_all(query)


# 2. Get league by ID
def get_league_by_id(league_id):
    query = """
        SELECT * FROM leagues WHERE id = ?
    """
    return fetch_one(query, (league_id,))


# 3. Get fixtures by league ID
def get_fixtures_by_league(league_id):
    query = """
        SELECT 
            m.id AS match_id, 
            t1.name AS home_team, 
            t2.name AS away_team,
            m.match_datetime, 
            m.status, 
            m.home_score, 
            m.away_score, 
            m.Venue_name, 
            m.matchday,
            t1.logo_path AS home_logo, 
            t2.logo_path AS away_logo,
            l.country AS nationality, 
            l.name AS league_name,
            s.name AS stage_name
        FROM matches m
        JOIN teams t1 ON m.home_team_id = t1.id
        JOIN teams t2 ON m.away_team_id = t2.id
        JOIN leagues l ON m.league_id = l.id
        LEFT JOIN stages s ON m.stage_id = s.id
        WHERE m.league_id = ?
        ORDER BY m.match_datetime ASC
    """
    rows = fetch_all(query, (league_id,))
    return [dict(row) for row in rows]  # convert each row to dict for easy access



# 4. Get league table from matches
# Uses finished matches only and computes team points
# 3 pts for win, 1 pt for draw, 0 pt for loss

def get_league_table(league_id, country):
    query = """
        SELECT
            t.id,
            t.name AS team_name,
            -- Points
            SUM(
                CASE
                    WHEN (m.home_team_id = t.id AND m.home_score > m.away_score) OR
                        (m.away_team_id = t.id AND m.away_score > m.home_score) THEN 3
                    WHEN m.home_score = m.away_score THEN 1
                    ELSE 0
                END
            ) AS points,

            -- Played games (count matches where team played)
            COUNT(m.id) AS played,

            -- Wins
            SUM(
                CASE
                    WHEN (m.home_team_id = t.id AND m.home_score > m.away_score) OR
                        (m.away_team_id = t.id AND m.away_score > m.home_score) THEN 1
                    ELSE 0
                END
            ) AS wins,

            -- Draws
            SUM(
                CASE
                    WHEN m.home_score = m.away_score THEN 1
                    ELSE 0
                END
            ) AS draws,

            -- Losses
            SUM(
                CASE
                    WHEN (m.home_team_id = t.id AND m.home_score < m.away_score) OR
                        (m.away_team_id = t.id AND m.away_score < m.home_score) THEN 1
                    ELSE 0
                END
            ) AS losses,

            -- Goals for
            SUM(
                CASE WHEN m.home_team_id = t.id THEN m.home_score
                    WHEN m.away_team_id = t.id THEN m.away_score
                    ELSE 0
                END
            ) AS goals_for,

            -- Goals against
            SUM(
                CASE WHEN m.home_team_id = t.id THEN m.away_score
                    WHEN m.away_team_id = t.id THEN m.home_score
                    ELSE 0
                END
            ) AS goals_against

        FROM teams t
        LEFT JOIN matches m
            ON (m.home_team_id = t.id OR m.away_team_id = t.id)
            AND m.league_id = ?
            AND m.status = 'finished'
        WHERE t.nationality = ?
        GROUP BY t.id, t.name
        ORDER BY points DESC, (goals_for - goals_against) DESC;
    """
    rows = fetch_all(query, (league_id, country))
    return [dict(row) for row in rows]
