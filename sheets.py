# ============================================================
# sheets.py — All Google Sheets read/write operations
# ============================================================

import time
import gspread
from gspread.utils import rowcol_to_a1
from google.oauth2.service_account import Credentials
import streamlit as st

from config import (
    SHEET_ID, SHEET_YAMAMIM, SHEET_SHAOT, SHEET_NIKUD,
    NAMES_START_ROW, NAMES_END_ROW, DATES_ROW,
    SENTINEL_HEADER, CACHE_TTL, LEADERBOARD_SIZE,
    DATA_START_COL,
)
from utils import hex_to_rgb_float, format_date_str, format_time_str, get_israel_now

# ── Google API Scopes ────────────────────────────────────────
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]


# ── Authentication ───────────────────────────────────────────

def _get_credentials() -> Credentials:
    """
    Load service account credentials.
    1. Tries st.secrets['gcp_service_account'] (Streamlit Cloud deployment).
    2. Falls back to local file 'secrets/service_account.json' (development).
    """
    try:
        creds_dict = dict(st.secrets["gcp_service_account"])
        return Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
    except Exception:
        return Credentials.from_service_account_file(
            "secrets/service_account.json", scopes=SCOPES
        )


@st.cache_resource
def _get_client() -> gspread.Client:
    """Authenticated gspread client — cached for the lifetime of the server process."""
    return gspread.authorize(_get_credentials())


@st.cache_resource
def _get_spreadsheet() -> gspread.Spreadsheet:
    """Open the target spreadsheet — cached as a resource."""
    return _get_client().open_by_key(SHEET_ID)


def _get_sheet(sheet_name: str) -> gspread.Worksheet:
    """Get a worksheet by name (uses the cached spreadsheet object)."""
    return _get_spreadsheet().worksheet(sheet_name)


# ── Name Loading ─────────────────────────────────────────────

@st.cache_data(ttl=CACHE_TTL)
def load_names() -> list[dict]:
    """
    Load all participant names from 'ימ"מים' sheet (A3:B60).

    Returns:
        List of dicts with keys: full_name, surname, family_name, row
        'row' is the 1-based sheet row number.
        Only rows with a non-empty surname are included.
    """
    ws = _get_sheet(SHEET_YAMAMIM)
    data = ws.get(f"A{NAMES_START_ROW}:B{NAMES_END_ROW}")
    names = []
    for i, row in enumerate(data):
        surname     = row[0].strip() if len(row) > 0 else ""
        family_name = row[1].strip() if len(row) > 1 else ""
        if surname:
            names.append({
                "full_name":   f"{surname} {family_name}".strip(),
                "surname":     surname,
                "family_name": family_name,
                "row":         NAMES_START_ROW + i,  # 1-based sheet row
            })
    return names


def get_user_info(full_name: str, names: list[dict]) -> dict | None:
    """Return the name dict for a given full_name, or None if not found."""
    for n in names:
        if n["full_name"] == full_name:
            return n
    return None


def count_participants(names: list[dict]) -> int:
    """Return the total number of active participants (N)."""
    return len(names)


# ── Date Column Lookup ───────────────────────────────────────

@st.cache_data(ttl=CACHE_TTL)
def find_column_map() -> dict:
    """
    Scan row 2 of 'ימ"מים' from column C onwards to build a dynamic column map.

    Scans until it finds the sentinel value 'סה"כ', which marks:
      - End of date columns (exclusive)
      - The total cumulative score column (inclusive)
      - The rank column = sentinel_col + 1

    Returns dict with keys:
        'dates'       : {date_str: col_idx (1-based), ...} for all date columns
        'total_score' : col_idx (1-based) of the 'סה"כ' column
        'rank'        : col_idx (1-based) of the rank column (after 'סה"כ')
    """
    ws = _get_sheet(SHEET_YAMAMIM)
    row2 = ws.row_values(DATES_ROW)  # Full row 2 as list (0-indexed)

    col_map = {"dates": {}, "total_score": None, "rank": None}

    for i, val in enumerate(row2):
        col_1based = i + 1
        if col_1based < DATA_START_COL:
            continue  # Skip A and B columns
        stripped = val.strip()
        if stripped == SENTINEL_HEADER:
            col_map["total_score"] = col_1based
            col_map["rank"]        = col_1based + 1
            break  # Stop scanning — no date columns after sentinel
        if stripped:  # Non-empty, non-sentinel → it's a date
            col_map["dates"][stripped] = col_1based

    return col_map


def find_date_column(date_str: str) -> int | None:
    """
    Find the 1-based column index for a given date string (d.m format).
    Uses the cached column map built from the sentinel scan.

    Returns:
        Column index (int, 1-based) if found, else None.
    """
    col_map = find_column_map()
    return col_map["dates"].get(date_str)


# ── Submission Status Checks ─────────────────────────────────

@st.cache_data(ttl=CACHE_TTL)
def load_status_column(date_str: str) -> tuple[list, int | None]:
    """
    Load the full status column for a given date from 'ימ"מים'.

    Returns:
        (column_values_list, col_idx) or ([], None) if date not found.
        column_values_list is 0-indexed; row 3 = index 2.
    """
    col_idx = find_date_column(date_str)
    if col_idx is None:
        return [], None
    ws = _get_sheet(SHEET_YAMAMIM)
    return ws.col_values(col_idx), col_idx


def has_user_submitted(user_row: int, date_str: str) -> bool:
    """
    Check if a specific user has already submitted for a given date.
    Uses cached column data.
    """
    col_values, _ = load_status_column(date_str)
    if not col_values:
        return False
    idx = user_row - 1  # Convert 1-based row → 0-based list index
    return idx < len(col_values) and bool(col_values[idx].strip())


def count_submissions_for_date(date_str: str) -> int:
    """
    Count how many unique users have submitted for a given date.
    Used to determine submission_position for score calculation.
    Each name can only appear once (re-submissions overwrite),
    so counting non-empty cells = counting unique reporters.
    """
    col_values, _ = load_status_column(date_str)
    if not col_values:
        return 0
    # Data rows are NAMES_START_ROW (3) to NAMES_END_ROW (60)
    # List is 0-indexed, so rows 3-60 = indices 2-59
    data_slice = col_values[NAMES_START_ROW - 1 : NAMES_END_ROW]
    return sum(1 for v in data_slice if v.strip())


# ── Score & Rank Loading ─────────────────────────────────────

def load_user_score_and_rank(user_row: int) -> tuple[float | None, int | None]:
    """
    Read total cumulative score and rank for a specific user row.
    Column positions are discovered dynamically via find_column_map().
    Makes a direct (uncached) API call so values are always fresh after a write.
    """
    col_map = find_column_map()
    total_col = col_map["total_score"]
    rank_col  = col_map["rank"]

    if total_col is None or rank_col is None:
        return None, None

    ws = _get_sheet(SHEET_NIKUD)
    total_score_val = ws.cell(user_row, total_col).value
    rank_val        = ws.cell(user_row, rank_col).value

    total_score = float(total_score_val) if total_score_val else None
    rank        = int(rank_val)         if rank_val        else None
    return total_score, rank


def load_daily_score(user_row: int, date_str: str) -> float | None:
    """
    Read the daily score for a user on a specific date from 'ניקוד'.
    Returns None if no score exists for that date.
    """
    col_idx = find_date_column(date_str)
    if col_idx is None:
        return None
    ws = _get_sheet(SHEET_NIKUD)
    val = ws.cell(user_row, col_idx).value
    return float(val) if val else None


# ── Leaderboard ──────────────────────────────────────────────

@st.cache_data(ttl=CACHE_TTL)
def load_leaderboard() -> list[dict]:
    """
    Load the top LEADERBOARD_SIZE users by rank.
    Score and rank column positions are discovered dynamically via find_column_map().

    Returns:
        List of dicts: {name, total_score, rank}, sorted by rank ascending.
    """
    col_map    = find_column_map()
    total_col  = col_map["total_score"]
    rank_col   = col_map["rank"]

    if total_col is None or rank_col is None:
        return []

    ws_nikud   = _get_sheet(SHEET_NIKUD)
    ws_yamamim = _get_sheet(SHEET_YAMAMIM)

    # Batch read names and score/rank columns in one call each
    names_data  = ws_yamamim.get(f"A{NAMES_START_ROW}:B{NAMES_END_ROW}")
    # Read from A to rank column for each row
    scores_data = ws_nikud.get(f"A{NAMES_START_ROW}:A{NAMES_END_ROW}"), \
                  ws_nikud.get(f"A{NAMES_START_ROW}:B{NAMES_END_ROW}")

    # Read total_score and rank columns directly
    from utils import col_num_to_letter
    total_col_letter = col_num_to_letter(total_col)
    rank_col_letter  = col_num_to_letter(rank_col)
    score_range = f"{total_col_letter}{NAMES_START_ROW}:{rank_col_letter}{NAMES_END_ROW}"
    score_rank_data = ws_nikud.get(score_range)

    leaderboard = []
    for i, name_row in enumerate(names_data):
        surname     = name_row[0].strip() if len(name_row) > 0 else ""
        family_name = name_row[1].strip() if len(name_row) > 1 else ""
        if not surname:
            continue
        score_row   = score_rank_data[i] if i < len(score_rank_data) else []
        total_score_val = score_row[0].strip() if len(score_row) > 0 else ""
        rank_val        = score_row[1].strip() if len(score_row) > 1 else ""

        leaderboard.append({
            "name":        f"{surname} {family_name}".strip(),
            "total_score": float(total_score_val) if total_score_val else 0.0,
            "rank":        int(rank_val) if rank_val else 999,
        })

    leaderboard.sort(key=lambda x: x["rank"])
    return leaderboard[:LEADERBOARD_SIZE]


# ── Streak Calculation ───────────────────────────────────────

def calculate_streak(user_row: int) -> int:
    """
    Count consecutive days (backwards from yesterday) where the user
    has a non-empty status cell in 'ימ"מים'.

    Returns:
        int: streak count (0 if no streak).
    """
    from datetime import timedelta

    ws = _get_sheet(SHEET_YAMAMIM)
    date_row  = ws.row_values(DATES_ROW)       # All date header values
    user_row_values = ws.row_values(user_row)   # All values for this user

    today   = get_israel_now()
    streak  = 0
    check   = today - timedelta(days=1)  # Start from yesterday

    for _ in range(len(date_row)):
        date_str = format_date_str(check)
        if date_str in date_row:
            col_idx = date_row.index(date_str)  # 0-based
            if col_idx < len(user_row_values) and user_row_values[col_idx].strip():
                streak += 1
            else:
                break
        else:
            break
        check -= timedelta(days=1)

    return streak


# ── Write Operations ─────────────────────────────────────────

def submit_status(user_row: int, col_idx: int, color_rgb: dict) -> bool:
    """
    Write status '1' and paint the cell background in 'ימ"מים'.
    Called on every submission (first and re-submissions).

    Returns:
        True on success, False on failure.
    """
    try:
        ws = _get_sheet(SHEET_YAMAMIM)
        cell_addr = rowcol_to_a1(user_row, col_idx)
        ws.update_cell(user_row, col_idx, 1)
        ws.format(cell_addr, {"backgroundColor": color_rgb})
        return True
    except Exception as e:
        st.error(f"שגיאה בכתיבת הסטטוס: {e}")
        return False


def submit_time(user_row: int, col_idx: int, time_str: str) -> bool:
    """
    Write the reporting time to 'שעות דיווח'.
    Called only on the FIRST submission of the day.

    Returns:
        True on success, False on failure.
    """
    try:
        ws = _get_sheet(SHEET_SHAOT)
        ws.update_cell(user_row, col_idx, time_str)
        return True
    except Exception as e:
        st.error(f"שגיאה בכתיבת הזמן: {e}")
        return False


def submit_score(user_row: int, col_idx: int, score: float) -> bool:
    """
    Write the daily score to 'ניקוד'.
    Called only on the FIRST submission of the day.

    Returns:
        True on success, False on failure.
    """
    try:
        ws = _get_sheet(SHEET_NIKUD)
        ws.update_cell(user_row, col_idx, score)
        return True
    except Exception as e:
        st.error(f"שגיאה בכתיבת הניקוד: {e}")
        return False


def wait_for_sheet_recalc(seconds: float = 2.0):
    """
    Wait briefly for Google Sheets to recalculate formulas
    (CS total and CT rank columns) after a score write.
    """
    time.sleep(seconds)


# ── Full Submission Flow ─────────────────────────────────────

def perform_first_submission(
    user_row: int,
    date_str: str,
    color_rgb: dict,
    score: float,
) -> tuple[float | None, int | None, bool]:
    """
    Complete first-submission flow:
    1. Write status + color to ימ"מים
    2. Write time to שעות דיווח
    3. Write score to ניקוד
    4. Wait for sheet recalc
    5. Read back total score and rank

    Returns:
        (total_score, rank, success_bool)
    """
    col_idx = find_date_column(date_str)
    if col_idx is None:
        return None, None, False

    now      = get_israel_now()
    time_str = format_time_str(now)

    ok1 = submit_status(user_row, col_idx, color_rgb)
    ok2 = submit_time(user_row, col_idx, time_str)
    ok3 = submit_score(user_row, col_idx, score)

    if not (ok1 and ok2 and ok3):
        return None, None, False

    wait_for_sheet_recalc(2.0)
    total_score, rank = load_user_score_and_rank(user_row)

    # Invalidate cached column data so UI reflects the new submission
    load_status_column.clear()

    return total_score, rank, True


def perform_resubmission(
    user_row: int,
    date_str: str,
    color_rgb: dict,
) -> bool:
    """
    Re-submission flow (status change only — time and score unchanged):
    1. Write new status + color to ימ"מים
    Returns:
        True on success.
    """
    col_idx = find_date_column(date_str)
    if col_idx is None:
        return False

    ok = submit_status(user_row, col_idx, color_rgb)
    if ok:
        load_status_column.clear()
    return ok
