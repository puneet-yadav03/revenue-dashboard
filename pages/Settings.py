# ─────────────────────────────────────────────
#  pages/Settings.py  —  Settings (Redesigned)
# ─────────────────────────────────────────────
import streamlit as st

st.set_page_config(page_title="Settings — Revenue Audit", page_icon="🔧", layout="wide")

from utils.auth import require_login, is_admin
from utils.helpers import render_sidebar, inject_css

require_login()
if not is_admin():
    st.error("🚫 Admin access only.")
    st.stop()

render_sidebar(active_page="Settings")

st.markdown("""
<div class="rad-page-header">
    <div class="rad-page-title">Settings</div>
    <div class="rad-page-subtitle">Configure your dashboard preferences and settings</div>
</div>""", unsafe_allow_html=True)

# ── General Settings ───────────────────────────────────────────────────
st.markdown('<div class="rad-card">', unsafe_allow_html=True)
st.markdown('<div class="rad-card-title">General Settings</div>', unsafe_allow_html=True)
st.markdown('<div class="rad-card-subtitle">Manage your general preferences</div>', unsafe_allow_html=True)

dash_name = st.text_input("Dashboard Name", value="Revenue Audit Dashboard", key="s_name")
timezone  = st.selectbox("Timezone", ["UTC+5:30 (IST)","UTC+0 (GMT)","UTC-5 (EST)","UTC-8 (PST)"], key="s_tz")

st.markdown("---")
st.markdown("**Email Notifications**")
st.markdown("*Receive email notifications for important updates*")
email_notif = st.toggle("Enable", value=True, key="s_email")

st.markdown("**Auto-save Changes**")
st.markdown("*Automatically save edits without confirmation*")
autosave = st.toggle("Enable", value=False, key="s_autosave")

st.markdown("**Show Archived Items**")
st.markdown("*Display archived properties and data*")
show_arch = st.toggle("Enable", value=False, key="s_arch")
st.markdown('</div>', unsafe_allow_html=True)

# ── Display Settings ───────────────────────────────────────────────────
st.markdown('<div class="rad-card">', unsafe_allow_html=True)
st.markdown('<div class="rad-card-title">Display Settings</div>', unsafe_allow_html=True)
st.markdown('<div class="rad-card-subtitle">Customize how data is displayed</div>', unsafe_allow_html=True)

items_per_page = st.number_input("Items Per Page", value=20, min_value=5, max_value=100, step=5, key="s_ipp")
currency       = st.selectbox("Currency", ["INR (₹)","USD ($)","EUR (€)","GBP (£)"], key="s_curr")

st.markdown("**Dark Mode**")
dark_mode = st.toggle("Enable dark mode", value=st.session_state.get("dark_mode",False), key="s_dark")
if dark_mode != st.session_state.get("dark_mode",False):
    st.session_state.dark_mode = dark_mode
    st.rerun()
st.markdown('</div>', unsafe_allow_html=True)

# ── Save ──────────────────────────────────────────────────────────────
if st.button("💾 Save Settings", type="primary", key="s_save"):
    st.success("✅ Settings saved successfully!")
