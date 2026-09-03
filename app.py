import streamlit as st

from utils.auth import verify_login
from utils.supabase_client import is_demo_mode

st.set_page_config(page_title="Login - JMS App", page_icon="🔐", layout="centered")

# ---- session defaults ------------------------------------------------------
if "user" not in st.session_state:
    st.session_state.user = None
if "selected_site" not in st.session_state:
    st.session_state.selected_site = None
if "jms_line_items" not in st.session_state:
    st.session_state.jms_line_items = None

# ---- already logged in -----------------------------------------------------
if st.session_state.user:
    st.success(f"Logged in as **{st.session_state.user['team_name']}**")
    st.write("👈 Use the sidebar: **My Sites** to pick a site, then **Create JMS**.")
    if st.button("Logout"):
        st.session_state.user = None
        st.session_state.selected_site = None
        st.session_state.jms_line_items = None
        st.rerun()
    st.stop()

# ---- login form -------------------------------------------------------------
st.title("🔐 Login")

if is_demo_mode():
    st.info("Demo mode: Supabase not connected yet. Use mobile **9999999999** / password **demo123**.")

with st.form("login_form"):
    mobile_number = st.text_input("Mobile Number")
    password = st.text_input("Password", type="password")
    submitted = st.form_submit_button("Login", type="primary", use_container_width=True)

    if submitted:
        user = verify_login(mobile_number, password)
        if user:
            st.session_state.user = user
            st.rerun()
        else:
            st.error("Invalid mobile number or password.")
