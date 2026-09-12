"""SHARK CREW 勤務確認（月間カレンダー版）。Streamlit 1.41 以上。"""
import calendar
import re
from collections import defaultdict
from datetime import date, datetime, timedelta, timezone

import streamlit as st
from database import get_connection, init_db
from auth import login


JST = timezone(timedelta(hours=9))


def database_error(message, exc):
    st.error(message)
    # 接続URL・認証情報を出さず、原因の種類とSQLSTATEだけ表示する。
    code = getattr(exc, "pgcode", None)
    name = type(exc).__name__
    safe_code = code if isinstance(code, str) and re.fullmatch(r"[A-Z0-9]{5}", code) else None
    st.caption(f"エラー種別：{name}" + (f" ／ SQLSTATE：{safe_code}" if safe_code else ""))
    if safe_code == "42P01":
        st.info("勤務確認は public.crew_users／public.crew_work_logs を参照しています。接続先のテーブルを確認してください。")


def read_rows(sql, params=()):
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(sql, params)
            return [dict(row) for row in cur.fetchall()]
    finally:
        conn.close()


DETAIL_SQL = """
SELECT w.*, u.display_name, c.display_name AS checked_name
FROM public.crew_work_logs w
LEFT JOIN public.crew_users u ON u.id = w.user_id
LEFT JOIN public.crew_users c ON c.id = w.checked_by
"""


def shift_month(month, delta):
    index = month.year * 12 + month.month - 1 + delta
    year, month_index = divmod(index, 12)
    return date(year, month_index + 1, 1)


def navigate(delta=None):
    st.session_state.crew_calendar_month = (
        datetime.now(JST).date().replace(day=1) if delta is None
        else shift_month(st.session_state.crew_calendar_month, delta)
    )


def approve(log_id, amount):
    # ダイアログからの再実行時も管理者権限を確認する。
    if st.session_state.get("role") != "admin":
        raise PermissionError("管理者専用です")
    if amount <= 0:
        raise ValueError("支給金額を入力してください")
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE public.crew_work_logs
                SET amount = %s, status = 'approved', checked_by = %s,
                    checked_at = %s
                WHERE id = %s AND status = 'pending'
            """, (int(amount), st.session_state.user_id,
                  datetime.now(JST).strftime("%Y-%m-%d %H:%M:%S"), log_id))
            updated = cur.rowcount == 1
        conn.commit()
        return updated
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


@st.dialog("勤務の詳細・承認", width="large")
def show_detail(log_id):
    if st.session_state.get("role") != "admin":
        st.error("管理者専用ページです。")
        return
    # 古い画面から開いた場合も、承認状態はDBから取り直す。
    try:
        records = read_rows(DETAIL_SQL + " WHERE w.id = %s", (log_id,))
    except Exception as exc:
        database_error("勤怠を取得できませんでした。閉じてもう一度お試しください。", exc)
        return
    if not records:
        st.warning("この勤怠は見つかりませんでした。")
        return
    row = records[0]
    st.subheader(row.get("display_name") or "名前未登録")
    left, right = st.columns(2)
    with left:
        st.write("**現場**：", row["site_name"])
        st.write("**勤務日**：", str(row["work_date"]))
        st.write("**時間**：", f"{row['start_time']} ～ {row['end_time']}")
    with right:
        st.write("**一緒に働いた社員**：", row.get("partner_name") or "なし")
        st.write("**備考**：", row.get("memo") or "なし")
    if row["status"] == "approved":
        st.success("🟢 承認済み")
        amount = row.get("amount")
        st.write("**支給額**：", f"{amount:,} 円" if amount is not None else "未設定")
        st.write("**承認者**：", row.get("checked_name") or "不明")
        st.write("**承認日時**：", str(row.get("checked_at") or "なし"))
    elif row["status"] == "pending":
        st.warning("🟠 未承認")
        with st.form(f"crew_approve_form_{log_id}"):
            amount = st.number_input("支給金額（円）", min_value=0, step=1000,
                                     value=0, key=f"crew_amount_{log_id}")
            submitted = st.form_submit_button("承認する", type="primary")
        if submitted:
            if amount <= 0:
                st.error("支給金額を入力してください。")
            else:
                try:
                    updated = approve(log_id, amount)
                except Exception as exc:
                    database_error("承認できませんでした。エラー種別を確認してください。", exc)
                    return
                st.session_state.crew_calendar_notice = (
                    "承認しました！" if updated
                    else "この勤怠は更新済み、または削除されています。最新の状態を表示しました。"
                )
                st.rerun()
    else:
        st.info(f"状態：{row['status']}")
    if st.button("閉じる", key=f"crew_close_{log_id}"):
        st.rerun()


st.set_page_config(page_title="勤務確認", page_icon="📅", layout="wide")
init_db()
login()
if st.session_state.get("role") != "admin":
    st.error("管理者専用ページです。")
    st.stop()

st.title("📅 勤務確認")
st.caption("カレンダーの勤怠を押すと、詳細確認・支給金額の入力・承認ができます。")
if "crew_calendar_notice" in st.session_state:
    st.success(st.session_state.pop("crew_calendar_notice"))

today = datetime.now(JST).date()
st.session_state.setdefault("crew_calendar_month", today.replace(day=1))
try:
    counts = read_rows("SELECT status, COUNT(*) AS count FROM public.crew_work_logs GROUP BY status")
except Exception as exc:
    database_error("勤怠を取得できませんでした。エラー種別を確認してください。", exc)
    st.stop()
count_map = {r["status"]: r["count"] for r in counts}
left, right = st.columns(2)
with left:
    st.metric("未承認（全期間）", f"{count_map.get('pending', 0)} 件")
with right:
    st.metric("承認済（全期間）", f"{count_map.get('approved', 0)} 件")

prev, heading, current, following = st.columns([1, 3, 1, 1])
with prev:
    st.button("◀ 前月", on_click=navigate, args=(-1,), use_container_width=True)
with current:
    st.button("今月", on_click=navigate, use_container_width=True)
with following:
    st.button("翌月 ▶", on_click=navigate, args=(1,), use_container_width=True)
month = st.session_state.crew_calendar_month
with heading:
    st.subheader(f"{month.year}年 {month.month}月")
next_month = shift_month(month, 1)
try:
    rows = read_rows(DETAIL_SQL + """
        WHERE w.work_date >= %s AND w.work_date < %s
        ORDER BY w.work_date, w.start_time, u.display_name, w.id
    """, (month.isoformat(), next_month.isoformat()))
except Exception as exc:
    database_error("この月の勤怠を取得できませんでした。再読み込みしてください。", exc)
    st.stop()

st.caption(f"表示月：{len(rows)} 件　｜　🟠 未承認　🟢 承認済み")
if not rows:
    st.info("この月の勤務データはありません。前月・翌月から他の月を確認できます。")
by_day = defaultdict(list)
for row in rows:
    by_day[str(row["work_date"])[:10]].append(row)

# st.container のキーを利用し、カレンダー内だけに装飾を適用。
st.markdown("""
<style>
div[class*="st-key-crew_day_"] {
    min-height: 175px; border-radius: 10px;
}
div[class*="st-key-crew_event_"] button {
    text-align: left; justify-content: flex-start;
    min-height: 76px; border-radius: 7px; padding: 7px 9px;
}
div[class*="st-key-crew_event_"] button p { white-space: pre-line; }
div[class*="st-key-crew_event_pending_"] button {
    background: #fff2df; color: #713b0c; border: 1px solid #edb468;
    border-left: 5px solid #ed9427;
}
div[class*="st-key-crew_event_approved_"] button {
    background: #e7f5ec; color: #175437; border: 1px solid #8dcca5;
    border-left: 5px solid #329762;
}
div[class*="st-key-crew_event_"] button:hover { filter: brightness(.95); }
</style>
""", unsafe_allow_html=True)

for col, weekday in zip(st.columns(7), ["日", "月", "火", "水", "木", "金", "土"]):
    with col:
        color = "red" if weekday == "日" else "blue" if weekday == "土" else "gray"
        st.markdown(f":{color}[**{weekday}**]")

clicked_id = None
for week_index, week in enumerate(calendar.Calendar(firstweekday=6).monthdatescalendar(month.year, month.month)):
    for col, day in zip(st.columns(7), week):
        with col:
            with st.container(border=True, key=f"crew_day_{day.isoformat()}"):
                if day.month != month.month:
                    st.caption(f"{day.month}/{day.day}")
                    continue
                day_label = f"**{day.day}**" + ("　今日" if day == today else "")
                st.markdown(f":blue[{day_label}]" if day == today else day_label)
                for row in by_day.get(day.isoformat(), []):
                    status = row["status"]
                    style = status if status in ("pending", "approved") else "other"
                    marker = "🟢" if status == "approved" else "🟠" if status == "pending" else "⚪"
                    state_label = "承認済み" if status == "approved" else "未承認" if status == "pending" else str(status)
                    label = (f"{marker} {row.get('display_name') or '名前未登録'}\n"
                             f"{row['site_name']}\n"
                             f"{str(row['start_time'])[:5]} ～ {str(row['end_time'])[:5]}")
                    with st.container(key=f"crew_event_{style}_{row['id']}"):
                        if st.button(label, key=f"crew_open_{row['id']}",
                                     help=f"{state_label}：押すと勤怠の詳細を開きます",
                                     use_container_width=True):
                            clicked_id = row["id"]

if clicked_id is not None:
    show_detail(clicked_id)
