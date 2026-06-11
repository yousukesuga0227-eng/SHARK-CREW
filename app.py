import streamlit as st
from datetime import date
from database import init_db, get_connection
from auth import login

st.set_page_config(
    page_title="SHARK CREW",
    page_icon="🦈",
    layout="wide"
)

init_db()
login()
if "role" not in st.session_state:
    st.stop()


st.title("🦈 SHARK CREW")

st.markdown("---")

st.subheader(
    f"👋 ようこそ {st.session_state.display_name}"
)

st.success(f"ログイン中：{st.session_state.display_name}")

if st.button("ログアウト"):
    st.session_state.clear()
    st.rerun()

st.divider()

conn = get_connection()

today = date.today().strftime("%Y-%m-%d")

pending_count = conn.execute("""
SELECT COUNT(*) AS count
FROM work_logs
WHERE status = 'pending'
""").fetchone()["count"]

today_count = conn.execute("""
SELECT COUNT(*) AS count
FROM work_logs
WHERE work_date = ?
""", (today,)).fetchone()["count"]

active_user_count = conn.execute("""
SELECT COUNT(*) AS count
FROM users
WHERE is_active = 1
""").fetchone()["count"]

conn.close()

col1, col2, col3 = st.columns(3)

with col1:
    if pending_count > 0:
        st.error(f"🚨 未承認\n\n# {pending_count} 件")
    else:
        st.success("🟢 未承認\n\n# 0 件")

with col2:
    st.info(f"👷 今日の勤務\n\n# {today_count} 件")

with col3:
    st.info(f"👥 有効ユーザー\n\n# {active_user_count} 人")

st.divider()

st.info("左メニューから勤務入力・勤務確認・CSV出力・ユーザー管理を開いてください。")