from Controllers.db_controller import get_connection
from Controllers.utils import fetch_one, fetch_all, execute_query

def calculate_prediction_score(match, prediction):
    actual_home = match['home_score']
    actual_away = match['away_score']
    predicted_home = prediction['predicted_home_score']
    predicted_away = prediction['predicted_away_score']
    predicted_penalty_winner_id = prediction['predicted_penalty_winner_id']
    actual_penalty_winner_id = match.get('penalty_winner')
    if actual_home is None or actual_away is None:
        return 0  # Match not finished

    score = 0

    def outcome(h, a):
        return 'home' if h > a else 'away' if h < a else 'draw'

    actual_result = outcome(actual_home, actual_away)
    predicted_result = outcome(predicted_home, predicted_away)

    if actual_home == predicted_home and actual_away == predicted_away:
        score = 3
    elif actual_result == predicted_result:
        score = 1

    # Bonus point if penalty winner prediction matches actual
    if actual_penalty_winner_id and predicted_penalty_winner_id:
        if actual_penalty_winner_id == predicted_penalty_winner_id:
            score += 1

    return score


def update_scores_for_match(match_id):
    # Get match details
    match_query = "SELECT * FROM matches WHERE id = ?;"
    match_row = fetch_one(match_query, (match_id,))
    
    if not match_row or match_row['home_score'] is None or match_row['away_score'] is None:
        return  # Match not finished

    match = dict(match_row)  # Convert sqlite3.Row to dict

    # Get all predictions for that match
    pred_query = "SELECT * FROM predictions WHERE match_id = ?;"
    predictions = fetch_all(pred_query, (match_id,))

    for pred in predictions:
        score = calculate_prediction_score(match, pred)
        update_query = "UPDATE predictions SET score = ? WHERE id = ?;"
        execute_query(update_query, (score, pred['id']))
