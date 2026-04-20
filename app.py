# ─────────────────────────────────────────────
#  app.py  —  Entrypoint
# ─────────────────────────────────────────────
import streamlit as st

st.set_page_config(
    page_title="Revenue Audit Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={}
)

# Hide Streamlit's auto-generated sidebar page nav immediately
st.markdown("""
<style>
[data-testid="stSidebarNav"],
[data-testid="stSidebarNavItems"],
section[data-testid="stSidebar"] ul,
section[data-testid="stSidebar"] nav {
    display: none !important;
}
</style>
""", unsafe_allow_html=True)

from utils.auth import require_login
require_login()
st.switch_page("pages/Overview.py")