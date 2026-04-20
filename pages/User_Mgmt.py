# ─────────────────────────────────────────────
#  pages/User_Mgmt.py  —  User Management (Fully Functional)
# ─────────────────────────────────────────────
import streamlit as st

st.set_page_config(page_title="User Management — Revenue Audit", page_icon="👥", layout="wide")

from utils.auth import require_login, is_admin, current_user
from utils.helpers import render_sidebar, inject_css
from utils.sheets import (
    load_users_sheet, add_user_sheet,
    update_user_sheet, delete_user_sheet,
)

require_login()
if not is_admin():
    st.error("🚫 Admin access only.")
    st.stop()

render_sidebar(active_page="User_Mgmt")

# ── All available OTAs ────────────────────────────────────────────────
ALL_OTAS = ["MMT/GI", "BDC", "GMB", "WebApp", "Agoda", "Expedia", "Cleartrip", "PL"]
ROLES    = ["admin", "member"]

# ── Session state for modals ──────────────────────────────────────────
if "um_action"      not in st.session_state: st.session_state.um_action      = None  # "add"|"edit"|"delete"|"deactivate"
if "um_target_user" not in st.session_state: st.session_state.um_target_user = None
if "um_msg"         not in st.session_state: st.session_state.um_msg         = None  # ("success"|"error", text)

# ── Page header ───────────────────────────────────────────────────────
hcol, bcol = st.columns([5, 1])
with hcol:
    st.markdown("""
    <div class="rad-page-header">
        <div class="rad-page-title">User Management</div>
        <div class="rad-page-subtitle">Add, edit, deactivate, and delete user accounts</div>
    </div>""", unsafe_allow_html=True)
with bcol:
    st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)
    if st.button("➕ Add User", type="primary", use_container_width=True, key="um_open_add"):
        st.session_state.um_action      = "add"
        st.session_state.um_target_user = None
        st.rerun()

# ── Flash message ─────────────────────────────────────────────────────
if st.session_state.um_msg:
    kind, text = st.session_state.um_msg
    if kind == "success":
        st.success(text)
    else:
        st.error(text)
    st.session_state.um_msg = None

# ── Role info cards ───────────────────────────────────────────────────
r1, r2, r3 = st.columns(3)
roles_info = [
    ("Admin",  "#5B5FEF", "Full access",         ["Manage all users", "Edit all data", "View all reports", "System settings"]),
    ("Member", "#8B5CF6", "OTA-scoped access",   ["Edit assigned OTA data", "View own reports", "Manage tasks", "No user management"]),
    ("Viewer", "#94A3B8", "Read-only (planned)",  ["View assigned data", "View reports", "No editing rights", "No admin access"]),
]
for col, (role_name, role_col, role_desc, perms) in zip([r1, r2, r3], roles_info):
    perms_html = "".join(
        f"<div style='font-size:12px;color:var(--text-secondary);margin-bottom:3px;'>• {p}</div>"
        for p in perms
    )
    with col:
        st.markdown(f"""
        <div class="rad-card" style="height:100%;">
            <div style="display:flex;align-items:center;gap:10px;margin-bottom:12px;">
                <div style="width:36px;height:36px;background:{role_col}22;border-radius:50%;
                    display:flex;align-items:center;justify-content:center;font-size:18px;">🛡️</div>
                <div>
                    <div style="font-weight:700;color:var(--text-primary);font-size:15px;">{role_name}</div>
                    <div style="font-size:12px;color:var(--text-secondary);">{role_desc}</div>
                </div>
            </div>
            {perms_html}
        </div>""", unsafe_allow_html=True)

st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════
# ADD USER FORM
# ══════════════════════════════════════════════════════════════════════
if st.session_state.um_action == "add":
    with st.container(border=True):
        st.markdown("### ➕ Add New User")
        c1, c2 = st.columns(2)
        with c1:
            new_username = st.text_input("Username *", placeholder="e.g. john.doe", key="um_new_uname").strip().lower()
            new_password = st.text_input("Password *", type="password", key="um_new_pass")
            new_email    = st.text_input("Email", placeholder="e.g. john.doe@fabhotels.com", key="um_new_email").strip()
        with c2:
            new_role = st.selectbox("Role *", ROLES, key="um_new_role")
            new_otas = st.multiselect("Assign OTAs", ALL_OTAS, key="um_new_otas",
                                      help="Leave empty for admin (all access)")

        btn1, btn2 = st.columns([1, 5])
        with btn1:
            if st.button("✅ Create User", type="primary", key="um_do_add"):
                if not new_username or not new_password:
                    st.error("Username and password are required.")
                elif len(new_password) < 6:
                    st.error("Password must be at least 6 characters.")
                elif new_email and "@" not in new_email:
                    st.error("Please enter a valid email address.")
                else:
                    try:
                        ok = add_user_sheet(new_username, new_password, new_role, new_otas, new_email)
                        if ok:
                            st.session_state.um_msg    = ("success", f"✅ User '{new_username}' created successfully!")
                            st.session_state.um_action = None
                            st.rerun()
                        else:
                            st.error(f"Username '{new_username}' already exists.")
                    except Exception as e:
                        st.error(f"Error creating user: {e}")
        with btn2:
            if st.button("✖ Cancel", key="um_cancel_add"):
                st.session_state.um_action = None
                st.rerun()

# ══════════════════════════════════════════════════════════════════════
# EDIT USER FORM
# ══════════════════════════════════════════════════════════════════════
elif st.session_state.um_action == "edit" and st.session_state.um_target_user:
    target = st.session_state.um_target_user
    users_df = load_users_sheet()
    user_row = users_df[users_df["Username"].str.lower() == target.lower()]

    if user_row.empty:
        st.error("User not found.")
        st.session_state.um_action = None
    else:
        row = user_row.iloc[0]
        existing_otas  = [o.strip() for o in str(row.get("OTAs","")).split(",") if o.strip()]
        existing_email = str(row.get("Email ID","")).strip()

        with st.container(border=True):
            st.markdown(f"### ✏️ Edit User: `{target}`")
            c1, c2 = st.columns(2)
            with c1:
                edit_password = st.text_input("New Password (leave blank to keep)", type="password", key="um_edit_pass")
                edit_email    = st.text_input("Email", value=existing_email,
                                              placeholder="e.g. john.doe@fabhotels.com", key="um_edit_email").strip()
                edit_status   = st.selectbox("Account Status", ["active", "inactive"],
                                             index=0 if row.get("Status","active") == "active" else 1,
                                             key="um_edit_status")
            with c2:
                edit_role = st.selectbox("Role", ROLES,
                                         index=ROLES.index(row.get("Role","member")) if row.get("Role","member") in ROLES else 1,
                                         key="um_edit_role")
                edit_otas = st.multiselect("Assign OTAs", ALL_OTAS,
                                           default=[o for o in existing_otas if o in ALL_OTAS],
                                           key="um_edit_otas")

            btn1, btn2 = st.columns([1, 5])
            with btn1:
                if st.button("💾 Save Changes", type="primary", key="um_do_edit"):
                    final_password = edit_password if edit_password else str(row.get("Password",""))
                    if edit_password and len(edit_password) < 6:
                        st.error("Password must be at least 6 characters.")
                    elif edit_email and "@" not in edit_email:
                        st.error("Please enter a valid email address.")
                    else:
                        try:
                            ok = update_user_sheet(target, final_password, edit_role, edit_otas,
                                                   edit_status, edit_email)
                            if ok:
                                st.session_state.um_msg    = ("success", f"✅ User '{target}' updated successfully!")
                                st.session_state.um_action = None
                                st.rerun()
                            else:
                                st.error("User not found in sheet.")
                        except Exception as e:
                            st.error(f"Error updating user: {e}")
            with btn2:
                if st.button("✖ Cancel", key="um_cancel_edit"):
                    st.session_state.um_action = None
                    st.rerun()

# ══════════════════════════════════════════════════════════════════════
# DELETE CONFIRM
# ══════════════════════════════════════════════════════════════════════
elif st.session_state.um_action == "delete" and st.session_state.um_target_user:
    target = st.session_state.um_target_user
    with st.container(border=True):
        st.markdown(f"### 🗑️ Delete User: `{target}`")
        st.warning(f"⚠️ This will **permanently delete** the user `{target}`. This cannot be undone.")
        b1, b2, _ = st.columns([1, 1, 4])
        with b1:
            if st.button("🗑️ Yes, Delete", type="primary", key="um_do_delete"):
                if target == current_user():
                    st.error("You cannot delete your own account.")
                else:
                    try:
                        ok = delete_user_sheet(target)
                        if ok:
                            st.session_state.um_msg    = ("success", f"🗑️ User '{target}' deleted.")
                            st.session_state.um_action = None
                            st.rerun()
                        else:
                            st.error("User not found in sheet.")
                    except Exception as e:
                        st.error(f"Error deleting user: {e}")
        with b2:
            if st.button("✖ Cancel", key="um_cancel_delete"):
                st.session_state.um_action = None
                st.rerun()

# ══════════════════════════════════════════════════════════════════════
# USERS TABLE
# ══════════════════════════════════════════════════════════════════════
st.markdown("---")
st.markdown('<div class="rad-card-title">All Users</div>', unsafe_allow_html=True)
st.markdown('<div class="rad-card-subtitle">Manage existing user accounts and permissions</div>', unsafe_allow_html=True)

users_df = load_users_sheet()

if users_df.empty:
    st.info("No users found in the Users sheet. Click '➕ Add User' to create the first user.")
else:
    # Deduplicate — keep last occurrence of each username (most recent write wins)
    if "Username" in users_df.columns:
        users_df = users_df.copy()
        users_df["Username"] = users_df["Username"].str.strip().str.lower()
        users_df = users_df.drop_duplicates(subset=["Username"], keep="last").reset_index(drop=True)

    role_colors   = {"admin": ("#EDE9FE", "#5B5FEF"), "member": ("#E0E7FF", "#4F46E5")}
    status_colors = {"active": ("#D1FAE5", "#065F46"), "inactive": ("#FEE2E2", "#991B1B")}

    for row_idx, (_, row) in enumerate(users_df.iterrows()):
        uname  = str(row.get("Username", "")).strip()
        role   = str(row.get("Role", "member")).strip()
        otas   = str(row.get("OTAs", "")).strip()
        status = str(row.get("Status", "active")).strip()
        email  = str(row.get("Email ID", "")).strip()
        created= str(row.get("Created At", "")).strip()

        if not uname:
            continue

        display_name  = uname.replace(".", " ").title()
        email_display = email if email else f"{uname}@fabhotels.com"
        r_bg, r_col  = role_colors.get(role, ("#F1F3F9", "#6B7280"))
        s_bg, s_col  = status_colors.get(status, ("#F1F3F9", "#6B7280"))
        otas_display = otas if otas else ("All OTAs" if role == "admin" else "—")
        is_current   = (uname == current_user())

        you_badge = (
            ' <span style="background:#EDE9FE;color:#5B5FEF;padding:1px 7px;'
            'border-radius:20px;font-size:10px;font-weight:600;">You</span>'
            if is_current else ""
        )

        # Row layout: info | edit | delete
        info_col, edit_col, del_col = st.columns([8, 1, 1])

        with info_col:
            st.markdown(f"""
            <div style="background:var(--bg-card);border:1px solid var(--border);border-radius:10px;
                padding:14px 18px;display:flex;align-items:center;gap:20px;flex-wrap:wrap;">
                <!-- Avatar -->
                <div style="width:40px;height:40px;background:var(--accent-light);border-radius:50%;
                    display:flex;align-items:center;justify-content:center;font-size:18px;flex-shrink:0;">
                    {"👑" if role == "admin" else "👤"}
                </div>
                <!-- Name + email -->
                <div style="min-width:160px;flex:2;">
                    <div style="font-weight:600;color:var(--text-primary);font-size:14px;">
                        {display_name}{you_badge}
                    </div>
                    <div style="font-size:12px;color:var(--text-secondary);font-family:monospace;">
                        {email_display}
                    </div>
                </div>
                <!-- Role -->
                <div style="flex:1;min-width:90px;">
                    <div style="font-size:10px;color:var(--text-muted);margin-bottom:3px;">ROLE</div>
                    <span style="background:{r_bg};color:{r_col};padding:3px 10px;
                        border-radius:20px;font-size:11px;font-weight:600;">{role.title()}</span>
                </div>
                <!-- OTAs -->
                <div style="flex:2;min-width:140px;">
                    <div style="font-size:10px;color:var(--text-muted);margin-bottom:3px;">OTAs</div>
                    <div style="font-size:12px;color:var(--text-secondary);">{otas_display}</div>
                </div>
                <!-- Status -->
                <div style="flex:1;min-width:90px;">
                    <div style="font-size:10px;color:var(--text-muted);margin-bottom:3px;">STATUS</div>
                    <span style="background:{s_bg};color:{s_col};padding:3px 10px;
                        border-radius:20px;font-size:11px;font-weight:600;">{status.title()}</span>
                </div>
                <!-- Created -->
                <div style="flex:1;min-width:100px;">
                    <div style="font-size:10px;color:var(--text-muted);margin-bottom:3px;">CREATED</div>
                    <div style="font-size:11px;color:var(--text-secondary);">{created[:10] if created else "—"}</div>
                </div>
            </div>""", unsafe_allow_html=True)

        with edit_col:
            st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)
            if st.button("✏️ Edit", key=f"um_edit_{row_idx}_{uname}", use_container_width=True):
                st.session_state.um_action      = "edit"
                st.session_state.um_target_user = uname
                st.rerun()

        with del_col:
            st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)
            if st.button("🗑️ Del", key=f"um_del_{row_idx}_{uname}", use_container_width=True,
                         disabled=is_current):
                st.session_state.um_action      = "delete"
                st.session_state.um_target_user = uname
                st.rerun()

    st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)
    # Summary counts
    total   = len(users_df)
    active  = len(users_df[users_df["Status"] == "active"])
    admins  = len(users_df[users_df["Role"] == "admin"])
    m1, m2, m3, _ = st.columns([1, 1, 1, 3])
    with m1: st.metric("Total Users",  total)
    with m2: st.metric("Active",       active)
    with m3: st.metric("Admins",       admins)

# ── Reload button ─────────────────────────────────────────────────────
st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
if st.button("🔄 Refresh Users", key="um_refresh"):
    load_users_sheet.clear()
    st.rerun()