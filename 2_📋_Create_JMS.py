import datetime
import sys
from pathlib import Path

import pandas as pd
import streamlit as st

sys.path.append(str(Path(__file__).resolve().parent.parent))
from utils.guard import require_login
from utils.data import get_items, get_templates, get_template_items
from utils.pdf_generator import generate_jms_pdf

st.set_page_config(page_title="Create JMS", page_icon="📋", layout="wide")

user = require_login()

st.title("📋 Create JMS")

if not st.session_state.get("selected_site"):
    st.warning("Pehle **My Sites** page se ek site select karo.")
    st.stop()

site = st.session_state.selected_site

if st.session_state.get("jms_line_items") is None:
    st.session_state.jms_line_items = []  # list of dicts

items_master = get_items()
templates_df = get_templates()


@st.dialog("Create JMS", width="large")
def create_jms_dialog():
    # ---- Site header (read-only) -------------------------------------------
    c1, c2, c3 = st.columns(3)
    c1.markdown(f"**Project ID**  \n{site.get('Project ID', '')}")
    c2.markdown(f"**Site ID**  \n{site.get('Site ID', '')}")
    c3.markdown(f"**Site Name**  \n{site.get('Site Name', '')}")
    st.divider()

    # ---- Extra header fields ------------------------------------------------
    hc1, hc2 = st.columns(2)
    with hc1:
        circle = st.text_input("Circle", value=st.session_state.get("jms_circle", "Maharashtra"), key="jms_circle")
        rl_id = st.text_input("RL ID", value=st.session_state.get("jms_rl_id", ""), key="jms_rl_id")
        supervisor = st.text_input(
            "Partner Supervisor Name",
            value=st.session_state.get("jms_supervisor", user["full_name"]),
            key="jms_supervisor",
        )
    with hc2:
        jms_date = st.date_input("Date", value=datetime.date.today(), key="jms_date")
        engineer = st.text_input("Audit Engineer Name", value=st.session_state.get("jms_engineer", ""), key="jms_engineer")
        agency = st.text_input(
            "Agency Name",
            value=st.session_state.get("jms_agency", site.get("Team Name", "")),
            key="jms_agency",
        )

    st.divider()

    # ---- Load from template --------------------------------------------------
    st.markdown("**Load a template**")
    tc1, tc2 = st.columns([3, 1])
    with tc1:
        if not templates_df.empty:
            tpl_choice = st.selectbox(
                "Template", options=templates_df["id"], format_func=lambda tid: templates_df.set_index("id").loc[tid, "template_name"]
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
        # Keep session_state in sync with edits/deletes
        st.session_state.jms_line_items = edited_df.to_dict("records")
    else:
        st.info("Abhi koi item add nahi hua. Template load karo ya manually item add karo.")
        edited_df = pd.DataFrame(columns=["item_code", "item_description", "unit", "qty", "remarks"])

    st.divider()

    if st.button("✅ Submit & Generate PDF", type="primary", use_container_width=True, disabled=edited_df.empty):
        header = {
            "circle": circle,
            "date": jms_date.strftime("%d/%m/%Y"),
            "tsp_partner": "VISIONTECH INFRA SOLUTIONS",
            "site_id": site.get("Site ID", ""),
            "site_name": site.get("Site Name", ""),
            "rl_id": rl_id,
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


st.info(f"Selected site: **{site.get('Site ID')} — {site.get('Site Name')}**")
if st.button("+ Create JMS", type="primary"):
    create_jms_dialog()
