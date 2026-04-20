# ─────────────────────────────────────────────
#  utils/helpers.py  —  Shared UI utilities (Redesigned)
# ─────────────────────────────────────────────
import streamlit as st
import pandas as pd
from utils.config import STATUS_COLORS
from utils.auth import current_user, current_role, current_otas, logout, is_admin

PAGE_FILES = {
    "Overview":      "pages/Overview.py",
    "Property_View": "pages/Property_View.py",
    "Property_Wise": "pages/Property_Wise.py",
    "Data_Entry":    "pages/Data_Entry.py",
    "Analytics":     "pages/Analytics.py",
    "Owner_Report":  "pages/Owner_Report.py",
    "Admin":         "pages/Admin.py",
    "Settings":      "pages/Settings.py",
    "User_Mgmt":     "pages/User_Mgmt.py",
}

# ── Master CSS ─────────────────────────────────────────────────────────
GLOBAL_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:opsz,wght@9..40,300;9..40,400;9..40,500;9..40,600;9..40,700&family=DM+Mono:wght@400;500&display=swap');

:root {
    --bg-primary:#F8F9FC; --bg-secondary:#FFFFFF; --bg-card:#FFFFFF;
    --bg-hover:#F1F3F9; --bg-active:#EEF0FF; --bg-input:#F5F6FA;
    --border:#E8EAF0; --border-light:#F0F2F8;
    --text-primary:#1A1D2E; --text-secondary:#6B7280; --text-muted:#9CA3AF;
    --text-sidebar:#374151; --accent:#5B5FEF; --accent-light:#EEF0FF;
    --accent-hover:#4A4EDD; --green:#10B981; --green-light:#D1FAE5;
    --green-text:#065F46; --red:#EF4444; --red-light:#FEE2E2;
    --red-text:#991B1B; --orange:#F59E0B; --orange-light:#FEF3C7;
    --orange-text:#92400E; --blue:#3B82F6; --blue-light:#DBEAFE;
    --purple:#8B5CF6; --purple-light:#EDE9FE;
    --shadow-sm:0 1px 3px rgba(0,0,0,0.06); --shadow-md:0 4px 12px rgba(0,0,0,0.08);
    --shadow-lg:0 8px 24px rgba(0,0,0,0.10);
    --radius-sm:6px; --radius-md:10px; --radius-lg:14px;
}
.dark-mode,:root.dark {
    --bg-primary:#0F1117; --bg-secondary:#161B27; --bg-card:#1E2436;
    --bg-hover:#252B3B; --bg-active:#2A2F50; --bg-input:#252B3B;
    --border:#2A3040; --border-light:#232838;
    --text-primary:#F1F3F9; --text-secondary:#9CA3AF; --text-muted:#6B7280;
    --text-sidebar:#CBD5E1; --accent:#6366F1; --accent-light:#2A2F50;
    --accent-hover:#7578F3; --green-light:#052E16; --green-text:#34D399;
    --red-light:#2D1515; --red-text:#FC8181; --orange-light:#2D1E08;
    --orange-text:#FCD34D; --blue-light:#1E2D4A; --purple-light:#2D1E4A;
    --shadow-sm:0 1px 3px rgba(0,0,0,0.3);
}

*,*::before,*::after{box-sizing:border-box;margin:0;padding:0;}
html,body,[data-testid="stApp"]{font-family:'DM Sans',sans-serif!important;}

#MainMenu,footer,header,[data-testid="stDecoration"]{display:none!important;}
.block-container{padding:28px 32px 32px!important;max-width:100%!important;}

/* ── Hide Streamlit's auto-generated default page nav links ── */
[data-testid="stSidebarNav"],
[data-testid="stSidebarNavItems"],
[data-testid="stSidebarNavSeparator"],
section[data-testid="stSidebar"] > div > div > div > ul,
section[data-testid="stSidebar"] nav,
.st-emotion-cache-pbsa85,
.st-emotion-cache-16idsys,
div[class*="stSidebarNav"] {
    display: none !important;
    visibility: hidden !important;
    height: 0 !important;
    overflow: hidden !important;
}

/* sidebar */
[data-testid="stSidebar"]{background:var(--bg-secondary)!important;border-right:1px solid var(--border)!important;min-width:240px!important;max-width:240px!important;}
[data-testid="stSidebarContent"]{padding:0!important;}

/* nav items via page_link */
[data-testid="stSidebar"] a[data-testid="stPageLink"]{
    display:flex!important;align-items:center!important;
    padding:8px 12px!important;border-radius:6px!important;
    font-size:13px!important;font-weight:500!important;
    color:var(--text-sidebar)!important;text-decoration:none!important;
    margin:1px 0!important;transition:all .12s!important;
}
[data-testid="stSidebar"] a[data-testid="stPageLink"]:hover{background:var(--bg-hover)!important;color:var(--text-primary)!important;}

/* streamlit widget tweaks */
div[data-testid="stSelectbox"]>label,
div[data-testid="stTextInput"]>label,
div[data-testid="stTextArea"]>label,
div[data-testid="stMultiSelect"]>label{
    font-size:11px!important;font-weight:600!important;color:var(--text-muted)!important;
    font-family:'DM Sans',sans-serif!important;text-transform:uppercase;letter-spacing:.5px;
}
.stButton>button{border-radius:6px!important;font-family:'DM Sans',sans-serif!important;font-weight:600!important;font-size:13px!important;}
.stButton>button[kind="primary"]{background:var(--accent)!important;border:none!important;}

/* cards */
.rad-card{background:var(--bg-card);border:1px solid var(--border);border-radius:var(--radius-lg);padding:22px 24px;box-shadow:var(--shadow-sm);margin-bottom:16px;}
.rad-card-title{font-size:15px;font-weight:600;color:var(--text-primary);margin-bottom:4px;}
.rad-card-subtitle{font-size:12px;color:var(--text-secondary);margin-bottom:16px;}

/* metric card */
.rad-metric-card{background:var(--bg-card);border:1px solid var(--border);border-radius:var(--radius-lg);padding:20px 22px;box-shadow:var(--shadow-sm);height:100%;}
.rad-metric-top{display:flex;align-items:center;justify-content:space-between;margin-bottom:14px;}
.rad-metric-label{font-size:13px;font-weight:500;color:var(--text-secondary);}
.rad-metric-icon{width:38px;height:38px;border-radius:10px;display:flex;align-items:center;justify-content:center;font-size:18px;}
.rad-metric-value{font-size:28px;font-weight:700;color:var(--text-primary);letter-spacing:-.5px;line-height:1;}
.rad-metric-delta{display:flex;align-items:center;gap:4px;font-size:12px;margin-top:6px;color:var(--text-secondary);}
.rad-delta-up{color:var(--green);} .rad-delta-down{color:var(--red);}

/* page header */
.rad-page-header{margin-bottom:24px;}
.rad-page-title{font-size:26px;font-weight:700;color:var(--text-primary);letter-spacing:-.5px;line-height:1.2;}
.rad-page-subtitle{font-size:14px;color:var(--text-secondary);margin-top:4px;}
.rad-page-header-row{display:flex;align-items:flex-start;justify-content:space-between;}

/* tabs */
.rad-tabs{display:flex;align-items:center;background:#F0F0F5;border-radius:10px;padding:4px;gap:2px;width:fit-content;margin-bottom:20px;}
.rad-tab{padding:8px 18px;border-radius:8px;font-size:13px;font-weight:500;color:var(--text-secondary);cursor:pointer;transition:all .15s;white-space:nowrap;border:none;background:transparent;display:inline-flex;align-items:center;gap:6px;}
.rad-tab:hover{color:var(--text-primary);}
.rad-tab.active{background:var(--bg-card);color:var(--text-primary);font-weight:600;box-shadow:var(--shadow-sm);}

/* badges */
.rad-badge{display:inline-flex;align-items:center;padding:3px 10px;border-radius:20px;font-size:11px;font-weight:600;white-space:nowrap;}
.rad-badge-green{background:var(--green-light);color:var(--green-text);}
.rad-badge-red{background:var(--red-light);color:var(--red-text);}
.rad-badge-orange{background:var(--orange-light);color:var(--orange-text);}
.rad-badge-blue{background:var(--blue-light);color:var(--blue);}
.rad-badge-purple{background:var(--purple-light);color:var(--purple);}
.rad-badge-gray{background:#F1F3F9;color:#6B7280;}

/* table */
.rad-table-wrapper{background:var(--bg-card);border:1px solid var(--border);border-radius:var(--radius-lg);overflow:hidden;box-shadow:var(--shadow-sm);}
.rad-table{width:100%;border-collapse:collapse;font-size:13px;}
.rad-table th{text-align:left;padding:12px 16px;font-size:12px;font-weight:600;color:var(--text-secondary);border-bottom:1px solid var(--border);background:var(--bg-primary);}
.rad-table td{padding:13px 16px;color:var(--text-primary);border-bottom:1px solid var(--border-light);font-size:13px;}
.rad-table tr:last-child td{border-bottom:none;}
.rad-table tr:hover td{background:var(--bg-hover);}

/* progress */
.rad-progress{height:5px;background:#E8EAF0;border-radius:3px;overflow:hidden;margin-top:8px;}
.rad-progress-fill{height:100%;border-radius:3px;transition:width .3s;}

/* expand card */
.rad-expand-card{background:var(--bg-card);border:1px solid var(--border);border-radius:var(--radius-lg);padding:20px 24px;margin-bottom:12px;box-shadow:var(--shadow-sm);}
.rad-expand-header{display:flex;align-items:center;justify-content:space-between;}
.rad-expand-title{font-size:17px;font-weight:600;color:var(--text-primary);}
.rad-expand-loc{font-size:13px;color:var(--text-secondary);margin-top:2px;}
.rad-expand-btn{display:flex;align-items:center;gap:5px;font-size:12px;font-weight:500;color:var(--text-secondary);}
.rad-expand-body{display:grid;grid-template-columns:repeat(4,1fr);gap:0;margin-top:20px;padding-top:20px;border-top:1px solid var(--border-light);}
.rad-expand-metric-label{display:flex;align-items:center;gap:4px;font-size:11px;color:var(--text-muted);margin-bottom:6px;}
.rad-expand-metric-value{font-size:22px;font-weight:700;color:var(--text-primary);letter-spacing:-.3px;}
.rad-expand-metric-delta{font-size:11px;margin-top:3px;}

/* brand in sidebar */
.rad-brand{display:flex;align-items:center;gap:10px;padding:16px 14px 12px;}
.rad-brand-icon{width:36px;height:36px;background:linear-gradient(135deg,#5B5FEF 0%,#8B5CF6 100%);border-radius:9px;display:flex;align-items:center;justify-content:center;font-size:17px;color:#fff;flex-shrink:0;}
.rad-brand-name{font-size:14px;font-weight:600;color:var(--text-primary);line-height:1.2;}
.rad-brand-sub{font-size:10px;color:var(--text-muted);margin-top:1px;}
.rad-divider{height:1px;background:var(--border-light);margin:2px 10px;}
.rad-nav-parent{display:flex;align-items:center;justify-content:space-between;padding:8px 12px;border-radius:6px;cursor:default;font-size:13px;font-weight:500;color:var(--text-sidebar);margin:1px 0;}
.rad-nav-parent-left{display:flex;align-items:center;gap:8px;}
.rad-nav-sub a[data-testid="stPageLink"]{padding-left:28px!important;}
.rad-user-info{padding:10px 14px;border-top:1px solid var(--border-light);}
.rad-user-name{font-weight:600;color:var(--text-primary);font-size:13px;}
.rad-user-role{font-size:11px;color:var(--text-muted);margin-top:2px;}
.rad-nav-active-label{display:flex;align-items:center;gap:8px;padding:8px 12px;border-radius:6px;background:var(--accent-light);font-size:13px;font-weight:600;color:var(--accent);margin:1px 0;}

/* filter row */
.rad-filter-row{display:flex;align-items:center;gap:10px;margin-bottom:20px;flex-wrap:wrap;}
.rad-search-box{display:flex;align-items:center;gap:8px;background:var(--bg-input);border:1px solid var(--border);border-radius:6px;padding:7px 12px;flex:1;min-width:200px;max-width:380px;font-size:13px;color:var(--text-secondary);}

/* btn */
.rad-btn{display:inline-flex;align-items:center;gap:6px;padding:8px 18px;border-radius:6px;font-size:13px;font-weight:600;cursor:pointer;border:none;transition:all .15s;white-space:nowrap;font-family:'DM Sans',sans-serif;}
.rad-btn-primary{background:var(--accent);color:#fff;}
.rad-btn-primary:hover{background:var(--accent-hover);}
.rad-btn-outline{background:var(--bg-card);border:1px solid var(--border);color:var(--text-primary);}
.rad-btn-green{background:var(--green);color:#fff;}

/* toggle */
.rad-toggle-row{display:flex;align-items:center;gap:10px;font-size:13px;font-weight:500;color:var(--text-secondary);}

/* toast */
.rad-toast{position:fixed;bottom:24px;right:24px;background:var(--text-primary);color:#fff;padding:12px 20px;border-radius:10px;font-size:13px;font-weight:500;box-shadow:var(--shadow-lg);z-index:9999;}

/* dataframe */
[data-testid="stDataFrame"]{border-radius:10px!important;overflow:hidden;border:1px solid var(--border)!important;}
</style>
"""


DARK_CSS = """
<style>
/* ── Override CSS variables for dark mode ── */
:root, html, body {
    --bg-primary:#0F1117 !important; --bg-secondary:#161B27 !important; --bg-card:#1E2436 !important;
    --bg-hover:#252B3B !important; --bg-active:#2A2F50 !important; --bg-input:#252B3B !important;
    --border:#2A3040 !important; --border-light:#232838 !important;
    --text-primary:#F1F3F9 !important; --text-secondary:#9CA3AF !important; --text-muted:#6B7280 !important;
    --text-sidebar:#CBD5E1 !important; --accent:#6366F1 !important; --accent-light:#2A2F50 !important;
    --accent-hover:#7578F3 !important; --green-light:#052E16 !important; --green-text:#34D399 !important;
    --red-light:#2D1515 !important; --red-text:#FC8181 !important; --orange-light:#2D1E08 !important;
    --orange-text:#FCD34D !important; --blue-light:#1E2D4A !important; --purple-light:#2D1E4A !important;
    --shadow-sm:0 1px 3px rgba(0,0,0,0.3) !important;
}

/* ── Force dark background on ALL Streamlit containers ── */
html, body,
.stApp,
[data-testid="stApp"],
[data-testid="stAppViewContainer"],
[data-testid="stAppViewBlockContainer"],
[data-testid="stMain"],
[data-testid="stMainBlockContainer"],
[data-testid="stBottom"],
.main,
.main > div,
.block-container,
section.main,
section.main > div,
div[class*="appview-container"],
div[class*="main"] {
    background-color: #0F1117 !important;
    color: #F1F3F9 !important;
}

/* ── Sidebar ── */
[data-testid="stSidebar"],
[data-testid="stSidebar"] > div,
[data-testid="stSidebarContent"],
section[data-testid="stSidebar"],
section[data-testid="stSidebar"] > div {
    background-color: #161B27 !important;
    border-right: 1px solid #2A3040 !important;
}

/* ── Text elements ── */
p, span, li, label, div, h1, h2, h3, h4, h5, h6,
[data-testid="stMarkdownContainer"] *,
[data-testid="stText"],
[data-testid="caption"] {
    color: #F1F3F9 !important;
}

/* ── Inputs ── */
[data-testid="stTextInput"] input,
[data-testid="stTextArea"] textarea,
[data-testid="stNumberInput"] input {
    background-color: #252B3B !important;
    color: #F1F3F9 !important;
    border-color: #2A3040 !important;
}
[data-testid="stTextInput"] input::placeholder,
[data-testid="stTextArea"] textarea::placeholder { color: #6B7280 !important; }

/* ── Selectbox / Multiselect ── */
[data-testid="stSelectbox"] > div > div,
[data-testid="stMultiSelect"] > div > div,
[data-baseweb="select"] > div,
[data-baseweb="input"] > div {
    background-color: #252B3B !important;
    color: #F1F3F9 !important;
    border-color: #2A3040 !important;
}
[data-testid="stSelectbox"] svg,
[data-testid="stMultiSelect"] svg { fill: #9CA3AF !important; }
[data-baseweb="popover"],
[data-baseweb="menu"],
[role="listbox"],
[data-baseweb="popover"] > div {
    background-color: #1E2436 !important;
    border: 1px solid #2A3040 !important;
}
[role="option"], [data-baseweb="option"] {
    background-color: #1E2436 !important;
    color: #F1F3F9 !important;
}
[role="option"]:hover, [data-baseweb="option"]:hover { background-color: #252B3B !important; }

/* ── Cards / Containers ── */
[data-testid="stVerticalBlockBorderWrapper"],
[data-testid="stVerticalBlockBorderWrapper"] > div,
[data-testid="stHorizontalBlock"],
[data-testid="element-container"] {
    background-color: transparent !important;
}
[data-testid="stVerticalBlockBorderWrapper"] > div[style*="border"] {
    background-color: #1E2436 !important;
    border-color: #2A3040 !important;
}

/* ── Metrics ── */
[data-testid="stMetric"] { background-color: transparent !important; }
[data-testid="stMetricValue"] { color: #F1F3F9 !important; }
[data-testid="stMetricLabel"] { color: #9CA3AF !important; }
[data-testid="stMetricDelta"] { color: #34D399 !important; }

/* ── DataFrame / Table ── */
[data-testid="stDataFrame"],
[data-testid="stDataFrame"] iframe,
.dvn-scroller { background-color: #1E2436 !important; }

/* ── Buttons ── */
.stButton > button {
    background-color: #1E2436 !important;
    color: #F1F3F9 !important;
    border-color: #2A3040 !important;
}
.stButton > button[kind="primary"],
.stButton > button[data-testid="baseButton-primary"] {
    background-color: #6366F1 !important;
    color: #fff !important;
    border-color: #6366F1 !important;
}
.stButton > button:hover { background-color: #252B3B !important; }
.stButton > button[kind="primary"]:hover { background-color: #7578F3 !important; }

/* ── Radio ── */
[data-testid="stRadio"] label,
[data-testid="stRadio"] label span { color: #F1F3F9 !important; }
[data-testid="stRadio"] > div > label > div:first-child > div {
    border-color: #6366F1 !important;
}

/* ── Toggle / Checkbox ── */
[data-testid="stToggle"] label,
[data-testid="stCheckbox"] label,
[data-testid="stCheckbox"] span { color: #F1F3F9 !important; }

/* ── Expander ── */
[data-testid="stExpander"] {
    background-color: #1E2436 !important;
    border-color: #2A3040 !important;
}
[data-testid="stExpander"] summary,
[data-testid="stExpander"] summary span { color: #F1F3F9 !important; }
[data-testid="stExpander"] > div { background-color: #1E2436 !important; }

/* ── Alerts / Info boxes ── */
[data-testid="stAlert"],
[data-testid="stInfo"],
[data-testid="stWarning"],
[data-testid="stError"],
[data-testid="stSuccess"] {
    background-color: #1E2436 !important;
    border-color: #2A3040 !important;
    color: #F1F3F9 !important;
}

/* ── Download button ── */
[data-testid="stDownloadButton"] button {
    background-color: #1E2436 !important;
    color: #F1F3F9 !important;
    border-color: #2A3040 !important;
}

/* ── Caption ── */
[data-testid="stCaptionContainer"],
[data-testid="stCaptionContainer"] p { color: #6B7280 !important; }

/* ── Number input buttons ── */
[data-testid="stNumberInput"] button {
    background-color: #252B3B !important;
    color: #F1F3F9 !important;
    border-color: #2A3040 !important;
}

/* ── Spinner ── */
[data-testid="stSpinner"] { color: #F1F3F9 !important; }

/* ── Tabs (native streamlit) ── */
[data-testid="stTabs"] [role="tab"] {
    background-color: #1E2436 !important;
    color: #9CA3AF !important;
    border-color: #2A3040 !important;
}
[data-testid="stTabs"] [role="tab"][aria-selected="true"] {
    background-color: #252B3B !important;
    color: #F1F3F9 !important;
    border-bottom-color: #6366F1 !important;
}
[data-testid="stTabs"] [role="tabpanel"] { background-color: #0F1117 !important; }

/* ── Scrollbar ── */
::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: #161B27; }
::-webkit-scrollbar-thumb { background: #2A3040; border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: #6366F1; }
</style>
"""


# JavaScript injected once to keep body class in sync with dark_mode state
def _dark_mode_script(enabled: bool):
    cls = "dark-mode-active" if enabled else ""
    return f"""
<script>
(function() {{
    var attempts = 0;
    function applyTheme() {{
        var app = document.querySelector('[data-testid="stApp"]') ||
                  document.querySelector('.stApp') ||
                  document.body;
        if (app) {{
            if ({'true' if enabled else 'false'}) {{
                document.documentElement.setAttribute('data-theme', 'dark');
                document.body.classList.add('dark-mode-active');
                app.setAttribute('data-theme', 'dark');
            }} else {{
                document.documentElement.removeAttribute('data-theme');
                document.body.classList.remove('dark-mode-active');
                app.removeAttribute('data-theme');
            }}
        }} else if (attempts < 20) {{
            attempts++;
            setTimeout(applyTheme, 100);
        }}
    }}
    applyTheme();
}})();
</script>
"""


def inject_css():
    st.markdown(GLOBAL_CSS, unsafe_allow_html=True)
    dark = st.session_state.get("dark_mode", False)
    if dark:
        st.markdown(DARK_CSS, unsafe_allow_html=True)
    st.markdown(_dark_mode_script(dark), unsafe_allow_html=True)


def render_sidebar(active_page: str = ""):
    inject_css()
    username  = current_user()
    role      = current_role()
    user_otas = current_otas()
    if "dark_mode" not in st.session_state:
        st.session_state.dark_mode = False

    with st.sidebar:
        # ── Logo / Brand ───────────────────────────────────────────────
        st.markdown("""
        <div class="rad-brand">
            <div class="rad-brand-icon">📊</div>
            <div>
                <div class="rad-brand-name">Revenue Audit</div>
                <div class="rad-brand-sub">FabHotels Dashboard</div>
            </div>
        </div>
        <div class="rad-divider"></div>
        """, unsafe_allow_html=True)

        # ── Main nav links ─────────────────────────────────────────────
        _nav_link("📋", "Summary",          "Overview",      active_page)
        _nav_link("🏢", "Full View",        "Property_View", active_page)
        _nav_link("ℹ️", "Property Wise",    "Property_Wise", active_page)
        _nav_link("☑️", "Tasks",            "Data_Entry",    active_page)
        _nav_link("📈", "OTA Analytics",    "Analytics",     active_page)
        _nav_link("📄", "Owner Report",     "Owner_Report",  active_page)
        _nav_link("⚙️", "Admin Panel",      "Admin",         active_page)

        st.markdown('<div class="rad-divider" style="margin:6px 10px;"></div>', unsafe_allow_html=True)

        # ── Settings & User Management with main tabs ──────────────────
        if is_admin():
            _nav_link("🔧", "Settings",        "Settings",  active_page)
            _nav_link("👥", "User Management", "User_Mgmt", active_page)

        # ── Spacer pushes profile to bottom ───────────────────────────
        st.markdown('<div style="flex:1;min-height:30px;"></div>', unsafe_allow_html=True)
        st.markdown('<div class="rad-divider" style="margin:4px 10px 6px;"></div>', unsafe_allow_html=True)

        # ── Profile info ───────────────────────────────────────────────
        st.markdown(f"""
        <div class="rad-user-info">
            <div class="rad-user-name">{username.replace('.', ' ').title()}</div>
            <div class="rad-user-role">{role.capitalize()} · {', '.join(user_otas) if user_otas else 'All OTAs'}</div>
        </div>""", unsafe_allow_html=True)

        # ── Theme + Logout ─────────────────────────────────────────────
        c1, c2 = st.columns(2)
        with c1:
            dm = "🌙" if not st.session_state.dark_mode else "☀️"
            if st.button(f"{dm} Theme", use_container_width=True, key="sb_theme"):
                st.session_state.dark_mode = not st.session_state.dark_mode
                st.rerun()
        with c2:
            if st.button("🚪 Logout", use_container_width=True, key="sb_logout"):
                logout()


def _nav_link(icon: str, label: str, page_key: str, active_page: str):
    is_active = (active_page == page_key)
    if is_active:
        st.markdown(
            f'<div class="rad-nav-active-label">'
            f'<span>{icon}</span><span>{label}</span>'
            f'</div>',
            unsafe_allow_html=True
        )
    elif page_key in PAGE_FILES:
        st.page_link(PAGE_FILES[page_key], label=f"{icon}  {label}")


def page_header(title: str, subtitle: str = "", right_html: str = ""):
    inject_css()
    st.markdown(f"""
    <div class="rad-page-header">
        <div class="rad-page-header-row">
            <div>
                <div class="rad-page-title">{title}</div>
                {'<div class="rad-page-subtitle">'+subtitle+'</div>' if subtitle else ''}
            </div>
            {right_html}
        </div>
    </div>""", unsafe_allow_html=True)


def metric_card_html(icon, icon_bg, value, label, delta="", delta_up=True):
    d_class = "rad-delta-up" if delta_up else "rad-delta-down"
    d_arrow = "↑" if delta_up else "↓"
    d_html  = f'<div class="rad-metric-delta {d_class}">{d_arrow} {delta}</div>' if delta else ""
    return f"""
    <div class="rad-metric-card">
        <div class="rad-metric-top">
            <span class="rad-metric-label">{label}</span>
            <div class="rad-metric-icon" style="background:{icon_bg};">{icon}</div>
        </div>
        <div class="rad-metric-value">{value}</div>
        {d_html}
    </div>"""


def status_badge(value: str) -> str:
    color = STATUS_COLORS.get(str(value).strip(), "#94A3B8")
    return (
        f'<span style="background:{color};color:#fff;padding:3px 10px;'
        f'border-radius:20px;font-size:11px;font-weight:600;">'
        f'{value}</span>'
    )


def completion_pct(df: pd.DataFrame, cols: list) -> float:
    if df.empty or not cols:
        return 0.0
    existing = [c for c in cols if c in df.columns]
    if not existing:
        return 0.0
    total  = len(df) * len(existing)
    checks = df[existing].apply(lambda c: c.str.strip().str.lower() == "check").sum().sum()
    return round((checks / total) * 100, 1) if total else 0.0


def global_filters(df: pd.DataFrame, key_prefix: str = "") -> pd.DataFrame:
    col1, col2, col3, col4 = st.columns(4)
    cities   = ["All"] + sorted(df["Property City"].dropna().unique().tolist())
    cats     = ["All"] + sorted(df["Category (A/B/C)"].dropna().unique().tolist())
    statuses = ["All"] + sorted(df["FH Status"].dropna().unique().tolist()) if "FH Status" in df.columns else ["All"]
    with col1:
        city = st.selectbox("City", cities, key=f"{key_prefix}_city")
    with col2:
        cat  = st.selectbox("Category", cats, key=f"{key_prefix}_cat")
    with col3:
        status = st.selectbox("FH Status", statuses, key=f"{key_prefix}_status")
    with col4:
        search = st.text_input("Search FH ID / Name", key=f"{key_prefix}_search")
    out = df.copy()
    if city   != "All": out = out[out["Property City"] == city]
    if cat    != "All": out = out[out["Category (A/B/C)"] == cat]
    if status != "All" and "FH Status" in out.columns:
        out = out[out["FH Status"] == status]
    if search:
        mask = (
            out["FH"].str.contains(search, case=False, na=False) |
            out["Property Name"].str.contains(search, case=False, na=False)
        )
        out = out[mask]
    return out