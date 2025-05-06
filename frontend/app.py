# FILE: frontend/app.py

import streamlit as st
from utils.login import show_login
from utils.signup import show_signup
from utils.home import show_home
from utils.knowledge_base import show_knowledge_base
from utils.nutrition_agent_streamlit import show_nutrition_agent
from utils.nutrition_dashboard import show_nutrition_dashboard
from utils.location_search_streamlit import location_assistance_page
from utils.live_news import render_live_news_page


# Configure the API URL
API_URL = "http://fastapi_service:8000"

# ========== PAGE SETTINGS ==========
st.set_page_config(
    page_title="Chronic Disease Management",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ========== SESSION STATE INIT ==========
if "token" not in st.session_state:
    st.session_state.token = None
    st.session_state.username = None

if "nav_selection" not in st.session_state and st.session_state.token is not None:
    st.session_state.nav_selection = "Home"

# ========== PAGE TITLE ==========
st.title("ChronicCare.AI")

# ========== NOT LOGGED IN ==========
if st.session_state.token is None:
    tab1, tab2 = st.tabs(["Login", "Sign Up"])

    with tab1:
        show_login(API_URL)

    with tab2:
        show_signup(API_URL)

# ========== LOGGED IN ==========
else:
    # Sidebar UI
    st.sidebar.success(f"Logged in as: {st.session_state.username}")

    nav = st.sidebar.radio(
        "Navigation",
        ["Home", "My Profile", "Knowledge Assistant", "Nutrition Planner", "Nutrition Dashboard", "Location Assitance", "Live News"]
    )
    st.session_state.nav_selection = nav

    if st.sidebar.button("Logout"):
        user_keys = [
            "token", "username", "tdee", "remaining_kcal", "selected_recipes",
            "selected_cuisines", "selected_meals", "last_result", "chronic_condition",
            ]
        for key in user_keys:
            if key in st.session_state:
                del st.session_state[key]
        
        if "nav_selection" in st.session_state:
            del st.session_state.nav_selection
        st.rerun()
        

    # ====== Navigation Logic ======
    if nav == "Home":
        show_home(API_URL, section="home")
    elif nav == "My Profile":
        show_home(API_URL, section="profile")
    elif nav == "Knowledge Assistant":
        show_knowledge_base()
    elif nav == "Nutrition Planner":  # ✅ New Option
        show_nutrition_agent(API_URL)
    elif nav == "Nutrition Dashboard":
        show_nutrition_dashboard()
    elif nav == "Location Assitance":
        location_assistance_page()
    elif nav == "Live News":
        render_live_news_page()
