"""
Shared browser-cookie manager, used to keep a team member logged in across
page reloads / the app "waking up" again — instead of forcing login every
single time.
"""

import extra_streamlit_components as stx

COOKIE_NAME = "jms_mobile"


def get_cookie_manager():
    # NOT cached — this component needs to be recreated each script run so
    # Streamlit can match it up with its browser-side counterpart.
    return stx.CookieManager(key="jms_cookie_manager")
