# ============================================================
# scoring.py — Gamification score calculation
# ============================================================

from utils import get_time_bonus


def calculate_daily_score(
    position: int,
    total_participants: int,
    dt=None,
    time_bonus_override: float = None,
) -> float:
    """
    Calculate the daily gamification score for a user.

    Formula:
        Base Score  = (total_participants + 1 - position) / 10
        Time Bonus  = based on Israel hour (or override for pre-reports)
        Total Score = Base Score + Time Bonus

    Args:
        position (int):
            1-based submission order for this user on this day.
            Counted as: (non-empty cells in today's column) + 1.
        total_participants (int):
            Total number of active participants (N), read dynamically
            from the sheet so it updates when names are added.
        dt (datetime, optional):
            Israel datetime used to calculate the time bonus.
            Required unless time_bonus_override is provided.
        time_bonus_override (float, optional):
            If set, skips the time-based calculation and uses this
            value directly. Used for Thursday pre-reporting, where
            the bonus is always the maximum (2.5 — as if reporting
            at 00:00).

    Returns:
        float: Daily score, rounded to 1 decimal place.

    Examples:
        # 1st to report at 05:30 Israel time, 58 participants
        calculate_daily_score(1, 58, dt=...) → 5.8 + 2.5 = 8.3

        # 10th to report at 07:45, 58 participants
        calculate_daily_score(10, 58, dt=...) → 4.9 + 1.0 = 5.9

        # Pre-report on Thursday for Friday (always +2.5 bonus)
        calculate_daily_score(3, 58, time_bonus_override=2.5) → 5.6 + 2.5 = 8.1
    """
    base_score = (total_participants + 1 - position) / 10

    if time_bonus_override is not None:
        time_bonus = time_bonus_override
    elif dt is not None:
        time_bonus = get_time_bonus(dt)
    else:
        time_bonus = 0.0

    return round(base_score + time_bonus, 1)


def get_max_possible_score(total_participants: int) -> float:
    """
    Return the maximum possible score for a given participant count.
    Achieved by being 1st and reporting between 00:00–05:59.
    """
    return calculate_daily_score(1, total_participants, time_bonus_override=2.5)
