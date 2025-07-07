import os
import io
import base64
import glob
from PIL import Image
import streamlit as st
from Controllers.players_controller import get_player_info, update_player_info, delete_player
from streamlit_extras.metric_cards import style_metric_cards

AVATAR_FOLDER = "Assets/Avatars"

def image_to_base64(img: Image.Image) -> str:
    buffered = io.BytesIO()
    img.save(buffered, format="PNG")
    return base64.b64encode(buffered.getvalue()).decode()

def render(player_id):
    

    st.markdown("""
        <style>
        .animated-header {
            animation: fadeInSlide 1s ease forwards;
            font-size: 2.8rem;
            font-weight: 700;
            color: #2c3e50;
            text-align: center;
            margin-bottom: 1rem;
            font-family: 'Poppins', sans-serif;
        }
        .avatar-frame {
            width: 160px;
            height: 160px;
            border-radius: 50%;
            overflow: hidden;
            box-shadow: 0 0 20px #60a5fa;
            margin: auto;
            border: 4px solid #3b82f6;
            background-position: center;
            background-repeat: no-repeat;
            background-size: cover;
            background-color: #eee;
            animation: glow 2s infinite alternate;
        }
        @keyframes glow {
            from { box-shadow: 0 0 10px #3b82f6; }
            to { box-shadow: 0 0 25px #60a5fa; }
        }
        img.avatar-thumb {
            border-radius: 50%;
            transition: 0.3s ease-in-out;
            margin-bottom: 5px;
        }
        img.avatar-thumb:hover {
            transform: scale(1.1);
            box-shadow: 0 0 12px rgba(59,130,246,0.8);
            cursor: pointer;
        }
        </style>
    """, unsafe_allow_html=True)

    st.markdown('<div class="animated-header">⚽ My Profile ⚽</div>', unsafe_allow_html=True)

    player = get_player_info(player_id)
    if not player:
        st.error("Player info not found!")
        return

    rank = player['rank']
    st.markdown(f"""
    <div style="
        text-align:center;
        font-size:1.8rem;
        font-weight:700;
        color:#6366f1;
        background-color:#f0f4ff;
        padding:0.75rem 1.25rem;
        border-radius:10px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.08);
        margin-bottom:1rem;
        font-family:'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    ">
        🏅 Your Global Rank: <span style="color:#3b82f6;"> {player['rank']}</span>
    </div>
""", unsafe_allow_html=True)


    col1, col2, col3 = st.columns([1, 2, 3])
    with col1:
        avatar_name = player.get("avatar_name")
        avatar_path = os.path.join(AVATAR_FOLDER, avatar_name) if avatar_name else None

        if not st.session_state.get("edit_mode", False):
            if avatar_path and os.path.exists(avatar_path):
                img = Image.open(avatar_path)
                b64_img = image_to_base64(img)
                st.markdown(
                    f'<div class="avatar-frame" style="background-image: url(data:image/png;base64,{b64_img});"></div>',
                    unsafe_allow_html=True
                )
            else:
                st.markdown(
                    '<div class="avatar-frame" style="display:flex;align-items:center;justify-content:center;color:#999;font-size:1.2rem;">No Avatar</div>',
                    unsafe_allow_html=True
                )
        else:
            st.markdown("### 🖼️ Choose Your Avatar")
            avatar_files = sorted([
                os.path.basename(p)
                for ext in ("*.png", "*.jpg", "*.jpeg")
                for p in glob.glob(os.path.join(AVATAR_FOLDER, ext))
            ])

            if not avatar_files:
                st.warning("❌ No avatars found in Assets/Avatars. Please add PNG or JPG files.")
            else:
                selected_avatar = st.session_state.get("selected_avatar_name", player.get("avatar_name"))
                cols = st.columns(5)

                for idx, avatar_file in enumerate(avatar_files):
                    avatar_path = os.path.join(AVATAR_FOLDER, avatar_file)
                    img = Image.open(avatar_path)
                    b64_img = image_to_base64(img)

                    border_color = "#3b82f6" if avatar_file == selected_avatar else "#ccc"
                    with cols[idx % 5]:
                        if st.button(" ", key=f"avatar_{avatar_file}"):
                            st.session_state.selected_avatar_name = avatar_file

                        st.markdown(
                            f"<img class='avatar-thumb' src='data:image/png;base64,{b64_img}' width='80' "
                            f"style='border: 4px solid {border_color}; border-radius: 50%;'/>",
                            unsafe_allow_html=True
                        )
                        if avatar_file == selected_avatar:
                            st.markdown("<center><small style='color:#3b82f6;'>✅ Selected</small></center>", unsafe_allow_html=True)
                        else:
                            st.markdown("<br>", unsafe_allow_html=True)

    with col2:
        st.markdown(f"**👤 Name:** {player['username']}")
        st.markdown(f"**📧 Email:** {player['email']}")
        st.markdown(f"**🗓️ Joined:** {player['created_at']}")
        # img = qrcode.make(f"https://yourdomain.com/player/{player_id}")
        buf = io.BytesIO()
        # img.save(buf)
        # st.image(buf.getvalue(), caption="📲 Scan to View My Profile")

    with col3:
        colA, colB, colC = st.columns(3)
        colA.metric("⭐ Points", player["total_points"])
        colB.metric("🏆 Leagues", player["total_leagues_won"])
        colC.metric("🥇 Cups", player["total_cups_won"])
        style_metric_cards(
            background_color="#ff9f9",  # light background
            border_left_color="#6366f1",  # more readable indigo border
            border_color="#e5e7eb",       # light gray border
            border_radius_px=10,
            box_shadow=True,
        )

        achievements = []
        if player["total_points"] > 80:
            achievements.append("🔓 500+ Points Master")
        if player["total_leagues_won"] > 2:
            achievements.append("🏆 League Dominator")
        if player["total_cups_won"] >= 1:
            achievements.append("🥇 Cup Champion")
        if achievements:
            st.markdown("### 🏅 Achievements")
            for a in achievements:
                st.markdown(f"- {a}")


    if st.button("✏️ Edit Profile"):
        st.session_state.edit_mode = not st.session_state.get("edit_mode", False)
        st.rerun()

    if st.session_state.get("edit_mode", False):
        st.subheader("✍️ Edit Your Information")
        new_username = st.text_input("👤 Name", value=player['username'])
        new_email = st.text_input("📧 Email", value=player['email'])
        new_password = st.text_input("🔑 Password", value="", type="password")

        if st.button("💾 Save Changes"):
            new_avatar_name = st.session_state.get("selected_avatar_name", player.get("avatar_name"))
            success = update_player_info(
                player_id,
                username=new_username,
                email=new_email,
                password=new_password if new_password else None,
                avatar_name=new_avatar_name
            )
            if success:
                st.success("✅ Profile updated successfully!")
                st.session_state.edit_mode = False
                st.session_state.username = new_username
                st.rerun()
            else:
                st.error("❌ Failed to update profile. Please try again.")

    if st.button("🗑️ Delete My Account", key="delete_account"):
        st.session_state.show_confirm_delete = True

    if st.session_state.get("show_confirm_delete", False):
        confirmed = st.checkbox("⚠️ Are you sure you want to delete your account?", key="confirm_delete")
        if confirmed and st.button("🔥 Confirm Delete", key="confirm_delete_btn"):
            if delete_player(player_id):
                st.success("🗑️ Account deleted successfully.")
                for key in list(st.session_state.keys()):
                    del st.session_state[key]
                return
            else:
                st.error("❌ Failed to delete account.")

