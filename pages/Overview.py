# ─────────────────────────────────────────────
#  pages/Overview.py  —  Summary Page
# ─────────────────────────────────────────────
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import numpy as np

st.set_page_config(page_title="Summary — Revenue Audit", page_icon="📊", layout="wide")

from utils.auth import require_login, current_user
from utils.helpers import render_sidebar, metric_card_html, inject_css
from utils.sheets import load_data, load_reminders, force_reload
from utils.config import (
    OTA_LIVE_COLS, LOCATION_COLS, PHOTOS_COLS,
    AMENITIES_COLS, PHOTOSHOOT_COLS
)

require_login()
render_sidebar(active_page="Overview")

with st.spinner("Loading data..."):
    df = load_data()

if df.empty:
    st.warning("No data loaded. Check Google Sheets connection.")
    st.stop()

dark     = st.session_state.get("dark_mode", False)
plot_bg  = "rgba(0,0,0,0)"
grid_col = "#2A3040" if dark else "#F0F2F8"
font_col = "#9CA3AF" if dark else "#6B7280"

# ── Page header ────────────────────────────────────────────────────────
col_h, col_r = st.columns([4, 1])
with col_h:
    st.markdown("""
    <div class="rad-page-header">
        <div class="rad-page-title">Summary</div>
    
    </div>""", unsafe_allow_html=True)
with col_r:
    if st.button("↻ Refresh Data", key="ov_refresh", use_container_width=True):
        force_reload(); st.rerun()

# ── Filters ────────────────────────────────────────────────────────────
fc1, fc2 = st.columns(2)
with fc1:
    cats = ["All Categories"] + sorted(df["Category (A/B/C)"].dropna().unique().tolist())
    sel_cat = st.selectbox("Category", cats, key="ov_cat", label_visibility="collapsed")
with fc2:
    cities = ["All Cities"] + sorted(df["Property City"].dropna().unique().tolist())
    sel_city = st.selectbox("City", cities, key="ov_city", label_visibility="collapsed")

filt_df = df.copy()
if "FH Status" in filt_df.columns:
    filt_df = filt_df[filt_df["FH Status"].str.strip().str.lower() == "live"]
if sel_cat  != "All Categories": filt_df = filt_df[filt_df["Category (A/B/C)"].str.strip() == sel_cat]
if sel_city != "All Cities":     filt_df = filt_df[filt_df["Property City"].str.strip() == sel_city]

live = len(filt_df)

# ── Pending count ──────────────────────────────────────────────────────
all_check_cols = OTA_LIVE_COLS + LOCATION_COLS + PHOTOS_COLS + AMENITIES_COLS + PHOTOSHOOT_COLS
existing_cc    = [c for c in all_check_cols if c in filt_df.columns]
pending_count  = int(filt_df.apply(
    lambda row: any(str(row.get(c,"")).strip().lower() != "check" for c in existing_cc),
    axis=1).sum()) if existing_cc else 0

# ── Reminders ──────────────────────────────────────────────────────────
reminders_df = load_reminders()
rem_pending  = int((reminders_df["Status"] == "Pending").sum()) if (
    not reminders_df.empty and "Status" in reminders_df.columns) else 0

# ── Avg OTA Live % ─────────────────────────────────────────────────────
live_pcts = []
for c in OTA_LIVE_COLS:
    if c in filt_df.columns and len(filt_df):
        live_pcts.append((filt_df[c].str.strip().str.lower() == "check").sum() / len(filt_df) * 100)
avg_hygiene = round(sum(live_pcts)/len(live_pcts), 1) if live_pcts else 0

# ── Metric Cards ───────────────────────────────────────────────────────
m1, m2, m3, m4 = st.columns(4)
with m1:
    st.markdown(metric_card_html("🏨","#E6F7F8", live, "Total Live Properties", f"+{live} active", True), unsafe_allow_html=True)
with m2:
    st.markdown(metric_card_html("📈","#EAF3DE", f"{avg_hygiene}%", "Avg OTA Live %",
        "🟢 Good" if avg_hygiene>=90 else "🟡 OK" if avg_hygiene>=70 else "🔴 Low", avg_hygiene>=70), unsafe_allow_html=True)
with m3:
    st.markdown(metric_card_html("✏️","#FEF3C7", pending_count, "Pending Properties(100% Completion)",
        f"{pending_count} open" if pending_count else "All clear", pending_count==0), unsafe_allow_html=True)
with m4:
    st.markdown(metric_card_html("🔔","#FEE2E2", rem_pending, "Reminders Due",
        "needs attention" if rem_pending else "All clear", rem_pending==0), unsafe_allow_html=True)

st.markdown("<div style='height:24px'></div>", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════
# SECTION 1 — OTA Parameter Details
# Every OTA × every parameter with Check% and pending count
# ══════════════════════════════════════════════════════════════════════
st.markdown('<div class="rad-card-title">OTA Parameter Details</div>', unsafe_allow_html=True)

# Full parameter map per OTA
OTA_PARAM_MAP = {
    "WebApp": {
        "Location":   "Location [FH Web]",
        "Photos Q&A": "Photos Q&A [FH Web]",
        "Amenities":  "Amenities & RLD [FH]",
    },
    "MMT/GI": {
        "OTA Live":   "OTA Live [MMT/GI]",
        "Location":   "Location [MMT]",
        "Photos Q&A": "Photos Q&A [MMT]",
        "Amenities":  "Amenities & RLD [MMT]",
    },
    "BDC": {
        "OTA Live":   "OTA Live [BDC]",
        "Location":   "Location [BDC]",
        "Photos Q&A": "Photos Q&A [BDC]",
        "Amenities":  "Amenities & RLD [BDC]",
    },
    "GMB": {
        "OTA Live":   "OTA Live [GMB]",
        "Location":   "Location [GMB]",
        "Photos Q&A": "Photos Q&A [GMB]",
    },
    "Agoda": {
        "OTA Live":   "OTA Live [Agoda]",
    },
    "Cleartrip": {
        "OTA Live":   "OTA Live [Cleartrip]",
    },
    "Expedia": {
        "OTA Live":   "OTA Live [Expedia]",
    },
}

def pct_color(v):
    if v >= 90: return "#10B981", "#D1FAE5"
    if v >= 70: return "#D97706", "#FEF3C7"
    return "#DC2626", "#FEE2E2"

n = len(filt_df)
ota_cols_display = list(OTA_PARAM_MAP.keys())
tabs = st.tabs([f"📡 {o}" for o in ota_cols_display])

for tab, ota in zip(tabs, ota_cols_display):
    with tab:
        params = OTA_PARAM_MAP[ota]
        rows = []
        for param_name, col in params.items():
            if col not in filt_df.columns:
                continue
            vals = filt_df[col].str.strip().str.lower()
            checked  = int((vals == "check").sum())
            pending  = n - checked
            pct      = round(checked / n * 100, 1) if n else 0
            rows.append({
                "Parameter":  param_name,
                "Column":     col,
                "✅ Check":   checked,
                "⏳ Pending": pending,
                "% Complete": pct,
            })

        if not rows:
            st.info(f"No columns found for {ota} in the data.")
            continue

        param_df = pd.DataFrame(rows)

        # Summary mini-cards for this OTA
        overall_pct = round(param_df["% Complete"].mean(), 1) if not param_df.empty else 0
        txt_col, bg_col = pct_color(overall_pct)
        total_pending = int(param_df["⏳ Pending"].sum())

        mc1, mc2, mc3 = st.columns(3)
        with mc1:
            st.markdown(f"""
            <div style="background:{bg_col};border-radius:8px;padding:12px 16px;text-align:center;">
                <div style="font-size:11px;color:{txt_col};font-weight:600;margin-bottom:2px;">Overall Completion</div>
                <div style="font-size:26px;font-weight:800;color:{txt_col};">{overall_pct}%</div>
            </div>""", unsafe_allow_html=True)
        with mc2:
            st.markdown(f"""
            <div style="background:#EEF2FF;border-radius:8px;padding:12px 16px;text-align:center;">
                <div style="font-size:11px;color:#4338CA;font-weight:600;margin-bottom:2px;">Total Properties</div>
                <div style="font-size:26px;font-weight:800;color:#4338CA;">{n}</div>
            </div>""", unsafe_allow_html=True)
        with mc3:
            p_col = "#DC2626" if total_pending > 0 else "#059669"
            p_bg  = "#FEE2E2" if total_pending > 0 else "#D1FAE5"
            st.markdown(f"""
            <div style="background:{p_bg};border-radius:8px;padding:12px 16px;text-align:center;">
                <div style="font-size:11px;color:{p_col};font-weight:600;margin-bottom:2px;">Total Pending</div>
                <div style="font-size:26px;font-weight:800;color:{p_col};">{total_pending}</div>
            </div>""", unsafe_allow_html=True)

        st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

        # Progress bars per parameter
        bar_html = ""
        for _, r in param_df.iterrows():
            pct_v   = r["% Complete"]
            t_col, t_bg = pct_color(pct_v)
            bar_html += f"""
            <div style="display:flex;align-items:center;gap:10px;margin-bottom:10px;">
                <span style="font-size:12px;color:var(--text-secondary);width:110px;flex-shrink:0;">{r['Parameter']}</span>
                <div style="flex:1;height:8px;background:var(--border);border-radius:4px;overflow:hidden;">
                    <div style="width:{pct_v}%;height:100%;background:{t_col};border-radius:4px;transition:width .3s;"></div>
                </div>
                <span style="font-size:12px;font-weight:700;color:{t_col};width:46px;text-align:right;">{pct_v}%</span>
                <span style="font-size:11px;color:var(--text-muted);width:80px;text-align:right;">
                    {int(r['✅ Check'])} ✅ / {int(r['⏳ Pending'])} ⏳
                </span>
            </div>"""
        st.markdown(bar_html, unsafe_allow_html=True)

        # Detailed table (collapsible)
        with st.expander("📋 View full data table"):
            def style_pct(val):
                if not isinstance(val, (int, float)): return ""
                if val >= 90: return "background-color:#D1FAE5;color:#065F46;font-weight:600;"
                if val >= 70: return "background-color:#FEF3C7;color:#92400E;font-weight:600;"
                return "background-color:#FEE2E2;color:#991B1B;font-weight:600;"

            disp = param_df.drop(columns=["Column"])
            styled = disp.style.map(style_pct, subset=["% Complete"]) \
                               .format({"% Complete": "{:.1f}%"})
            st.dataframe(styled, use_container_width=True, hide_index=True)

st.markdown("<div style='height:24px'></div>", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════
# SECTION 2 — Section Completion Overview (all sections, progress bars)
# ══════════════════════════════════════════════════════════════════════
st.markdown('<div class="rad-card-title">Section Completion Overview</div>', unsafe_allow_html=True)

sections = {
    "OTA Live":   OTA_LIVE_COLS,
    "Location":   LOCATION_COLS,
    "Photos Q&A": PHOTOS_COLS,
    "Amenities":  AMENITIES_COLS,
    "Photoshoot": PHOTOSHOOT_COLS,
}

sec_rows = []
for sec_name, scols in sections.items():
    ecols = [c for c in scols if c in filt_df.columns]
    if not ecols or filt_df.empty: continue
    total_cells = len(filt_df) * len(ecols)
    checks = filt_df[ecols].apply(lambda c: c.str.strip().str.lower() == "check").sum().sum()
    pct    = round((checks / total_cells) * 100, 1) if total_cells else 0
    sec_rows.append((sec_name, pct, int(total_cells - checks)))

sc1, sc2 = st.columns(2)
for i, (sec_name, pct, pending_s) in enumerate(sec_rows):
    t_col, _ = pct_color(pct)
    target_col = sc1 if i % 2 == 0 else sc2
    with target_col:
        with st.container(border=True):
            st.markdown(f"""
            <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px;">
                <span style="font-size:13px;font-weight:600;color:var(--text-primary);">{sec_name}</span>
                <span style="font-size:18px;font-weight:800;color:{t_col};">{pct}%</span>
            </div>
            <div style="height:8px;background:var(--border);border-radius:4px;overflow:hidden;margin-bottom:6px;">
                <div style="width:{pct}%;height:100%;background:{t_col};border-radius:4px;"></div>
            </div>
            <div style="font-size:11px;color:var(--text-muted);">{pending_s} cells pending</div>
            """, unsafe_allow_html=True)

st.markdown("<div style='height:24px'></div>", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════
# SECTION 3 — Owner-wise Pending Reminders
# ══════════════════════════════════════════════════════════════════════
st.markdown('<div class="rad-card-title">Owner-wise Pending Reminders</div>', unsafe_allow_html=True)

if reminders_df.empty or "Status" not in reminders_df.columns:
    st.info("No reminders data found.")
else:
    pending_rem = reminders_df[reminders_df["Status"] == "Pending"].copy()

    if pending_rem.empty:
        st.success("✅ All reminders resolved — no pending reminders!")
    else:
        # Group by Username
        if "Username" in pending_rem.columns:
            owner_grp = (pending_rem.groupby("Username")
                         .agg(
                             Pending=("Status", "count"),
                         )
                         .reset_index()
                         .rename(columns={"Username": "Owner"})
                         .sort_values("Pending", ascending=False))

            # Cards for each owner
            n_owners = len(owner_grp)
            cols_per_row = min(n_owners, 4)
            owner_cols = st.columns(cols_per_row)
            for i, (_, row_o) in enumerate(owner_grp.iterrows()):
                p = int(row_o["Pending"])
                o_col = "#DC2626" if p > 5 else "#D97706" if p > 2 else "#059669"
                o_bg  = "#FEE2E2" if p > 5 else "#FEF3C7" if p > 2 else "#D1FAE5"
                with owner_cols[i % cols_per_row]:
                    st.markdown(f"""
                    <div style="background:{o_bg};border-radius:10px;padding:14px 12px;
                                text-align:center;margin-bottom:8px;">
                        <div style="font-size:13px;font-weight:700;color:{o_col};margin-bottom:4px;">
                            {row_o['Owner'].replace('.', ' ').title()}
                        </div>
                        <div style="font-size:28px;font-weight:800;color:{o_col};line-height:1.1;">
                            {p}
                        </div>
                        <div style="font-size:11px;color:{o_col};margin-top:2px;">pending</div>
                    </div>""", unsafe_allow_html=True)

            st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

            # Full reminder detail table
            with st.expander("📋 View all pending reminders in detail"):
                show_cols = [c for c in ["Username","FH ID","Property Name","Column","Value","Due Date","Created At"]
                             if c in pending_rem.columns]
                st.dataframe(pending_rem[show_cols].sort_values("Username") if "Username" in show_cols
                             else pending_rem[show_cols],
                             use_container_width=True, hide_index=True)

                # Also show per-owner breakdown with column detail
                st.markdown("**Breakdown by Owner & Column:**")
                if "Column" in pending_rem.columns:
                    detail_grp = (pending_rem.groupby(["Username","Column"])
                                  .size().reset_index(name="Count")
                                  .sort_values(["Username","Count"], ascending=[True, False]))
                    st.dataframe(detail_grp, use_container_width=True, hide_index=True)
        else:
            st.warning("No 'Username' column found in reminders sheet.")
            st.dataframe(pending_rem, use_container_width=True, hide_index=True)