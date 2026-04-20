# ─────────────────────────────────────────────
#  pages/Admin.py  —  Admin Panel (Redesigned)
# ─────────────────────────────────────────────
import streamlit as st
import pandas as pd

st.set_page_config(page_title="Admin Panel — Revenue Audit", page_icon="⚙️", layout="wide")

from utils.auth import require_login, is_admin
from utils.helpers import render_sidebar, inject_css
from utils.sheets import load_data, load_audit_log, load_reminders, resolve_reminder, force_reload
from utils.config import STATUS_COLORS

require_login()
if not is_admin():
    st.error("🚫 Admin access only.")
    st.stop()

render_sidebar(active_page="Admin")

st.markdown("""
<div class="rad-page-header">
    <div class="rad-page-title">Admin Panel</div>
    <div class="rad-page-subtitle"></div>
</div>""", unsafe_allow_html=True)

# ── Custom tab ─────────────────────────────────────────────────────────
if "admin_tab" not in st.session_state:
    st.session_state.admin_tab = "All Data"

tab_labels = ["All Data", "Audits", "Reminders"]
tab_icons  = {"All Data":"🗂️","Audits":"📝","Reminders":"🔔"}

tabs_html = '<div class="rad-tabs" style="margin-bottom:20px;">'
for t in tab_labels:
    active_cls = "active" if st.session_state.admin_tab == t else ""
    tabs_html += f'<div class="rad-tab {active_cls}" id="admtab_{t}">{tab_icons[t]} {t}</div>'
tabs_html += '</div>'

# Use st.radio for actual tab switching
sel_tab = st.radio("Admin Tab", tab_labels, horizontal=True,
                   key="admin_tab_sel", label_visibility="collapsed",
                   index=tab_labels.index(st.session_state.admin_tab))
st.session_state.admin_tab = sel_tab
active_tab = sel_tab

# ══════════════════════════════════════════════════════════════════════
# TAB: All Data
# ══════════════════════════════════════════════════════════════════════
if active_tab == "All Data":
    df = load_data()

    st.markdown('<div class="rad-card-title">All Properties Data</div>', unsafe_allow_html=True)
    st.markdown('<div class="rad-card-subtitle"></div>', unsafe_allow_html=True)

    if df.empty:
        st.warning("No data.")
    else:
        # Filters
        fc1, fc2, fc3, fc4 = st.columns([3, 1.5, 1.5, 1.5])
        with fc1:
            search = st.text_input("🔍 Search properties...", key="ad_search",
                                   placeholder="Search properties...", label_visibility="collapsed")
        with fc2:
            cities = ["All Cities"] + sorted(df["Property City"].dropna().unique().tolist())
            city   = st.selectbox("City", cities, key="ad_city", label_visibility="collapsed")
        with fc3:
            cats   = ["All Categories"] + sorted(df["Category (A/B/C)"].dropna().unique().tolist())
            cat    = st.selectbox("Category", cats, key="ad_cat", label_visibility="collapsed")
        with fc4:
            statuses = ["All Statuses"] + sorted(df["FH Status"].dropna().unique().tolist()) if "FH Status" in df.columns else ["All Statuses"]
            status   = st.selectbox("Status", statuses, key="ad_status", label_visibility="collapsed")

        filt = df.copy()
        if city   != "All Cities":      filt = filt[filt["Property City"] == city]
        if cat    != "All Categories":  filt = filt[filt["Category (A/B/C)"] == cat]
        if status != "All Statuses" and "FH Status" in filt.columns:
            filt = filt[filt["FH Status"] == status]
        if search:
            filt = filt[filt["FH"].str.contains(search, case=False, na=False) |
                        filt["Property Name"].str.contains(search, case=False, na=False)]

        # Multi-select cities expansion
        all_cities = sorted(df["Property City"].dropna().unique().tolist())
        sel_cities = st.multiselect("Multi-Select Cities", all_cities, key="ad_multicities",
                                    label_visibility="visible")
        if sel_cities:
            filt = filt[filt["Property City"].isin(sel_cities)]

        st.caption(f"**{len(filt)}** properties")
        display_cols = [c for c in filt.columns if c != "_row_index"]
        st.dataframe(filt[display_cols], use_container_width=True, hide_index=True)

        csv = filt[display_cols].to_csv(index=False).encode("utf-8")
        st.download_button("⬇️ Download CSV", csv, "ota_data_export.csv", "text/csv")

    if st.button("🔄 Refresh", key="ad_refresh"):
        force_reload(); st.rerun()

# ══════════════════════════════════════════════════════════════════════
# TAB: Audits
# ══════════════════════════════════════════════════════════════════════
elif active_tab == "Audits":
    st.markdown('<div class="rad-card-title">Audit Activity Log</div>', unsafe_allow_html=True)
    st.markdown('<div class="rad-card-subtitle">Track all changes made by users</div>', unsafe_allow_html=True)

    audit_df = load_audit_log()
    if audit_df.empty:
        st.info("No audit entries yet.")
    else:
        col1, col2 = st.columns(2)
        with col1:
            users_list = ["All"] + sorted(audit_df["Username"].dropna().unique().tolist()) if "Username" in audit_df.columns else ["All"]
            user_filt  = st.selectbox("Filter by User", users_list, key="aud_user")
        with col2:
            ota_filt_list = ["All"] + sorted(audit_df["OTA"].dropna().unique().tolist()) if "OTA" in audit_df.columns else ["All"]
            ota_filt  = st.selectbox("Filter by OTA", ota_filt_list, key="aud_ota")

        shown = audit_df.copy()
        if user_filt != "All" and "Username" in shown.columns:
            shown = shown[shown["Username"] == user_filt]
        if ota_filt  != "All" and "OTA" in shown.columns:
            shown = shown[shown["OTA"] == ota_filt]
        if "Timestamp" in shown.columns:
            shown = shown.sort_values("Timestamp", ascending=False)

        # Activity cards (last 20)
        for _, row in shown.head(20).iterrows():
            ts      = row.get("Timestamp","")
            col_ch  = row.get("Column","")
            old_v   = row.get("Old Value","")
            new_v   = row.get("New Value","")
            fh_id   = row.get("FH ID","")
            prop    = row.get("Property Name","")
            user    = row.get("Username","")
            st.markdown(f"""
            <div style="background:var(--bg-card);border:1px solid var(--border);border-radius:10px;
                padding:14px 16px;margin-bottom:8px;display:flex;align-items:flex-start;gap:14px;">
                <div style="width:36px;height:36px;background:var(--accent-light);border-radius:50%;
                    display:flex;align-items:center;justify-content:center;flex-shrink:0;font-size:16px;">🔄</div>
                <div style="flex:1;">
                    <div style="display:flex;justify-content:space-between;align-items:flex-start;">
                        <div style="font-weight:600;color:var(--text-primary);font-size:14px;">
                            Updated {col_ch or 'field'}</div>
                        <div style="font-size:11px;color:var(--text-muted);">{ts}</div>
                    </div>
                    <div style="font-size:12px;color:var(--text-secondary);margin-top:2px;">
                        Property: <b>{prop}</b> &nbsp;·&nbsp; User: <b>{user}</b></div>
                    <div style="font-size:12px;color:var(--accent);margin-top:4px;">
                        {f'Changed from <b>{old_v}</b> → <b>{new_v}</b>' if old_v or new_v else ''}</div>
                </div>
            </div>""", unsafe_allow_html=True)

        st.caption(f"Showing 20 of {len(shown)} entries")
        with st.expander("View full table"):
            st.dataframe(shown, use_container_width=True, hide_index=True)
            csv2 = shown.to_csv(index=False).encode("utf-8")
            st.download_button("⬇️ Download Audit Log", csv2, "audit_log.csv", "text/csv")

# ══════════════════════════════════════════════════════════════════════
# TAB: Reminders
# ══════════════════════════════════════════════════════════════════════
elif active_tab == "Reminders":
    st.markdown('<div class="rad-card-title">Active Reminders</div>', unsafe_allow_html=True)
    st.markdown('<div class="rad-card-subtitle">Manage your pending tasks and reminders</div>', unsafe_allow_html=True)

    rem_df = load_reminders()
    if rem_df.empty:
        st.info("No reminders yet.")
    else:
        status_filt = st.radio("Show", ["Pending","Resolved","All"], horizontal=True, key="rem_status")
        shown_rem   = rem_df.copy()
        if status_filt != "All" and "Status" in shown_rem.columns:
            shown_rem = shown_rem[shown_rem["Status"] == status_filt]

        for i, (_, r) in enumerate(shown_rem.iterrows()):
            col_name = r.get("Column","")
            val      = r.get("Value","")
            fh_id    = r.get("FH ID","?")
            due      = r.get("Due Date","")
            rem_status = r.get("Status","")

            priority_label = "High Priority"
            priority_bg    = "#FEE2E2"
            priority_col   = "#EF4444"
            if rem_status == "Resolved":
                priority_label = "Resolved"
                priority_bg    = "#D1FAE5"
                priority_col   = "#10B981"

            col_card, col_btn = st.columns([8,1])
            with col_card:
                st.markdown(f"""
                <div style="background:var(--bg-card);border:1px solid var(--border);border-radius:10px;
                    padding:14px 16px;display:flex;align-items:center;gap:14px;">
                    <div style="width:36px;height:36px;background:#FEF3C7;border-radius:50%;
                        display:flex;align-items:center;justify-content:center;font-size:18px;flex-shrink:0;">🔔</div>
                    <div style="flex:1;">
                        <div style="font-weight:600;color:var(--text-primary);font-size:14px;">
                            {col_name or 'Reminder'} — {fh_id}</div>
                        <div style="margin-top:4px;">
                            <span style="background:{priority_bg};color:{priority_col};padding:2px 8px;border-radius:20px;font-size:11px;font-weight:600;margin-right:6px;">{priority_label}</span>
                            <span style="background:#F1F3F9;color:#6B7280;padding:2px 8px;border-radius:20px;font-size:11px;font-weight:600;margin-right:6px;">{rem_status}</span>
                            {f'<span style="font-size:11px;color:var(--text-muted);">Due: {due}</span>' if due else ''}
                        </div>
                    </div>
                </div>""", unsafe_allow_html=True)
            with col_btn:
                if rem_status == "Pending":
                    if st.button("✓ Resolve", key=f"rem_res_{i}", use_container_width=True):
                        sheet_row = shown_rem.index[i] + 2
                        try:
                            resolve_reminder(sheet_row)
                            st.success("Marked as resolved!")
                            from utils.sheets import load_reminders as lr
                            lr.clear()
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error: {e}")
