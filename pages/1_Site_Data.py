import sys
from pathlib import Path

import pandas as pd
import streamlit as st

sys.path.append(str(Path(__file__).resolve().parent.parent))
from utils.guard import require_login
from utils.data import (
    get_items, get_sites_for_user, get_templates, get_template_items, truncate_words,
    get_full_site_detail, get_technician_fse_for_site, submit_status_request,
)
from utils.pdf_generator import generate_jms_pdf
from utils.email_sender import send_site_photos_email, is_email_configured

st.set_page_config(page_title="Site Data", page_icon="📍", layout="wide")

user = require_login()

# --- LAVISH TABLE CSS (matches the Team & Vendor Billing look) -------------
st.markdown(
    """
    <style>
    .stApp { background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%); }

    .st-key-site_table_header {
        background: linear-gradient(90deg, #4f46e5 0%, #6366f1 45%, #8b5cf6 100%) !important;
        border-radius: 14px 14px 0 0 !important;
        overflow: hidden !important;
        box-shadow: 0 10px 25px -5px rgba(15, 23, 42, 0.10) !important;
    }
    .st-key-site_table_header div[data-testid="stHorizontalBlock"] {
        align-items: center !important;
        flex-wrap: nowrap !important;
        padding: 10px 0 !important;
    }
    .st-key-site_table_wrap {
        background: #ffffff !important;
        border: 1px solid #e2e8f0 !important;
        border-top: none !important;
        border-radius: 0 0 14px 14px !important;
        box-shadow: 0 10px 25px -5px rgba(15, 23, 42, 0.10), 0 4px 6px -2px rgba(15, 23, 42, 0.04) !important;
        padding: 4px 0 !important;
        margin-bottom: 20px !important;
    }
    .st-key-site_table_wrap div[data-testid="stHorizontalBlock"] {
        align-items: center !important;
        border-bottom: 1px solid #f1f5f9 !important;
        padding: 8px 0 !important;
        flex-wrap: nowrap !important;
    }
    .st-key-site_table_wrap div[data-testid="stHorizontalBlock"]:hover {
        background: #eef2ff !important;
    }
    .st-key-site_table_header div[data-testid="column"] {
        padding: 0 12px !important;
        border-right: 1px solid rgba(255, 255, 255, 0.15);
    }
    .st-key-site_table_wrap div[data-testid="column"] {
        padding: 0 12px !important;
        border-right: 1px solid #f8fafc;
    }
    .tbl-head { color: #ffffff !important; font-size: 0.75rem !important; font-weight: 800 !important;
        letter-spacing: 0.5px !important; text-transform: uppercase !important; }
    .tbl-cell { color: #1e293b !important; font-size: 0.85rem !important; }
    .tbl-serial { color: #94a3b8 !important; font-weight: 800 !important; }

    button[data-testid="baseButton-primary"], button[data-testid="stBaseButton-primary"] {
        background: linear-gradient(90deg, #6366f1 0%, #4f46e5 100%) !important;
        color: white !important; border: none !important; border-radius: 8px !important;
        font-weight: 800 !important;
    }

    /* Mobile card view */
    .site-card-title { font-size: 1.02rem; font-weight: 800; color: #0f172a; margin-bottom: 6px; }
    .site-card-row { display: flex; justify-content: space-between; padding: 4px 0; border-bottom: 1px dashed #e2e8f0; font-size: 0.85rem; }
    .site-card-row:last-child { border-bottom: none; }
    .site-card-label { color: #64748b; font-weight: 600; }
    .site-card-value { color: #1e293b; font-weight: 600; text-align: right; }

    [data-testid="stSelectboxVirtualDropdown"] li,
    [data-testid="stSelectboxVirtualDropdown"] li > div,
    [data-testid="stSelectboxVirtualDropdown"] li div,
    div[data-baseweb="popover"] li,
    div[data-baseweb="popover"] li > div,
    div[data-baseweb="menu"] li,
    div[data-baseweb="menu"] li > div,
    ul[role="listbox"] li,
    ul[role="listbox"] li > div,
    li[role="option"],
    li[role="option"] > div,
    li[role="option"] div {
        white-space: normal !important;
        word-break: break-word !important;
        overflow: visible !important;
        text-overflow: unset !important;
        height: auto !important;
        min-height: auto !important;
        line-height: 1.35 !important;
        padding-top: 8px !important;
        padding-bottom: 8px !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    f"<h1 style='color:#0f172a;'>📍 Site Data — {user['team_name']}</h1>",
    unsafe_allow_html=True,
)

if "jms_view_mode" not in st.session_state:
    st.session_state.jms_view_mode = "cards"

# --- Load sites for this user (Team Name match) -----------------------------
sites_df = get_sites_for_user(user["team_name"])
items_master = get_items()
templates_df = get_templates()

if sites_df.empty:
    st.warning(
        f"'{user['team_name']}' naam se site_data mein koi site nahi mili. "
        "Check karo ki site_data ke 'Team Name' column mein aapka naam exactly "
        "isi spelling mein hai."
    )
    st.stop()

col_search, col_toggle = st.columns([4, 1.3])
with col_search:
    search = st.text_input("🔍 Search sites", placeholder="Site ID, Site Name, ya Project ID se search karo...", label_visibility="collapsed")
with col_toggle:
    toggle_label = "📱 Mobile View" if st.session_state.jms_view_mode == "table" else "🖥️ Table View"
    if st.button(toggle_label, use_container_width=True):
        st.session_state.jms_view_mode = "cards" if st.session_state.jms_view_mode == "table" else "table"
        st.rerun()

filtered_df = sites_df
if search:
    mask = sites_df.astype(str).apply(lambda col: col.str.contains(search, case=False, na=False)).any(axis=1)
    filtered_df = sites_df[mask]

# --- Session state defaults --------------------------------------------------
if "jms_line_items" not in st.session_state:
    st.session_state.jms_line_items = []
if "jms_active_site_id" not in st.session_state:
    st.session_state.jms_active_site_id = None
if "last_jms_pdf" not in st.session_state:
    st.session_state.last_jms_pdf = None
if "jms_open_site" not in st.session_state:
    st.session_state.jms_open_site = None
if "jms_item_widget_gen" not in st.session_state:
    st.session_state.jms_item_widget_gen = 0


def render_create_jms_tab(site: dict):
    circle = st.text_input("Circle", value="Maharashtra", key="jms_circle")
    st.divider()

    st.markdown("**Load a template**")
    tc1, tc2 = st.columns([3, 1])
    with tc1:
        if not templates_df.empty:
            tpl_choice = st.selectbox(
                "Template",
                options=templates_df["id"],
                format_func=lambda tid: templates_df.set_index("id").loc[tid, "template_name"],
            )
        else:
            tpl_choice = None
            st.caption("Koi template configure nahi hai abhi.")
    with tc2:
        st.write("")
        st.write("")
        if st.button("Load Template", use_container_width=True, disabled=tpl_choice is None):
            tpl_items = get_template_items(tpl_choice)
            for _, r in tpl_items.iterrows():
                st.session_state.jms_line_items.append(
                    {
                        "item_code": r["item_code"],
                        "item_description": truncate_words(r["item_description"]),
                        "qty": float(r["default_qty"]) if pd.notna(r["default_qty"]) else 0.0,
                        "remarks": "",
                    }
                )
            st.rerun()

    st.markdown("**Add item in JMS**")
    if items_master.empty:
        st.warning("Item Code table mein abhi koi items nahi hai. Pehle wahan items add karo.")
    else:
        item_options = ["-- Search & select an item --"] + list(items_master["item_code"])
        widget_gen = st.session_state.jms_item_widget_gen

        item_choice = st.selectbox(
            "Item",
            options=item_options,
            index=0,
            format_func=lambda code: code if code == "-- Search & select an item --"
            else f"{code} — {items_master.set_index('item_code').loc[code, 'item_description']}",
            key=f"item_select_{widget_gen}",
        )

        if item_choice != "-- Search & select an item --":
            full_desc = items_master.set_index("item_code").loc[item_choice, "item_description"]
            st.info(f"📄 **{item_choice}**\n\n{full_desc}")

        ac2, ac3 = st.columns([1, 1])
        with ac2:
            qty_input = st.number_input(
                "Qty", min_value=0.0, step=1.0, value=None, placeholder="0",
                key=f"add_qty_{widget_gen}",
            )
        with ac3:
            st.write("")
            st.write("")
            add_disabled = item_choice == "-- Search & select an item --"
            if st.button("Add in JMS", use_container_width=True, disabled=add_disabled):
                row = items_master.set_index("item_code").loc[item_choice]
                st.session_state.jms_line_items.append(
                    {
                        "item_code": item_choice,
                        "item_description": truncate_words(row["item_description"]),
                        "qty": qty_input if qty_input is not None else 0.0,
                        "remarks": "",
                    }
                )
                st.session_state.jms_item_widget_gen += 1
                st.rerun()

    st.divider()
    st.markdown("**Line items** (edit qty/remarks, or delete a row with the ⓧ)")

    if st.session_state.jms_line_items:
        edited_df = st.data_editor(
            pd.DataFrame(st.session_state.jms_line_items),
            use_container_width=True,
            hide_index=True,
            num_rows="dynamic",
            column_config={
                "item_code": st.column_config.TextColumn("Item Code", disabled=True),
                "item_description": st.column_config.TextColumn("Description", disabled=True, width="large"),
                "qty": st.column_config.NumberColumn("Qty", min_value=0.0, step=1.0),
                "remarks": st.column_config.TextColumn("Remarks"),
            },
            key="line_items_editor",
        )
        st.session_state.jms_line_items = edited_df.to_dict("records")
    else:
        st.info("Abhi koi item add nahi hua. Template load karo ya manually item add karo.")
        edited_df = pd.DataFrame(columns=["item_code", "item_description", "qty", "remarks"])

    st.divider()

    if st.button("✅ Submit & Generate PDF", type="primary", use_container_width=True, disabled=edited_df.empty):
        header = {
            "circle": circle,
            "tsp_partner": "VISIONTECH INFRA SOLUTIONS",
            "site_id": site.get("Site ID", ""),
            "site_name": site.get("Site Name", ""),
            "project_id": site.get("Project ID", ""),
        }
        pdf_bytes = generate_jms_pdf(header, edited_df)
        st.session_state["last_jms_pdf"] = pdf_bytes
        st.session_state["last_jms_filename"] = f"JMS_{site.get('Site ID', 'site')}.pdf"
        st.success("PDF ban gayi! Neeche download karo.")

    if st.session_state.get("last_jms_pdf"):
        st.download_button(
            "⬇️ Download JMS PDF",
            data=st.session_state["last_jms_pdf"],
            file_name=st.session_state.get("last_jms_filename", "JMS.pdf"),
            mime="application/pdf",
            use_container_width=True,
        )
        st.caption("Note: Ye PDF sirf aapke mobile/device pe save hogi — Supabase mein kuch save nahi hota.")


def render_site_status_tab(site: dict):
    current_status = site.get("Site Status") or "-"
    st.markdown(f"**Current Status:** {current_status}")
    st.divider()

    status_choice = st.selectbox("New Status", options=["Completed", "HOLD"], key="status_choice")
    remark = st.text_area("Remark", placeholder="Site status ke baare mein kuch likho...", key="status_remark")

    st.caption("⚠️ Ye status seedha update nahi hoga — request admin ko jayegi approval ke liye.")

    if st.button("📨 Submit Request", type="primary", use_container_width=True):
        submit_status_request(site, status_choice, remark, user["team_name"])
        st.success("Request bhej di gayi! Admin approve karega to status update ho jayega.")


def render_site_photos_tab(site: dict):
    if not is_email_configured():
        st.warning(
            "Email abhi configure nahi hai. Streamlit Secrets mein EMAIL_SENDER, "
            "EMAIL_PASSWORD, EMAIL_RECEIVER daalo (README dekho)."
        )

    photos = st.file_uploader(
        "Site Photos", type=["jpg", "jpeg", "png"], accept_multiple_files=True,
        key=f"site_photos_{site.get('id')}",
    )
    note = st.text_input("Note (optional)", key=f"site_photo_note_{site.get('id')}")

    st.caption("Photos sirf email ke through bheji jaati hai — Supabase ya kahi bhi save nahi hoti.")

    if st.button("📧 Submit Photos", type="primary", use_container_width=True, disabled=not photos):
        with st.spinner("Email bheji jaa rahi hai..."):
            success, message = send_site_photos_email(site, photos, user["team_name"], note)
        if success:
            st.success(message)
        else:
            st.error(message)


@st.dialog("Site Detail", width="large")
def site_detail_dialog(site: dict):
    if st.session_state.jms_active_site_id != site.get("id"):
        st.session_state.jms_active_site_id = site.get("id")
        st.session_state.jms_line_items = []
        st.session_state.last_jms_pdf = None
        st.session_state.jms_item_widget_gen += 1

    full_detail = get_full_site_detail(site.get("id"))
    tech_fse = get_technician_fse_for_site(site.get("Site ID", ""))

    st.markdown(f"### {site.get('Site Name', '')}")
    c1, c2, c3 = st.columns(3)
    c1.markdown(f"**Project ID**  \n{full_detail.get('Project ID', '')}")
    c2.markdown(f"**Site ID**  \n{full_detail.get('Site ID', '')}")
    c3.markdown(f"**Cluster**  \n{full_detail.get('Cluster', '')}")

    d1, d2, d3 = st.columns(3)
    d1.markdown(f"**Work Description**  \n{full_detail.get('Work Description', '-')}")
    d2.markdown(f"**Technician**  \n{tech_fse.get('tech_name', '-')} ({tech_fse.get('tech_num', '-')})")
    d3.markdown(f"**FSE**  \n{tech_fse.get('fse_name', '-')} ({tech_fse.get('fse_num', '-')})")

    st.divider()

    tab1, tab2, tab3 = st.tabs(["📊 Site Status", "🧾 Create JMS", "📸 Site Photos"])
    with tab1:
        render_site_status_tab(site)
    with tab2:
        render_create_jms_tab(site)
    with tab3:
        render_site_photos_tab(site)

    st.divider()
    if st.button("✖ Close", use_container_width=True):
        st.session_state.jms_open_site = None
        st.rerun()


# --- Keep the dialog open across reruns (fixes it closing after any click) --
if st.session_state.jms_open_site is not None:
    site_detail_dialog(st.session_state.jms_open_site)


# --- Sites table / cards with an "Open Site" action per row -----------------
if st.session_state.jms_view_mode == "cards":
    # ---------------------------------------------------------------
    # MOBILE CARD VIEW
    # ---------------------------------------------------------------
    for pos, (_, row) in enumerate(filtered_df.reset_index(drop=True).iterrows()):
        with st.container(border=True):
            st.markdown(
                f"""
                <div class="site-card-title">#{pos + 1} — {row.get('Site Name', '')}</div>
                <div class="site-card-row"><span class="site-card-label">Site ID</span><span class="site-card-value">{row.get('Site ID', '')}</span></div>
                <div class="site-card-row"><span class="site-card-label">Project ID</span><span class="site-card-value">{row.get('Project ID', '')}</span></div>
                <div class="site-card-row"><span class="site-card-label">Cluster</span><span class="site-card-value">{row.get('Cluster', '')}</span></div>
                <div class="site-card-row"><span class="site-card-label">Work Description</span><span class="site-card-value">{row.get('Work Description', '')}</span></div>
                <div class="site-card-row"><span class="site-card-label">Site Status</span><span class="site-card-value">{row.get('Site Status', '')}</span></div>
                """,
                unsafe_allow_html=True,
            )
            if st.button("📂 Open Site", key=f"open_site_card_{row.get('id')}", use_container_width=True, type="primary"):
                st.session_state.jms_open_site = row.to_dict()
                st.rerun()
else:
    # ---------------------------------------------------------------
    # DESKTOP WIDE TABLE VIEW
    # ---------------------------------------------------------------
    COL_RATIOS = [0.4, 1.6, 1.2, 1.6, 1.1, 1.8, 1.1, 1.1]
    COL_LABELS = ["#", "PROJECT ID", "SITE ID", "SITE NAME", "CLUSTER", "WORK DESCRIPTION", "STATUS", "ACTION"]

    with st.container(key="site_table_header"):
        h_cols = st.columns(COL_RATIOS)
        for h_col, label in zip(h_cols, COL_LABELS):
            h_col.markdown(f"<div class='tbl-cell tbl-head'>{label}</div>", unsafe_allow_html=True)

    with st.container(key="site_table_wrap"):
        for pos, (_, row) in enumerate(filtered_df.reset_index(drop=True).iterrows()):
            rcols = st.columns(COL_RATIOS)
            rcols[0].markdown(f"<div class='tbl-cell tbl-serial'>{pos + 1}</div>", unsafe_allow_html=True)
            rcols[1].markdown(f"<div class='tbl-cell'>{row.get('Project ID', '')}</div>", unsafe_allow_html=True)
            rcols[2].markdown(f"<div class='tbl-cell'>{row.get('Site ID', '')}</div>", unsafe_allow_html=True)
            rcols[3].markdown(f"<div class='tbl-cell'>{row.get('Site Name', '')}</div>", unsafe_allow_html=True)
            rcols[4].markdown(f"<div class='tbl-cell'>{row.get('Cluster', '')}</div>", unsafe_allow_html=True)
            rcols[5].markdown(f"<div class='tbl-cell'>{row.get('Work Description', '')}</div>", unsafe_allow_html=True)
            rcols[6].markdown(f"<div class='tbl-cell'>{row.get('Site Status', '')}</div>", unsafe_allow_html=True)
            with rcols[7]:
                if st.button("📂 Open", key=f"open_site_{row.get('id')}", use_container_width=True, type="primary"):
                    st.session_state.jms_open_site = row.to_dict()
                    st.rerun()
