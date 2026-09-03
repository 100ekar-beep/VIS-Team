"""
Login logic: verifies mobile_number + password against app_users.password_hash
(bcrypt). In demo mode (no Supabase configured) it checks against a fixed
demo password instead.
"""

import bcrypt

from utils.data import get_user_by_mobile, DEMO_PASSWORD
from utils.supabase_client import is_demo_mode


def verify_login(mobile_number: str, password: str):
    """
    Returns the user dict (id, team_name, mobile_number, user_id) on success,
    or None if the mobile number / password is wrong.
    """
    mobile_number = (mobile_number or "").strip()
    password = password or ""

    user = get_user_by_mobile(mobile_number)
    if user is None:
        return None

    if is_demo_mode():
        if password == DEMO_PASSWORD:
            return {k: v for k, v in user.items() if k != "password"}
        return None

    stored_hash = user.get("password")
    if not stored_hash:
        return None

    try:
        ok = bcrypt.checkpw(password.encode("utf-8"), stored_hash.encode("utf-8"))
    except (ValueError, TypeError):
        return None

    if not ok:
        return None

    return {k: v for k, v in user.items() if k != "password"}
