import sys
from pathlib import Path

import streamlit as st

sys.path.append(str(Path(__file__).resolve().parent.parent))
from utils.guard import require_login
from utils.data import get_pending_requests, approve_request, reject_request

st.set_page_config(page_title="Team Request", page_icon="✅", layout="wide")

user = require_login()

if not user.get("is_admin"):
    st.warning("Ye page sirf admin ke liye hai.")
    st.stop()

st.markdown("<h1 style='color:#0f172a;'>✅ Team Request — Site Status Approvals</h1>", unsafe_allow_html=True)
st.caption("Team ne jo Site Status change request kiya hai, wo yaha dikhega. Accept karte hi Site Status update ho jayega.")

requests_df = get_pending_requests()

if requests_df.empty:
    st.info("Abhi koi pending request nahi hai. 🎉")
    st.stop()

for _, row in requests_df.iterrows():
    with st.container(border=True):
        c1, c2, c3, c4 = st.columns([2, 2, 1.5, 1.5])
        c1.markdown(f"**Site Name**  \n{row.get('site_name', '')}")
        c2.markdown(f"**Site ID**  \n{row.get('site_id', '')}")
        c3.markdown(f"**Requested By**  \n{row.get('requested_by', '')}")
        c4.markdown(f"**New Status**  \n🟡 {row.get('requested_status', '')}")

        if row.get("remark"):
            st.markdown(f"**Remark:** {row.get('remark')}")

        st.caption(f"Requested at: {row.get('created_at', '')}")

        bc1, bc2 = st.columns(2)
        with bc1:
            if st.button("✅ Accept", key=f"accept_{row['id']}", use_container_width=True, type="primary"):
                approve_request(row["id"], row.get("site_row_id"), row.get("requested_status"))
                st.success(f"Approved! {row.get('site_name')} ab '{row.get('requested_status')}' hai.")
                st.rerun()
        with bc2:
            if st.button("❌ Reject", key=f"reject_{row['id']}", use_container_width=True):
                reject_request(row["id"])
                st.warning("Request reject kar di gayi.")
                st.rerun()
