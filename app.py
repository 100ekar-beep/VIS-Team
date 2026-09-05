import datetime

import streamlit as st

from utils.auth import verify_login
from utils.data import get_user_by_mobile
from utils.supabase_client import is_demo_mode
from utils.cookies import get_cookie_manager, COOKIE_NAME

st.set_page_config(page_title="Login - JMS App", page_icon="🔐", layout="centered")

cookie_manager = get_cookie_manager()

# ---- session defaults ------------------------------------------------------
if "user" not in st.session_state:
    st.session_state.user = None
if "jms_line_items" not in st.session_state:
    st.session_state.jms_line_items = None

# ---- try to auto-login from the "remember me" cookie ------------------------
# This is what keeps a team member logged in across reloads / the app
# "waking up" again on Streamlit Cloud, instead of asking for login every time.
if st.session_state.user is None:
    saved_mobile = cookie_manager.get(COOKIE_NAME)
    if saved_mobile:
        auto_user = get_user_by_mobile(saved_mobile)
        if auto_user:
            st.session_state.user = {k: v for k, v in auto_user.items() if k != "password"}

# ---- already logged in -----------------------------------------------------
if st.session_state.user:
    st.success(f"Logged in as **{st.session_state.user['team_name']}**")
    st.write("👈 Sidebar se **Site Data** page pe jao — apni sites ki list dikhegi, har site ke saamne 'Open Site' button hoga.")
    if st.session_state.user.get("is_admin"):
        st.caption("🛡️ Aap admin ho — sidebar mein **Team Request** page bhi dikhega.")
    if st.button("Logout"):
        st.session_state.user = None
        st.session_state.jms_line_items = None
        cookie_manager.delete(COOKIE_NAME, key="delete_login_cookie")
        st.rerun()
    st.stop()

# ---- login form -------------------------------------------------------------
st.title("🔐 Login")

if is_demo_mode():
    st.info("Demo mode: Supabase not connected yet. Use mobile **9999999999** / password **demo123**.")
    debug_msg = st.session_state.get("_supabase_debug")
    if debug_msg:
        st.caption(f"🔍 Debug: {debug_msg}")

with st.form("login_form"):
    mobile_number = st.text_input("Mobile Number")
    password = st.text_input("Password", type="password")
    submitted = st.form_submit_button("Login", type="primary", use_container_width=True)

    if submitted:
        user = verify_login(mobile_number, password)
        if user:
            st.session_state.user = user
            # Remember this login on this browser for 90 days, so they
            # don't have to log in again every time the app is opened.
            cookie_manager.set(
                COOKIE_NAME,
                mobile_number.strip(),
                key="set_login_cookie",
                expires_at=datetime.datetime.now() + datetime.timedelta(days=90),
            )
            st.rerun()
        else:
            st.error("Invalid mobile number or password.")
