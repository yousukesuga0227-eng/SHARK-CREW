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

st.title("🦈 SHARK CREW")
st.subheader("Smart Handling Attendance & Resource Keeper - Crew System")

st.success(f"ログイン中：{st.session_state.display_name}")

if st.button("ログアウト"):
    st.session_state.clear()
    st.rerun()

st.divider()

conn = get_connection()
cur = conn.cursor()

today = date.today().strftime("%Y-%m-%d")

cur.execute("""
SELECT COUNT(*) AS count
FROM work_logs
WHERE status = 'pending'
""")
pending_count = cur.fetchone()["count"]

cur.execute("""
SELECT COUNT(*) AS count
FROM work_logs
WHERE work_date = %s
""", (today,))
today_count = cur.fetchone()["count"]

cur.execute("""
SELECT COUNT(*) AS count
FROM users
WHERE is_active = 1
""")
active_user_count = cur.fetchone()["count"]

cur.close()
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