# ============================================================
# config.py — App-wide constants and configuration
# ============================================================

# ── Google Sheet ────────────────────────────────────────────
SHEET_ID = "1-jCThK6QogAExN-Iu_iTkTIlt-D47fvZvswXjyRLMrQ"

SHEET_YAMAMIM = 'ימ"מים'    # Status sheet
SHEET_SHAOT   = 'שעות דיווח' # Reporting times sheet
SHEET_NIKUD   = 'ניקוד'      # Scores sheet

# ── Data Layout (1-based row/col numbers) ───────────────────
NAMES_START_ROW = 3    # First row of name data
NAMES_END_ROW   = 60   # Last possible row
DATES_ROW       = 2    # Row containing date headers (d.m format)
DATA_START_COL  = 3    # Column C — first date column

# Sentinel header that marks the end of date columns in row 2.
# The app scans row 2 from column C until it finds this value.
# סה"כ column = total cumulative score
# Column immediately after סה"כ = rank/position
SENTINEL_HEADER = 'סה"כ'

# ── Timezone ────────────────────────────────────────────────
TIMEZONE = "Asia/Jerusalem"  # Handles Israel DST automatically

# ── Caching ─────────────────────────────────────────────────
CACHE_TTL = 45  # Seconds before cached sheet data is refreshed

# ── Status Options ──────────────────────────────────────────
# Each option: id, Hebrew label, cell background color (RGB object), emoji
# Google Sheets API requires RGB values as floats between 0.0 and 1.0
STATUS_OPTIONS = [
    {
        "id":        "army",
        "label":     "בצבא",
        "color_rgb": {"red": 0.0, "green": 1.0, "blue": 0.0},   # Green (#00ff00)
        "emoji":     "🟢",
    },
    {
        "id":        "home",
        "label":     "בבית",
        "color_rgb": {"red": 1.0, "green": 1.0, "blue": 0.0},   # Yellow (#ffff00)
        "emoji":     "🟡",
    },
    {
        "id":        "returning",
        "label":     "מגיע היום",
        "color_rgb": {"red": 1.0, "green": 0.6, "blue": 0.0},   # Orange (#ff9900)
        "emoji":     "🟠",
    },
    {
        "id":        "leaving",
        "label":     "יוצא היום",
        "color_rgb": {"red": 1.0, "green": 0.6, "blue": 0.0},   # Orange (#ff9900)
        "emoji":     "🟠",
    },
]

# ── Thursday Pre-Reporting Labels ───────────────────────────
THURSDAY_DATE_OPTIONS = {
    "today":    "היום - יום ה'",
    "friday":   "מחר - יום ו'",
    "saturday": "מחרתיים - שבת",
}

# ── Leaderboard ─────────────────────────────────────────────
LEADERBOARD_SIZE = 5  # Number of top users to show

# ── UI Text (Hebrew) ─────────────────────────────────────────
TXT_APP_TITLE        = "דיווח יומי 📍"
TXT_SELECT_NAME      = "מי אתה?"
TXT_SELECT_NAME_HINT = "בחר את שמך מהרשימה"
TXT_REPORTED         = "✅ דיווחת היום!"
TXT_NOT_REPORTED     = "❌ טרם דיווחת היום"
TXT_SCORE_TODAY      = "ניקוד היום"
TXT_SCORE_TOTAL      = "ניקוד כולל"
TXT_RANK             = "מקום"
TXT_STREAK           = "רצף"
TXT_DAYS             = "ימים"
TXT_REFRESH          = "🔄 רענן"
TXT_CHANGE_NAME      = "החלף שם"
TXT_LEADERBOARD      = "🏆 טבלת מובילים"
TXT_ERROR_CONNECT    = "לא ניתן להתחבר לגיליון. נסה שוב מאוחר יותר."
TXT_ERROR_DATE       = "התאריך לא נמצא בגיליון. פנה למנהל."
TXT_ERROR_USER       = "המשתמש לא נמצא. אנא בחר שם מחדש."
TXT_CONFIRM          = "אישור"
TXT_DAYS_STREAK      = "ימי רצף"
