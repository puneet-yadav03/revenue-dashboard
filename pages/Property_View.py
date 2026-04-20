# ─────────────────────────────────────────────
#  pages/Property_View.py  —  Full View (Redesigned)
# ─────────────────────────────────────────────
import streamlit as st
import pandas as pd

st.set_page_config(page_title="Full View — Revenue Audit", page_icon="🏢", layout="wide")

from utils.auth import require_login
from utils.helpers import render_sidebar, page_header, status_badge, inject_css
from utils.sheets import load_data
from utils.config import STATUS_COLORS

require_login()
render_sidebar(active_page="Property_View")

# ── Page header ────────────────────────────────────────────────────────
st.markdown("""
<div class="rad-page-header">
    <div class="rad-page-title">Full View</div>
</div>""", unsafe_allow_html=True)

df = load_data()
if df.empty:
    st.warning("No data loaded.")
    st.stop()

# ── Filters row ────────────────────────────────────────────────────────
st.markdown('<div class="rad-card-title">All Properties Data</div>', unsafe_allow_html=True)

fcol1, fcol2, fcol3, fcol4 = st.columns([3, 1.5, 1.5, 1])
with fcol1:
    search = st.text_input("🔍 Search properties...", key="fv_search", label_visibility="collapsed",
                            placeholder="🔍 Search properties...")
with fcol2:
    locs = ["All Locations"] + sorted(df["Property City"].dropna().unique().tolist())
    sel_loc = st.selectbox("Location", locs, key="fv_loc", label_visibility="collapsed")
with fcol3:
    cats = ["All Categories"] + sorted(df["Category (A/B/C)"].dropna().unique().tolist())
    sel_cat = st.selectbox("Category", cats, key="fv_cat", label_visibility="collapsed")
with fcol4:
    sort_opts = ["Default", "FH ↑", "FH ↓", "Name ↑", "Name ↓"]
    sort_sel  = st.selectbox("Sort", sort_opts, key="fv_sort", label_visibility="collapsed")

all_statuses = sorted(df["FH Status"].dropna().unique().tolist()) if "FH Status" in df.columns else []
sel_statuses = st.multiselect(
    "Filter by FH Status",
    options=all_statuses,
    default=[],
    placeholder="FH Status",
    key="fv_status",
    label_visibility="collapsed",
)

# Apply filters
filt = df.copy()
if sel_statuses and "FH Status" in filt.columns:
    filt = filt[filt["FH Status"].isin(sel_statuses)]
if sel_loc != "All Locations": filt = filt[filt["Property City"] == sel_loc]
if sel_cat != "All Categories": filt = filt[filt["Category (A/B/C)"] == sel_cat]
if search:
    filt = filt[
        filt["FH"].str.contains(search, case=False, na=False) |
        filt["Property Name"].str.contains(search, case=False, na=False)
    ]
if sort_sel == "FH ↑":   filt = filt.sort_values("FH")
elif sort_sel == "FH ↓": filt = filt.sort_values("FH", ascending=False)
elif sort_sel == "Name ↑": filt = filt.sort_values("Property Name")
elif sort_sel == "Name ↓": filt = filt.sort_values("Property Name", ascending=False)

st.caption(f"Showing **{len(filt)}** of {len(df)} properties")

# ── Determine display columns ─────────────────────────────────────────
display_cols = ["FH", "Property Name", "Property City", "Category (A/B/C)", "FH Status"]
from utils.config import OTA_LIVE_COLS
for c in OTA_LIVE_COLS:
    if c in filt.columns:
        display_cols.append(c)
extra = ["Remarks", "Final CheckDate"]
for c in extra:
    if c in filt.columns:
        display_cols.append(c)
display_cols = [c for c in display_cols if c in filt.columns]

# ── HTML table rendering ───────────────────────────────────────────────
def status_color_badge(val):
    color = STATUS_COLORS.get(str(val).strip(), "#94A3B8")
    return f'<span style="background:{color};color:#fff;padding:3px 9px;border-radius:20px;font-size:11px;font-weight:600;">{val}</span>'

def pct_color(pct_val):
    if pct_val >= 90: return "#10B981"
    if pct_val >= 70: return "#F59E0B"
    return "#EF4444"

# Build table HTML
thead_cols = ["", "Property Name", "Location", "Category", "Status"] + \
             [c.replace("OTA Live ", "").replace("[","").replace("]","") for c in OTA_LIVE_COLS if c in filt.columns]

header_html = "".join(f"<th>{c}</th>" for c in thead_cols)

rows_html = ""
for i, (_, row) in enumerate(filt.iterrows()):
    fh_status = str(row.get("FH Status","")).strip()
    status_badge_html = status_color_badge(fh_status) if fh_status else "—"

    cat_val = str(row.get("Category (A/B/C)","")).strip()
    cat_badge = f'<span style="border:1px solid #E8EAF0;border-radius:4px;padding:2px 8px;font-size:11px;background:#F8F9FC;">{cat_val}</span>' if cat_val else "—"

    ota_cells = ""
    for c in OTA_LIVE_COLS:
        if c not in filt.columns: continue
        val = str(row.get(c,"")).strip()
        col = STATUS_COLORS.get(val, "#94A3B8")
        ota_cells += f'<td><span style="background:{col};color:#fff;padding:2px 8px;border-radius:10px;font-size:11px;font-weight:600;">{val or "—"}</span></td>'

    rows_html += f"""
    <tr>
        <td><input type="checkbox" class="rad-checkbox"></td>
        <td style="font-weight:600;">{row.get('Property Name','—')}</td>
        <td style="color:var(--text-secondary);">{row.get('Property City','—')}</td>
        <td>{cat_badge}</td>
        <td>{status_badge_html}</td>
        {ota_cells}
    </tr>"""

table_html = f"""
<style>
.rad-table-wrapper {{ overflow-y: auto; max-height: 72vh; }}
.rad-table thead tr th {{ position: sticky; top: 0; z-index: 10; background: var(--bg-primary); box-shadow: 0 1px 0 var(--border); }}
</style>
<div class="rad-table-wrapper">
    <table class="rad-table">
        <thead><tr>{header_html}</tr></thead>
        <tbody>{rows_html}</tbody>
    </table>
</div>"""

st.markdown(table_html, unsafe_allow_html=True)

# ── Refresh button ────────────────────────────────────────────────────
st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
if st.button("🔄 Refresh Data", key="fv_refresh"):
    from utils.sheets import force_reload
    force_reload(); st.rerun()