import streamlit as st

from utils.data import get_user_by_mobile
from utils.cookies import get_cookie_manager, COOKIE_NAME


def require_login():
    """
    Call at the top of every protected page. Tries to auto-login from the
    "remember me" cookie if the session doesn't already have a user (e.g. the
    person bookmarked this page directly, or the app went to sleep and woke
    back up). Stops the page if still not logged in.
    """
    if "user" not in st.session_state:
        st.session_state.user = None

    if not st.session_state.user:
        cookie_manager = get_cookie_manager()
        saved_mobile = cookie_manager.get(COOKIE_NAME)
        if saved_mobile:
            auto_user = get_user_by_mobile(saved_mobile)
            if auto_user:
                st.session_state.user = {k: v for k, v in auto_user.items() if k != "password"}

    if not st.session_state.user:
        st.warning("Please login first (see the main page in the sidebar).")
        st.stop()

    return st.session_state.user
