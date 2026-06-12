import streamlit as st
import pandas as pd
from datetime import date, timedelta
from database import get_connection, init_db
from auth import login

st.set_page_config(
    page_title="CSV出力",
    page_icon="📄",
    layout="wide"
)

init_db()
login()

if st.session_state.role != "admin":
    st.error("管理者専用ページです。")
    st.stop()

st.title("📄 CSV出力")
st.caption("週払い用：日曜〜土曜の勤務データを出力します")

today = date.today()

start_of_week = today - timedelta(days=(today.weekday() + 1) % 7)
end_of_week = start_of_week + timedelta(days=6)

col1, col2 = st.columns(2)

with col1:
    start_date = st.date_input("開始日（日曜）", value=start_of_week)

with col2:
    end_date = st.date_input("終了日（土曜）", value=end_of_week)

conn = get_connection()
cur = conn.cursor()

cur.execute("""
SELECT COUNT(*) AS count
FROM work_logs
WHERE work_date BETWEEN %s AND %s
AND status = 'pending'
""", (
    start_date.strftime("%Y-%m-%d"),
    end_date.strftime("%Y-%m-%d")
))
pending_count = cur.fetchone()["count"]

cur.execute("""
SELECT
    users.display_name AS 名前,
    work_logs.site_name AS 現場,
    work_logs.work_date AS 勤務日,
    work_logs.start_time AS 開始時間,
    work_logs.end_time AS 終了時間,
    work_logs.partner_name AS 一緒に働いた社員,
    work_logs.memo AS 備考,
    work_logs.amount AS 支給額,
    work_logs.status AS 状態
FROM work_logs
LEFT JOIN users
ON users.id = work_logs.user_id
WHERE work_date BETWEEN %s AND %s
ORDER BY work_date ASC, users.display_name ASC
""", (
    start_date.strftime("%Y-%m-%d"),
    end_date.strftime("%Y-%m-%d")
))
rows = cur.fetchall()

cur.close()
conn.close()

st.divider()

st.write(f"対象期間：**{start_date} 〜 {end_date}**")
st.write(f"未承認件数：**{pending_count} 件**")

if pending_count > 0:
    st.error("🚫 未確認データがあります。CSV出力できません。")
    st.stop()

if len(rows) == 0:
    st.info("対象期間の勤務データがありません。")
    st.stop()

df = pd.DataFrame(rows)

st.success("🟢 全件承認済みです。CSV出力できます。")
st.dataframe(df, use_container_width=True)

csv = df.to_csv(index=False).encode("utf-8-sig")

file_name = f"SHARK_CREW_{start_date}_{end_date}.csv"

st.download_button(
    label="CSV出力",
    data=csv,
    file_name=file_name,
    mime="text/csv"
)