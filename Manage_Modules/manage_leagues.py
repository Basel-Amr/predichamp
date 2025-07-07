import streamlit as st
import os
from Manage_Controllers import manage_leagues_controller as ctrl
import datetime

def manage_leagues():
    st.header("🏆 Manage Leagues")
    st.info("Here you can view, edit, delete, and add leagues and their stages.")

    # === Top Buttons ===
    col_api, col_del, col_add = st.columns([2, 1, 2])

    with col_api:
        if st.button("🌐 Fetch Leagues from API"):
            leagues = ctrl.fetch_leagues_from_api()
            for league in leagues:
                ctrl.insert_league(league)
            st.success("Leagues fetched and inserted successfully!")
            st.rerun()

    with col_del:
        if st.button("🗑️ Delete All Leagues", help="This will remove all leagues!"):
            ctrl.delete_all_leagues()
            st.warning("All leagues have been deleted.")
            st.rerun()
    
    # === Add League Button Toggle ===
    if "show_add_form" not in st.session_state:
        st.session_state.show_add_form = False

    with col_add:
        if st.button("➕ Add League", help="This button is used to add a league or cup"):
            st.session_state.show_add_form = not st.session_state.show_add_form

    # === Add League Form ===
    if st.session_state.show_add_form:
        st.markdown("## ➕ Add New League")
        with st.form("add_league_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                name = st.text_input("League Name")
                trade_name = st.text_input("Trade Name")
                country = st.text_input("Country")
                type_value = st.selectbox("Type", ["LEAGUE", "CUP"])
                is_active = st.checkbox("Active", value=True)
                start_date = st.date_input("Start Date")
                end_date = st.date_input("End Date")
            with col2:
                logo_file = st.file_uploader("Upload Logo", type=["png", "jpg", "svg"], key="new_logo")

            submitted = st.form_submit_button("✅ Submit")
            if submitted:
                if not name or not logo_file:
                    st.error("League name and logo are required.")
                else:
                    logo_filename = f"{name.replace(' ', '_')}_{logo_file.name}"
                    os.makedirs("Assets/Leagues", exist_ok=True)
                    with open(f"Assets/Leagues/{logo_filename}", "wb") as f:
                        f.write(logo_file.read())

                    code = logo_file.name.split(".")[0].upper()
                    ctrl.add_league(
                        name.strip(),
                        country.strip() if country else "Unknown",
                        type_value,
                        int(is_active),
                        logo_filename,
                        code,
                        trade_name.strip() if trade_name else name.strip(),
                        start_date,
                        end_date
                    )
                    st.success(f"✅ League '{name}' added successfully!")
                    st.session_state.show_add_form = False
                    st.rerun()

    # === Show Leagues ===
    leagues = ctrl.get_all_leagues()
    if not leagues:
        st.warning("No leagues found.")
        return

    for league in leagues:
        logo_path = ctrl.get_league_logo_path(league['logo_path'])

        with st.container():
            col_logo, col_info = st.columns([1, 4])
            try:
                with col_logo:
                    if logo_path and os.path.exists(logo_path):
                        st.image(logo_path, width=80)
                    else:
                        st.image("Assets/default_league.png", width=40, caption="No Logo")
            except:
                pass

            with col_info:
                st.markdown(f"### ⚽ {league['name']} ({league['country']})")

            with st.expander("Edit League & Stages", expanded=False):
                col1, col2 = st.columns([3, 1])

                with col1:
                    # Convert to datetime.date if value exists
                    start_date_value = datetime.date.fromisoformat(league['start_date']) if league['start_date'] else datetime.date.today()
                    end_date_value = datetime.date.fromisoformat(league['end_date']) if league['end_date'] else datetime.date.today()
                    try:
                        st.image(logo_path, width=40)
                    except:
                        pass
                    st.markdown("### ✏️ Edit League Info")
                    name = st.text_input("Name", value=league['name'], key=f"name_{league['id']}")
                    trade_name = st.text_input("Trade Name", value=league['Trade_Name'], key=f"trade_name_{league['id']}")
                    country = st.text_input("Country", value=league['country'], key=f"country_{league['id']}")
                    type_option = st.selectbox("Type", ["LEAGUE", "CUP"], key=f"type_{league['id']}")
                    is_active = st.checkbox("Active", value=True, key=f"active_{league['id']}")
                    start_date = st.date_input("Start Date",value=start_date_value, key=f"start_date_{league['id']}" )
                    end_date = st.date_input("End Date",value=end_date_value, key=f"end_date_{league['id']}" )
                    # start_date = st.date_input("Start Date")
                    # end_date = st.date_input("End Date")


                    logo_file = st.file_uploader("Upload Logo", type=["png", "jpg", "svg"], key=f"logo_{league['id']}")
                    logo_path = league['logo_path']
                    if logo_file:
                        logo_path = f"{league['id']}_{logo_file.name}"
                        os.makedirs("Assets/Leagues", exist_ok=True)
                        with open(f"Assets/Leagues/{logo_path}", "wb") as f:
                            f.write(logo_file.read())

                    if st.button("💾 Save Changes", key=f"update_{league['id']}"):
                        ctrl.update_league_details(
                            league['id'], name, country, type_option, int(is_active), logo_path, trade_name, start_date, end_date 
                        )
                        st.success("League updated!")
                        st.rerun()

                with col2:
                    if st.button("❌ Delete League", key=f"delete_{league['id']}"):
                        ctrl.delete_league(league['id'])
                        st.warning("League deleted!")
                        st.rerun()

                # === Stages Section ===
                st.markdown("### 🎯 Stages")
                stages = ctrl.get_stages_by_league(league['id'])
                for stage in stages:
                    col1, col2, col3, col4, col5 = st.columns([2, 1, 1, 1, 1])
                    new_name = col1.text_input("Stage Name", value=stage['name'], key=f"stage_name_{stage['id']}")
                    two_legged = col2.checkbox("Two-Legged", value=bool(stage['is_two_legged']), key=f"tl_{stage['id']}")
                    draw = col3.checkbox("Draws Allowed", value=bool(stage['allows_draw']), key=f"draw_{stage['id']}")
                    pen = col4.checkbox("Penalties", value=bool(stage['has_penalties']), key=f"pen_{stage['id']}")

                    if col5.button("💾", key=f"update_stage_{stage['id']}", help="Update this stage"):
                        ctrl.update_stage(stage['id'], new_name, int(two_legged), int(draw), int(pen))
                        st.success("Stage updated!")
                        st.rerun()

                    if col5.button("🗑️", key=f"delete_stage_{stage['id']}", help="Delete this stage"):
                        ctrl.delete_stage(stage['id'])
                        st.warning("Stage deleted!")
                        st.rerun()

                # === Add New Stage ===
                st.markdown("#### ➕ Add New Stage")
                new_stage_name = st.text_input("New Stage Name", key=f"new_stage_{league['id']}")
                if st.button("➕ Add Stage", key=f"add_stage_{league['id']}"):
                    if new_stage_name.strip():
                        ctrl.insert_stage(new_stage_name.strip(), league['id'])
                        st.success("New stage added!")
                        st.rerun()
                    else:
                        st.error("Stage name cannot be empty.")
                        
    

