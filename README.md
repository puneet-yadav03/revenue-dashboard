# Revenue Audit Dashboard — Redesigned UI

A full redesign of the FabHotels Revenue Audit Dashboard matching the Figma specifications.

## 🎨 Design Changes
- **New sidebar** with collapsible nav groups (Property View, Analytics), icons, active state highlight
- **Top navbar** with logo, app name, dark/light mode toggle, and user avatar
- **Modern metric cards** with icons, color-coded deltas
- **Redesigned tables** — Full View with checkboxes, search, sort, filter dropdowns
- **Property Wise Info** — expandable cards with hygiene progress bars
- **Tasks page** — table-style task list with Editing ON/OFF toggle + Save Changes button
- **OTA Analytics** — pill tab switcher, OTA score cards with progress bars, pie chart
- **Owner Report** — styled owner profile card, actual data + percentage data tables
- **Admin Panel** — pill tabs (All Data / Audits / Reminders), activity feed for audits, reminder cards
- **Settings & User Management** — new pages matching Figma design
- **Dark mode** — full dark theme toggle

## 📁 Project Structure
```
revenue_dashboard/
├── app.py                    ← Entry point
├── requirements.txt
├── .streamlit/
│   └── config.toml
├── utils/
│   ├── auth.py               ← UNCHANGED — Login & session management
│   ├── config.py             ← UNCHANGED — All column maps, dropdowns, colors
│   ├── sheets.py             ← UNCHANGED — Google Sheets read/write
│   └── helpers.py            ← REDESIGNED — New sidebar, cards, CSS
└── pages/
    ├── Overview.py           ← Summary page (redesigned)
    ├── Property_View.py      ← Full View table (redesigned)
    ├── Property_Wise.py      ← Property Wise Info cards (new)
    ├── Data_Entry.py         ← Tasks with editing toggle (redesigned)
    ├── Analytics.py          ← OTA Analytics (redesigned)
    ├── Owner_Report.py       ← Owner Report (redesigned)
    ├── Admin.py              ← Admin Panel (redesigned)
    ├── Settings.py           ← Settings page (new)
    └── User_Mgmt.py          ← User Management (new)
```

## 🚀 Setup

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Add credentials:**
   Place your `Credentials.json` (Google Service Account) in the root project folder.

3. **Run the app:**
   ```bash
   streamlit run app.py
   ```

## ⚠️ What Was NOT Changed
- `utils/auth.py` — Login logic, session management, role system
- `utils/config.py` — All column groups, OTA maps, dropdown values, status colors
- `utils/sheets.py` — Google Sheets connection, read/write, audit log, reminders
- All business logic: pending detection, save_entry(), batch_update(), force_reload()
- All data flow: OTA_TO_EDITABLE_COLS, OTA_COLUMN_MAP, COL_DROPDOWN_MAP
- Auto-fill "Not Live" logic for dependent columns
- Audit logging and reminder writing on save

## 🔑 Login Credentials (unchanged)
| Username | Password | Role | OTAs |
|---|---|---|---|
| admin | admin@123 | admin | All |
| mahak.goyal | mahak@123 | member | MMT/GI |
| puneet.yadav | puneet@123 | member | BDC, GMB, WebApp |
| abhishek.khushwa | abhishek@123 | member | Agoda |
| irfan | irfan@123 | member | Expedia |
| faique | faique@123 | member | Cleartrip |
| yash.yadav | yash@123 | member | PL |
