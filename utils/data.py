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
        "full_name": "Demo Field Engineer",
        "mobile_number": "9999999999",
        "is_admin": False,
    }
]
DEMO_PASSWORD = "demo123"  # only used in demo mode

DEMO_SITES = [
    {"id": "site-1", "Project ID": "OM-RELIBB-3208576", "Site ID": "IN-1330136", "Site Name": "Wadwani2", "Team Name": "Pramodkumar Jaju"},
    {"id": "site-2", "Project ID": "OM-RELIBB-3618036", "Site ID": "IN-3202039", "Site Name": "Kaudgaon Ghoda", "Team Name": "Pramodkumar Jaju"},
    {"id": "site-3", "Project ID": "OM-RELIBB-3127313", "Site ID": "IN-1106033", "Site Name": "Jategaon_Bed", "Team Name": "Pramodkumar Jaju"},
]

DEMO_ITEMS = [
    {"item_code": "ITM-001", "item_description": "Supply & Laying of Cable,16 Sq MM,1 Core Green,Copper Unarmoured", "unit": "Meter"},
    {"item_code": "ITM-002", "item_description": "Supply & Laying of Cable,70 Sq MM,1 Core Black,Copper Unarmoured", "unit": "Meter"},
    {"item_code": "ITM-003", "item_description": "Supply & Laying of Cable,70 Sq MM,1 Core Red,Copper Unarmoured", "unit": "Meter"},
    {"item_code": "ITM-004", "item_description": "GI Wire Reinforced HDPE Conduit Pipe 25 mm, Version 1.0", "unit": "Meter"},
    {"item_code": "ITM-005", "item_description": "GI Wire Reinforced HDPE Conduit Pipe 38 mm, Version 1.0", "unit": "Meter"},
    {"item_code": "ITM-006", "item_description": "Installation, Commissioning & Testing of SMPS (As per Indus standard)", "unit": "Each"},
    {"item_code": "ITM-007", "item_description": "Earthing, GI strip (25x3) mm with all installation accessories", "unit": "Meter"},
    {"item_code": "ITM-008", "item_description": "Battery Bank, Installation Charges for Battery Bank", "unit": "Each"},
    {"item_code": "ITM-009", "item_description": "Civil work for Battery Bank Foundation, Size of 1.5M x 1.5M", "unit": "Each"},
    {"item_code": "ITM-010", "item_description": "Installation Charges for Mount", "unit": "Each"},
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
        {"item_code": "ITM-007", "default_qty": 20},
    ],
    "tpl-3": [],
    "tpl-4": [],
}


def _demo_items_lookup():
    return {i["item_code"]: i for i in DEMO_ITEMS}


# ---------------------------------------------------------------------------
# USERS / AUTH DATA
# ---------------------------------------------------------------------------
def get_user_by_mobile(mobile_number: str):
    """Returns the raw app_users row (incl. password_hash) or None."""
    if is_demo_mode():
        for u in DEMO_USERS:
            if u["mobile_number"] == mobile_number:
                return {**u, "password_hash": None}
        return None

    client = get_supabase_client()
    resp = (
        client.table("app_users")
        .select("id, full_name, mobile_number, password_hash, is_admin")
        .eq("mobile_number", mobile_number)
        .limit(1)
        .execute()
    )
    return resp.data[0] if resp.data else None


# ---------------------------------------------------------------------------
# SITES
# ---------------------------------------------------------------------------
def get_sites_for_user(user_id: str) -> pd.DataFrame:
    """Returns sites allocated to this user (from user_site_allocation + site_data)."""
    if is_demo_mode():
        return pd.DataFrame(DEMO_SITES)

    client = get_supabase_client()
    resp = (
        client.table("user_site_allocation")
        .select('site_id, site_data(id,"Project ID","Site ID","Site Name","Team Name")')
        .eq("user_id", user_id)
        .execute()
    )
    rows = [r["site_data"] for r in resp.data if r.get("site_data")]
    if not rows:
        return pd.DataFrame(columns=["id", "Project ID", "Site ID", "Site Name", "Team Name"])
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# ITEM MASTER
# ---------------------------------------------------------------------------
def get_items() -> pd.DataFrame:
    if is_demo_mode():
        return pd.DataFrame(DEMO_ITEMS)

    client = get_supabase_client()
    resp = (
        client.table("item_master")
        .select("item_code, item_description, unit")
        .order("item_code")
        .execute()
    )
    return pd.DataFrame(resp.data)


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
    """Returns item_code, item_description, unit, default_qty for a template."""
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
                    "unit": item.get("unit", ""),
                    "default_qty": r["default_qty"],
                }
            )
        return pd.DataFrame(merged, columns=["item_code", "item_description", "unit", "default_qty"])

    client = get_supabase_client()
    resp = (
        client.table("ground_template_items")
        .select("item_code, default_qty, sort_order, item_master(item_description, unit)")
        .eq("template_id", template_id)
        .order("sort_order")
        .execute()
    )
    rows = []
    for r in resp.data:
        item = r.get("item_master") or {}
        rows.append(
            {
                "item_code": r["item_code"],
                "item_description": item.get("item_description", ""),
                "unit": item.get("unit", ""),
                "default_qty": r.get("default_qty", 0),
            }
        )
    return pd.DataFrame(rows, columns=["item_code", "item_description", "unit", "default_qty"])
