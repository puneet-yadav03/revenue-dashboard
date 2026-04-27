# ─────────────────────────────────────────────
#  utils/sheets.py  —  Google Sheets connector
# ─────────────────────────────────────────────
import streamlit as st
import gspread
import pandas as pd
from google.oauth2.service_account import Credentials
from datetime import datetime, timezone, timedelta
import os

# IST = UTC + 5:30
_IST = timezone(timedelta(hours=5, minutes=30))

def _now_ist() -> str:
    """Return current IST time as a plain string Google Sheets won't auto-parse."""
    return datetime.now(_IST).strftime("%Y-%m-%d %H:%M:%S")

from utils.config import (
    SHEET_ID, WORKSHEET_NAME,
    AUDIT_SHEET_NAME, REMINDER_SHEET_NAME, TASK_SHEET_NAME,
    REMINDER_TRIGGER_COLS,
)

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

CACHE_TTL = 300  # 5 minutes

CREDENTIALS_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "Credentials.json")

USERS_SHEET_NAME = "Users"

# ── Auth ──────────────────────────────────────────────────────────────
@st.cache_resource
def get_client():
    try:
        # Cloud deployment: read from Streamlit secrets
        creds = Credentials.from_service_account_info(
            st.secrets["gcp_service_account"], scopes=SCOPES
        )
    except Exception:
        # Local development: read from Credentials.json file
        creds = Credentials.from_service_account_file(
            CREDENTIALS_PATH, scopes=SCOPES
        )
    return gspread.authorize(creds)


def get_spreadsheet():
    return get_client().open_by_key(SHEET_ID)


# ── Header normalisation ──────────────────────────────────────────────
import re as _re

def _normalize_header(h: str) -> str:
    h = h.replace("\n", " ").strip()
    h = _re.sub(r"\s*/\s*", "/", h)
    h = _re.sub(r"  +", " ", h)
    return h


# ── Main data ─────────────────────────────────────────────────────────
@st.cache_data(ttl=CACHE_TTL)
def load_data() -> pd.DataFrame:
    ws = get_spreadsheet().worksheet(WORKSHEET_NAME)
    raw = ws.get_all_values()
    if len(raw) < 2:
        return pd.DataFrame()
    headers = [_normalize_header(h) for h in raw[1]]
    data = raw[2:]
    df = pd.DataFrame(data, columns=headers)
    df = df.loc[:, df.columns != ""]
    df = df.loc[:, ~df.columns.duplicated()]
    if "FH" in df.columns:
        df = df[df["FH"].str.strip() != ""]
    # Normalize string columns to strip whitespace
    for col in df.columns:
        if df[col].dtype == object:
            df[col] = df[col].str.strip()
    df["_row_index"] = list(range(3, 3 + len(df)))
    return df


def force_reload():
    load_data.clear()
    load_dashboard_data.clear()
    st.cache_data.clear()


# ── Dashboard sheet ───────────────────────────────────────────────────
@st.cache_data(ttl=CACHE_TTL)
def load_dashboard_data() -> list:
    ws = get_spreadsheet().worksheet("Dashboard")
    raw = ws.get_all_values()
    if not raw:
        return []

    num_rows = len(raw)
    num_cols = max(len(r) for r in raw)
    padded = [r + [""] * (num_cols - len(r)) for r in raw]

    def c(ri, ci):
        if 0 <= ri < num_rows and 0 <= ci < num_cols:
            return padded[ri][ci].strip()
        return ""

    months_positions = []
    for ri in range(num_rows):
        for ci in range(num_cols):
            if c(ri, ci) == "Months":
                months_positions.append((ri, ci))

    blocks = []
    for anchor_ri, anchor_ci in months_positions:
        owner_name = ""
        if anchor_ri > 0:
            search_row = anchor_ri - 1
            candidate = c(search_row, anchor_ci)
            if candidate and candidate != "Months":
                owner_name = candidate
            else:
                for offset in range(1, 8):
                    for delta in (-offset, offset):
                        candidate = c(search_row, anchor_ci + delta)
                        if candidate and candidate != "Months":
                            owner_name = candidate
                            break
                    if owner_name:
                        break
        if not owner_name:
            for look_ci in range(anchor_ci - 1, max(anchor_ci - 8, -1), -1):
                candidate = c(anchor_ri, look_ci)
                if candidate and candidate != "Months":
                    owner_name = candidate
                    break
        if not owner_name:
            owner_name = f"Table @ row{anchor_ri+1} col{anchor_ci+1}"

        col_boundary = num_cols
        for (other_ri, other_ci) in months_positions:
            if other_ri == anchor_ri and other_ci > anchor_ci:
                col_boundary = min(col_boundary, other_ci)

        col_headers = []
        col_indices = []
        for hci in range(anchor_ci + 1, col_boundary):
            h = c(anchor_ri, hci)
            if h:
                col_headers.append(h)
                col_indices.append(hci)
        if not col_headers:
            continue

        next_band_row = num_rows
        for (other_ri, _) in months_positions:
            if other_ri > anchor_ri:
                next_band_row = min(next_band_row, other_ri)

        data_rows = []
        totals    = {h: None for h in col_headers}
        extras    = {}

        for data_ri in range(anchor_ri + 1, next_band_row):
            month_val = c(data_ri, anchor_ci)
            if not month_val:
                for hi, hci in enumerate(col_indices):
                    v = c(data_ri, hci)
                    if v and totals[col_headers[hi]] is None:
                        try:    totals[col_headers[hi]] = int(v)
                        except: totals[col_headers[hi]] = v
                continue
            if "-" in month_val:
                row_dict = {"Month": month_val}
                for hi, hci in enumerate(col_indices):
                    v = c(data_ri, hci)
                    try:    row_dict[col_headers[hi]] = int(v) if v else 0
                    except: row_dict[col_headers[hi]] = v if v else 0
                data_rows.append(row_dict)
            else:
                label = month_val
                for hci in col_indices:
                    v = c(data_ri, hci)
                    if v:
                        try:    extras[label] = int(v)
                        except: extras[label] = v
                        break

        for h in col_headers:
            if totals[h] is None:
                totals[h] = sum(r.get(h, 0) for r in data_rows if isinstance(r.get(h, 0), (int, float)))

        if " - " in owner_name:
            parts = owner_name.split(" - ", 1)
            person, channel = parts[0].strip(), parts[1].strip()
        else:
            person, channel = owner_name.strip(), ""

        if data_rows:
            blocks.append({
                "owner": owner_name, "person": person, "channel": channel,
                "columns": col_headers, "rows": data_rows,
                "totals": totals, "extras": extras,
            })
    return blocks


# ── Write a single cell ───────────────────────────────────────────────
def update_cell(row_index: int, col_name: str, value: str):
    ws = get_spreadsheet().worksheet(WORKSHEET_NAME)
    headers_row = [_normalize_header(h) for h in ws.row_values(2)]
    col_name_norm = _normalize_header(col_name)
    try:
        col_index = headers_row.index(col_name_norm) + 1
    except ValueError:
        raise ValueError(f"Column '{col_name}' not found in sheet headers.")
    ws.update_cell(row_index, col_index, value)


def batch_update(row_index: int, updates: dict) -> list:
    ws = get_spreadsheet().worksheet(WORKSHEET_NAME)
    headers_row = [_normalize_header(h) for h in ws.row_values(2)]
    cell_list, skipped = [], []
    for col_name, value in updates.items():
        col_name_norm = _normalize_header(col_name)
        try:
            col_index = headers_row.index(col_name_norm) + 1
            cell_list.append(gspread.Cell(row_index, col_index, value))
        except ValueError:
            skipped.append(col_name)
    if cell_list:
        ws.update_cells(cell_list, value_input_option="USER_ENTERED")
    return skipped


# ── Audit log ─────────────────────────────────────────────────────────
def _ensure_audit_sheet():
    ss = get_spreadsheet()
    try:
        return ss.worksheet(AUDIT_SHEET_NAME)
    except Exception:
        ws = ss.add_worksheet(title=AUDIT_SHEET_NAME, rows=10000, cols=10)
        ws.append_row(["Timestamp","Username","FH ID","Property Name","OTA","Column","Old Value","New Value","Action","Notes"])
        return ws


def write_audit_log(username, fh_id, prop_name, ota, col, old_val, new_val):
    ws = _ensure_audit_sheet()
    ws.append_row([
        "'" + _now_ist(),   # leading apostrophe forces plain text in Sheets
        username, fh_id, prop_name, ota, col,
        str(old_val), str(new_val), "Update", ""
    ], value_input_option="RAW")


@st.cache_data(ttl=60)
def load_audit_log() -> pd.DataFrame:
    _cols = ["Timestamp","Username","FH ID","Property Name","OTA","Column","Old Value","New Value","Action","Notes"]
    try:
        ws   = get_spreadsheet().worksheet(AUDIT_SHEET_NAME)
        data = ws.get_all_records()
        return pd.DataFrame(data) if data else pd.DataFrame(columns=_cols)
    except Exception:
        return pd.DataFrame(columns=_cols)


# ── Reminders ─────────────────────────────────────────────────────────
def _ensure_reminder_sheet():
    ss = get_spreadsheet()
    try:
        return ss.worksheet(REMINDER_SHEET_NAME)
    except Exception:
        ws = ss.add_worksheet(title=REMINDER_SHEET_NAME, rows=10000, cols=8)
        ws.append_row(["Timestamp","Username","FH ID","Property Name","Column","Value","Due Date","Status"])
        return ws


def write_reminder(username, fh_id, prop_name, col, value):
    ws = _ensure_reminder_sheet()
    ws.append_row([
        "'" + _now_ist(),   # leading apostrophe forces plain text in Sheets
        username, fh_id, prop_name, col, str(value), "", "Pending"
    ], value_input_option="RAW")


@st.cache_data(ttl=60)
def load_reminders() -> pd.DataFrame:
    _cols = ["Timestamp","Username","FH ID","Property Name","Column","Value","Due Date","Status"]
    try:
        ws   = get_spreadsheet().worksheet(REMINDER_SHEET_NAME)
        data = ws.get_all_records()
        return pd.DataFrame(data) if data else pd.DataFrame(columns=_cols)
    except Exception:
        return pd.DataFrame(columns=_cols)


def resolve_reminder(sheet_row: int):
    ws = get_spreadsheet().worksheet(REMINDER_SHEET_NAME)
    ws.update_cell(sheet_row, 8, "Resolved")


# ── Save entry (main write + audit + reminder) ────────────────────────
def save_entry(row_index: int, updates: dict, username: str,
               fh_id: str, prop_name: str, ota: str,
               old_values: dict | None = None) -> list:
    skipped = batch_update(row_index, updates)
    if old_values is None:
        old_values = {}
    for col, new_val in updates.items():
        if col in skipped: continue
        old_val = old_values.get(col, "")
        if str(new_val) == str(old_val): continue
        write_audit_log(username, fh_id, prop_name, ota, col, old_val, new_val)
        if col in REMINDER_TRIGGER_COLS and str(new_val).strip() not in ("", "Check"):
            write_reminder(username, fh_id, prop_name, col, new_val)
    force_reload()
    return skipped


# ── Tasks ─────────────────────────────────────────────────────────────
def _ensure_task_sheet():
    ss = get_spreadsheet()
    try:
        return ss.worksheet(TASK_SHEET_NAME)
    except Exception:
        ws = ss.add_worksheet(title=TASK_SHEET_NAME, rows=10000, cols=12)
        ws.append_row(["Task ID","Title","Description","Priority","Assigned To","Created By","Created At","Due Date","Status","Closed By","Closed At","Notes"])
        return ws


def write_task(title, description, priority, assigned_to, created_by):
    from datetime import date
    ws = _ensure_task_sheet()
    existing = ws.get_all_records()
    task_id  = f"T{len(existing)+1:04d}"
    ws.append_row([task_id, title, description, priority, assigned_to, created_by,
                   "'" + _now_ist(),
                   "'" + date.today().strftime("%Y-%m-%d"), "Open", "", "", ""],
                  value_input_option="RAW")
    load_tasks.clear()
    return task_id


@st.cache_data(ttl=30)
def load_tasks() -> pd.DataFrame:
    _cols = ["Task ID","Title","Description","Priority","Assigned To","Created By","Created At","Due Date","Status","Closed By","Closed At","Notes"]
    try:
        ws   = get_spreadsheet().worksheet(TASK_SHEET_NAME)
        data = ws.get_all_records()
        return pd.DataFrame(data) if data else pd.DataFrame(columns=_cols)
    except Exception:
        return pd.DataFrame(columns=_cols)


def close_task(task_id, closed_by, notes=""):
    ws = _ensure_task_sheet()
    for i, row in enumerate(ws.get_all_records()):
        if str(row.get("Task ID","")).strip() == str(task_id).strip():
            sheet_row = i + 2
            ws.update_cell(sheet_row, 9,  "Closed")
            ws.update_cell(sheet_row, 10, closed_by)
            ws.update_cell(sheet_row, 11, "'" + _now_ist())
            ws.update_cell(sheet_row, 12, notes)
            load_tasks.clear()
            return True
    return False


# ══════════════════════════════════════════════════════════════════════
# ── Users Sheet ───────────────────────────────────────────────────────
# KEY DESIGN:
#   load_users_sheet()  → @st.cache_data, pure READ, NO side-effects
#   _get_users_ws()     → uncached, handles create/seed, only on writes
#   get_all_users_dict()→ uncached direct read for auth (always fresh)
# ══════════════════════════════════════════════════════════════════════

def _config_users_as_df() -> pd.DataFrame:
    """Return config.py USERS as a DataFrame (fallback)."""
    from utils.config import USERS as D
    return pd.DataFrame([{
        "Username": k, "Password": v["password"], "Role": v["role"],
        "OTAs": ",".join(v.get("otas",[])), "Status": "active", "Created At": "",
    } for k, v in D.items()])


@st.cache_data(ttl=30)
def load_users_sheet() -> pd.DataFrame:
    """
    Cached pure-read of the Users sheet.
    Returns config.py defaults if sheet doesn't exist yet (first run).
    No sheet creation here — that happens lazily on first write.
    """
    try:
        ss = get_spreadsheet()
        try:
            ws = ss.worksheet(USERS_SHEET_NAME)
        except gspread.WorksheetNotFound:
            # Sheet not created yet → return defaults so UI still renders
            return _config_users_as_df()

        all_vals = ws.get_all_values()
        if len(all_vals) < 2:
            return _config_users_as_df()

        headers = all_vals[0]
        rows = []
        for row in all_vals[1:]:
            padded = row + [""] * max(0, len(headers) - len(row))
            d = dict(zip(headers, padded))
            if d.get("Username","").strip():
                rows.append(d)

        if not rows:
            return _config_users_as_df()

        df = pd.DataFrame(rows)
        df["OTAs"]   = df.get("OTAs",   pd.Series(dtype=str)).fillna("").astype(str)
        df["Status"] = df.get("Status", pd.Series(dtype=str)).fillna("active").astype(str)
        return df

    except Exception:
        return _config_users_as_df()


def _get_users_ws():
    """
    Get (or create+seed) the Users worksheet.
    Only called from write operations — never from cached functions.
    """
    ss = get_spreadsheet()
    try:
        ws = ss.worksheet(USERS_SHEET_NAME)
        vals = ws.get_all_values()
        if not vals:
            # Empty sheet — write header + seed
            ws.append_row(["Username","Password","Role","OTAs","Status","Created At"])
            _do_seed(ws)
        return ws
    except gspread.WorksheetNotFound:
        ws = ss.add_worksheet(title=USERS_SHEET_NAME, rows=500, cols=6)
        ws.append_row(["Username","Password","Role","OTAs","Status","Created At"])
        _do_seed(ws)
        return ws


def _do_seed(ws):
    from utils.config import USERS as D
    now  = _now_ist()
    rows = [[k, v["password"], v["role"], ",".join(v.get("otas",[])), "active", now]
            for k, v in D.items()]
    if rows:
        ws.append_rows(rows)


def get_all_users_dict() -> dict:
    """
    Uncached direct read for auth.py — always gets fresh data.
    Falls back to config.py if anything goes wrong.
    """
    try:
        ss = get_spreadsheet()
        try:
            ws = ss.worksheet(USERS_SHEET_NAME)
        except gspread.WorksheetNotFound:
            from utils.config import USERS
            return USERS

        all_vals = ws.get_all_values()
        if len(all_vals) < 2:
            from utils.config import USERS
            return USERS

        headers = all_vals[0]
        users   = {}
        for row in all_vals[1:]:
            padded = row + [""] * max(0, len(headers) - len(row))
            d      = dict(zip(headers, padded))
            uname  = d.get("Username","").strip().lower()
            if not uname:
                continue
            otas_raw = d.get("OTAs","").strip()
            otas = [o.strip() for o in otas_raw.split(",") if o.strip()] if otas_raw else []
            users[uname] = {
                "password": d.get("Password",""),
                "role":     d.get("Role","member"),
                "otas":     otas,
                "status":   d.get("Status","active"),
            }
        return users if users else __import__("utils.config", fromlist=["USERS"]).USERS
    except Exception:
        from utils.config import USERS
        return USERS


def add_user_sheet(username: str, password: str, role: str, otas: list, email: str = "") -> bool:
    """Add new user. Returns False if username already exists."""
    ws       = _get_users_ws()
    all_vals = ws.get_all_values()
    existing = {str(r[0]).strip().lower() for r in all_vals[1:] if r}
    if username.strip().lower() in existing:
        return False
    ws.append_row([
        username.strip().lower(), password, role,
        ",".join(otas), "active",
        "'" + _now_ist(),
        email.strip(),
    ], value_input_option="RAW")
    load_users_sheet.clear()
    return True


def update_user_sheet(username: str, password: str, role: str, otas: list, status: str = "active", email: str = "") -> bool:
    """Update existing user by username."""
    ws       = _get_users_ws()
    all_vals = ws.get_all_values()
    headers  = all_vals[0] if all_vals else []
    for i, row in enumerate(all_vals[1:], start=2):
        if row and str(row[0]).strip().lower() == username.strip().lower():
            ws.update_cell(i, 2, password)
            ws.update_cell(i, 3, role)
            ws.update_cell(i, 4, ",".join(otas))
            ws.update_cell(i, 5, status)
            # Write email to col 7 if header exists, else append
            if "Email ID" in headers:
                ws.update_cell(i, headers.index("Email ID") + 1, email.strip())
            load_users_sheet.clear()
            return True
    return False


def delete_user_sheet(username: str) -> bool:
    """Delete user row by username."""
    ws       = _get_users_ws()
    all_vals = ws.get_all_values()
    for i, row in enumerate(all_vals[1:], start=2):
        if row and str(row[0]).strip().lower() == username.strip().lower():
            ws.delete_rows(i)
            load_users_sheet.clear()
            return True
    return False