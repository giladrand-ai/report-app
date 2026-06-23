# ============================================================
# utils.py — Date, time, and color helper functions
# ============================================================

import pytz
from datetime import datetime, timedelta
from config import TIMEZONE


def get_israel_now() -> datetime:
    """Return current datetime in Israel timezone (DST-aware)."""
    tz = pytz.timezone(TIMEZONE)
    return datetime.now(tz)


def format_date_str(dt: datetime) -> str:
    """
    Format a datetime as 'd.m' — no leading zeros.
    Examples: 1.6,  20.6,  5.11
    """
    return f"{dt.day}.{dt.month}"


def get_time_bonus(dt: datetime) -> float:
    """
    Return the time-of-day bonus points based on Israel hour.
    00:00–05:59 → 2.5
    06:00–06:59 → 1.5
    07:00–07:59 → 1.0
    08:00–08:59 → 0.5
    09:00+      → 0.0
    """
    hour = dt.hour
    if hour < 6:   return 2.5
    elif hour < 7: return 1.5
    elif hour < 8: return 1.0
    elif hour < 9: return 0.5
    else:          return 0.0


def is_thursday(dt: datetime = None) -> bool:
    """Return True if the given datetime (or now) is Thursday in Israel."""
    if dt is None:
        dt = get_israel_now()
    return dt.weekday() == 3  # Monday=0, Thursday=3, Saturday=5


def get_thursday_target_dates(dt: datetime = None) -> dict:
    """
    Returns the three selectable dates for Thursday pre-reporting.
    Keys: 'today', 'friday', 'saturday'
    Values: (datetime object, 'd.m' string)
    """
    if dt is None:
        dt = get_israel_now()
    friday   = dt + timedelta(days=1)
    saturday = dt + timedelta(days=2)
    return {
        "today":    (dt,       format_date_str(dt)),
        "friday":   (friday,   format_date_str(friday)),
        "saturday": (saturday, format_date_str(saturday)),
    }


def hex_to_rgb_float(hex_color: str) -> dict:
    """
    Convert a hex color string to Google Sheets API RGB format (0.0–1.0 scale).
    Example: '#4CAF50' → {'red': 0.298, 'green': 0.686, 'blue': 0.314}
    """
    hex_color = hex_color.lstrip("#")
    return {
        "red":   int(hex_color[0:2], 16) / 255,
        "green": int(hex_color[2:4], 16) / 255,
        "blue":  int(hex_color[4:6], 16) / 255,
    }


def format_time_str(dt: datetime) -> str:
    """Format a datetime as HH:MM:SS for reporting times."""
    return dt.strftime("%H:%M:%S")


def col_num_to_letter(col: int) -> str:
    """
    Convert a 1-based column number to a column letter string.
    Examples: 1→'A', 26→'Z', 27→'AA', 97→'CS', 98→'CT'
    """
    result = ""
    while col > 0:
        col, remainder = divmod(col - 1, 26)
        result = chr(65 + remainder) + result
    return result
