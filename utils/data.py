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
    }
]
DEMO_PASSWORD = "demo123"  # only used in demo mode

DEMO_SITES = [
    {"id": "site-1", "Project ID": "OM-RELIBB-3208576", "Site ID": "IN-1330136", "Site Name": "Wadwani2", "Team Name": "Pramodkumar Jaju"},
    {"id": "site-2", "Project ID": "OM-RELIBB-3618036", "Site ID": "IN-3202039", "Site Name": "Kaudgaon Ghoda", "Team Name": "Pramodkumar Jaju"},
    {"id": "site-3", "Project ID": "OM-RELIBB-3127313", "Site ID": "IN-1106033", "Site Name": "Jategaon_Bed", "Team Name": "Pramodkumar Jaju"},
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
                return {**u, "password": None}
        return None

    client = get_supabase_client()
    resp = (
        client.table("app_users")
        .select("id, team_name, mobile_number, user_id, password")
        .eq("mobile_number", mobile_number)
        .limit(1)
        .execute()
    )
    return resp.data[0] if resp.data else None


# ---------------------------------------------------------------------------
# SITES
# ---------------------------------------------------------------------------
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
        .select('id,"Project ID","Site ID","Site Name","Team Name"')
        .eq("Team Name", team_name)
        .execute()
    )
    return pd.DataFrame(resp.data, columns=["id", "Project ID", "Site ID", "Site Name", "Team Name"])


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
