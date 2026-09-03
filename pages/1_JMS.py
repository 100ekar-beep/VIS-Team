import sys
from pathlib import Path

import pandas as pd
import streamlit as st

sys.path.append(str(Path(__file__).resolve().parent.parent))
from utils.guard import require_login
from utils.data import get_items, get_sites_for_user, get_templates, get_template_items
from utils.pdf_generator import generate_jms_pdf

st.set_page_config(page_title="JMS", page_icon="📋", layout="wide")

user = require_login()

# --- LAVISH TABLE CSS (matches the Team & Vendor Billing look) -------------
st.markdown(
    """
    <style>
    .stApp { background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%); }

    .st-key-jms_table_header {
        background: linear-gradient(90deg, #4f46e5 0%, #6366f1 45%, #8b5cf6 100%) !important;
        border-radius: 14px 14px 0 0 !important;
        overflow: hidden !important;
        box-shadow: 0 10px 25px -5px rgba(15, 23, 42, 0.10) !important;
    }
    .st-key-jms_table_header div[data-testid="stHorizontalBlock"] {
        align-items: center !important;
        flex-wrap: nowrap !important;
        padding: 10px 0 !important;
    }
    .st-key-jms_table_wrap {
        background: #ffffff !important;
        border: 1px solid #e2e8f0 !important;
        border-top: none !important;
        border-radius: 0 0 14px 14px !important;
        box-shadow: 0 10px 25px -5px rgba(15, 23, 42, 0.10), 0 4px 6px -2px rgba(15, 23, 42, 0.04) !important;
        padding: 4px 0 !important;
        margin-bottom: 20px !important;
    }
    .st-key-jms_table_wrap div[data-testid="stHorizontalBlock"] {
        align-items: center !important;
        border-bottom: 1px solid #f1f5f9 !important;
        padding: 8px 0 !important;
        flex-wrap: nowrap !important;
    }
    .st-key-jms_table_wrap div[data-testid="stHorizontalBlock"]:hover {
        background: #eef2ff !important;
    }
    .st-key-jms_table_header div[data-testid="column"] {
        padding: 0 12px !important;
        border-right: 1px solid rgba(255, 255, 255, 0.15);
    }
    .st-key-jms_table_wrap div[data-testid="column"] {
        padding: 0 12px !important;
        border-right: 1px solid #f8fafc;
    }
    .tbl-head { color: #ffffff !important; font-size: 0.78rem !important; font-weight: 800 !important;
        letter-spacing: 0.5px !important; text-transform: uppercase !important; }
    .tbl-cell { color: #1e293b !important; font-size: 0.9rem !important; }
    .tbl-serial { color: #94a3b8 !important; font-weight: 800 !important; }

    button[data-testid="baseButton-primary"], button[data-testid="stBaseButton-primary"] {
        background: linear-gradient(90deg, #6366f1 0%, #4f46e5 100%) !important;
        color: white !important; border: none !important; border-radius: 8px !important;
        font-weight: 800 !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    f"<h1 style='color:#0f172a;'>📋 JMS — {user['team_name']}</h1>",
    unsafe_allow_html=True,
)

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

search = st.text_input("🔍 Search sites", placeholder="Site ID, Site Name, ya Project ID se search karo...")
filtered_df = sites_df
if search:
    mask = sites_df.astype(str).apply(lambda col: col.str.contains(search, case=False, na=False)).any(axis=1)
    filtered_df = sites_df[mask]

if "jms_line_items" not in st.session_state:
    st.session_state.jms_line_items = []
if "jms_active_site_id" not in st.session_state:
    st.session_state.jms_active_site_id = None
if "last_jms_pdf" not in st.session_state:
    st.session_state.last_jms_pdf = None


@st.dialog("Create JMS", width="large")
def create_jms_dialog(site: dict):
    # Reset the line-item list whenever a different site's dialog is opened
    if st.session_state.jms_active_site_id != site.get("id"):
        st.session_state.jms_active_site_id = site.get("id")
        st.session_state.jms_line_items = []
        st.session_state.last_jms_pdf = None

    c1, c2, c3 = st.columns(3)
    c1.markdown(f"**Project ID**  \n{site.get('Project ID', '')}")
    c2.markdown(f"**Site ID**  \n{site.get('Site ID', '')}")
    c3.markdown(f"**Site Name**  \n{site.get('Site Name', '')}")
    st.divider()

    hc1, hc2 = st.columns(2)
    with hc1:
        circle = st.text_input("Circle", value="Maharashtra", key="jms_circle")
        supervisor = st.text_input("Partner Supervisor Name", value=user["team_name"], key="jms_supervisor")
    with hc2:
        engineer = st.text_input("Audit Engineer Name", value="", key="jms_engineer")
        agency = st.text_input("Agency Name", value=site.get("Team Name", ""), key="jms_agency")

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
                        "item_description": r["item_description"],
                        "unit": r["unit"],
                        "qty": float(r["default_qty"]) if pd.notna(r["default_qty"]) else 0.0,
                        "remarks": "",
                    }
                )
            st.rerun()

    st.markdown("**+ Add a single item**")
    ac1, ac2, ac3 = st.columns([3, 1, 1])
    with ac1:
        item_choice = st.selectbox(
            "Item",
            options=items_master["item_code"],
            format_func=lambda code: f"{code} — {items_master.set_index('item_code').loc[code, 'item_description']}",
        )
    with ac2:
        qty_input = st.number_input("Qty", min_value=0.0, step=1.0, value=1.0, key="add_qty")
    with ac3:
        st.write("")
        st.write("")
        if st.button("+ Item", use_container_width=True):
            row = items_master.set_index("item_code").loc[item_choice]
            st.session_state.jms_line_items.append(
                {
                    "item_code": item_choice,
                    "item_description": row["item_description"],
                    "unit": row["unit"],
                    "qty": qty_input,
                    "remarks": "",
                }
            )
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
                "unit": st.column_config.TextColumn("Unit", disabled=True),
                "qty": st.column_config.NumberColumn("Qty", min_value=0.0, step=1.0),
                "remarks": st.column_config.TextColumn("Remarks"),
            },
            key="line_items_editor",
        )
        st.session_state.jms_line_items = edited_df.to_dict("records")
    else:
        st.info("Abhi koi item add nahi hua. Template load karo ya manually item add karo.")
        edited_df = pd.DataFrame(columns=["item_code", "item_description", "unit", "qty", "remarks"])

    st.divider()

    if st.button("✅ Submit & Generate PDF", type="primary", use_container_width=True, disabled=edited_df.empty):
        header = {
            "circle": circle,
            "tsp_partner": "VISIONTECH INFRA SOLUTIONS",
            "site_id": site.get("Site ID", ""),
            "site_name": site.get("Site Name", ""),
            "project_id": site.get("Project ID", ""),
            "partner_supervisor_name": supervisor,
            "audit_engineer_name": engineer,
            "agency_name": agency,
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


# --- Sites table with a "Create JMS" action per row -------------------------
COL_RATIOS = [0.5, 2, 1.5, 2, 1.3]
COL_LABELS = ["#", "PROJECT ID", "SITE ID", "SITE NAME", "ACTION"]

with st.container(key="jms_table_header"):
    h_cols = st.columns(COL_RATIOS)
    for h_col, label in zip(h_cols, COL_LABELS):
        h_col.markdown(f"<div class='tbl-cell tbl-head'>{label}</div>", unsafe_allow_html=True)

with st.container(key="jms_table_wrap"):
    for pos, (_, row) in enumerate(filtered_df.reset_index(drop=True).iterrows()):
        rcols = st.columns(COL_RATIOS)
        rcols[0].markdown(f"<div class='tbl-cell tbl-serial'>{pos + 1}</div>", unsafe_allow_html=True)
        rcols[1].markdown(f"<div class='tbl-cell'>{row.get('Project ID', '')}</div>", unsafe_allow_html=True)
        rcols[2].markdown(f"<div class='tbl-cell'>{row.get('Site ID', '')}</div>", unsafe_allow_html=True)
        rcols[3].markdown(f"<div class='tbl-cell'>{row.get('Site Name', '')}</div>", unsafe_allow_html=True)
        with rcols[4]:
            if st.button("🧾 Create JMS", key=f"create_jms_{row.get('id')}", use_container_width=True, type="primary"):
                create_jms_dialog(row.to_dict())
