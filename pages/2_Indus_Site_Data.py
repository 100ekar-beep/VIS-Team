import sys
from pathlib import Path

import streamlit as st

st.set_page_config(page_title="Indus Site Data - DEBUG", page_icon="📊", layout="wide")
st.write("✅ CHECKPOINT 1: imports + set_page_config OK")

import pandas as pd
import requests
st.write("✅ CHECKPOINT 2: pandas + requests import OK")

sys.path.append(str(Path(__file__).resolve().parent.parent))
from utils.guard import require_login
from utils.supabase_client import get_supabase_client, is_demo_mode
st.write("✅ CHECKPOINT 3: utils import OK")

user = require_login()
st.write("✅ CHECKPOINT 4: require_login OK, user =", user)

supabase = get_supabase_client()
st.write("✅ CHECKPOINT 5: get_supabase_client() returned, is None?", supabase is None)

try:
    URL = st.secrets["SUPABASE_URL"]
    KEY = st.secrets["SUPABASE_KEY"]
    st.write("✅ CHECKPOINT 6: secrets read OK")
except Exception as e:
    URL = None
    KEY = None
    st.write("⚠️ CHECKPOINT 6: secrets read FAILED:", e)

if supabase is not None:
    st.write("Trying a tiny test query to dropdown_master ...")
    try:
        res = supabase.table("dropdown_master").select("category").limit(1).execute()
        st.write("✅ CHECKPOINT 7: Supabase query OK, rows:", len(res.data))
    except Exception as e:
        st.write("⚠️ CHECKPOINT 7: Supabase query FAILED:", e)

st.write("🎉 ALL CHECKPOINTS DONE — page fully loaded.")
