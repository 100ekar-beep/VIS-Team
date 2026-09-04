import sys
from pathlib import Path
import urllib.parse

import streamlit as st
import pandas as pd
import requests  # dropdown_master fallback fetch ke liye

sys.path.append(str(Path(__file__).resolve().parent.parent))
from utils.guard import require_login
from utils.supabase_client import get_supabase_client, is_demo_mode

# --- 1. PAGE CONFIGURATION -------------------------------------------------
st.set_page_config(page_title="Indus Site Data", page_icon="📊", layout="wide")

user = require_login()

# --- 2. CONNECTION (reuses the same Supabase secrets as the rest of the app)
supabase = get_supabase_client()
try:
    URL = st.secrets["SUPABASE_URL"]
    KEY = st.secrets["SUPABASE_KEY"]
except Exception:
    URL = None
    KEY = None

if supabase is None:
    st.warning(
        "Supabase abhi connect nahi hai (demo mode). Ye page real Supabase data ke "
        "bina kaam nahi karega — Settings → Secrets mein SUPABASE_URL / SUPABASE_KEY daalo."
    )
    st.stop()

# --- 3. LAVISH CUSTOM CSS ---
st.markdown("""
    <style>
    .stApp { background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%); color: #0f172a; font-family: 'Inter', sans-serif; }
    
    /* Primary Buttons */
    button[data-testid="baseButton-primary"] {
        background: linear-gradient(90deg, #3b82f6 0%, #2563eb 100%) !important;
        color: white !important; border: none !important; border-radius: 8px !important;
        font-weight: 800 !important; padding: 0.6rem 1.2rem !important;
        box-shadow: 0 4px 6px -1px rgba(59, 130, 246, 0.4) !important;
    }
    
    /* ========================================================
       100% GUARANTEED LAVISH GREEN WHATSAPP BUTTON FIX
       ======================================================== */
    .st-key-wa_send_btn button {
        background: linear-gradient(90deg, #25D366 0%, #128C7E 100%) !important;
        color: white !important; 
        border: 2px solid #128C7E !important; 
        border-radius: 8px !important;
        font-weight: 800 !important; 
        padding: 0.6rem 1.2rem !important;
        box-shadow: 0 4px 10px rgba(37, 211, 102, 0.4) !important;
        width: 100% !important;
    }
    .st-key-wa_send_btn button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 10px 15px -3px rgba(37, 211, 102, 0.6) !important;
        border-color: #075E54 !important;
    }

    /* ========================================================
       FIX FOR INVISIBLE INPUT BOXES (SOLID BORDERS ADDED EVERYWHERE)
       ======================================================== */
    .stTextInput > div > div {
        border: 2px solid #3b82f6 !important; /* Thick Blue Border */
        border-radius: 8px !important;
        background-color: #ffffff !important;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05) !important;
    }
    .stTextInput > div > div:focus-within {
        border-color: #1e3a8a !important;
        box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.3) !important;
    }
    .stTextInput input {
        color: #0f172a !important;
        font-weight: 600 !important;
    }
    
    /* Inputs & Labels */
    label p, label[data-testid="stWidgetLabel"] p { color: #475569 !important; font-weight: 700 !important; font-size: 0.9rem !important; text-transform: uppercase; }
    [data-testid="stDataFrame"] th { background-color: #1E3A8A !important; color: white !important; font-weight: 700 !important; }

    /* Expanders */
    [data-testid="stExpander"] { background-color: #ffffff; border-radius: 12px; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05); border: 1px solid #e2e8f0; }
    
    /* Custom Info Cards WITH SOLID BORDER FIX */
    .info-card {
        background: #ffffff; 
        border-radius: 12px; 
        padding: 20px;
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1); 
        border: 2px solid #94a3b8 !important; /* Solid Border */
        margin-bottom: 15px;
    }
    .info-card-inner {
        border: 1px solid #cbd5e1;
        padding: 10px;
        border-radius: 8px;
        margin-bottom: 10px;
        background-color: #f8fafc;
    }
    </style>
""", unsafe_allow_html=True)


# =====================================================================
# --- EGRESS OPTIMIZATION HELPERS ---
# Search + dropdown lookups are cached so repeat interactions (selecting a
# team, sending WhatsApp, adding a route stop) don't re-run the same
# Supabase queries over and over.
# =====================================================================

@st.cache_data(ttl=30, show_spinner=False)
def search_indus_site(in_id, in_nm):
    """Tries table/column-name variants (cached) to find a matching Indus site record."""
    tables_to_try = ["Excalation Matrix", "Escalation Matrix", "Indus Data"]
    id_cols_to_try = ["Indus ID", "Site ID", "indus_id", "site_id"]
    name_cols_to_try = ["Site Name", "site_name"]

    last_error = ""
    for t in tables_to_try:
        for id_col in id_cols_to_try:
            for nm_col in name_cols_to_try:
                try:
                    query = supabase.table(t).select("*")
                    if in_id:
                        query = query.ilike(id_col, f"%{in_id.strip()}%")
                    if in_nm:
                        query = query.ilike(nm_col, f"%{in_nm.strip()}%")
                    res = query.execute()

                    if res.data:
                        return res.data, "", True
                    elif not in_id and not in_nm:
                        return [], "", True
                except Exception as e:
                    last_error = str(e)
                    continue
    return None, last_error, False


@st.cache_data(ttl=60, show_spinner=False)
def fetch_team_dropdown_cached():
    """Cached fetch of Team Name -> mobile mapping from dropdown_master."""
    team_dict = {}
    dropdown_data = []
    try:
        res = supabase.table("dropdown_master").select("category, option_value, mobile").execute()
        if res.data:
            dropdown_data = res.data
    except Exception:
        try:
            headers = {"apikey": KEY, "Authorization": f"Bearer {KEY}"}
            r = requests.get(f"{URL}/rest/v1/dropdown_master?select=category,option_value,mobile", headers=headers)
            if r.status_code == 200:
                dropdown_data = r.json()
        except Exception:
            pass

    if isinstance(dropdown_data, list) and len(dropdown_data) > 0:
        for r in dropdown_data:
            cat_val = str(r.get('category', '')).strip()
            if cat_val.lower() == 'team name':
                team_name = r.get('option_value')
                team_mobile = r.get('mobile')
                if team_name:
                    team_dict[str(team_name).strip()] = str(team_mobile).strip() if team_mobile else ""
    return team_dict


@st.cache_data(ttl=30, show_spinner=False)
def search_site_for_route(add_sid):
    """Cached lookup used by the Route Plan 'Add to List' form."""
    tables_to_try = ["Excalation Matrix", "Escalation Matrix", "Indus Data"]
    id_cols_to_try = ["Indus ID", "Site ID", "indus_id", "site_id"]

    for t in tables_to_try:
        for id_col in id_cols_to_try:
            try:
                s_res = supabase.table(t).select("*").ilike(id_col, f"%{add_sid.strip()}%").execute()
                if s_res.data:
                    return s_res.data[0]
            except Exception:
                pass
    return None


# =====================================================================
# 📊 INDUS BASIC DATA
# =====================================================================

st.markdown("<h1 style='text-align: center; color: #1E3A8A; margin-bottom: 30px;'>📊 Indus Site Data</h1>", unsafe_allow_html=True)

with st.form("ind_form_v5"):
    i1, i2, i3 = st.columns(3)
    with i1: in_id = st.text_input("📍 Site ID Search")
    with i2: in_nm = st.text_input("🏢 Site Name Search")
    with i3: 
        st.write("")
        sub_ind = st.form_submit_button("🔍 Search Indus")
    
# --- STREAMLIT MEMORY FIX: Dropdown change karne par screen blank hone se rokne ke liye ---
if sub_ind:
    st.session_state['keep_search_active'] = True
    st.session_state['saved_in_id'] = in_id
    st.session_state['saved_in_nm'] = in_nm

if st.session_state.get('keep_search_active'):
    # Memory se variables wapas load karna
    in_id = st.session_state['saved_in_id']
    in_nm = st.session_state['saved_in_nm']

    # --- Bulletproof Search Logic (cached — see search_indus_site above) ---
    res_data, last_error, search_success = search_indus_site(in_id, in_nm)
    res_ind = True if search_success else None  # kept for downstream compatibility

    if search_success and res_data:
        df_ind = pd.DataFrame(res_data)
        st.dataframe(df_ind, use_container_width=True, hide_index=True)
        st.divider()
        
        # --- WhatsApp share button: opens WhatsApp on the user's own phone
        # with the message pre-filled — they pick who to send it to themselves
        # (no team dropdown / no stored mobile number needed at all). ---
        st.markdown("### 💬 Share Site Detail on WhatsApp")
            
        row_in = res_data[0]
        
        # Mapping Data Safely for WhatsApp & Display
        site_id_val = row_in.get('Indus ID', row_in.get('Site ID', row_in.get('indus_id', '-')))
        site_name_val = row_in.get('Site Name', row_in.get('site_name', '-'))
        area_val = row_in.get('Area', row_in.get('Area Name', row_in.get('Site Address', '-')))
        district_val = row_in.get('District', area_val) # Fallback to area if district not found
        cluster_val = row_in.get('Cluster', '-')
        
        tech_name = row_in.get('Technician Detail', row_in.get('Tech Name', '-'))
        tech_num = row_in.get('Technician Number', row_in.get('Tech Number', '-'))
        tech_full = f"{tech_name} ({tech_num})" if tech_num and tech_num != '-' else tech_name
        
        fse_name = row_in.get('FSE Detail', row_in.get('FSE Name', row_in.get('FSE', '-')))
        fse_num = row_in.get('FSE Number', '-')
        fse_full = f"{fse_name} ({fse_num})" if fse_num and fse_num != '-' else fse_name
        
        aom_name = row_in.get('AOM Detail', row_in.get('AOM Name', '-'))
        aom_num = row_in.get('AOM Number', '-')
        aom_full = f"{aom_name} ({aom_num})" if aom_num and aom_num != '-' else aom_name
        
        lat = row_in.get('Lat', row_in.get('Latitude', row_in.get('latitude', '')))
        lon = row_in.get('Long', row_in.get('longitude', row_in.get('Longitude', '')))
        
        # Variables for WhatsApp Template (2 spaces exactly between lat and long)
        lat_long_spaced = f"{lat}  {lon}" if lat and lon else "N/A"
        maps_link = f"https://www.google.com/maps/search/?api=1&query={lat},{lon}" if lat and lon else "N/A"

        def clean_val(v):
            val = str(v).strip()
            return val if val and val != "None" and val != "nan" else "-"

        message_text = (
            f"*नमस्कार*\n\n"
            f"*Site Name* : {clean_val(site_name_val)}\n"
            f"*Site ID* :- {clean_val(site_id_val)}\n"
            f"*District/Area* : {clean_val(district_val)}\n"
            f"*Cluster* : {clean_val(cluster_val)}\n"
            f"*Lat/Long* : {clean_val(lat_long_spaced)}\n\n"
            f"*Technician Detail* :- {clean_val(tech_full)}\n"
            f"*FSE Detail* :- {clean_val(fse_full)}\n"
            f"*AOM Detail* :- {clean_val(aom_full)}\n\n"
            f"*साईट ची लिंक* :-\n"
            f" {clean_val(maps_link)}"
        )
        # No phone number in the link -> WhatsApp opens and lets the user
        # pick which contact/chat to send it to themselves.
        wa_link = f"https://wa.me/?text={urllib.parse.quote(message_text)}"

        with st.container(key="wa_send_btn"):
            st.markdown(
                f'<a href="{wa_link}" target="_blank" style="text-decoration:none;">'
                f'<button style="width:100%; background:linear-gradient(90deg,#25D366 0%,#128C7E 100%);'
                f'color:white;border:2px solid #128C7E;border-radius:8px;font-weight:800;'
                f'padding:0.6rem 1.2rem;cursor:pointer;box-shadow:0 4px 10px rgba(37,211,102,0.4);">'
                f'💬 Send on WhatsApp</button></a>',
                unsafe_allow_html=True,
            )
            
        st.divider()

        # --- Displaying Site Details ---
        st.subheader("📌 Vertical Site Details")
        
        def call_html(label, name, num):
            if num and str(num).strip() not in ['-', '', 'None', 'nan']:
                return f'<div class="info-card-inner">{label}:<br><b>{name}</b> ({num}) <br><a href="tel:{num}" style="text-decoration:none;"><button style="margin-top:5px; background-color:#3b82f6;color:white;border:none;padding:4px 12px;border-radius:6px;cursor:pointer;font-weight:bold;box-shadow: 0 2px 4px rgba(0,0,0,0.1);">📞 Call</button></a></div>'
            return f'<div class="info-card-inner">{label}:<br><b>{name}</b> (-)</div>'
        
        st.markdown("<div class='info-card'>", unsafe_allow_html=True)
        v1, v2 = st.columns(2)
        with v1:
            st.markdown(f"<div class='info-card-inner'>🛰️ <b>Area</b> :- {area_val}</div>", unsafe_allow_html=True)
            st.markdown(call_html("👨‍🔧 <b>Technician Detail</b>", tech_name, tech_num), unsafe_allow_html=True)
            st.markdown(call_html("👨‍💼 <b>AOM Detail</b>", aom_name, aom_num), unsafe_allow_html=True)
        with v2:
            st.markdown(f"<div class='info-card-inner'>📍 <b>Cluster</b> :- {cluster_val}</div>", unsafe_allow_html=True)
            st.markdown(call_html("👷 <b>FSE Detail</b>", fse_name, fse_num), unsafe_allow_html=True)
            if lat and lon and str(lat).strip() not in ['-', '', 'None', 'nan']:
                st.markdown(f"<div class='info-card-inner'>📍 <b>Lat/Long</b> :- {lat} / {lon} <br><a href='{maps_link}' target='_blank' style='text-decoration:none;'><button style='margin-top:5px; background-color:#ef4444;color:white;border:none;padding:4px 12px;border-radius:6px;cursor:pointer;font-weight:bold;box-shadow: 0 2px 4px rgba(0,0,0,0.1);'>📍 View Map</button></a></div>", unsafe_allow_html=True)
            else: 
                st.markdown(f"<div class='info-card-inner'>📍 <b>Lat/Long</b> :- {lat if lat else '-'} / {lon if lon else '-'}</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
        
    elif res_ind is not None: 
        st.info("No data found matching your search in the Database. Kripya Site ID theek se check karein.")
    else:
        st.error(f"⚠️ Search Failed! Aapke naye database mein Table ya Column ka naam alag hai. Supabase Error: {last_error}")

st.divider()

# =====================================================================
# 🧭 ROUTE PLAN
# =====================================================================

st.subheader("🧭 ROUTE PLAN")
if 'route_list' not in st.session_state: st.session_state.route_list = []

with st.expander("🛠️ Add Sites to Route", expanded=True):
    c1, c2 = st.columns(2)
    with c1: start_coords = st.text_input("🏠 Start Location", value="Lonikand, Pune")
    with c2: end_coords = st.text_input("🏁 End Location", placeholder="e.g. Mumbai")
    
    with st.form("add_site_form", clear_on_submit=True):
        add_sid = st.text_input("📍 Add Site ID")
        if st.form_submit_button("➕ Add to List"):
            if add_sid:
                # --- Cached route add logic (see search_site_for_route above) ---
                s_data = search_site_for_route(add_sid)

                if s_data: 
                    # Data normalization for route table
                    norm_data = {
                        'Site ID': s_data.get('Site ID', s_data.get('Indus ID', s_data.get('indus_id', '-'))),
                        'Site Name': s_data.get('Site Name', s_data.get('site_name', '-')),
                        'Lat': s_data.get('Lat', s_data.get('Latitude', s_data.get('latitude', ''))),
                        'Long': s_data.get('Long', s_data.get('longitude', s_data.get('Longitude', '')))
                    }
                    st.session_state.route_list.append(norm_data)
                    st.success(f"Site {add_sid} added!")
                    st.rerun()
                else: st.error("Site ID not found or Database Error!")

    # --- Current Added Sites List ---
    if st.session_state.route_list:
        st.write("### 📋 Added Sites:")
        temp_df = pd.DataFrame(st.session_state.route_list)[['Site ID', 'Site Name', 'Lat', 'Long']]
        st.dataframe(temp_df, use_container_width=True, hide_index=True)
        if st.button("🗑️ Clear All Sites", use_container_width=True):
            st.session_state.route_list = []
            st.rerun()

if st.button("🚀 Calculate Best Route (Point-wise)", use_container_width=True, type="primary"):
    if not start_coords or not end_coords or not st.session_state.route_list: 
        st.warning("Please add Start, End and at least one Site!")
    else:
        try:
            # Importing locally to prevent crash if not in requirements.txt
            from geopy.geocoders import Nominatim
            from geopy.distance import geodesic
            
            geolocator = Nominatim(user_agent="vis_route_planner")
            def get_lat_lon(loc):
                if ',' in loc and any(c.isdigit() for c in loc): return [float(x.strip()) for x in loc.split(',')]
                l = geolocator.geocode(loc); return [l.latitude, l.longitude] if l else None
            
            curr_p, end_p = get_lat_lon(start_coords), get_lat_lon(end_coords)
            if not curr_p or not end_p: st.error("Invalid Start or End Location.")
            else:
                unvisited = [s for s in st.session_state.route_list if s.get('Lat') and s.get('Long')]
                final_path = []
                while unvisited:
                    next_s = min(unvisited, key=lambda x: geodesic(curr_p, (float(x['Lat']), float(x['Long']))).km)
                    final_path.append(next_s)
                    curr_p = (float(next_s['Lat']), float(next_s['Long']))
                    unvisited.remove(next_s)
                
                # Showing Sequential Table
                route_results = []
                for i, s in enumerate(final_path, 1):
                    route_results.append({"Stop No": i, "Site ID": s.get('Site ID', '-'), "Name": s.get('Site Name','-')})
                st.table(pd.DataFrame(route_results))
                
                # Point-wise Google Maps Link
                stops = "/".join([f"{s['Lat']},{s['Long']}" for s in final_path])
                gmaps_route = f"https://www.google.com/maps/dir/{start_coords}/{stops}/{end_coords}"
                st.markdown(f'<a href="{gmaps_route}" target="_blank"><button style="width:100%; background-color:#10b981; color:white; border:none; padding:12px; border-radius:8px; font-weight:800; font-size:16px; cursor:pointer; box-shadow: 0 4px 6px -1px rgba(16, 185, 129, 0.4);">🗺️ Open Sequential Route (1-2-3-4)</button></a>', unsafe_allow_html=True)
        except Exception as e: st.error(f"Error: {e} | Ensure 'geopy' is added to requirements.txt file on GitHub.")
