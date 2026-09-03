"""
Central place to get the Supabase client.

If SUPABASE_URL / SUPABASE_KEY aren't set in .streamlit/secrets.toml yet,
the app runs in DEMO MODE using sample data (see utils/data.py) so you can
test the UI before wiring up the real database.
"""

import streamlit as st

try:
    from supabase import create_client, Client
except ImportError:  # pragma: no cover
    create_client = None
    Client = None


@st.cache_resource(show_spinner=False)
def get_supabase_client():
    """Returns a Supabase client, or None if not configured (-> demo mode)."""
    try:
        url = st.secrets["SUPABASE_URL"]
        key = st.secrets["SUPABASE_KEY"]
    except Exception as e:
        st.session_state["_supabase_debug"] = f"Secrets not found/readable: {e}"
        return None

    if not url or not key or create_client is None:
        st.session_state["_supabase_debug"] = "URL/Key empty, or supabase package not installed."
        return None

    try:
        client = create_client(url, key)
        st.session_state["_supabase_debug"] = "Connected OK"
        return client
    except Exception as e:
        st.session_state["_supabase_debug"] = f"create_client() failed: {e}"
        return None


def is_demo_mode() -> bool:
    return get_supabase_client() is None
