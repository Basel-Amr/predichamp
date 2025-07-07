# from Modules import under_update
# def render():
#     under_update.under_update_view()

import streamlit as st



ASSET_LOGO_FOLDER = "Assets/Leagues"

from Renders import render_leagues_helper as leagues_view

def render():
    leagues_view.render()
