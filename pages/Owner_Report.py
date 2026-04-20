# ─────────────────────────────────────────────
#  pages/Owner_Report.py  —  Owner Report (Redesigned)
# ─────────────────────────────────────────────
import streamlit as st
import pandas as pd
import re

st.set_page_config(page_title="Owner Report — Revenue Audit", page_icon="📄", layout="wide")

from utils.auth import require_login
from utils.helpers import render_sidebar, inject_css
from utils.sheets import load_dashboard_data, force_reload

require_login()
render_sidebar(active_page="Owner_Report")

# ── Page header ────────────────────────────────────────────────────────
hcol, btncol = st.columns([5,1])
with hcol:
    st.markdown("""
    <div class="rad-page-header">
        <div class="rad-page-title">Owner Report</div>
    
    </div>""", unsafe_allow_html=True)
with btncol:
    st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)
    if st.button("⬇️ Download Report", type="primary", use_container_width=True, key="or_download"):
        st.info("Export functionality — data available in dataframes below.")

with st.spinner("Loading dashboard data..."):
    dashboard = load_dashboard_data()

if not dashboard:
    st.warning("No data found in Dashboard sheet. Make sure the tab is named 'Dashboard'.")
    st.stop()

all_persons  = sorted(set(b["person"]  for b in dashboard if b["person"]))
all_channels = sorted(set(b["channel"] for b in dashboard if b["channel"]))



# ── Filters ────────────────────────────────────────────────────────────
with st.container(border=True):
    fc1, fc2, fc3, fc4 = st.columns([2,2,2,1])
    with fc1:
        sel_persons = st.multiselect("Owner", all_persons, placeholder="All owners", key="or_persons")
    with fc2:
        sel_channels = st.multiselect("Channel", all_channels, placeholder="All channels", key="or_channels")
    with fc3:
        cat_opts_all = []
        sel_cats_or = st.multiselect("Category", cat_opts_all, placeholder="All categories", key="or_cats")
    with fc4:
        st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)
        if st.button("Reset Filters", use_container_width=True, key="or_reset"):
            for k in ["or_persons","or_channels","or_cats"]:
                if k in st.session_state: del st.session_state[k]
            st.rerun()
# Apply filters
blocks_to_show = list(dashboard)
if sel_persons:  blocks_to_show = [b for b in blocks_to_show if b["person"] in sel_persons]
if sel_channels: blocks_to_show = [b for b in blocks_to_show if b["channel"] in sel_channels]
if not blocks_to_show:
    st.info("No tables found for the selected filter.")
    st.stop()

def month_sort_key(m):
    try: mm,yy=m.split("-"); return int(yy)*100+int(mm)
    except: return 0

MONTH_RE = re.compile(r"^\d{2}-\d{2}$")

def color_pct(val):
    if not isinstance(val,(int,float)): return ""
    if val >= 90: return "background-color:#D1FAE5;color:#065F46;font-weight:600;"
    if val >= 70: return "background-color:#FEF3C7;color:#92400E;font-weight:600;"
    return "background-color:#FEE2E2;color:#991B1B;font-weight:600;"


def is_pl_block(b):
    return "pl" in (b.get("channel") or "").lower()

# Fixed channel order: WebApp → MMT → BDC → GMB → Agoda → Cleartrip → Expedia → PL (last)
CHANNEL_ORDER = {
    "webapp": 0, "web": 0,
    "mmt":    1, "mmt/gi": 1, "gi": 1,
    "bdc":    2,
    "gmb":    3,
    "agoda":  4,
    "cleartrip": 5,
    "expedia": 6,
}

def sort_key(b):
    channel = (b.get("channel") or "").lower().strip()
    person  = (b.get("person")  or "").lower().strip()
    # Check if PL block
    is_pl = ("pl" in channel and not any(
        k in channel for k in ["mmt","bdc","gmb","agoda","cleartrip","expedia","webapp"]
    )) or "yash" in person
    if is_pl:
        return (99, person)
    # Match channel order
    for key, order in CHANNEL_ORDER.items():
        if key in channel:
            return (order, person)
    return (50, person)

blocks_to_show = sorted(blocks_to_show, key=sort_key)

# ── Actual Data & Percentage Data tables ──────────────────────────────
for block in blocks_to_show:
    owner   = block["owner"]
    person  = block["person"]
    channel = block["channel"]
    columns = block["columns"]
    rows    = block["rows"]
    totals  = block["totals"]
    extras  = block.get("extras",{})

    if not columns: continue
    clean_rows = [r for r in rows if MONTH_RE.match(str(r.get("Month","")).strip())]
    if not clean_rows: continue

    data_df = pd.DataFrame(clean_rows)
    for c in columns:
        if c in data_df.columns:
            data_df[c] = pd.to_numeric(data_df[c], errors="coerce").fillna(0).astype(int)
    data_df["_sort"] = data_df["Month"].apply(month_sort_key)
    data_df = data_df.sort_values("_sort").drop(columns=["_sort"]).reset_index(drop=True)

    props_col   = columns[0] if columns else None
    metric_cols = [c for c in columns if c != "Month" and c != props_col]

    # Pct rows
    pct_rows = []
    for _, r in data_df.iterrows():
        month = str(r.get("Month","")).strip()
        props = int(r.get(props_col,0) or 0) if props_col else 0
        pct_row = {"Month": month}
        for mc in metric_cols:
            val = int(r.get(mc,0) or 0)
            pct_row[mc] = round(val/props*100,1) if props else 0.0
        pct_rows.append(pct_row)
    pct_df = pd.DataFrame(pct_rows) if pct_rows else pd.DataFrame()

    totals_row = {"Month": "Total"}
    for col_name in columns:
        totals_row[col_name] = totals.get(col_name, int(data_df[col_name].sum()) if col_name in data_df.columns else "")
    display_df = pd.concat([data_df, pd.DataFrame([totals_row])], ignore_index=True)

    channel_part = f" — {channel}" if channel else ""
    st.markdown(f"""
    <div style="background:linear-gradient(90deg,var(--accent) 0%,var(--accent-light) 100%);
        padding:8px 16px;border-radius:8px;margin-bottom:8px;">
        <span style="color:#fff;font-size:13px;font-weight:700;">{person}{channel_part}</span>
        
    </div>""", unsafe_allow_html=True)

    left_col, right_col = st.columns(2)
    with left_col:
        with st.container(border=True):
            st.markdown('<div style="font-size:11px;color:var(--text-muted);font-weight:600;margin-bottom:6px;">📊 Actual Data</div>', unsafe_allow_html=True)

            n_rows = len(display_df)
            h = min(32+14*n_rows, 210)
            col_cfg = {"Month": st.column_config.TextColumn("Month", width=55)}
            for col_name in columns:
                col_cfg[col_name] = st.column_config.NumberColumn(col_name, width=70)
            st.dataframe(display_df, use_container_width=True, hide_index=True, height=h, column_config=col_cfg)

    with right_col:
        with st.container(border=True):
            st.markdown('<div style="font-size:11px;color:var(--text-muted);font-weight:600;margin-bottom:6px;">✅ Percentage Data</div>', unsafe_allow_html=True)

            if not pct_df.empty and metric_cols:
                styled_pct = pct_df.style.map(color_pct, subset=metric_cols).format({mc:"{:.1f}%" for mc in metric_cols})
                n_pct = len(pct_df)
                h_pct = min(32+14*n_pct,210)
                st.dataframe(styled_pct, use_container_width=True, hide_index=True, height=h_pct)
            else:
                st.info("No metric columns to compute % for.")

    clean_extras = {k:v for k,v in extras.items() if not str(k).startswith("_")}
    if clean_extras:
        ex_cols = st.columns(min(len(clean_extras),4))
        for ei,(label,val) in enumerate(clean_extras.items()):
            with ex_cols[ei%4]:
                st.metric(label,val)

    st.markdown("<hr style='border:none;border-top:1px solid var(--border);margin:10px 0 12px;'>", unsafe_allow_html=True)

if st.button("🔄 Refresh Dashboard Data", key="or_refresh"):
    force_reload(); st.rerun()