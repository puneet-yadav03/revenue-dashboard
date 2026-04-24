# ─────────────────────────────────────────────
#  config.py  —  Central configuration
# ─────────────────────────────────────────────

SHEET_NAME          = "Revenue_Audit_Checks"
WORKSHEET_NAME      = "Post Apr'25"
AUDIT_SHEET_NAME    = "Audit_Log"
REMINDER_SHEET_NAME = "Reminders"
TASK_SHEET_NAME     = "Tasks"
SHEET_ID = "1oan8wyMMFZtieEAlQnwwivbDcA_kQ1MGUO2mXq7do6k"

# ── Users ────────────────────────────────────────────────────────────
USERS = {
    "admin":    {"password": "admin@123",    "role": "admin",  "otas": []},
    "mahak.goyal":    {"password": "mahak@123",    "role": "member", "otas": ["MMT/GI"]},
    "puneet.yadav":   {"password": "puneet@123",   "role": "member", "otas": ["BDC", "GMB", "WebApp"]},
    "abhishek.khushwa": {"password": "abhishek@123", "role": "member", "otas": ["Agoda"]},
    "irfan":    {"password": "irfan@123",    "role": "member", "otas": ["Expedia"]},
    "faique":   {"password": "faique@123",   "role": "member", "otas": ["Cleartrip"]},
    "yash.yadav":  {"password": "yash@123",     "role": "member", "otas": ["PL"]},
}

# ── Column groups ─────────────────────────────────────────────────────
IDENTITY_COLS = ["FH", "Property Name", "Property City", "Category (A/B/C)"]

OTA_LIVE_COLS = [
    "OTA Live [MMT/GI]", "OTA Live [BDC]", "OTA Live [GMB]",
    "OTA Live [Agoda]", "OTA Live [Cleartrip]", "OTA Live [Expedia]",
]
REVIEW_RATING_COLS = [
    "Review | Rating [MMT]", "Review | Rating [BDC]",
    "Review | Rating [GMB]", "Review | Rating [GI]",
]
PARALLEL_LISTING_COLS = [
    "Parallel Listing [MMT]", "Parallel Listing [BDC]",
    "Parallel Listing [GMB]", "Parallel Listing [GI]",
]
LOCATION_COLS = [
    "Location [FH Web]", "Location [MMT]", "Location [BDC]",
    "Location [GMB]", "Location [GI]",
]
PHOTOSHOOT_COLS = ["Photoshoot"]
PHOTOS_COLS = [
    "Photos Q&A [FH Web]", "Photos Q&A [MMT]", "Photos Q&A [BDC]",
    "Photos Q&A [GMB]", "Photos Q&A [GI]",
]
AMENITIES_COLS = [
    "Amenities & RLD [FH]", "Amenities & RLD [MMT]",
    "Amenities & RLD [BDC]", "Amenities & RLD [GI]",
]
COMPSET_COLS = ["Compset [MMT]", "OTA Price Visible [GMB]"]
OTHER_COLS   = ["Findings", "No. of Checks"]

ALL_EDITABLE_COLS = (
    ["Remarks", "Final CheckDate"]
    + OTA_LIVE_COLS + LOCATION_COLS + PHOTOSHOOT_COLS
    + PHOTOS_COLS + AMENITIES_COLS
)

REMINDER_TRIGGER_COLS = (
    OTA_LIVE_COLS + LOCATION_COLS + PHOTOSHOOT_COLS
    + PHOTOS_COLS + AMENITIES_COLS
)

# ── Dropdowns ─────────────────────────────────────────────────────────
DROPDOWNS = {
    "ota_live":   ["Check", "Not Live"],
    "location":   ["Check", "Wrong", "Slightly Wrong"],
    "photoshoot": ["Check", "Not Done", "Runner", "Facade", "Reception"],
    "photos":     ["Check", "Not Done"],
    "amenities":  ["Check", "Less Amenities", "Not Live"],
    "fh_status":  ["Live", "Churned", "SoldOut"],
    "compset":    ["Check", "Not added"],
    "parallel":   ["Check", "Not Live"],
}

COL_DROPDOWN_MAP = {
    **{c: "ota_live"   for c in OTA_LIVE_COLS},
    **{c: "location"   for c in LOCATION_COLS},
    **{c: "photos"     for c in PHOTOS_COLS},
    **{c: "amenities"  for c in AMENITIES_COLS},
    **{c: "parallel"   for c in PARALLEL_LISTING_COLS},
    **{c: "compset"    for c in COMPSET_COLS},
    "Photoshoot": "photoshoot",
    "FH Status":  "fh_status",
}

OTA_COLUMN_MAP = {
    "MMT/GI": {
        "live_col": "OTA Live [MMT/GI]",
        "dependent": [
            "Review | Rating [MMT]", "Review | Rating [GI]",
            "Parallel Listing [MMT]", "Location [MMT]",
            "Photos Q&A [MMT]", "Amenities & RLD [MMT]", "Compset [MMT]",
        ]
    },
    "BDC": {
        "live_col": "OTA Live [BDC]",
        "dependent": [
            "Review | Rating [BDC]", "Parallel Listing [BDC]",
            "Location [BDC]", "Photos Q&A [BDC]", "Amenities & RLD [BDC]",
        ]
    },
    "GMB": {
        "live_col": "OTA Live [GMB]",
        "dependent": [
            "Review | Rating [GMB]", "Parallel Listing [GMB]",
            "Location [GMB]", "Photos Q&A [GMB]", "OTA Price Visible [GMB]",
        ]
    },
    "Agoda":     {"live_col": "OTA Live [Agoda]",     "dependent": []},
    "Cleartrip": {"live_col": "OTA Live [Cleartrip]", "dependent": []},
    "Expedia":   {"live_col": "OTA Live [Expedia]",   "dependent": []},
}

OTA_TO_EDITABLE_COLS = {
    "MMT/GI": [
        "OTA Live [MMT/GI]", "Review | Rating [MMT]", "Review | Rating [GI]",
        "Location [MMT]", "Photos Q&A [MMT]", "Amenities & RLD [MMT]",
        "Parallel Listing [MMT]", "Compset [MMT]", "Remarks", "Final CheckDate",
    ],
    "BDC": [
        "OTA Live [BDC]", "Review | Rating [BDC]", "Location [BDC]",
        "Photos Q&A [BDC]", "Amenities & RLD [BDC]", "Parallel Listing [BDC]",
        "Remarks", "Final CheckDate",
    ],
    "GMB": [
        "OTA Live [GMB]", "Review | Rating [GMB]", "Location [GMB]",
        "Photos Q&A [GMB]", "Parallel Listing [GMB]", "OTA Price Visible [GMB]",
        "Remarks", "Final CheckDate",
    ],
    "Agoda":     ["OTA Live [Agoda]",     "Remarks", "Final CheckDate"],
    "Cleartrip": ["OTA Live [Cleartrip]", "Remarks", "Final CheckDate"],
    "Expedia":   ["OTA Live [Expedia]",   "Remarks", "Final CheckDate"],
    "WebApp":    ["Location [FH Web]", "Photos Q&A [FH Web]", "Amenities & RLD [FH]",
                  "Remarks", "Final CheckDate"],
    "PL":        ["Parallel Listing [MMT]", "Parallel Listing [BDC]",
                  "Parallel Listing [GMB]", "Parallel Listing [GI]",
                  "Remarks", "Final CheckDate"],
}

STATUS_COLORS = {
    "Check":          "#10B981",
    "Not Live":       "#EF4444",
    "Wrong":          "#F97316",
    "Slightly Wrong": "#F59E0B",
    "Not Done":       "#EF4444",
    "Runner":         "#8B5CF6",
    "Facade":         "#6366F1",
    "Reception":      "#EC4899",
    "Less Amenities": "#F97316",
    "Churned":        "#EF4444",
    "SoldOut":        "#64748B",
    "Live":           "#10B981",
    "Added":          "#10B981",
    "Not added":      "#EF4444",
}