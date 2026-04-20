# ─────────────────────────────────────────────
#  pages/Analytics.py  —  OTA Analytics
# ─────────────────────────────────────────────
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import re, numpy as np

st.set_page_config(page_title="OTA Analytics — Revenue Audit", page_icon="📈", layout="wide")

from utils.auth import require_login
from utils.helpers import render_sidebar, inject_css
from utils.sheets import load_data
from utils.config import OTA_LIVE_COLS, LOCATION_COLS, PHOTOS_COLS, AMENITIES_COLS

require_login()
render_sidebar(active_page="Analytics")

st.markdown("""
<div class="rad-page-header">
    <div class="rad-page-title">OTA Analytics</div>

</div>""", unsafe_allow_html=True)

df = load_data()
if df.empty:
    st.warning("No data loaded.")
    st.stop()

if "FH Status" in df.columns:
    df = df[df["FH Status"].str.strip().str.lower() == "live"].copy()

# ── Month parsing ──────────────────────────────────────────────────────
def extract_month(val):
    if not val or str(val).strip() == "": return None
    s = str(val).strip()
    for fmt in ("%b-%Y", "%b-%y", "%B-%Y", "%B-%y", "%m-%Y", "%m/%Y", "%m-%y", "%m/%y"):
        try: return pd.to_datetime(s, format=fmt).strftime("%m-%y")
        except: pass
    try: return pd.to_datetime(s).strftime("%m-%y")
    except: return None

def month_sort_key(m):
    try:
        mm, yy = m.split("-"); return int(yy)*100+int(mm)
    except: return 0

if "Cohort Month" in df.columns:
    df["_month"] = df["Cohort Month"].apply(extract_month)
elif "Final CheckDate" in df.columns:
    df["_month"] = df["Final CheckDate"].apply(extract_month)
else:
    df["_month"] = None

# ── Config maps ────────────────────────────────────────────────────────
OTA_LIVE_COL_MAP = {
    "MMT/GI":    "OTA Live [MMT/GI]",
    "BDC":       "OTA Live [BDC]",
    "GMB":       "OTA Live [GMB]",
    "Agoda":     "OTA Live [Agoda]",
    "Cleartrip": "OTA Live [Cleartrip]",
    "Expedia":   "OTA Live [Expedia]",
}
CHANNEL_COLS = {
    "MMT/GI":    ["OTA Live [MMT/GI]", "Amenities & RLD [MMT]", "Photos Q&A [MMT]", "Location [MMT]"],
    "BDC":       ["OTA Live [BDC]", "Amenities & RLD [BDC]", "Photos Q&A [BDC]", "Location [BDC]"],
    "GMB":       ["OTA Live [GMB]", "Photos Q&A [GMB]", "Location [GMB]"],
    "Agoda":     ["OTA Live [Agoda]"],
    "Cleartrip": ["OTA Live [Cleartrip]"],
    "Expedia":   ["OTA Live [Expedia]"],
}
OTA_HYGIENE_PARAMS = {
    "MMT":       ["Amenities & RLD [MMT]", "Photos Q&A [MMT]", "Location [MMT]"],
    "BDC":       ["Amenities & RLD [BDC]", "Photos Q&A [BDC]", "Location [BDC]"],
    "GMB":       ["Photos Q&A [GMB]", "Location [GMB]"],
    "WebApp":    ["Amenities & RLD [FH]", "Photos Q&A [FH Web]", "Location [FH Web]"],
    "Agoda":     [], "Cleartrip": [], "Expedia": [],
}
OTA_LIVE_MAP = {
    "MMT": "OTA Live [MMT/GI]", "BDC": "OTA Live [BDC]", "GMB": "OTA Live [GMB]",
    "WebApp": None, "Agoda": "OTA Live [Agoda]",
    "Cleartrip": "OTA Live [Cleartrip]", "Expedia": "OTA Live [Expedia]",
}
PARAM_DISPLAY = {
    "Amenities & RLD [FH]":  "Amenities",
    "Amenities & RLD [MMT]": "Amenities",
    "Amenities & RLD [BDC]": "Amenities",
    "Photos Q&A [FH Web]":   "Photos",
    "Photos Q&A [MMT]":      "Photos",
    "Photos Q&A [BDC]":      "Photos",
    "Photos Q&A [GMB]":      "Photos",
    "Location [FH Web]":     "Location",
    "Location [MMT]":        "Location",
    "Location [BDC]":        "Location",
    "Location [GMB]":        "Location",
}
FIXED_PARAM_COLS = ["Amenities", "Photos", "Location"]

def color_pct_style(val):
    if not isinstance(val, (int, float)): return ""
    if val >= 90: return "background-color:#D1FAE5;color:#065F46;font-weight:600;"
    if val >= 70: return "background-color:#FEF3C7;color:#92400E;font-weight:600;"
    return "background-color:#FEE2E2;color:#991B1B;font-weight:600;"

def avg_completion(sub_df, cols):
    existing = [c for c in cols if c in sub_df.columns]
    if not existing or len(sub_df) == 0: return None
    pcts = [(sub_df[c].str.strip().str.lower() == "check").sum() / len(sub_df) * 100 for c in existing]
    return round(float(np.mean(pcts)), 1)

dark     = st.session_state.get("dark_mode", False)
plot_bg  = "rgba(0,0,0,0)"
font_col = "#9CA3AF" if dark else "#6B7280"

# ── Sub-tab switcher ───────────────────────────────────────────────────
sub_tab = st.radio("View", ["OTA Live Completion %", "Property Hygiene Score"],
                   horizontal=True, key="an_subtab", label_visibility="collapsed")

# ══════════════════════════════════════════════════════════════════════
# SUB-TAB 1 — OTA Live Completion %
# ══════════════════════════════════════════════════════════════════════
if sub_tab == "OTA Live Completion %":

    st.markdown("### 📊 Channel-wise Completion %")

    view_mode = st.radio(
        "View by", ["Month-wise", "Category-wise", "Month × Category"],
        horizontal=True, key="t1_view_mode"
    )

    ff1, ff2, ff3 = st.columns(3)
    with ff1:
        cat_opts  = sorted(df["Category (A/B/C)"].dropna().unique().tolist())
        sel_cats  = st.multiselect("Category", cat_opts, placeholder="All categories", key="t1_cats")
    with ff2:
        month_opts = sorted([m for m in df["_month"].dropna().unique() if m], key=month_sort_key)
        sel_months = st.multiselect("Month", month_opts, placeholder="All months", key="t1_months")
    with ff3:
        all_channels = list(OTA_LIVE_COL_MAP.keys())
        sel_channels = st.multiselect("Channel", all_channels, placeholder="All channels", key="t1_channels")

    channels_to_show = sel_channels if sel_channels else all_channels
    base_df = df.copy()
    if sel_cats:   base_df = base_df[base_df["Category (A/B/C)"].isin(sel_cats)]
    if sel_months: base_df = base_df[base_df["_month"].isin(sel_months)]

    st.caption(f"**{len(base_df)}** properties · 🟢 ≥90% · 🟡 70–89% · 🔴 <70%")
    st.divider()

    def build_channel_table(data, group_col, group_label, channels):
        rows = []
        for grp_val, grp_df in data.groupby(group_col, sort=False):
            row = {group_label: grp_val, "# Props": len(grp_df)}
            for ch in channels:
                live_col = OTA_LIVE_COL_MAP.get(ch)
                if live_col and live_col in grp_df.columns and len(grp_df):
                    pct = round(
                        (grp_df[live_col].str.strip().str.lower() == "check").sum()
                        / len(grp_df) * 100, 1
                    )
                    row[ch] = pct
                else:
                    row[ch] = float("nan")
            rows.append(row)
        return pd.DataFrame(rows)

    def show_table(tbl_df, channels):
        num_cols = [c for c in channels if c in tbl_df.columns]
        styled = (tbl_df.style
                  .map(color_pct_style, subset=num_cols)
                  .format({c: "{:.1f}%" for c in num_cols}, na_rep="—"))
        n = len(tbl_df)
        st.dataframe(styled, use_container_width=True, hide_index=True,
                     height=min(36*(n+1)+4, 580))

    if base_df.empty:
        st.info("No data after filters.")

    elif view_mode == "Month-wise":
        mdf = base_df.dropna(subset=["_month"])
        if mdf.empty:
            st.warning("No month data available (check Cohort Month / Final CheckDate column).")
        else:
            tbl = build_channel_table(mdf, "_month", "Month", channels_to_show)
            tbl = tbl.sort_values("Month", key=lambda s: s.map(month_sort_key))
            show_table(tbl, channels_to_show)

    elif view_mode == "Category-wise":
        if "Category (A/B/C)" not in base_df.columns:
            st.warning("No category column found.")
        else:
            tbl = build_channel_table(base_df, "Category (A/B/C)", "Category", channels_to_show)
            tbl = tbl.sort_values("Category")
            show_table(tbl, channels_to_show)

    else:  # Month × Category
        mdf = base_df.dropna(subset=["_month"])
        if mdf.empty or "Category (A/B/C)" not in mdf.columns:
            st.warning("Month or Category data missing.")
        else:
            rows = []
            for (month, cat), grp in mdf.groupby(["_month", "Category (A/B/C)"], sort=False):
                row = {"Month": month, "Category": cat, "# Props": len(grp)}
                for ch in channels_to_show:
                    cols = CHANNEL_COLS.get(ch, [])
                    val  = avg_completion(grp, cols)
                    row[ch] = val if val is not None else float("nan")
                rows.append(row)
            if rows:
                mx_df = pd.DataFrame(rows)
                mx_df = mx_df.sort_values(
                    ["Month", "Category"],
                    key=lambda s: s.map(month_sort_key) if s.name == "Month" else s
                )
                num_cols = [c for c in channels_to_show if c in mx_df.columns]
                styled = (mx_df.style
                          .map(color_pct_style, subset=num_cols)
                          .format({c: "{:.1f}%" for c in num_cols}, na_rep="—"))
                st.dataframe(styled, use_container_width=True, hide_index=True,
                             height=min(36*(len(mx_df)+1)+4, 580))

                if len(channels_to_show) > 1 and len(mx_df["Month"].unique()) > 1:
                    st.caption("📈 Pick a category to see month-wise trend chart")
                    cat_pick = st.selectbox("Category for trend",
                                            sorted(mx_df["Category"].unique()),
                                            key="t1_cat_pick")
                    cat_sub = mx_df[mx_df["Category"] == cat_pick]
                    melted  = cat_sub.melt(
                        id_vars=["Month"], value_vars=channels_to_show,
                        var_name="Channel", value_name="Completion %"
                    ).dropna(subset=["Completion %"])
                    if not melted.empty:
                        fig_mx = px.line(melted, x="Month", y="Completion %",
                                         color="Channel", markers=True,
                                         title=f"Category {cat_pick} — Month-wise",
                                         color_discrete_sequence=px.colors.qualitative.Set2)
                        fig_mx.update_layout(
                            height=280, plot_bgcolor="#F8FAFC", paper_bgcolor="#F8FAFC",
                            yaxis=dict(range=[0, 110], gridcolor="#E2E8F0"),
                            xaxis=dict(tickangle=-30),
                            legend=dict(orientation="h", y=-0.4, x=0, font=dict(size=11)),
                            margin=dict(t=30, b=90, l=0, r=0)
                        )
                        fig_mx.add_hline(y=100, line_dash="dot", line_color="#10B981")
                        st.plotly_chart(fig_mx, use_container_width=True, key="chart_mx_trend")
            else:
                st.info("No data for Month × Category view.")

    st.divider()
    if st.button("🔄 Refresh Data", key="an_refresh_1"):
        from utils.sheets import force_reload
        force_reload(); st.rerun()

# ══════════════════════════════════════════════════════════════════════
# SUB-TAB 2 — Property Hygiene Score
# ══════════════════════════════════════════════════════════════════════
else:

    # ── Overall vs Month-wise toggle ───────────────────────────────────
    hyg_view = st.radio(
        "Hygiene View", ["Overall", "Month-wise"],
        horizontal=True, key="hyg_view_mode", label_visibility="collapsed"
    )

    hf1, hf2 = st.columns(2)
    with hf1:
        hyg_cat_opts  = sorted(df["Category (A/B/C)"].dropna().unique().tolist())
        hyg_sel_cats  = st.multiselect("📂 Filter by Category", hyg_cat_opts,
                                       placeholder="All categories", key="hyg_cats")
    with hf2:
        hyg_month_opts = sorted([m for m in df["_month"].dropna().unique() if m], key=month_sort_key)
        hyg_sel_months = st.multiselect("📅 Filter by Month", hyg_month_opts,
                                        placeholder="All months", key="hyg_months")

    # ══════════════════════════════════════════════════════════════════
    # OVERALL HYGIENE VIEW
    # ══════════════════════════════════════════════════════════════════
    if hyg_view == "Overall":
        hyg_df = df.copy()
        if hyg_sel_cats:   hyg_df = hyg_df[hyg_df["Category (A/B/C)"].isin(hyg_sel_cats)]
        if hyg_sel_months: hyg_df = hyg_df[hyg_df["_month"].isin(hyg_sel_months)]

        active_filters = []
        if hyg_sel_cats:   active_filters.append(f"Category: {', '.join(hyg_sel_cats)}")
        if hyg_sel_months: active_filters.append(f"Month: {', '.join(hyg_sel_months)}")
        filter_label = " · ".join(active_filters) if active_filters else "All properties (no filter)"
        st.caption(f"🔎 Hygiene computed on **{len(hyg_df)}** properties — {filter_label}")

        if hyg_df.empty:
            st.info("No data after filters.")
            st.stop()

        # ── Compute scores ─────────────────────────────────────────────────
        hyg_summary = []
        detail_rows = []
        debug_rows  = []

        for ota, params in OTA_HYGIENE_PARAMS.items():
            live_col_h = OTA_LIVE_MAP.get(ota)
            if live_col_h and live_col_h in hyg_df.columns:
                live_sub = hyg_df[hyg_df[live_col_h].str.strip().str.lower() == "check"]
            else:
                live_sub = hyg_df
            n_live = len(live_sub)
            if n_live == 0: continue

            avail_params = [p for p in params if p in hyg_df.columns]
            new_row   = {"OTA": ota, "Listing Live": n_live}
            debug_row = {"OTA": ota, "Listing Live": n_live}
            for pg in FIXED_PARAM_COLS:
                new_row[pg]   = "None"
                debug_row[pg] = "—"

            hyg_score = None
            if avail_params:
                param_pcts_local = []
                for p in avail_params:
                    cnt = int((live_sub[p].str.strip().str.lower() == "check").sum())
                    pct = round((cnt / n_live) * 100, 1)
                    param_pcts_local.append(pct)
                    grp = PARAM_DISPLAY.get(p)
                    if grp:
                        new_row[grp]   = pct
                        debug_row[grp] = f"{cnt}/{n_live}"
                hyg_score = round(float(np.median(param_pcts_local)), 1)
            elif live_col_h and live_col_h in hyg_df.columns:
                hyg_score = round(
                    (hyg_df[live_col_h].str.strip().str.lower() == "check").sum() / len(hyg_df) * 100, 1)

            new_row["🏅 Hygiene Score"]   = hyg_score if hyg_score is not None else "—"
            debug_row["🏅 Hygiene Score"] = f"{hyg_score}%" if hyg_score is not None else "—"
            if hyg_score is not None:
                hyg_summary.append({"OTA": ota, "Listing Live": n_live, "Score": hyg_score})
            detail_rows.append(new_row)
            debug_rows.append(debug_row)

        if not hyg_summary:
            st.warning("Not enough data to compute hygiene scores.")
            st.stop()

        # ── Score cards ────────────────────────────────────────────────────
        card_cols = st.columns(min(len(hyg_summary), 7))
        for i, h in enumerate(hyg_summary):
            score   = h["Score"]
            pct_col = "#10B981" if score >= 90 else "#F59E0B" if score >= 70 else "#EF4444"
            card_bg = "#F0FDF4" if score >= 90 else "#FFFBEB" if score >= 70 else "#FFF1F2"
            dot     = "🟢" if score >= 90 else "🟡" if score >= 70 else "🔴"
            with card_cols[i % min(len(hyg_summary), 7)]:
                st.markdown(f"""
                <div style="background:{card_bg};border:1px solid #E2E8F0;border-radius:10px;
                            padding:14px 10px;text-align:center;margin-bottom:4px;">
                    <div style="font-size:12px;font-weight:700;color:#1E293B;margin-bottom:4px;">
                        {dot} {h['OTA']}
                    </div>
                    <div style="font-size:30px;font-weight:800;color:{pct_col};
                                letter-spacing:-1px;line-height:1.1;">
                        {score}%
                    </div>
                    <div style="font-size:11px;color:#64748B;margin-top:4px;">
                        {int(h['Listing Live'])} listing live
                    </div>
                </div>""", unsafe_allow_html=True)

        st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)

        # ── Tabs: Summary chart + Detail Table ────────────────────────────
        hyg_tabs = st.tabs(["📊 Summary", "📋 Detail Table"])

        with hyg_tabs[0]:
            hyg_sum_df = pd.DataFrame(hyg_summary)
            colors     = px.colors.qualitative.Set2
            fig_hyg    = go.Figure()
            for i, row_h in hyg_sum_df.iterrows():
                fig_hyg.add_trace(go.Bar(
                    name=row_h["OTA"],
                    x=[row_h["OTA"]],
                    y=[row_h["Score"]],
                    marker_color=colors[i % len(colors)],
                    text=[f"{row_h['Score']:.1f}%"],
                    textposition="outside",
                ))
            fig_hyg.update_layout(
                barmode="group", height=340,
                plot_bgcolor=plot_bg, paper_bgcolor=plot_bg,
                yaxis=dict(range=[0, 115], gridcolor="#E2E8F0", title="Hygiene Score %"),
                xaxis=dict(tickangle=-15),
                showlegend=False,
                margin=dict(t=20, b=60, l=0, r=0),
                font=dict(family="DM Sans", color=font_col),
            )
            fig_hyg.add_hline(y=100, line_dash="dot", line_color="#10B981")
            st.plotly_chart(fig_hyg, use_container_width=True, key="hyg_bar")

        with hyg_tabs[1]:
            if detail_rows:
                detail_tbl = pd.DataFrame(detail_rows)
                style_cols = FIXED_PARAM_COLS + ["🏅 Hygiene Score"]

                def style_detail(val):
                    if val == "None": return "color:#CBD5E1;font-style:italic;"
                    try:    return color_pct_style(float(val))
                    except: return ""

                def fmt_cell(v):
                    if v == "None": return "None"
                    try:    return f"{float(v):.1f}%"
                    except: return str(v)

                detail_styled = (detail_tbl.style
                                 .map(style_detail, subset=style_cols)
                                 .format({c: fmt_cell for c in style_cols}))
                st.dataframe(detail_styled, use_container_width=True, hide_index=True,
                             height=min(36*(len(detail_tbl)+1)+4, 320))

            # Raw counts expander
            if debug_rows:
                with st.expander("🔢 Raw counts (checks / listing-live) — click to verify"):
                    st.caption("Format per cell: checks / listing-live on that channel")
                    debug_tbl = pd.DataFrame(debug_rows)
                    st.dataframe(debug_tbl, use_container_width=True, hide_index=True)

    # ══════════════════════════════════════════════════════════════════
    # MONTH-WISE HYGIENE VIEW
    # ══════════════════════════════════════════════════════════════════
    elif hyg_view == "Month-wise":
        mw_df = df.copy()
        if hyg_sel_cats:   mw_df = mw_df[mw_df["Category (A/B/C)"].isin(hyg_sel_cats)]
        mw_df = mw_df.dropna(subset=["_month"])

        if mw_df.empty:
            st.info("No month data available (check Cohort Month / Final CheckDate column).")
            st.stop()

        # ── Multi-select channel filter — WebApp default ───────────────────
        all_ota_channels = list(OTA_HYGIENE_PARAMS.keys())
        mw_sel_channels = st.multiselect(
            "🔍 Filter by Channel",
            options=all_ota_channels,
            default=["WebApp"],
            key="mw_channel_filter",
            placeholder="Select channels…",
        )
        # If nothing selected, fall back to WebApp
        channels_selected = mw_sel_channels if mw_sel_channels else ["WebApp"]

        all_months = sorted(mw_df["_month"].dropna().unique().tolist(), key=month_sort_key)

        def style_detail_mw(val):
            if pd.isna(val): return "color:#CBD5E1;font-style:italic;"
            try:    return color_pct_style(float(val))
            except: return ""

        def fmt_detail_mw(v):
            if pd.isna(v): return "—"
            try:    return f"{float(v):.1f}%"
            except: return str(v)

        # ── One detail table per selected channel ──────────────────────────
        for ota_sel in channels_selected:
            params_sel       = OTA_HYGIENE_PARAMS.get(ota_sel, [])
            live_col_sel     = OTA_LIVE_MAP.get(ota_sel)
            avail_params_sel = [p for p in params_sel if p in mw_df.columns]

            st.markdown(f"""
            <div style="background:linear-gradient(90deg,var(--accent,#5B5FEF) 0%,#818CF8 100%);
                padding:8px 16px;border-radius:8px;margin:16px 0 8px;">
                <span style="color:#fff;font-size:13px;font-weight:700;">
                    📊 {ota_sel} — Monthly Hygiene Detail (Amenities / Photos / Location)
                </span>
            </div>""", unsafe_allow_html=True)

            if not avail_params_sel:
                st.info(f"No hygiene params configured for **{ota_sel}** (only live count is tracked).")
                continue

            # Build month × param breakdown rows
            detail_mw_rows = []
            for month in all_months:
                month_sub = mw_df[mw_df["_month"] == month]
                if live_col_sel and live_col_sel in month_sub.columns:
                    live_sub = month_sub[month_sub[live_col_sel].str.strip().str.lower() == "check"]
                else:
                    live_sub = month_sub
                n_live = len(live_sub)

                detail_row = {"Month": month, "Listing Live": n_live}
                param_pcts = []
                for p in avail_params_sel:
                    grp_label = PARAM_DISPLAY.get(p, p)
                    if n_live > 0:
                        pct = round(
                            (live_sub[p].str.strip().str.lower() == "check").sum() / n_live * 100, 1
                        )
                    else:
                        pct = float("nan")
                    detail_row[grp_label] = pct
                    if not pd.isna(pct):
                        param_pcts.append(pct)

                detail_row["🏅 Hygiene Score"] = round(float(np.median(param_pcts)), 1) if param_pcts else float("nan")
                detail_mw_rows.append(detail_row)

            if detail_mw_rows:
                detail_mw_df = pd.DataFrame(detail_mw_rows)
                detail_mw_df = detail_mw_df.loc[:, ~detail_mw_df.columns.duplicated()]
                style_cols_d = [c for c in detail_mw_df.columns if c not in ("Month", "Listing Live")]

                styled_detail_mw = (
                    detail_mw_df.style
                    .map(style_detail_mw, subset=style_cols_d)
                    .format({c: fmt_detail_mw for c in style_cols_d})
                )
                st.dataframe(styled_detail_mw, use_container_width=True, hide_index=True,
                             height=min(36*(len(detail_mw_df)+1)+4, 480))
                st.caption(" ")

    st.divider()
    if st.button("🔄 Refresh Data", key="an_refresh_2"):
        from utils.sheets import force_reload
        force_reload(); st.rerun()