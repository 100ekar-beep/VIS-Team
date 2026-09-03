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
    except Exception:
        return None

    if not url or not key or create_client is None:
        return None

    try:
        return create_client(url, key)
    except Exception:
        return None


def is_demo_mode() -> bool:
    return get_supabase_client() is None
