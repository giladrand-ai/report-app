# ============================================================
# app.py — Friends Location & Gamification App
# ============================================================

import streamlit as st
import time
from datetime import datetime, timedelta
import extra_streamlit_components as stx

from sheets import (
    load_names, count_submissions_for_date,
    has_user_submitted, load_user_score_and_rank, load_daily_score,
    load_leaderboard, calculate_streak, perform_first_submission,
    perform_resubmission, get_user_info, count_participants,
    find_date_column,
)
from scoring import calculate_daily_score
from utils import get_israel_now, format_date_str, is_thursday, get_thursday_target_dates
from config import STATUS_OPTIONS, THURSDAY_DATE_OPTIONS

# ── Page config ──────────────────────────────────────────────
st.set_page_config(
    page_title="דיווח יומי 📍",
    page_icon="📍",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# ════════════════════════════════════════════════════════════
# GLOBAL CSS
# ════════════════════════════════════════════════════════════
st.markdown("""<style>
@import url('https://fonts.googleapis.com/css2?family=Heebo:wght@300;400;500;600;700;800;900&display=swap');

html, body, [class*="css"] {
    font-family: 'Heebo', sans-serif !important;
    direction: rtl;
}
.stApp {
    background: radial-gradient(ellipse at top, #E8EEF5 0%, #F4F7FA 50%, #DFE7F0 100%);
    min-height: 100vh;
}
#MainMenu, footer, header, .stDeployButton { visibility: hidden; }
.block-container {
    padding: 0.4rem 0.8rem 3rem !important;
    max-width: 440px !important;
    margin: 0 auto !important;
}

/* ── App Title ── */
.app-title {
    font-size: 1.65rem; font-weight: 900; text-align: center;
    background: linear-gradient(135deg, #4CAF50 0%, #FFC107 55%, #FF9800 100%);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    background-clip: text;
    margin: 0.3rem 0 0.05rem;
}

/* ── Time Block ── */
.time-block {
    text-align: center; background: rgba(0,0,0,0.02);
    border-radius: 14px; padding: 0.7rem 1rem 0.5rem;
    margin: 0.4rem 0; border: 1px solid rgba(0,0,0,0.06);
    box-shadow: 0 4px 15px rgba(0,0,0,0.02);
}
.time-big { font-size: 2.1rem; font-weight: 900; color: #222; letter-spacing: 4px; }
.date-text { font-size: 0.78rem; color: rgba(0,0,0,0.55); }

/* ── Badge ── */
.badge-wrap { text-align: center; margin: 0.35rem 0; }
.badge {
    display: inline-block; padding: 0.3rem 1.1rem;
    border-radius: 20px; font-size: 0.87rem; font-weight: 700;
}
.badge-ok { background: rgba(76,175,80,0.15); border: 1.5px solid #4CAF50; color: #81C784; }
.badge-no { background: rgba(239,83,80,0.12); border: 1.5px solid rgba(239,83,80,0.4); color: #EF9A9A; }

/* ── Score Cards ── */
.scores-row { display: flex; gap: 0.38rem; margin: 0.42rem 0; }
.score-card {
    flex: 1; background: #fff;
    border-radius: 12px; padding: 0.62rem 0.15rem;
    text-align: center; border: 1px solid rgba(0,0,0,0.06);
    box-shadow: 0 2px 8px rgba(0,0,0,0.03);
}
.sv { font-size: 1.38rem; font-weight: 900; line-height: 1.1; }
.sl { font-size: 0.63rem; color: rgba(0,0,0,0.5); margin-top: 0.1rem; font-weight: 600; }
.sv-today { color: #FFB300; }
.sv-total { color: #0288D1; }
.sv-rank  { color: #43A047; }
.sv-streak{ color: #F57C00; }

/* ════════════════════════════════════════════════════════════
   STATUS CIRCLES
   Strategy: inject a marker div (#circ-grid-start) right
   before the circles, then use CSS sibling selectors to
   target ONLY the two rows of circles — no fragile column
   counting, no JavaScript.
   ════════════════════════════════════════════════════════════ */

/* ── Center the stButton wrapper in every circle column ── */
div[data-testid="column"] .stButton {
    display: flex !important;
    justify-content: center !important;
    align-items: center !important;
}

/* ── Base style for ALL circle buttons ── */
div[data-testid="stVerticalBlockChild"]:has(#circ-grid-start)
  ~ div[data-testid="stVerticalBlockChild"]
  div[data-testid="stHorizontalBlock"]:not(:has(button[data-testid="baseButton-primary"]))
  .stButton > button {
    border-radius: 50% !important;
    width: 140px !important;
    height: 140px !important;
    min-height: 0 !important;
    padding: 6px !important;
    font-family: 'Heebo', sans-serif !important;
    font-size: 0.88rem !important;
    font-weight: 800 !important;
    color: white !important;
    white-space: pre-line !important;
    line-height: 1.35 !important;
    text-align: center !important;
    border: 2.5px solid rgba(255,255,255,0.2) !important;
    box-shadow: 0 6px 22px rgba(0,0,0,0.5) !important;
    transition: all 0.25s cubic-bezier(0.34, 1.56, 0.64, 1) !important;
    display: flex !important;
    flex-direction: column !important;
    align-items: center !important;
    justify-content: center !important;
    /* Default = orange (fallback for row 2) */
    background: #ff9900 !important;
    border-color: #ff9900 !important;
    color: black !important;
}
div[data-testid="stVerticalBlockChild"]:has(#circ-grid-start)
  ~ div[data-testid="stVerticalBlockChild"]
  div[data-testid="stHorizontalBlock"]:not(:has(button[data-testid="baseButton-primary"]))
  .stButton > button:hover {
    transform: scale(1.09) !important;
    box-shadow: 0 10px 30px rgba(0,0,0,0.6) !important;
}
div[data-testid="stVerticalBlockChild"]:has(#circ-grid-start)
  ~ div[data-testid="stVerticalBlockChild"]
  div[data-testid="stHorizontalBlock"]:not(:has(button[data-testid="baseButton-primary"]))
  .stButton > button:active {
    transform: scale(0.93) !important;
}

/* ── ROW 1 COLORS (the stHorizontalBlock immediately after the marker) ── */
/* GREEN — col 1 (בצבא) */
div[data-testid="stVerticalBlockChild"]:has(#circ-grid-start)
  + div[data-testid="stVerticalBlockChild"]
  div[data-testid="stHorizontalBlock"]
  > div:nth-child(1) .stButton > button {
    background: #00ff00 !important;
    border-color: #00ff00 !important;
    color: black !important;
}
/* YELLOW — col 2 (בבית) */
div[data-testid="stVerticalBlockChild"]:has(#circ-grid-start)
  + div[data-testid="stVerticalBlockChild"]
  div[data-testid="stHorizontalBlock"]
  > div:nth-child(2) .stButton > button {
    background: #ffff00 !important;
    border-color: #ffff00 !important;
    color: black !important;
}

/* ── ROW 2 COLORS (second stHorizontalBlock after the marker) ── */
/* ORANGE — col 1 (חוזר היום) */
div[data-testid="stVerticalBlockChild"]:has(#circ-grid-start)
  + div[data-testid="stVerticalBlockChild"]
  + div[data-testid="stVerticalBlockChild"]
  div[data-testid="stHorizontalBlock"]
  > div:nth-child(1) .stButton > button {
    background: #ff9900 !important;
    border-color: #ff9900 !important;
    color: black !important;
}
/* ORANGE — col 2 (יוצא היום) */
div[data-testid="stVerticalBlockChild"]:has(#circ-grid-start)
  + div[data-testid="stVerticalBlockChild"]
  + div[data-testid="stVerticalBlockChild"]
  div[data-testid="stHorizontalBlock"]
  > div:nth-child(2) .stButton > button {
    background: #ff9900 !important;
    border-color: #ff9900 !important;
    color: black !important;
}

/* ── SECONDARY BUTTONS — base style for all pages ── */
button[data-testid="baseButton-secondary"] {
    border-radius: 14px !important;
    min-height: 56px !important;
    height: auto !important;
    font-family: 'Heebo', sans-serif !important;
    font-size: 1rem !important;
    font-weight: 700 !important;
    border: 2px solid rgba(255,255,255,0.15) !important;
    box-shadow: 0 4px 14px rgba(0,0,0,0.4) !important;
    transition: all 0.2s ease !important;
    padding: 0.6rem 1rem !important;
}
button[data-testid="baseButton-secondary"]:active {
    transform: scale(0.96) !important;
}
button[data-testid="baseButton-primary"] {
    background: #fff !important;
    color: #444 !important;
    border: 1px solid rgba(0,0,0,0.1) !important;
    border-radius: 10px !important;
    height: auto !important;
    padding: 0.28rem 0.85rem !important;
    font-size: 0.8rem !important;
    font-weight: 600 !important;
    font-family: 'Heebo', sans-serif !important;
    box-shadow: 0 2px 6px rgba(0,0,0,0.03) !important;
    transition: all 0.18s ease !important;
    line-height: 1.5 !important;
}
button[data-testid="baseButton-primary"]:hover {
    background: #f8f9fa !important;
    color: #111 !important;
    border-color: rgba(0,0,0,0.2) !important;
    transform: translateY(-1px) !important;
    box-shadow: 0 4px 10px rgba(0,0,0,0.06) !important;
}

/* ════════════════════════════════
   CENTERED SPINNER OVERLAY
   ════════════════════════════════ */
div[data-testid="stSpinner"] {
    position: fixed !important;
    inset: 0 !important;
    z-index: 9999 !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    background: rgba(255, 255, 255, 0.65) !important;
    backdrop-filter: blur(5px) !important;
    -webkit-backdrop-filter: blur(5px) !important;
}
div[data-testid="stSpinner"] > div {
    background: #fff !important;
    border: 1px solid rgba(0,0,0,0.08) !important;
    border-radius: 22px !important;
    padding: 2.2rem 3rem !important;
    display: flex !important;
    flex-direction: column !important;
    align-items: center !important;
    gap: 1rem !important;
    box-shadow: 0 20px 60px rgba(0,0,0,0.15) !important;
}
div[data-testid="stSpinner"] p {
    color: #333 !important;
    font-size: 1rem !important;
    font-weight: 600 !important;
    font-family: 'Heebo', sans-serif !important;
    direction: rtl !important;
    margin: 0 !important;
}

/* ════════════════════════════════
   SUCCESS PAGE
   ════════════════════════════════ */
.success-page {
    text-align: center;
    padding: 1.5rem 1rem 3rem;
    display: flex; flex-direction: column;
    align-items: center; gap: 1rem;
    min-height: 70vh; justify-content: center;
}
.success-emoji { font-size: 4rem; animation: popIn 0.6s ease; line-height: 1.2; }
.success-title {
    font-size: 2.8rem; font-weight: 900; margin: 0;
    background: linear-gradient(135deg, #4CAF50, #FFC107, #FF9800);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    background-clip: text;
    animation: slideUp 0.5s ease 0.1s both;
}
.success-msg { font-size: 1.05rem; color: rgba(0,0,0,0.6); margin: 0; animation: slideUp 0.5s ease 0.2s both; font-weight: 600; }
.success-scores {
    display: flex; gap: 1rem; margin: 0.5rem 0;
    width: 100%; max-width: 300px;
    animation: slideUp 0.5s ease 0.3s both;
}
.success-card {
    flex: 1; background: #fff;
    border: 1px solid rgba(0,0,0,0.08); border-radius: 20px;
    padding: 1.5rem 0.6rem; display: flex;
    flex-direction: column; align-items: center; gap: 0.25rem;
    box-shadow: 0 4px 15px rgba(0,0,0,0.04);
}
.s-val  { font-size: 2.4rem; font-weight: 900; line-height: 1; }
.s-gold { color: #FF9800; }
.s-green{ color: #4CAF50; }
.s-label{ font-size: 0.75rem; color: rgba(0,0,0,0.5); margin-top: 0.15rem; font-weight: 700; }

@keyframes popIn {
    0%   { transform: scale(0.4) rotate(-10deg); opacity: 0; }
    65%  { transform: scale(1.12) rotate(3deg); }
    100% { transform: scale(1) rotate(0deg); opacity: 1; }
}
@keyframes slideUp {
    from { transform: translateY(24px); opacity: 0; }
    to   { transform: translateY(0);    opacity: 1; }
}

/* ── Leaderboard ── */
.lb-title {
    font-size: 0.74rem; font-weight: 800; color: rgba(0,0,0,0.45);
    text-transform: uppercase; letter-spacing: 1.5px;
    text-align: center; margin: 0.55rem 0 0.28rem;
}
.lb-row {
    display: flex; justify-content: space-between; align-items: center;
    padding: 0.38rem 0.8rem; border-radius: 9px; margin: 0.17rem 0;
    background: #fff; border: 1px solid rgba(0,0,0,0.06);
    font-size: 0.85rem; box-shadow: 0 2px 5px rgba(0,0,0,0.02);
}
.lb-row.me { background: rgba(76,175,80,0.08); border-color: rgba(76,175,80,0.3); }
.lb-r { font-weight: 900; min-width: 26px; color: rgba(0,0,0,0.4); }
.lb-n { flex: 1; color: #222; padding: 0 0.4rem; font-weight: 600; }
.lb-s { font-weight: 800; color: #4CAF50; min-width: 40px; text-align: left; }

/* ── Misc ── */
.mdiv {
    height: 1px;
    background: linear-gradient(90deg, transparent, rgba(0,0,0,0.06), transparent);
    margin: 0.5rem 0;
}
.sec-label {
    text-align: center; font-size: 0.7rem; font-weight: 700;
    color: rgba(0,0,0,0.4); letter-spacing: 1.8px;
    text-transform: uppercase; margin: 0.6rem 0 0.28rem;
}
.name-modal {
    background: #fff;
    border: 1px solid rgba(0,0,0,0.08); border-radius: 20px;
    padding: 1.6rem 1.4rem 0.9rem; text-align: center; margin: 0.8rem 0;
    box-shadow: 0 10px 30px rgba(0,0,0,0.05);
}
.modal-icon { font-size: 2.4rem; line-height: 1.2; }
.modal-title { font-size: 1.75rem; font-weight: 900; color: #222; margin: 0.4rem 0 0.15rem; }
.modal-sub   { font-size: 0.88rem; color: rgba(0,0,0,0.55); margin-bottom: 0.8rem; font-weight: 600; }

/* Thursday radio */
.stRadio > label { color: rgba(0,0,0,0.6) !important; font-size: 0.85rem !important; font-weight: 600 !important; }
div[role="radiogroup"] { flex-direction: row !important; gap: 0.4rem !important; }

/* RTL fixes */
.stSelectbox label { direction: rtl !important; text-align: right !important; }
div[data-baseweb="select"] { direction: rtl !important; }
.stAlert { direction: rtl !important; text-align: right !important; }
</style>""", unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════
# SESSION STATE
# ════════════════════════════════════════════════════════════
_defaults = {
    "user_name":       None,
    "user_row":        None,
    "show_name_form":  False,
    "target_date_key": "today",
    "show_success":    False,
    "sub_score":       None,
    "sub_total":       None,
    "sub_rank":        None,
}
for _k, _v in _defaults.items():
    if _k not in st.session_state:
        st.session_state[_k] = _v


# ════════════════════════════════════════════════════════════
# LOAD BASE DATA
# ════════════════════════════════════════════════════════════
now       = get_israel_now()
today_str = format_date_str(now)
thursday  = is_thursday(now)

try:
    names = load_names()
except Exception as _ex:
    st.error(f"❌ שגיאת חיבור לגיליון: {_ex}")
    st.stop()

# ── Cookie Auth ──────────────────────────────────────────────
cookie_manager = stx.CookieManager()
saved_cookie_name = cookie_manager.get("saved_user_name")

if st.session_state.user_name is None and not st.session_state.show_name_form:
    if saved_cookie_name:
        info = get_user_info(saved_cookie_name, names)
        if info:
            st.session_state.user_name = info["full_name"]
            st.session_state.user_row  = info["row"]


# ════════════════════════════════════════════════════════════
# PAGE: NAME SELECTION
# ════════════════════════════════════════════════════════════
if st.session_state.user_name is None or st.session_state.show_name_form:

    st.markdown("""<style>
    button[data-testid="baseButton-secondary"] {
        background: linear-gradient(135deg, #1B5E20, #4CAF50) !important;
        border-color: #4CAF50 !important; border-radius: 12px !important;
        height: auto !important; padding: 0.68rem 2rem !important;
        font-size: 1.05rem !important; box-shadow: 0 4px 18px rgba(76,175,80,0.35) !important;
    }
    </style>""", unsafe_allow_html=True)

    st.markdown('<div class="app-title">📍 דיווח יומי</div>', unsafe_allow_html=True)
    st.markdown("""
    <div class="name-modal">
        <div class="modal-icon">👋</div>
        <div class="modal-title">מי אתה?</div>
        <div class="modal-sub">בחר את שמך מהרשימה כדי להמשיך</div>
    </div>
    """, unsafe_allow_html=True)

    full_names = [n["full_name"] for n in names]
    sel = st.selectbox("שם מלא", ["— בחר שם —"] + full_names, label_visibility="collapsed")
    is_valid = sel and sel != "— בחר שם —"

    if st.button("✓  אישור", disabled=not is_valid, use_container_width=True):
        info = get_user_info(sel, names)
        if info:
            st.session_state.user_name      = info["full_name"]
            st.session_state.user_row       = info["row"]
            st.session_state.show_name_form = False
            # Save name in cookie for 10 years
            expire_date = datetime.now() + timedelta(days=3650)
            cookie_manager.set("saved_user_name", info["full_name"], expires_at=expire_date)
            # DO NOT call st.rerun() here. Let the script continue downwards 
            # so the main app renders AND the set_cookie command is sent!
        else:
            st.stop()
    else:
        st.stop()


# ════════════════════════════════════════════════════════════
# PAGE: SUCCESS CELEBRATION
# ════════════════════════════════════════════════════════════
if st.session_state.show_success:

    st.markdown("""<style>
    button[data-testid="baseButton-secondary"] {
        background: linear-gradient(135deg, #1B5E20, #4CAF50) !important;
        border-color: #4CAF50 !important; border-radius: 14px !important;
        height: auto !important; padding: 0.75rem 2.5rem !important;
        font-size: 1.1rem !important; font-weight: 700 !important;
        box-shadow: 0 4px 20px rgba(76,175,80,0.4) !important;
    }
    </style>""", unsafe_allow_html=True)

    score_val = f"{st.session_state.sub_score:.1f}" if st.session_state.sub_score is not None else "—"
    rank_val  = f"#{st.session_state.sub_rank}"    if st.session_state.sub_rank  is not None else "—"

    st.balloons()

    st.markdown(f"""
    <div class="success-page">
        <div class="success-emoji">🎊</div>
        <div class="success-title">כל הכבוד!</div>
        <div class="success-msg">הדיווח נשמר בהצלחה 🎯</div>
        <div class="success-scores">
            <div class="success-card">
                <div class="s-val s-gold">{score_val}</div>
                <div class="s-label">ניקוד היום</div>
            </div>
            <div class="success-card">
                <div class="s-val s-green">{rank_val}</div>
                <div class="s-label">מקום</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    if st.button("המשך ←", use_container_width=False):
        st.session_state.show_success = False
        st.rerun()

    st.stop()


# ════════════════════════════════════════════════════════════
# PAGE: MAIN REPORTING
# ════════════════════════════════════════════════════════════
user_name = st.session_state.user_name
user_row  = st.session_state.user_row

# ── Resolve target date ──────────────────────────────────────
if thursday:
    thu_dates = get_thursday_target_dates(now)
    _, target_date_str = thu_dates[st.session_state.target_date_key]
else:
    target_date_str = today_str

date_col   = find_date_column(target_date_str)
date_valid = date_col is not None

# ── Load data ────────────────────────────────────────────────
has_submitted = has_user_submitted(user_row, target_date_str) if date_valid else False
total_score, rank = load_user_score_and_rank(user_row)
daily_score = load_daily_score(user_row, target_date_str) if date_valid else None

try:
    streak = calculate_streak(user_row)
except Exception:
    streak = 0

# ── Header ───────────────────────────────────────────────────
st.markdown('<div class="app-title">📍 דיווח יומי</div>', unsafe_allow_html=True)

_days_he = ['שני', 'שלישי', 'רביעי', 'חמישי', 'שישי', 'שבת', 'ראשון']
_day_he  = _days_he[now.weekday()]
st.markdown(f"""
<div class="time-block">
    <div class="time-big">{now.strftime('%H:%M')}</div>
    <div class="date-text">יום {_day_he} &nbsp;·&nbsp; {today_str}</div>
</div>
""", unsafe_allow_html=True)

# ── User bar ─────────────────────────────────────────────────
st.markdown(f"""
<div style="display:flex; align-items:center; justify-content:center; gap:0.5rem; padding:0.4rem 0; margin-top:0.2rem;">
    <span style="font-size:1.2rem">👤</span>
    <span style="font-size:1.2rem; font-weight:800; color:#0D47A1;">{user_name}</span>
</div>""", unsafe_allow_html=True)

_, _c_sw, _ = st.columns([1, 1, 1])
with _c_sw:
    if st.button("החלף שם", type="primary", key="switch_btn", use_container_width=True):
        st.session_state.show_name_form = True
        st.session_state.show_success   = False
        cookie_manager.delete("saved_user_name")
        st.rerun()

# ── Thursday date selector ───────────────────────────────────
if thursday:
    st.markdown('<div class="mdiv"></div>', unsafe_allow_html=True)
    _opts = list(THURSDAY_DATE_OPTIONS.values())
    _keys = list(THURSDAY_DATE_OPTIONS.keys())
    _idx  = _keys.index(st.session_state.target_date_key)
    _sel_day = st.radio("📅 יום לדיווח:", options=_opts, index=_idx, horizontal=True)
    _new_key = _keys[_opts.index(_sel_day)]
    if _new_key != st.session_state.target_date_key:
        st.session_state.target_date_key = _new_key
        st.session_state.show_success    = False
        st.rerun()

st.markdown('<div class="mdiv"></div>', unsafe_allow_html=True)

# ── Status badge ─────────────────────────────────────────────
if has_submitted:
    st.markdown(
        '<div class="badge-wrap"><span class="badge badge-ok">✅&nbsp; דיווחת היום!</span></div>',
        unsafe_allow_html=True,
    )
else:
    st.markdown(
        '<div class="badge-wrap"><span class="badge badge-no">⏳&nbsp; טרם דיווחת היום</span></div>',
        unsafe_allow_html=True,
    )

# ── Score cards ──────────────────────────────────────────────
_d = f"{daily_score:.1f}" if daily_score is not None else "—"
_t = f"{total_score:.1f}" if total_score is not None else "—"
_r = f"#{rank}"           if rank        is not None else "—"
_s = f"{streak}"          if streak > 0  else "0"

st.markdown(f"""
<div class="scores-row">
  <div class="score-card"><div class="sv sv-today">{_d}</div><div class="sl">ניקוד היום</div></div>
  <div class="score-card"><div class="sv sv-total">{_t}</div><div class="sl">ניקוד כולל</div></div>
  <div class="score-card"><div class="sv sv-rank">{_r}</div><div class="sl">מקום</div></div>
  <div class="score-card"><div class="sv sv-streak">{_s} 🔥</div><div class="sl">רצף ימים</div></div>
</div>
""", unsafe_allow_html=True)

# ── Leaderboard (post-submission) ────────────────────────────
if has_submitted:
    st.markdown('<div class="mdiv"></div>', unsafe_allow_html=True)
    st.markdown('<p class="lb-title">🏆 &nbsp; טבלת מובילים</p>', unsafe_allow_html=True)
    try:
        _medals = ["🥇", "🥈", "🥉", "4", "5"]
        for _i, _e in enumerate(load_leaderboard()):
            _cls = "lb-row me" if _e["name"] == user_name else "lb-row"
            st.markdown(f"""
            <div class="{_cls}">
                <span class="lb-r">{_medals[_i]}</span>
                <span class="lb-n">{_e['name']}</span>
                <span class="lb-s">{_e['total_score']:.1f}</span>
            </div>""", unsafe_allow_html=True)
    except Exception:
        st.caption("לא ניתן לטעון את הטבלה כרגע.")

    # Shrink circles when already submitted (re-submission mode)
    st.markdown("""<style>
    div[data-testid="stVerticalBlockChild"]:has(#circ-grid-start)
      ~ div[data-testid="stVerticalBlockChild"]
      div[data-testid="stHorizontalBlock"]:not(:has(button[data-testid="baseButton-primary"]))
      .stButton > button {
        width: 105px !important;
        height: 105px !important;
        font-size: 0.75rem !important;
        opacity: 0.85 !important;
        box-shadow: 0 3px 14px rgba(0,0,0,0.45) !important;
    }
    </style>""", unsafe_allow_html=True)

# ── Status Circles (2×2 grid) ────────────────────────────────
st.markdown('<div class="mdiv"></div>', unsafe_allow_html=True)

if not date_valid:
    st.warning("⚠️ התאריך לא נמצא בגיליון. פנה למנהל.")
else:
    _lbl = "עדכן סטטוס" if has_submitted else "בחר סטטוס לדיווח"
    st.markdown(f'<p class="sec-label">{_lbl}</p>', unsafe_allow_html=True)

    # ── CSS MARKER — circle rows follow this element ──────────
    st.markdown('<div id="circ-grid-start"></div>', unsafe_allow_html=True)

    # ── Row 1: army (green)  |  home (yellow) ─────────────────
    _r1c1, _r1c2 = st.columns(2)
    with _r1c1:
        _army = st.button("בצבא",       key="btn_army", use_container_width=True)
    with _r1c2:
        _home = st.button("בבית",       key="btn_home", use_container_width=True)

    # ── Row 2: returning (orange)  |  leaving (orange) ────────
    _r2c1, _r2c2 = st.columns(2)
    with _r2c1:
        _ret  = st.button("מגיע\nהיום", key="btn_ret",  use_container_width=True)
    with _r2c2:
        _lea  = st.button("יוצא\nהיום", key="btn_lea",  use_container_width=True)

    _clicked = None
    if _army: _clicked = STATUS_OPTIONS[0]
    elif _home: _clicked = STATUS_OPTIONS[1]
    elif _ret:  _clicked = STATUS_OPTIONS[2]
    elif _lea:  _clicked = STATUS_OPTIONS[3]

    # ── Handle click ──────────────────────────────────────────
    if _clicked:
        if not has_submitted:
            # First submission
            with st.spinner("שולח דיווח..."):
                _N   = max(count_participants(names), 1)
                _pos = min(count_submissions_for_date(target_date_str) + 1, _N)
                _is_pre = thursday and (target_date_str != today_str)
                _score  = calculate_daily_score(
                    _pos, _N,
                    dt=(None if _is_pre else now),
                    time_bonus_override=(2.5 if _is_pre else None),
                )
                _tot, _rnk, _ok = perform_first_submission(
                    user_row, target_date_str, _clicked["color_rgb"], _score
                )
            if _ok:
                st.session_state.show_success = True
                st.session_state.sub_score    = _score
                st.session_state.sub_total    = _tot
                st.session_state.sub_rank     = _rnk
                st.rerun()
            else:
                st.error("❌ שגיאה בשמירת הדיווח. נסה שוב.")
        else:
            # Re-submission (status change only)
            with st.spinner("מעדכן סטטוס..."):
                _ok = perform_resubmission(user_row, target_date_str, _clicked["color_rgb"])
            if _ok:
                st.success(f"✅ הסטטוס עודכן ל'{_clicked['label']}'")
                time.sleep(0.8)
                st.rerun()
            else:
                st.error("❌ שגיאה בעדכון. נסה שוב.")

# ── JS: Paint circle buttons by text content ─────────────────
# Works on ALL browsers/devices — no CSS :has() needed.
# MutationObserver re-applies colors after every React re-render.
st.markdown(r"""
<img src="x3" style="display:none;" onerror="(function(){function p(){var i=!!document.querySelector('.badge-ok');var sz=i?'105px':'140px';var fs=i?'0.75rem':'0.88rem';var op=i?'0.85':'1.0';document.querySelectorAll('button').forEach(function(b){var t=(b.innerText||'').replace(/[\r\n\s]+/g,' ').trim();var s=b.style;var isS=(t==='בצבא'||t==='בבית'||t==='מגיע היום'||t==='יוצא היום');if(!isS)return;s.setProperty('border-radius','50%','important');s.setProperty('width',sz,'important');s.setProperty('height',sz,'important');s.setProperty('min-height','0px','important');s.setProperty('padding','6px','important');s.setProperty('font-family','Heebo, sans-serif','important');s.setProperty('font-size',fs,'important');s.setProperty('font-weight','800','important');s.setProperty('white-space','pre-line','important');s.setProperty('line-height','1.35','important');s.setProperty('text-align','center','important');s.setProperty('box-shadow','0 6px 22px rgba(0,0,0,0.5)','important');s.setProperty('transition','all 0.25s cubic-bezier(0.34, 1.56, 0.64, 1)','important');s.setProperty('display','inline-flex','important');s.setProperty('flex-direction','column','important');s.setProperty('align-items','center','important');s.setProperty('justify-content','center','important');s.setProperty('opacity',op,'important');if(t==='בצבא'){s.setProperty('background','#00ff00','important');s.setProperty('border','2.5px solid #00ff00','important');s.setProperty('color','black','important');}else if(t==='בבית'){s.setProperty('background','#ffff00','important');s.setProperty('border','2.5px solid #ffff00','important');s.setProperty('color','black','important');}else if(t==='מגיע היום'||t==='יוצא היום'){s.setProperty('background','#ff9900','important');s.setProperty('border','2.5px solid #ff9900','important');s.setProperty('color','black','important');}if(!b.dataset.animated){b.dataset.animated='true';b.addEventListener('mouseenter',function(){b.style.setProperty('transform','scale(1.09)','important');b.style.setProperty('box-shadow','0 10px 30px rgba(0,0,0,0.6)','important');});b.addEventListener('mouseleave',function(){b.style.setProperty('transform','none','important');b.style.setProperty('box-shadow','0 6px 22px rgba(0,0,0,0.5)','important');});b.addEventListener('mousedown',function(){b.style.setProperty('transform','scale(0.93)','important');});b.addEventListener('mouseup',function(){b.style.setProperty('transform','scale(1.09)','important');});b.addEventListener('touchstart',function(){b.style.setProperty('transform','scale(0.93)','important');});b.addEventListener('touchend',function(){b.style.setProperty('transform','none','important');});}})}p();if(!window.paintObserver){window.paintObserver=new MutationObserver(p);window.paintObserver.observe(document.body,{childList:true,subtree:true});}})()">
""", unsafe_allow_html=True)

# ── Refresh button ────────────────────────────────────────────
st.markdown('<div class="mdiv"></div>', unsafe_allow_html=True)
_, _cr, _ = st.columns([2, 1, 2])
with _cr:
    if st.button("🔄 רענן", type="primary", key="refresh_btn", use_container_width=True):
        st.cache_data.clear()
        st.cache_resource.clear()
        st.session_state.show_success = False
        st.rerun()

# ── Scoring Rules Expander ─────────────────────────────────────
with st.expander("ℹ️ חוקי הניקוד"):
    st.markdown("""
    **איך מחושב הניקוד היומי שלך?**
    הניקוד מורכב משני חלקים: **מיקום** + **בונוס שעה**.

    🏆 **1. ניקוד על מיקום (סדר דיווח):**
    ככל שתדווח מוקדם יותר ביחס לשאר החברים, כך תקבל יותר נקודות.
    (הראשון מקבל את הניקוד המקסימלי על מיקום, והאחרון יקבל 0.1 נק').

    ⏰ **2. בונוס שעת דיווח:**
    * **00:00 - 05:59** 🥇 בונוס **+2.5** נק'
    * **06:00 - 06:59** 🥈 בונוס **+2.0** נק'
    * **07:00 - 07:59** 🥉 בונוס **+1.0** נק'
    * **08:00 - 08:29** 🏃 בונוס **+0.5** נק'
    * **מ-08:30 והלאה** 🐢 ללא בונוס (0 נק')

    📅 **דיווח מוקדם לסופ"ש (חמישי):**
    דיווח מראש ביום חמישי עבור ימי שישי ושבת מזכה **אוטומטית** בבונוס השעה המקסימלי (+2.5 נק') ללא תלות בשעת הדיווח בפועל!
    """)

# Force deploy 1
