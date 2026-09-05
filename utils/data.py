"""
Data layer: talks to Supabase (app_users, site_data, item_master,
ground_template, ground_template_items, user_site_allocation).

If Supabase isn't configured yet (see utils/supabase_client.py), every
function below falls back to DEMO DATA so the app is fully click-through
testable without a live database.
"""

import pandas as pd
import streamlit as st

from utils.supabase_client import get_supabase_client, is_demo_mode

# ---------------------------------------------------------------------------
# DEMO DATA (used only when Supabase isn't connected)
# ---------------------------------------------------------------------------
DEMO_USERS = [
    {
        "id": "demo-user-1",
        "team_name": "Pramodkumar Jaju",  # must match Team Name in DEMO_SITES below
        "mobile_number": "9999999999",
        "user_id": "EMP-DEMO",
        "is_admin": True,  # so the Team Request admin page is also testable in demo mode
    }
]
DEMO_PASSWORD = "demo123"  # only used in demo mode

DEMO_SITES = [
    {"id": "site-1", "Project ID": "OM-RELIBB-3208576", "Site ID": "IN-1330136", "Site Name": "Wadwani2", "Team Name": "Pramodkumar Jaju", "Cluster": "Beed", "Work Description": "Battery Bank SRN", "Site Status": "Open"},
    {"id": "site-2", "Project ID": "OM-RELIBB-3618036", "Site ID": "IN-3202039", "Site Name": "Kaudgaon Ghoda", "Team Name": "Pramodkumar Jaju", "Cluster": "Beed", "Work Description": "Battery Bank SRN", "Site Status": "Open"},
    {"id": "site-3", "Project ID": "OM-RELIBB-3127313", "Site ID": "IN-1106033", "Site Name": "Jategaon_Bed", "Team Name": "Pramodkumar Jaju", "Cluster": "Beed", "Work Description": "Battery Bank SRN", "Site Status": "Open"},
]

DEMO_ITEMS = [
    {"item_code": "11-312D28-0-00-09-ZZ-000", "item_description": "ACDB, Outdoor IP54, 40 KVA, 3 Phase, without SPD, Make - Sanhit"},
    {"item_code": "11-326400-0-01-ZZ-ZZ-000", "item_description": "DCDB Kit (Outdoor) including MCBs and cables"},
    {"item_code": "ITM-001", "item_description": "Supply & Laying of Cable,16 Sq MM,1 Core Green,Copper Unarmoured"},
    {"item_code": "ITM-008", "item_description": "Battery Bank, Installation Charges for Battery Bank"},
    {"item_code": "ITM-009", "item_description": "Civil work for Battery Bank Foundation, Size of 1.5M x 1.5M"},
    {"item_code": "ITM-010", "item_description": "Installation Charges for Mount"},
]

DEMO_TEMPLATES = [
    {"id": "tpl-1", "template_name": "Battery Bank"},
    {"id": "tpl-2", "template_name": "LA"},
    {"id": "tpl-3", "template_name": "Optional"},
    {"id": "tpl-4", "template_name": "Sharing"},
]

DEMO_TEMPLATE_ITEMS = {
    "tpl-1": [
        {"item_code": "ITM-008", "default_qty": 1},
        {"item_code": "ITM-009", "default_qty": 1},
        {"item_code": "ITM-010", "default_qty": 1},
    ],
    "tpl-2": [
        {"item_code": "11-326400-0-01-ZZ-ZZ-000", "default_qty": 1},
    ],
    "tpl-3": [],
    "tpl-4": [],
}


def truncate_words(text, max_words: int = 60) -> str:
    """Keep only the first `max_words` words of a description, to keep the PDF small."""
    if not text:
        return ""
    words = str(text).split()
    if len(words) <= max_words:
        return str(text)
    return " ".join(words[:max_words]) + "..."


def _demo_items_lookup():
    return {i["item_code"]: i for i in DEMO_ITEMS}


# ---------------------------------------------------------------------------
# USERS / AUTH DATA
# ---------------------------------------------------------------------------
def get_user_by_mobile(mobile_number: str):
    """Returns the raw app_users row (incl. password hash) or None."""
    if is_demo_mode():
        for u in DEMO_USERS:
            if u["mobile_number"] == mobile_number:
                return {**u, "password": None, "is_admin": u.get("is_admin", False)}
        return None

    client = get_supabase_client()
    resp = (
        client.table("app_users")
        .select("id, team_name, mobile_number, user_id, password, is_admin")
        .eq("mobile_number", mobile_number)
        .limit(1)
        .execute()
    )
    return resp.data[0] if resp.data else None


# ---------------------------------------------------------------------------
# SITES
# ---------------------------------------------------------------------------
SITE_LIST_COLUMNS = ["id", "Project ID", "Site ID", "Site Name", "Team Name", "Cluster", "Work Description", "Site Status"]


def get_sites_for_user(team_name: str) -> pd.DataFrame:
    """
    Returns sites where site_data."Team Name" matches this user's team_name.
    (No separate allocation table needed — Team Name in site_data IS the
    allocation, since that's how sites already get assigned to a team member.)
    """
    if is_demo_mode():
        df = pd.DataFrame(DEMO_SITES)
        return df[df["Team Name"] == team_name].reset_index(drop=True)

    client = get_supabase_client()
    resp = (
        client.table("site_data")
        .select('id,"Project ID","Site ID","Site Name","Team Name","Cluster","Work Description","Site Status"')
        .eq("Team Name", team_name)
        .execute()
    )
    return pd.DataFrame(resp.data, columns=SITE_LIST_COLUMNS)


def get_full_site_detail(site_row_id: str) -> dict:
    """Returns the FULL site_data row (every column) for the detail view."""
    if is_demo_mode():
        for s in DEMO_SITES:
            if s["id"] == site_row_id:
                return s
        return {}

    client = get_supabase_client()
    resp = client.table("site_data").select("*").eq("id", site_row_id).limit(1).execute()
    return resp.data[0] if resp.data else {}


# ---------------------------------------------------------------------------
# TECHNICIAN / FSE (from the "Excalation Matrix" table, matched by Site ID —
# same variant-column matching approach as the Indus Site Data page)
# ---------------------------------------------------------------------------
@st.cache_data(ttl=60, show_spinner=False)
def get_technician_fse_for_site(site_id: str) -> dict:
    empty = {"tech_name": "-", "tech_num": "-", "fse_name": "-", "fse_num": "-"}
    if not site_id:
        return empty
    if is_demo_mode():
        return {"tech_name": "Demo Technician", "tech_num": "9999999999", "fse_name": "Demo FSE", "fse_num": "8888888888"}

    client = get_supabase_client()
    tables_to_try = ["Excalation Matrix", "Escalation Matrix", "Indus Data"]
    id_cols_to_try = ["Indus ID", "Site ID", "indus_id", "site_id"]

    for t in tables_to_try:
        for id_col in id_cols_to_try:
            try:
                res = client.table(t).select("*").ilike(id_col, f"%{site_id}%").execute()
                if res.data:
                    row = res.data[0]
                    return {
                        "tech_name": row.get("Technician Detail", row.get("Tech Name", "-")),
                        "tech_num": row.get("Technician Number", row.get("Tech Number", "-")),
                        "fse_name": row.get("FSE Detail", row.get("FSE Name", row.get("FSE", "-"))),
                        "fse_num": row.get("FSE Number", "-"),
                    }
            except Exception:
                continue
    return empty


# ---------------------------------------------------------------------------
# SITE STATUS REQUESTS (team submits -> pending -> admin approves/rejects)
# ---------------------------------------------------------------------------
DEMO_REQUESTS = []  # in-memory, demo mode only


def submit_status_request(site: dict, requested_status: str, remark: str, requested_by: str):
    payload = {
        "site_row_id": site.get("id"),
        "site_id": site.get("Site ID", ""),
        "site_name": site.get("Site Name", ""),
        "project_id": site.get("Project ID", ""),
        "requested_status": requested_status,
        "remark": remark,
        "requested_by": requested_by,
        "status": "pending",
    }
    if is_demo_mode():
        payload["id"] = len(DEMO_REQUESTS) + 1
        DEMO_REQUESTS.append(payload)
        return True

    client = get_supabase_client()
    client.table("site_status_requests").insert(payload).execute()
    return True


def get_pending_requests() -> pd.DataFrame:
    cols = ["id", "site_row_id", "site_id", "site_name", "project_id", "requested_status", "remark", "requested_by", "status", "created_at"]
    if is_demo_mode():
        pending = [r for r in DEMO_REQUESTS if r["status"] == "pending"]
        return pd.DataFrame(pending, columns=cols)

    client = get_supabase_client()
    resp = (
        client.table("site_status_requests")
        .select("*")
        .eq("status", "pending")
        .order("created_at", desc=False)
        .execute()
    )
    return pd.DataFrame(resp.data, columns=cols)


def approve_request(request_id, site_row_id, new_status: str):
    if is_demo_mode():
        for r in DEMO_REQUESTS:
            if r["id"] == request_id:
                r["status"] = "approved"
        for s in DEMO_SITES:
            if s["id"] == site_row_id:
                s["Site Status"] = new_status
        return True

    client = get_supabase_client()
    if site_row_id:
        client.table("site_data").update({"Site Status": new_status}).eq("id", site_row_id).execute()
    client.table("site_status_requests").update({"status": "approved"}).eq("id", request_id).execute()
    return True


def reject_request(request_id):
    if is_demo_mode():
        for r in DEMO_REQUESTS:
            if r["id"] == request_id:
                r["status"] = "rejected"
        return True

    client = get_supabase_client()
    client.table("site_status_requests").update({"status": "rejected"}).eq("id", request_id).execute()
    return True


# ---------------------------------------------------------------------------
# ITEM MASTER (reads from your existing "Item Code" table)
# ---------------------------------------------------------------------------
def get_items() -> pd.DataFrame:
    if is_demo_mode():
        return pd.DataFrame(DEMO_ITEMS)

    client = get_supabase_client()
    resp = (
        client.table("Item Code")
        .select("item_code, item_description")
        .execute()
    )
    df = pd.DataFrame(resp.data, columns=["item_code", "item_description"])
    # Drop rows with a blank item_code (the sample data had one empty row)
    df = df[df["item_code"].astype(str).str.strip() != ""].reset_index(drop=True)
    df["item_description"] = df["item_description"].apply(truncate_words)
    return df


# ---------------------------------------------------------------------------
# TEMPLATES
# ---------------------------------------------------------------------------
def get_templates() -> pd.DataFrame:
    if is_demo_mode():
        return pd.DataFrame(DEMO_TEMPLATES)

    client = get_supabase_client()
    resp = client.table("ground_template").select("id, template_name").order("template_name").execute()
    return pd.DataFrame(resp.data)


def get_template_items(template_id: str) -> pd.DataFrame:
    """Returns item_code, item_description, default_qty for a template."""
    if is_demo_mode():
        rows = DEMO_TEMPLATE_ITEMS.get(template_id, [])
        lookup = _demo_items_lookup()
        merged = []
        for r in rows:
            item = lookup.get(r["item_code"], {})
            merged.append(
                {
                    "item_code": r["item_code"],
                    "item_description": item.get("item_description", ""),
                    "default_qty": r["default_qty"],
                }
            )
        return pd.DataFrame(merged, columns=["item_code", "item_description", "default_qty"])

    client = get_supabase_client()
    resp = (
        client.table("ground_template_items")
        .select("item_code, default_qty, sort_order")
        .eq("template_id", template_id)
        .order("sort_order")
        .execute()
    )
    template_rows = pd.DataFrame(resp.data, columns=["item_code", "default_qty", "sort_order"])
    if template_rows.empty:
        return pd.DataFrame(columns=["item_code", "item_description", "default_qty"])

    # Join against the item master in Python (avoids relying on a DB foreign key)
    items = get_items()
    merged = template_rows.merge(items, on="item_code", how="left")
    merged["item_description"] = merged["item_description"].fillna("")
    return merged[["item_code", "item_description", "default_qty"]]
