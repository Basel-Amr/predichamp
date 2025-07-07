import streamlit as st
import os
from Manage_Controllers import manage_teams_controller as ctrl
import base64

import base64

def render_logo_with_border(logo_path, team_color, team_name):
    if logo_path and os.path.exists(logo_path):
        try:
            import base64
            with open(logo_path, "rb") as image_file:
                encoded = base64.b64encode(image_file.read()).decode()
            data_uri = f"data:image/png;base64,{encoded}"

            safe_class = team_name.replace(" ", "_").replace("-", "_").lower()
            initials = ''.join([w[0] for w in team_name.split()][:2]).upper()

            st.markdown(f"""
            <style>
            @keyframes pulse-{safe_class} {{
                0% {{ box-shadow: 0 0 10px {team_color}; }}
                50% {{ box-shadow: 0 0 22px {team_color}; }}
                100% {{ box-shadow: 0 0 10px {team_color}; }}
            }}
            .logo-container-{safe_class}:hover {{
                transform: scale(1.1);
                cursor: pointer;
            }}
            </style>

            <div style="
                display: flex;
                flex-direction: column;
                align-items: center;
                justify-content: center;
                margin-top: 10px;
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            ">
                <div class="logo-container-{safe_class}" title="{team_name}" style="
                    width: 120px;
                    height: 120px;
                    border-radius: 50%;
                    border: 4px solid {team_color};
                    background: transperent;
                    animation: pulse-{safe_class} 2s infinite;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    overflow: hidden;
                    transition: transform 0.3s ease-in-out;
                    position: relative;
                ">
                    <img src="{data_uri}" style="
                        width: 90px;
                        height: 90px;
                        border-radius: 50%;
                        object-fit: contain;
                        background-color: transperent;
                    " />
                    <div style="
                        position: absolute;
                        bottom: -6px;
                        right: -6px;
                        background-color: transperent;
                        color: {team_color};
                        font-weight: bold;
                        font-size: 0.8rem;
                        padding: 2px 6px;
                        border-radius: 999px;
                        border: 1px solid {team_color};
                        box-shadow: 0 0 4px rgba(0,0,0,0.4);
                    ">
                        {initials}
                    </div>
                </div>
                <div style="
                    margin-top: 8px;
                    font-size: 1rem;
                    font-weight: 700;
                    color: {team_color};
                    background-color: rgba(255, 255, 255, 0.85);
                    padding: 4px 10px;
                    border-radius: 8px;
                    text-shadow: none;
                    box-shadow: 0 2px 6px rgba(0, 0, 0, 0.3);
                    text-align: center;
                ">
                    {team_name}
                </div>
            </div>
            """, unsafe_allow_html=True)

        except Exception:
            render_logo_fallback(team_name, team_color)
    else:
        render_logo_fallback(team_name, team_color)





def render_logo_fallback(team_name, team_color):
    initials = ''.join([word[0] for word in team_name.split()][:2]).upper()

    st.markdown(f"""
    <div style="
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        margin-top: 10px;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    ">
        <div title='{team_name}' style="
            width: 90px;
            height: 90px;
            border-radius: 50%;
            border: 3px solid {team_color};
            background-color: {team_color};
            box-shadow: 0 0 12px {team_color};
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-size: 1.5rem;
            font-weight: bold;
            transition: transform 0.3s ease;
        "
        onmouseover="this.style.transform='scale(1.05)'" 
        onmouseout="this.style.transform='scale(1)'">
            {initials}
        </div>
        <div style="
            margin-top: 8px;
            font-size: 1rem;
            font-weight: 700;
            color: {team_color};
            background-color: rgba(255, 255, 255, 0.85);
            padding: 4px 10px;
            border-radius: 8px;
            text-shadow: none;
            box-shadow: 0 2px 6px rgba(0, 0, 0, 0.3);
            text-align: center;
        ">
            {team_name}
        </div>

    </div>
    """, unsafe_allow_html=True)



def manage_teams():
    st.header("👕 Manage Teams")
    st.info("Here you can view, edit, and update teams for each nationality.")

    # === Fetch All Nationalities with Counts ===
    nation_team_map = ctrl.get_nationalities_with_team_counts()
    if not nation_team_map:
        st.warning("No nationalities or teams found.")
        return
    # === Top Controls ===
    col_api, col_del, col_add = st.columns([3, 2, 2])
    # Prepare selectbox with counts
    options = [f"{nat} ({count})" for nat, count in nation_team_map.items()]
    selected_option = st.selectbox("🌍 Select Nationality", options=options)
    selected_nationality = selected_option.split(" (")[0]  # Extract nationality
    
    with col_api:
        if st.button("🌐 Fetch All Teams from All Competitions", help="This button is used to fetch all the teams"):
            added = ctrl.fetch_all_teams_from_api()
            st.success(f"✅ {added} teams fetched and inserted from API.")
            st.rerun()

    with col_del:
        if st.button("🗑️ Delete All Teams for This Nation", help="This button is used to delete all the teams"):
            ctrl.delete_teams_by_nationality(selected_nationality)
            st.warning(f"🗑️ All teams removed for '{selected_nationality}'.")
            st.rerun()
    
    with col_add:
        if "show_add_team_form" not in st.session_state:
            st.session_state.show_add_team_form = False

        if st.button("➕ Add Team Manually", help="This button is used to add a team manually"):
            st.session_state.show_add_team_form = not st.session_state.show_add_team_form
            
        if st.session_state.show_add_team_form:
            st.markdown("## ➕ Add New Team")

            with st.form("manual_team_form", clear_on_submit=True):
                col1, col2 = st.columns(2)

                with col1:
                    name = st.text_input("Short Name")
                    tla = st.text_input("TLA (3-letter code)")
                    official_name = st.text_input("Official Name")
                    nationality = st.text_input("Nationality", value=selected_nationality)
                    venue_name = st.text_input("Venue Name", value="no_data")
                    color = st.color_picker("Team Color", value="#cccccc", key="color_picker_add")

                with col2:
                    logo_file = st.file_uploader("Upload Logo", type=["png", "jpg", "svg"], key="manual_logo")

                submitted = st.form_submit_button("✅ Submit")
                if submitted:
                    if not name or not official_name or not logo_file:
                        st.error("ID, Name, Official Name, and Logo are required.")
                    else:
                        logo_filename = f"{nationality}_{name.replace(' ', '_')}_{logo_file.name}"
                        os.makedirs("Assets/Teams", exist_ok=True)
                        with open(f"Assets/Teams/{logo_filename}", "wb") as f:
                            f.write(logo_file.read())

                        # Call your controller method to insert
                        try:
                            ctrl.insert_team_manual(
                                name=name.strip(),
                                official_name=official_name.strip(),
                                tla=tla.strip(),
                                logo_path=logo_filename,
                                nationality=nationality.strip(),
                                venue_name=venue_name.strip(),
                            )
                            st.success(f"✅ Team '{official_name}' added successfully!")
                            st.session_state.show_add_team_form = False
                            st.rerun()
                        except Exception as e:
                            st.error(f"❌ Failed to add team: {e}")



    # === Fetch Teams for Selected Nationality ===
    teams = ctrl.get_teams_by_nationality(selected_nationality)
    if not teams:
        st.info(f"No teams found for {selected_nationality}.")
        return

    # === Show Each Team in Expander ===
    for team in teams:
        logo_path = ctrl.get_team_logo_path(team['logo_path'])
        with st.container():
            col_logo, col_info = st.columns([1, 4])
            with col_logo:
                if logo_path and os.path.exists(logo_path):
                    team_color = team['color']
                    team_name = team['name']
                    render_logo_with_border(logo_path, team_color, team_name)
                    pass
                else:
                    #st.image("Assets\Clubs\no_logo.jpg", width=40, caption="No Logo")
                    pass

            with col_info:
                st.markdown(f"### ⚽ {team['name']} ({team['nationality']})")
            with st.expander(f"🏷️ {team['name']} (#{team['id']})", expanded=False):
                col1, col2 = st.columns([3, 2])
                with col1:
                    raw_capacity = team.get('venue_capacity')
                    try:
                        default_capacity = int(raw_capacity)
                    except (TypeError, ValueError):
                        default_capacity = 0  # Fallback value if it's 'no_data', None, etc.
                    name = st.text_input("Short Name", value=team['name'], key=f"name_{team['id']}")
                    official_name = st.text_input("Official Name", value=team['official_name'], key=f"off_name_{team['id']}")
                    tla = st.text_input("TLA", value=team.get('tla') or "", key=f"tla_{team['id']}")
                    nationality = st.text_input("Nationality", value=team.get('nationality') or "", key=f"nat_{team['id']}")
                    venue_name = st.text_input("venue_name", value=team['Venue_name'], key=f"venue_name_{team['id']}")
                    venue_location = st.text_input("venue_location", value=team['venue_location'], key=f"venue_location{team['id']}")
                    venue_capacity = st.number_input("venue_capacity", value=default_capacity, key=f"venue_capacity{team['id']}")
                    color = st.color_picker("Team Color", value=team.get('color', '#cccccc'), key=f"color_{team['id']}")

                with col2:
                    logo_path = ctrl.get_team_logo_path(team['logo_path'])
                    if logo_path and os.path.exists(logo_path):
                        team_color = team['color']
                        team_name = team['name']
                        render_logo_with_border(logo_path, team_color, team_name)
                    else:
                        st.image("Assets/Clubs/no_logo.jpg", width=80, caption="No Logo")

                    logo_file = st.file_uploader("Upload New Logo", type=["png", "jpg", "svg"], key=f"logo_{team['id']}")
                    new_logo_filename = team['logo_path']
                    if logo_file:
                        new_logo_filename = f"{team['id']}_{logo_file.name}"
                        os.makedirs("Assets/Teams", exist_ok=True)
                        with open(f"Assets/Teams/{new_logo_filename}", "wb") as f:
                            f.write(logo_file.read())

                col_save, col_del = st.columns([1, 1])
                if col_save.button("💾 Save Changes", key=f"save_{team['id']}"):
                    ctrl.update_team_full(
                        team_id=team['id'],
                        name=name.strip(),
                        official_name=official_name.strip(),
                        tla=tla.strip(),
                        logo_path=new_logo_filename,
                        nationality=nationality.strip(),
                        venue_name=venue_name,
                        color=color,
                        venue_location = venue_location,
                        venue_capacity = venue_capacity
                    )
                    st.success(f"✅ Team '{name}' updated.")
                    st.rerun()

                if col_del.button("🗑️ Delete", key=f"delete_{team['id']}"):
                    ctrl.delete_team(team['id'])
                    st.warning(f"🗑️ Team '{team['name']}' deleted.")
                    st.rerun()
