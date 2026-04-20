# ─────────────────────────────────────────────
#  pages/Property_Wise.py  —  Property Wise Info (Redesigned)
# ─────────────────────────────────────────────
import streamlit as st
import pandas as pd

st.set_page_config(page_title="Property Wise Info — Revenue Audit", page_icon="ℹ️", layout="wide")

from utils.auth import require_login
from utils.helpers import render_sidebar, inject_css, status_badge
from utils.sheets import load_data
from utils.config import (
    OTA_LIVE_COLS, LOCATION_COLS, PHOTOSHOOT_COLS,
    PHOTOS_COLS, AMENITIES_COLS, REVIEW_RATING_COLS,
    PARALLEL_LISTING_COLS, STATUS_COLORS
)

require_login()
render_sidebar(active_page="Property_Wise")

st.markdown("""
<div class="rad-page-header">
    <div class="rad-page-title">Property Wise Information</div>
    <div class="rad-page-subtitle"></div>
</div>""", unsafe_allow_html=True)

df = load_data()
if df.empty:
    st.warning("No data loaded.")
    st.stop()

# ── Filters ────────────────────────────────────────────────────────────
fc1, fc2, fc3, fc4 = st.columns(4)
with fc1:
    cities = ["All"] + sorted(df["Property City"].dropna().unique().tolist())
    sel_city = st.selectbox("City", cities, key="pw_city")
with fc2:
    cats = ["All"] + sorted(df["Category (A/B/C)"].dropna().unique().tolist())
    sel_cat = st.selectbox("Category", cats, key="pw_cat")
with fc3:
    statuses = ["All"] + sorted(df["FH Status"].dropna().unique().tolist()) if "FH Status" in df.columns else ["All"]
    sel_status = st.selectbox("FH Status", statuses, key="pw_status")
with fc4:
    search = st.text_input("Search", placeholder="FH ID or Name", key="pw_search")

filt = df.copy()
if sel_city   != "All": filt = filt[filt["Property City"] == sel_city]
if sel_cat    != "All": filt = filt[filt["Category (A/B/C)"] == sel_cat]
if sel_status != "All" and "FH Status" in filt.columns:
    filt = filt[filt["FH Status"] == sel_status]
if search:
    filt = filt[
        filt["FH"].str.contains(search, case=False, na=False) |
        filt["Property Name"].str.contains(search, case=False, na=False)
    ]

st.caption(f"Showing **{len(filt)}** properties")

if filt.empty:
    st.info("No properties match your filters.")
    st.stop()

# ── Expandable property cards ─────────────────────────────────────────
for _, row in filt.head(50).iterrows():  # limit for performance
    prop_name = row.get("Property Name", "Unknown")
    prop_city = row.get("Property City", "")
    fh_id     = row.get("FH", "")
    fh_status = row.get("FH Status", "")
    category  = row.get("Category (A/B/C)", "")
    remarks   = row.get("Remarks", "")
    last_check= row.get("Final CheckDate", "")

    status_color = STATUS_COLORS.get(fh_status, "#94A3B8")

    # Build OTA live section
    ota_html = ""
    all_check_cols = OTA_LIVE_COLS + LOCATION_COLS + PHOTOS_COLS + AMENITIES_COLS
    existing = [c for c in all_check_cols if c in row.index]
    check_count   = sum(1 for c in existing if str(row.get(c,"")).strip().lower() == "check")
    total_cols    = len(existing)
    hygiene_pct   = round(check_count/total_cols*100, 0) if total_cols else 0

    bar_col = "#5B5FEF" if hygiene_pct >= 90 else "#10B981" if hygiene_pct >= 70 else "#F59E0B"

    expand_key = f"expand_{fh_id}"
    if expand_key not in st.session_state:
        st.session_state[expand_key] = False

    # Card
    st.markdown(f"""
    <div class="rad-expand-card" id="card_{fh_id}">
        <div class="rad-expand-header">
            <div>
                <div class="rad-expand-title">{prop_name}
                    <span style="margin-left:10px;background:{status_color};color:#fff;padding:2px 10px;
                    border-radius:20px;font-size:11px;font-weight:600;">{fh_status}</span>
                </div>
                <div class="rad-expand-loc">{prop_city} · {category} · FH: {fh_id}</div>
            </div>
            <div style="display:flex;align-items:center;gap:16px;">
                <div style="text-align:right;">
                    <div style="font-size:11px;color:var(--text-muted);margin-bottom:2px;">Hygiene Score</div>
                    <div style="font-size:18px;font-weight:700;color:{bar_col};">{int(hygiene_pct)}%</div>
                </div>
            </div>
        </div>
        <div class="rad-expand-body">
    """, unsafe_allow_html=True)

    # Four metric boxes
    ota_live_cols = [c for c in OTA_LIVE_COLS if c in row.index]
    ota_live_pct  = round(sum(1 for c in ota_live_cols if str(row.get(c,"")).strip().lower()=="check")/
                          len(ota_live_cols)*100, 0) if ota_live_cols else 0

    loc_cols  = [c for c in LOCATION_COLS  if c in row.index]
    loc_pct   = round(sum(1 for c in loc_cols  if str(row.get(c,"")).strip().lower()=="check")/
                      len(loc_cols)*100, 0) if loc_cols else 0

    ph_cols   = [c for c in PHOTOS_COLS    if c in row.index]
    ph_pct    = round(sum(1 for c in ph_cols    if str(row.get(c,"")).strip().lower()=="check")/
                      len(ph_cols)*100, 0) if ph_cols else 0

    am_cols   = [c for c in AMENITIES_COLS if c in row.index]
    am_pct    = round(sum(1 for c in am_cols    if str(row.get(c,"")).strip().lower()=="check")/
                      len(am_cols)*100, 0) if am_cols else 0

    def metric_box(icon, label, value, pct_val):
        col = "#10B981" if pct_val >= 90 else "#F59E0B" if pct_val >= 70 else "#EF4444"
        return f"""
        <div style="padding:0 20px 0 0;">
            <div class="rad-expand-metric-label">{icon} {label}</div>
            <div class="rad-expand-metric-value" style="color:{col};">{int(pct_val)}%</div>
            <div class="rad-progress" style="margin-top:6px;">
                <div class="rad-progress-fill" style="width:{pct_val}%;background:{col};"></div>
            </div>
            <div class="rad-expand-metric-delta" style="color:var(--text-muted);">{value}</div>
        </div>"""

    boxes = (
        metric_box("📡", "OTA Live",   f"{len(ota_live_cols)} channels", ota_live_pct) +
        metric_box("📍", "Location",   f"{len(loc_cols)} platforms",     loc_pct) +
        metric_box("🖼️","Photos Q&A",  f"{len(ph_cols)} channels",       ph_pct) +
        metric_box("🛎️","Amenities",   f"{len(am_cols)} channels",       am_pct)
    )
    st.markdown(boxes + "</div>", unsafe_allow_html=True)

    # Expand toggle
    col_exp, _ = st.columns([1, 5])
    with col_exp:
        btn_label = "▼ Collapse" if st.session_state[expand_key] else "▶ Expand"
        if st.button(btn_label, key=f"btn_{fh_id}", use_container_width=True):
            st.session_state[expand_key] = not st.session_state[expand_key]

    # Expanded detail
    if st.session_state[expand_key]:
        st.markdown("---")
        sections = {
            "📡 OTA Live":         OTA_LIVE_COLS,
            "📍 Location":         LOCATION_COLS,
            "📸 Photoshoot":       PHOTOSHOOT_COLS,
            "🖼️ Photos Q&A":      PHOTOS_COLS,
            "🛎️ Amenities & RLD": AMENITIES_COLS,
            "⭐ Reviews":          REVIEW_RATING_COLS,
            "📋 Parallel Listing": PARALLEL_LISTING_COLS,
        }
        for sec_title, sec_cols in sections.items():
            existing_sec = [c for c in sec_cols if c in row.index]
            if not existing_sec: continue
            badges = ""
            for c in existing_sec:
                val = str(row.get(c,"")).strip() or "—"
                col = STATUS_COLORS.get(val, "#94A3B8")
                short = c.replace("OTA Live ","").replace("Parallel Listing ","PL ").replace("Location ","Loc ").replace("Photos Q&A ","📷 ").replace("Amenities & RLD ","Amen ").replace("Review | Rating ","⭐ ")
                badges += f"""<div style="background:var(--bg-primary);border:1px solid var(--border);border-radius:8px;padding:8px 12px;min-width:130px;margin:4px;">
                    <div style="font-size:10px;color:var(--text-muted);margin-bottom:4px;">{short}</div>
                    <span style="background:{col};color:#fff;padding:2px 8px;border-radius:8px;font-size:11px;font-weight:600;">{val}</span>
                </div>"""
            st.markdown(f"<div style='margin-bottom:6px;font-size:13px;font-weight:600;color:var(--text-secondary);'>{sec_title}</div>", unsafe_allow_html=True)
            st.markdown(f'<div style="display:flex;flex-wrap:wrap;gap:0;margin-bottom:12px;">{badges}</div>', unsafe_allow_html=True)

        if remarks:
            st.markdown(f"**Remarks:** {remarks}")
        if last_check:
            st.markdown(f"**Last Check Date:** {last_check}")

    st.markdown("</div>", unsafe_allow_html=True)

st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
if st.button("🔄 Refresh", key="pw_refresh"):
    from utils.sheets import force_reload
    force_reload(); st.rerun()
