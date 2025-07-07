from Modules import under_update
from Controllers.teams_controller import get_all_teams
from Renders.render_helpers_team import render_team_gallery
def render():
    #under_update.under_update_view()
    teams = get_all_teams()
    render_team_gallery(teams)
    
    