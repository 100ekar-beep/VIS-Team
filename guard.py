import streamlit as st


def require_login():
    """Call at the top of every protected page. Stops the page if not logged in."""
    if "user" not in st.session_state:
        st.session_state.user = None
    if not st.session_state.user:
        st.warning("Please login first (see the main page in the sidebar).")
        st.stop()
    return st.session_state.user
