import sys
from pathlib import Path

import streamlit as st

sys.path.append(str(Path(__file__).resolve().parent.parent))
from utils.guard import require_login
from utils.data import get_sites_for_user

st.set_page_config(page_title="My Sites", page_icon="📍", layout="wide")

user = require_login()

st.title("📍 My Sites")
st.caption(f"Sites allocated to {user['full_name']}")

sites_df = get_sites_for_user(user["id"])

if sites_df.empty:
    st.warning("Koi site allocate nahi hui hai aapko abhi. Admin se contact karo.")
    st.stop()

st.dataframe(sites_df.drop(columns=["id"], errors="ignore"), use_container_width=True, hide_index=True)

st.divider()
st.subheader("Select a site to create JMS")

site_labels = [
    f"{row['Site ID']} — {row['Site Name']}" for _, row in sites_df.iterrows()
]
choice = st.selectbox("Site", options=range(len(sites_df)), format_func=lambda i: site_labels[i])

if st.button("Select this site →", type="primary"):
    st.session_state.selected_site = sites_df.iloc[choice].to_dict()
    st.session_state.jms_line_items = None  # reset when switching sites
    st.success(f"Site selected: {site_labels[choice]}. Ab **Create JMS** page pe jao.")

if st.session_state.get("selected_site"):
    s = st.session_state.selected_site
    st.info(f"Currently selected: **{s.get('Site ID')} — {s.get('Site Name')}**")
