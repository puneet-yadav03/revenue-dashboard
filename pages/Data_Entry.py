# ─────────────────────────────────────────────
#  pages/Data_Entry.py  —  Tasks + Per-Row Editing
# ─────────────────────────────────────────────
import streamlit as st
import pandas as pd
from datetime import date, timedelta

st.set_page_config(page_title="Tasks — Revenue Audit", page_icon="☑️", layout="wide")

from utils.auth import require_login, current_user, current_otas, is_admin
from utils.helpers import render_sidebar, inject_css
from utils.sheets import load_data, save_entry, force_reload, write_reminder
from utils.config import (
    OTA_TO_EDITABLE_COLS, OTA_COLUMN_MAP, COL_DROPDOWN_MAP,
    DROPDOWNS, REVIEW_RATING_COLS, PARALLEL_LISTING_COLS,
    STATUS_COLORS
)

require_login()
render_sidebar(active_page="Data_Entry")

df = load_data()
if df.empty:
    st.warning("No data loaded.")
    st.stop()

if "FH" not in df.columns:
    st.error("Column 'FH' not found in sheet. Check header row.")
    st.stop()

username  = current_user()
user_otas = current_otas()

# ── Session state init ─────────────────────────────────────────────────
for key, default in [
    ("row_edits", {}),
    ("row_editing", {}),
    ("reminder_needed", {}),
    ("reminder_dates", {}),
    ("remind_dialog_fh", None),
    ("saved_fhs", set()),
]:
    if key not in st.session_state:
        st.session_state[key] = default


# ══════════════════════════════════════════════════════════════════════
# TODAY'S TASKS SECTION
# ══════════════════════════════════════════════════════════════════════
from utils.sheets import load_tasks, write_task, close_task
from utils.config import USERS
from datetime import datetime as _dt

st.markdown(
    '<div class="rad-page-header" style="margin-bottom:12px;">'
    '<div class="rad-page-title">Today\'s Tasks</div></div>',
    unsafe_allow_html=True,
)

try:
    tasks_df = load_tasks()
except Exception:
    tasks_df = pd.DataFrame()

today_str    = date.today().strftime("%Y-%m-%d")
tomorrow_str = (date.today() + timedelta(days=1)).strftime("%Y-%m-%d")

if not tasks_df.empty and "Due Date" in tasks_df.columns and "Status" in tasks_df.columns:
    open_tasks = tasks_df[tasks_df["Status"] == "Open"].copy()
    if not is_admin() and "Assigned To" in open_tasks.columns:
        open_tasks = open_tasks[open_tasks["Assigned To"] == username].copy()
    todays_tasks = open_tasks[open_tasks["Due Date"].astype(str) <= today_str].copy()
else:
    open_tasks   = pd.DataFrame()
    todays_tasks = pd.DataFrame()

t_high = len(todays_tasks[todays_tasks["Priority"] == "High"]) if not todays_tasks.empty else 0
t_low  = len(todays_tasks[todays_tasks["Priority"] == "Low"])  if not todays_tasks.empty else 0
t_all  = len(open_tasks)

badge_html = (
    f'<div style="display:flex;gap:10px;margin-bottom:16px;flex-wrap:wrap;">'
    f'<div style="background:#FEE2E2;border-radius:8px;padding:8px 16px;text-align:center;min-width:100px;">'
    f'<div style="font-size:11px;font-weight:700;color:#DC2626;">🔴 High Priority</div>'
    f'<div style="font-size:22px;font-weight:800;color:#DC2626;">{t_high}</div></div>'
    f'<div style="background:#FEF3C7;border-radius:8px;padding:8px 16px;text-align:center;min-width:100px;">'
    f'<div style="font-size:11px;font-weight:700;color:#D97706;">🟡 Low Priority</div>'
    f'<div style="font-size:22px;font-weight:800;color:#D97706;">{t_low}</div></div>'
    f'<div style="background:#EEF2FF;border-radius:8px;padding:8px 16px;text-align:center;min-width:100px;">'
    f'<div style="font-size:11px;font-weight:700;color:#4338CA;">📋 All Open</div>'
    f'<div style="font-size:22px;font-weight:800;color:#4338CA;">{t_all}</div></div>'
    f'</div>'
)
st.markdown(badge_html, unsafe_allow_html=True)

if todays_tasks.empty:
    st.success("✅ No tasks due today or tomorrow!")
else:
    for priority, p_color, p_bg, p_label in [
        ("High", "#DC2626", "#FEE2E2", "🔴 High Priority — Due Today"),
        ("Low",  "#D97706", "#FEF3C7", "🟡 Low Priority — Due Today"),
    ]:
        grp = todays_tasks[todays_tasks["Priority"] == priority]
        if grp.empty:
            continue
        st.markdown(f"""
        <div style="background:{p_bg};border-left:4px solid {p_color};border-radius:0 8px 8px 0;
                    padding:8px 14px;margin-bottom:8px;font-size:13px;font-weight:700;color:{p_color};">
            {p_label} &nbsp;·&nbsp; {len(grp)} task(s)
        </div>""", unsafe_allow_html=True)

        for _, task_row in grp.iterrows():
            tid        = str(task_row.get("Task ID", ""))
            title      = str(task_row.get("Title", ""))
            desc       = str(task_row.get("Description", ""))
            assigned   = str(task_row.get("Assigned To", ""))
            created_by = str(task_row.get("Created By", ""))
            due        = str(task_row.get("Due Date", ""))

            with st.container(border=True):
                col_info, col_action = st.columns([5, 1])
                with col_info:
                    st.markdown(f"""
                    <div style="display:flex;align-items:flex-start;gap:12px;">
                        <div style="background:{p_bg};border-radius:6px;padding:4px 10px;
                                    font-size:11px;font-weight:700;color:{p_color};flex-shrink:0;">{tid}</div>
                        <div>
                            <div style="font-size:14px;font-weight:700;color:var(--text-primary);">{title}</div>
                            <div style="font-size:12px;color:var(--text-secondary);margin-top:2px;">{desc}</div>
                            <div style="font-size:11px;color:var(--text-muted);margin-top:4px;">
                                👤 Assigned to: <b>{assigned}</b> &nbsp;·&nbsp;
                                📅 Due: <b>{due}</b> &nbsp;·&nbsp;
                                🔖 Created by: {created_by}
                            </div>
                        </div>
                    </div>""", unsafe_allow_html=True)
                with col_action:
                    if is_admin():
                        if st.button("✅ Close", key=f"close_{tid}", use_container_width=True, type="primary"):
                            ok = close_task(str(tid), username, notes="Closed by admin")
                            if ok:
                                st.success(f"Task {tid} closed!")
                                load_tasks.clear()
                                st.rerun()
                            else:
                                st.error("Could not close task.")
                        if priority == "Low":
                            if st.button("📅 +1 day", key=f"ext_{tid}", use_container_width=True):
                                try:
                                    from utils.sheets import _ensure_task_sheet
                                    ws = _ensure_task_sheet()
                                    records = ws.get_all_records()
                                    for _i, _r in enumerate(records):
                                        if str(_r.get("Task ID", "")).strip() == str(tid):
                                            _new_due = (date.today() + timedelta(days=1)).strftime("%Y-%m-%d")
                                            ws.update_cell(_i + 2, 8, _new_due)
                                            load_tasks.clear()
                                            st.success("Extended to tomorrow!")
                                            st.rerun()
                                except Exception as _ex:
                                    st.error(f"Error: {_ex}")
                    else:
                        st.markdown(
                            '<div style="font-size:11px;color:var(--text-muted);text-align:center;padding-top:8px;">Admin closes tasks</div>',
                            unsafe_allow_html=True,
                        )

st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
with st.expander("➕ Create New Task", expanded=False):
    st.markdown('<div style="font-size:13px;font-weight:600;color:var(--text-primary);margin-bottom:8px;">New Task</div>', unsafe_allow_html=True)
    nf1, nf2 = st.columns(2)
    with nf1:
        new_title = st.text_input("Task Title *", key="new_task_title", placeholder="e.g. Fix BDC listing for FH1234")
    with nf2:
        new_priority = st.radio("Priority", ["High", "Low"], horizontal=True, key="new_task_priority")
    new_desc = st.text_area("Description", key="new_task_desc", placeholder="What needs to be done?", height=80)
    if is_admin():
        all_users    = list(USERS.keys())
        new_assigned = st.selectbox("Assign To", all_users, key="new_task_assign",
                                     format_func=lambda x: x.replace(".", " ").title())
    else:
        new_assigned = username
        st.markdown(f'<div style="font-size:12px;color:var(--text-muted);padding:4px 0;">Assigned to: <b>{username.replace(".", " ").title()}</b> (you)</div>', unsafe_allow_html=True)
    if st.button("📝 Create Task", type="primary", key="create_task_btn"):
        if not new_title.strip():
            st.error("Task title is required.")
        else:
            tid = write_task(
                title=new_title.strip(), description=new_desc.strip(),
                priority=new_priority, assigned_to=new_assigned, created_by=username,
            )
            st.success(f"✅ Task **{tid}** created!")
            load_tasks.clear()
            st.rerun()

_all_view = tasks_df[tasks_df["Status"] == "Open"].copy() if not tasks_df.empty and "Status" in tasks_df.columns else pd.DataFrame()
if not is_admin() and not _all_view.empty and "Assigned To" in _all_view.columns:
    _all_view = _all_view[_all_view["Assigned To"] == username].copy()
if not _all_view.empty:
    with st.expander(f"📋 All Open Tasks ({len(_all_view)})", expanded=False):
        for _, task_row in _all_view.iterrows():
            tid      = str(task_row.get("Task ID", ""))
            title    = str(task_row.get("Title", ""))
            priority = str(task_row.get("Priority", ""))
            assigned = str(task_row.get("Assigned To", ""))
            due      = str(task_row.get("Due Date", ""))
            p_col    = "#DC2626" if priority == "High" else "#D97706"
            p_bg     = "#FEE2E2" if priority == "High" else "#FEF3C7"
            c1, c2, c3, c4, c5 = st.columns([1, 3, 1.5, 1.5, 1])
            with c1:
                st.markdown(f'<span style="background:{p_bg};color:{p_col};padding:2px 8px;border-radius:4px;font-size:11px;font-weight:700;">{tid}</span>', unsafe_allow_html=True)
            with c2:
                st.markdown(f'<span style="font-size:13px;font-weight:600;">{title}</span>', unsafe_allow_html=True)
            with c3:
                st.markdown(f'<span style="font-size:11px;color:{p_col};font-weight:600;">{priority}</span>', unsafe_allow_html=True)
            with c4:
                st.markdown(f'<span style="font-size:11px;color:var(--text-secondary);">👤 {assigned} · 📅 {due}</span>', unsafe_allow_html=True)
            with c5:
                if is_admin():
                    if st.button("Close", key=f"close_all_{tid}", use_container_width=True):
                        close_task(str(tid), username)
                        load_tasks.clear()
                        st.rerun()

st.markdown("---")
st.markdown("""
<div class="rad-page-header" style="margin-bottom:12px;margin-top:8px;">
    <div class="rad-page-title">Data Entry</div>
</div>""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════
# OTA / CHANNEL SELECTOR
# ══════════════════════════════════════════════════════════════════════
if is_admin():
    all_otas     = list(OTA_TO_EDITABLE_COLS.keys())
    selected_ota = st.selectbox("OTA / Channel:", all_otas, key="de_ota_select")
else:
    if not user_otas:
        st.warning("No OTAs assigned to your account.")
        st.stop()
    if len(user_otas) > 1:
        selected_ota = st.selectbox("Your OTA:", user_otas, key="de_ota_select")
    else:
        selected_ota = user_otas[0]

OTA_BULK_COLS = {
    "MMT/GI": [
        "OTA Live [MMT/GI]", "Location [MMT]", "Location [GI]",
        "Photos Q&A [MMT]", "Photos Q&A [GI]",
        "Amenities & RLD [MMT]", "Amenities & RLD [GI]", "Compset [MMT]",
    ],
    "BDC": [
        "OTA Live [BDC]", "Review | Rating [BDC]", "Location [BDC]",
        "Photos Q&A [BDC]", "Amenities & RLD [BDC]",
    ],
    "GMB": [
        "OTA Live [GMB]", "Review | Rating [GMB]", "Location [GMB]",
        "Photos Q&A [GMB]", "OTA Price Visible [GMB]",
    ],
    "Agoda":     ["OTA Live [Agoda]"],
    "Cleartrip": ["OTA Live [Cleartrip]"],
    "Expedia":   ["OTA Live [Expedia]"],
    "WebApp":    ["Location [FH Web]", "Photos Q&A [FH Web]", "Amenities & RLD [FH]"],
    "PL": [
        "Parallel Listing [MMT]", "Parallel Listing [BDC]",
        "Parallel Listing [GMB]", "Parallel Listing [GI]",
    ],
}

IDENTITY_COLS = ["FH", "Property Name", "Property City", "Category (A/B/C)", "FH Status", "Remarks"]

ota_cols = [c for c in OTA_BULK_COLS.get(selected_ota, []) if c in df.columns]
id_cols  = [c for c in IDENTITY_COLS if c in df.columns]

OTA_FACTOR_GROUPS = {
    "MMT/GI":    {"OTA Live": ["OTA Live [MMT/GI]"], "Location": ["Location [MMT]", "Location [GI]"], "Photos Q&A": ["Photos Q&A [MMT]", "Photos Q&A [GI]"], "Amenities": ["Amenities & RLD [MMT]", "Amenities & RLD [GI]"]},
    "BDC":       {"OTA Live": ["OTA Live [BDC]"], "Location": ["Location [BDC]"], "Photos Q&A": ["Photos Q&A [BDC]"], "Amenities": ["Amenities & RLD [BDC]"]},
    "GMB":       {"OTA Live": ["OTA Live [GMB]"], "Location": ["Location [GMB]"], "Photos Q&A": ["Photos Q&A [GMB]"]},
    "Agoda":     {"OTA Live": ["OTA Live [Agoda]"]},
    "Cleartrip": {"OTA Live": ["OTA Live [Cleartrip]"]},
    "Expedia":   {"OTA Live": ["OTA Live [Expedia]"]},
    "WebApp":    {"Location": ["Location [FH Web]"], "Photos Q&A": ["Photos Q&A [FH Web]"], "Amenities": ["Amenities & RLD [FH]"]},
    "PL":        {"Parallel": ["Parallel Listing [MMT]", "Parallel Listing [BDC]", "Parallel Listing [GMB]", "Parallel Listing [GI]"]},
}
factor_groups     = OTA_FACTOR_GROUPS.get(selected_ota, {})
all_check_cols    = [c for cols in factor_groups.values() for c in cols if c in df.columns]
available_factors = [f for f, cols in factor_groups.items() if any(c in df.columns for c in cols)]

ota_key = selected_ota.replace("/", "_")

# ── Filters ────────────────────────────────────────────────────────────
with st.container(border=True):
    st.markdown('<div class="rad-card-title">🔎 Find Pending Properties</div>', unsafe_allow_html=True)
    pf1, pf2, pf3, pf4 = st.columns(4)
    with pf1:
        cats        = ["All"] + sorted(df["Category (A/B/C)"].dropna().unique().tolist())
        pf_category = st.selectbox("Category", cats, key=f"pf_cat_{ota_key}")
    with pf2:
        pf_status   = st.selectbox("FH Status", ["Live Only", "All", "Churned", "SoldOut"], key=f"pf_status_{ota_key}")
    with pf3:
        factor_opts = ["Any Pending"] + available_factors
        pf_factor   = st.selectbox("Pending in", factor_opts, key=f"pf_factor_{ota_key}")
    with pf4:
        cities  = ["All"] + sorted(df["Property City"].dropna().unique().tolist())
        pf_city = st.selectbox("City", cities, key=f"pf_city_{ota_key}")

# ── Build filtered dataframe ───────────────────────────────────────────
work_df = df.copy()
if pf_status == "Live Only":
    if "FH Status" in work_df.columns:
        work_df = work_df[work_df["FH Status"].str.strip().str.lower() == "live"]
elif pf_status != "All":
    if "FH Status" in work_df.columns:
        work_df = work_df[work_df["FH Status"] == pf_status]
if pf_category != "All" and "Category (A/B/C)" in work_df.columns:
    work_df = work_df[work_df["Category (A/B/C)"] == pf_category]
if pf_city != "All" and "Property City" in work_df.columns:
    work_df = work_df[work_df["Property City"] == pf_city]

if pf_factor == "Any Pending":
    check_cols = all_check_cols
else:
    check_cols = [c for c in factor_groups.get(pf_factor, []) if c in work_df.columns]

def is_pending(row):
    if not check_cols:
        return False
    return any(str(row.get(c, "")).strip().lower() != "check" for c in check_cols)

work_df["_pending"] = work_df.apply(is_pending, axis=1)
cat_order = {"A": 0, "B": 1, "C": 2}
if "Category (A/B/C)" in work_df.columns:
    work_df["_cat_order"] = work_df["Category (A/B/C)"].map(
        lambda x: cat_order.get(str(x).strip().upper(), 99)
    )
else:
    work_df["_cat_order"] = 99

work_df = work_df.sort_values(
    ["_pending", "_cat_order", "FH"], ascending=[False, True, True]
).reset_index(drop=True)

total_pending = int(work_df["_pending"].sum())
badge_col = "#EF4444" if total_pending > 0 else "#10B981"
st.markdown(
    f'<div style="display:inline-flex;align-items:center;gap:8px;background:{badge_col}18;'
    f'border:1px solid {badge_col}44;border-radius:8px;padding:6px 14px;margin:8px 0 16px;">'
    f'<span style="color:{badge_col};font-weight:600;font-size:13px;">'
    f'{"⏳" if total_pending > 0 else "✅"} {total_pending} pending propert{"ies" if total_pending != 1 else "y"}'
    f'</span></div>',
    unsafe_allow_html=True,
)

show_cols  = id_cols + ota_cols
keep_cols  = [c for c in show_cols if c in work_df.columns]
table_data = work_df[keep_cols + ["_row_index", "_pending"]].copy()

# ── DEDUP FIX: assign a per-appearance serial to each row ─────────────
# Root cause of StreamlitDuplicateElementKey: same FH ID can appear in
# multiple rows (e.g. duplicate sheet entries). Adding a serial counter
# makes every widget key globally unique regardless of FH ID duplicates.
_fh_seen: dict = {}
_row_serials: list = []
for fh_val in table_data["FH"].astype(str).str.strip():
    _fh_seen[fh_val] = _fh_seen.get(fh_val, -1) + 1
    _row_serials.append(_fh_seen[fh_val])
table_data = table_data.copy()
table_data["_serial"] = _row_serials


# ══════════════════════════════════════════════════════════════════════
# REMINDER DIALOG
# ══════════════════════════════════════════════════════════════════════
def _show_reminder_dialog(edit_key, fh_id, prop_name, non_check_cols, orig_row):
    min_date = date.today() + timedelta(days=1)
    st.markdown(f"""
    <div style="background:#FFF9E6;border:2px solid #F59E0B;border-radius:12px;
        padding:16px 20px;margin:8px 0 12px;">
        <div style="font-size:15px;font-weight:700;color:#92400E;margin-bottom:4px;">
            ⚠️ Set Recheck Reminder for <span style="color:#5B5FEF;">{prop_name}</span>
        </div>
        <div style="font-size:12px;color:#78350F;margin-bottom:10px;">
            The following columns are <b>not marked Check</b>. Please set a reminder date before closing editing.
        </div>
        <div style="display:flex;flex-wrap:wrap;gap:4px;">
            {"".join(
                f'<span style="background:#FEE2E2;color:#DC2626;padding:2px 8px;border-radius:4px;'
                f'font-size:11px;font-weight:600;">{c}</span>'
                for c in non_check_cols
            )}
        </div>
    </div>""", unsafe_allow_html=True)

    chosen = st.date_input(
        "📅 Recheck Reminder Date *",
        value=st.session_state.reminder_dates.get(edit_key, min_date),
        min_value=min_date,
        key=f"rdlg_date_{edit_key}",
    )
    st.session_state.reminder_dates[edit_key] = chosen

    c1, c2, _ = st.columns([1, 1, 3])
    with c1:
        if st.button("✅ Set & Close", key=f"rdlg_confirm_{edit_key}", type="primary", use_container_width=True):
            for col_name in non_check_cols:
                col_val = str(orig_row.get(col_name, "")).strip()
                if edit_key in st.session_state.row_edits:
                    col_val = st.session_state.row_edits[edit_key].get(col_name, col_val)
                try:
                    from utils.sheets import _ensure_reminder_sheet
                    from datetime import datetime
                    ws = _ensure_reminder_sheet()
                    ws.append_row([
                        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        chosen.strftime("%Y-%m-%d"),
                        username, fh_id, prop_name, col_name, col_val, "Pending", "",
                    ])
                except Exception as e:
                    st.warning(f"Could not write reminder for {col_name}: {e}")
            st.session_state.row_editing[edit_key]    = False
            st.session_state.remind_dialog_fh         = None
            st.session_state.reminder_needed.pop(edit_key, None)
            st.rerun()
    with c2:
        if st.button("✖ Cancel", key=f"rdlg_cancel_{edit_key}", use_container_width=True):
            st.session_state.row_editing[edit_key]   = True
            st.session_state.remind_dialog_fh        = None
            st.session_state.reminder_needed.pop(edit_key, None)
            st.rerun()


# ══════════════════════════════════════════════════════════════════════
# TABLE — sticky header + scrollable body (12 rows visible at a time)
# ══════════════════════════════════════════════════════════════════════

readonly_ota_cols = [c for c in ota_cols if c in REVIEW_RATING_COLS or c in PARALLEL_LISTING_COLS]
frozen_id_cols    = ["FH", "Property Name", "Property City"]
extra_id_cols     = [c for c in id_cols if c not in frozen_id_cols and c in table_data.columns]

edited_count = len([k for k, edits in st.session_state.row_edits.items() if edits])
if edited_count:
    st.markdown(
        f'<div style="display:inline-flex;align-items:center;gap:8px;background:#EEF6FF;'
        f'border:1px solid #5B5FEF44;border-radius:8px;padding:6px 14px;margin-bottom:8px;">'
        f'<span style="color:#5B5FEF;font-weight:600;font-size:13px;">'
        f'✏️ {edited_count} propert{"ies" if edited_count!=1 else "y"} with unsaved changes</span>'
        f'</div>',
        unsafe_allow_html=True,
    )

# helpers
def _short_label(col):
    return (col
        .replace("OTA Live ", "").replace("Parallel Listing ", "PL ")
        .replace("Location ", "Loc ").replace("Photos Q&A ", "📷 ")
        .replace("Amenities & RLD ", "Amen ").replace("Review | Rating ", "⭐ ")
        .replace("OTA Price Visible ", "Price ")
    )

def _badge_html(val):
    color = STATUS_COLORS.get(str(val).strip(), "#94A3B8")
    v     = str(val).strip()
    if not v:
        return '<span style="color:#9CA3AF;font-size:12px;">—</span>'
    return (f'<span style="background:{color};color:#fff;padding:2px 8px;'
            f'border-radius:20px;font-size:11px;font-weight:600;white-space:nowrap;">{v}</span>')

def _cv(edit_key, col, orig_row):
    return st.session_state.row_edits.get(edit_key, {}).get(col, str(orig_row.get(col, "")).strip())

# Column ratios
_W = {"edit": 52, "FH": 80, "Property Name": 160, "Property City": 100,
      "Category (A/B/C)": 88, "FH Status": 72, "Remarks": 130, "_ota": 100}
all_display_cols = frozen_id_cols + extra_id_cols + ota_cols
_widths  = [_W["edit"]] + [_W.get(c, _W["_ota"]) for c in all_display_cols]
_total_w = sum(_widths)
_ratios  = [w / _total_w for w in _widths]

# 12 rows visible → ~432 px scroll box
ROW_H      = 36
VISIBLE_N  = 12
BODY_MAX_H = ROW_H * VISIBLE_N

st.markdown(f"""
<style>
[data-testid="stTooltipIcon"] {{ display:none !important; }}

.de-hcell {{
    font-size: 10.5px; font-weight: 700; color: #6B7280;
    text-transform: uppercase; letter-spacing: 0.4px;
    padding: 8px 4px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
    background: #F2F3F8; border-bottom: 2px solid var(--border);
}}

/* Outer wrapper — rounded border around the whole table */
.de-table-outer {{
    border: 1px solid var(--border);
    border-radius: 10px;
    overflow: hidden;
    margin-bottom: 12px;
    background: var(--bg-card);
}}

/* Scrollable body — shows ~12 rows then scrolls */
.de-body-wrap {{
    overflow-y: auto;
    overflow-x: hidden;
    max-height: {BODY_MAX_H}px;
    background: var(--bg-card);
}}

.de-row {{ border-bottom: 1px solid var(--border-light); background: var(--bg-card); }}
.de-row:last-child {{ border-bottom: none; }}
.de-row:hover {{ background: #F5F6FB !important; }}
.de-row.pend  {{ background: #FFFBEB !important; }}
.de-row.edit  {{ background: #EEF6FF !important; border-left: 3px solid #5B5FEF; }}
.de-row.done  {{ background: #F0FDF4 !important; border-left: 3px solid #10B981; }}

.de-cell {{
    padding: 5px 6px; display: flex; align-items: center;
    min-height: {ROW_H}px; overflow: hidden;
}}
.de-cell-txt {{ font-size: 12px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }}

div[data-testid="stToggle"] {{ margin: 0 !important; padding: 0 !important; }}
div[data-testid="stToggle"] label {{ margin: 0 !important; }}
div[data-testid="stToggle"] p {{ display: none !important; }}

div[data-testid="stSelectbox"] {{ margin: 0 !important; }}
div[data-testid="stSelectbox"] > label {{ display: none !important; }}
div[data-testid="stSelectbox"] > div {{ min-height: 30px !important; }}
</style>
""", unsafe_allow_html=True)

# ── Reminder dialog shown ABOVE the table (outside scroll) ────────────
if st.session_state.remind_dialog_fh:
    _edit_key = st.session_state.remind_dialog_fh
    # edit_key format: "{fh_id}_{serial}"
    _parts     = _edit_key.rsplit("_", 1)
    _rfh_id    = _parts[0]
    _rserial   = _parts[1] if len(_parts) > 1 else "0"
    _rrows = table_data[
        (table_data["FH"].astype(str).str.strip() == _rfh_id) &
        (table_data["_serial"].astype(str) == _rserial)
    ]
    if not _rrows.empty:
        _rrow = _rrows.iloc[0]
        _show_reminder_dialog(
            _edit_key,
            _rfh_id,
            str(_rrow.get("Property Name", "")).strip(),
            st.session_state.reminder_needed.get(_edit_key, []),
            _rrow,
        )

# ── Table: header (sticky) + scrollable body ──────────────────────────
st.markdown('<div class="de-table-outer">', unsafe_allow_html=True)

# Header row — outside scroll wrapper so it stays pinned
hdr_cols  = st.columns(_ratios)
col_names = ["Edit"] + all_display_cols
for hc, name in zip(hdr_cols, col_names):
    hc.markdown(
        f'<div class="de-hcell">{"Edit" if name == "Edit" else _short_label(name)}</div>',
        unsafe_allow_html=True,
    )

st.markdown('<div class="de-body-wrap">', unsafe_allow_html=True)

for _, orig_row in table_data.iterrows():
    fh_id    = str(orig_row.get("FH", "")).strip()
    serial   = int(orig_row.get("_serial", 0))
    # ── THE FIX: edit_key always unique because serial differentiates
    #    duplicate FH IDs.  e.g. "1012971_0", "1012971_1"
    edit_key = f"{fh_id}_{serial}"

    prop_name  = str(orig_row.get("Property Name", "")).strip()
    city       = str(orig_row.get("Property City", "")).strip()
    is_pend    = bool(orig_row.get("_pending", False))
    is_editing = st.session_state.row_editing.get(edit_key, False)
    has_edits  = bool(st.session_state.row_edits.get(edit_key))

    # Skip row while reminder dialog is open for it (shown above table)
    if st.session_state.remind_dialog_fh == edit_key:
        continue

    row_cls = "edit" if is_editing else ("done" if has_edits else ("pend" if is_pend else ""))
    st.markdown(f'<div class="de-row {row_cls}">', unsafe_allow_html=True)

    cols = st.columns(_ratios)

    # Col 0: toggle  — key uses edit_key + ota_key → always unique
    with cols[0]:
        st.markdown('<div class="de-cell" style="justify-content:center;">', unsafe_allow_html=True)
        new_ed = st.toggle(
            "", value=is_editing,
            key=f"tog_{edit_key}_{ota_key}",
            label_visibility="collapsed",
        )
        st.markdown('</div>', unsafe_allow_html=True)

        if is_editing and not new_ed:
            non_check = [
                c for c in all_check_cols
                if str(_cv(edit_key, c, orig_row)).lower() not in ("check", "")
                and str(_cv(edit_key, c, orig_row)).strip() != ""
            ]
            if non_check:
                st.session_state.row_editing[edit_key]     = True
                st.session_state.reminder_needed[edit_key] = non_check
                st.session_state.remind_dialog_fh           = edit_key
                st.rerun()
            else:
                st.session_state.row_editing[edit_key] = False
                st.rerun()
        elif not is_editing and new_ed:
            st.session_state.row_editing[edit_key] = True
            st.rerun()

    # Cols 1-3: frozen identity
    with cols[1]:
        st.markdown(f'<div class="de-cell"><span class="de-cell-txt" style="font-weight:700;color:#5B5FEF;">{fh_id}</span></div>', unsafe_allow_html=True)
    with cols[2]:
        st.markdown(f'<div class="de-cell"><span class="de-cell-txt" style="font-weight:600;">{prop_name}</span></div>', unsafe_allow_html=True)
    with cols[3]:
        st.markdown(f'<div class="de-cell"><span class="de-cell-txt" style="color:#6B7280;">{city}</span></div>', unsafe_allow_html=True)

    # Extra identity cols
    for ci, col_name in enumerate(extra_id_cols):
        with cols[4 + ci]:
            val = str(orig_row.get(col_name, "")).strip()
            if col_name == "FH Status":
                st.markdown(f'<div class="de-cell">{_badge_html(val)}</div>', unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="de-cell"><span class="de-cell-txt" style="color:#6B7280;">{val or "—"}</span></div>', unsafe_allow_html=True)

    # OTA cols
    ota_start = 4 + len(extra_id_cols)
    for ci, col_name in enumerate(ota_cols):
        with cols[ota_start + ci]:
            current_val = _cv(edit_key, col_name, orig_row)
            is_ro = col_name in readonly_ota_cols

            if is_editing and not is_ro:
                dk   = COL_DROPDOWN_MAP.get(col_name)
                opts = DROPDOWNS.get(dk, []) if dk else []
                if opts:
                    idx    = opts.index(current_val) if current_val in opts else 0
                    chosen = st.selectbox(
                        "", opts, index=idx,
                        key=f"ep_{edit_key}_{col_name}_{ota_key}",
                        label_visibility="collapsed",
                    )
                    orig_v = str(orig_row.get(col_name, "")).strip()
                    if chosen != orig_v:
                        st.session_state.row_edits.setdefault(edit_key, {})[col_name] = chosen
                    else:
                        st.session_state.row_edits.get(edit_key, {}).pop(col_name, None)
                        if edit_key in st.session_state.row_edits and not st.session_state.row_edits[edit_key]:
                            del st.session_state.row_edits[edit_key]
                else:
                    new_v  = st.text_input(
                        "", value=current_val,
                        key=f"ep_{edit_key}_{col_name}_{ota_key}",
                        label_visibility="collapsed",
                    )
                    orig_v = str(orig_row.get(col_name, "")).strip()
                    if new_v != orig_v:
                        st.session_state.row_edits.setdefault(edit_key, {})[col_name] = new_v
                    else:
                        st.session_state.row_edits.get(edit_key, {}).pop(col_name, None)
            else:
                st.markdown(f'<div class="de-cell">{_badge_html(current_val)}</div>', unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)  # close .de-row

st.markdown('</div>', unsafe_allow_html=True)  # close .de-body-wrap
st.markdown('</div>', unsafe_allow_html=True)  # close .de-table-outer


# ══════════════════════════════════════════════════════════════════════
# SAVE CHANGES BUTTON
# ══════════════════════════════════════════════════════════════════════
st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

total_edits   = sum(len(v) for v in st.session_state.row_edits.values())
has_any_edits = total_edits > 0

save_col, refresh_col, _ = st.columns([2, 1.5, 6])

with save_col:
    save_clicked = st.button(
        f"💾 Save Changes ({edited_count} {'property' if edited_count == 1 else 'properties'})",
        type="primary",
        disabled=not has_any_edits,
        use_container_width=True,
        key="global_save_btn",
    )

with refresh_col:
    if st.button("🔄 Refresh Data", key="de_refresh", use_container_width=True):
        force_reload()
        st.rerun()

if save_clicked and has_any_edits:
    ota_info = OTA_COLUMN_MAP.get(selected_ota, {})
    live_col = ota_info.get("live_col", "")
    dep_cols = ota_info.get("dependent", [])

    saved_count  = 0
    error_count  = 0
    progress_bar = st.progress(0)

    all_edit_keys = list(st.session_state.row_edits.keys())
    total_keys    = len(all_edit_keys)

    for idx_s, edit_key in enumerate(all_edit_keys):
        updates = dict(st.session_state.row_edits[edit_key])
        if not updates:
            continue

        # Recover fh_id and serial from edit_key = "{fh_id}_{serial}"
        _parts     = edit_key.rsplit("_", 1)
        fh_id      = _parts[0]
        serial_str = _parts[1] if len(_parts) > 1 else "0"

        orig_rows = table_data[
            (table_data["FH"].astype(str).str.strip() == fh_id) &
            (table_data["_serial"].astype(str) == serial_str)
        ]
        if orig_rows.empty:
            orig_rows = df[df["FH"].astype(str).str.strip() == fh_id]
        if orig_rows.empty:
            continue

        orig_row  = orig_rows.iloc[0]
        row_index = int(orig_row.get("_row_index", 0))
        prop_name = str(orig_row.get("Property Name", "")).strip()

        if live_col and updates.get(live_col) == "Not Live":
            for dep in dep_cols:
                dk = COL_DROPDOWN_MAP.get(dep, "")
                if "Not Live" in DROPDOWNS.get(dk, []):
                    updates[dep] = "Not Live"

        old_values = {c: str(orig_row.get(c, "")).strip() for c in updates}

        try:
            save_entry(
                row_index=row_index,
                fh_id=fh_id,
                prop_name=prop_name,
                username=username,
                ota=selected_ota,
                updates=updates,
                old_values=old_values,
            )
            saved_count += 1
        except Exception as e:
            error_count += 1
            st.error(f"❌ Error saving {prop_name}: {e}")

        progress_bar.progress((idx_s + 1) / total_keys)

    progress_bar.empty()

    if saved_count > 0:
        st.success(f"✅ Saved changes for **{saved_count}** propert{'ies' if saved_count != 1 else 'y'}!")
        st.session_state.row_edits   = {}
        st.session_state.row_editing = {}
        st.session_state.saved_fhs   = set()
        force_reload()
        st.rerun()
    elif error_count == 0:
        st.info("ℹ️ No changes detected.")