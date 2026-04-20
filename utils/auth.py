# ─────────────────────────────────────────────
#  utils/auth.py  —  Login & session management
# ─────────────────────────────────────────────
import streamlit as st
from utils.config import USERS as DEFAULT_USERS


def _get_users() -> dict:
    """
    Load users from the Google Sheet (Users tab) at runtime.
    Falls back to config.py USERS if the sheet is unavailable.
    """
    try:
        from utils.sheets import get_all_users_dict
        users = get_all_users_dict()
        return users if users else DEFAULT_USERS
    except Exception:
        return DEFAULT_USERS


def login_page():
    """Render login form. Returns True if authenticated."""
    st.markdown("""
    <style>
    .login-box {
        max-width: 420px; margin: 80px auto 0 auto;
        padding: 40px 36px; border-radius: 12px;
        background: #0D1B2A; color: #fff;
        box-shadow: 0 8px 32px rgba(0,0,0,0.25);
    }
    .login-title { font-size: 26px; font-weight: 700;
        color: #0E7C86; margin-bottom: 6px; }
    .login-sub { font-size: 13px; color: #94a3b8; margin-bottom: 28px; }
    </style>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown('<div class="login-title">🏨 OTA Dashboard</div>', unsafe_allow_html=True)
        st.markdown('<div class="login-sub">FabHotels Revenue & Audit Team</div>', unsafe_allow_html=True)

        username = st.text_input("Username", placeholder="Enter your username").strip().lower()
        password = st.text_input("Password", type="password", placeholder="Enter your password")

        if st.button("Login", use_container_width=True, type="primary"):
            users = _get_users()
            if username in users and users[username]["password"] == password:
                # Reject deactivated users
                if users[username].get("status", "active") == "inactive":
                    st.error("Your account has been deactivated. Contact an admin.")
                else:
                    st.session_state["authenticated"] = True
                    st.session_state["username"] = username
                    st.session_state["role"] = users[username]["role"]
                    st.session_state["otas"] = users[username]["otas"]
                    st.rerun()
            else:
                st.error("Invalid username or password.")

    return st.session_state.get("authenticated", False)


def require_login():
    """Call at top of every page. Redirects to login if not authenticated."""
    if not st.session_state.get("authenticated"):
        login_page()
        st.stop()


def logout():
    for key in ["authenticated", "username", "role", "otas"]:
        st.session_state.pop(key, None)
    st.rerun()


def current_user():
    return st.session_state.get("username", "")


def current_role():
    return st.session_state.get("role", "")


def current_otas():
    return st.session_state.get("otas", [])


def is_admin():
    return st.session_state.get("role") == "admin"