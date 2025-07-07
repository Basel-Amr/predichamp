import streamlit as st
from streamlit_lottie import st_lottie
import requests

def load_lottieurl(url):
    r = requests.get(url)
    if r.status_code != 200:
        return None
    return r.json()

def under_update_view():
    lottie_url = "https://assets7.lottiefiles.com/packages/lf20_touohxv0.json"
    animation = load_lottieurl(lottie_url)
    
    # Remove the logo line if you don't have a logo yet
    # st.image("your_logo.png", width=150)  

    st.markdown("""
    <h1 style='text-align:center; color:#ff4b4b;'>🚧 Under Maintenance 🚧</h1>
    <h3 style='text-align:center;'>This feature is currently being updated.<br>Check back soon!</h3>
    """, unsafe_allow_html=True)

    if animation:
        st_lottie(animation, height=300, loop=True)

    st.caption("Thank you for your patience.")
