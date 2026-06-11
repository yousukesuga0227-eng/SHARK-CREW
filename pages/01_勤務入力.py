import streamlit as st
from datetime import datetime, date
from database import get_connection, init_db
from auth import login

login()

if st.session_state.role != "admin":
    st.error("管理者専用ページです。")
    st.stop()


st.set_page_config(
    page_title="勤務入力",
    page_icon="📝",
    layout="centered"
)

st.markdown("""
<style>
div[data-testid="stFormSubmitButton"] button {
    width: 100%;
    height: 60px;
    font-size: 22px;
    font-weight: bold;
}
</style>
""", unsafe_allow_html=True)

init_db()
login()

st.title("📝 勤務入力")
st.caption("SHARK CREW")

st.success(f"ログイン中：{st.session_state.display_name}")

if st.session_state.role != "part_time" and st.session_state.role != "admin":
    st.error("このページを表示する権限がありません。")
    st.stop()

conn = get_connection()

staff_members = conn.execute("""
SELECT name
FROM staff_members
WHERE is_active = 1
ORDER BY name
""").fetchall()

conn.close()

if not staff_members:
    st.warning("一緒に働いた社員が登録されていません。")
    st.stop()

staff_options = [staff["name"] for staff in staff_members]

time_options = [f"{hour:02d}:00" for hour in range(0, 25)]

with st.form("work_log_form"):

    site_name = st.text_input("現場名")
    work_date = st.date_input("勤務日", value=date.today())
    start_time = st.selectbox("開始時間", time_options, index=9)
    end_time = st.selectbox("終了時間", time_options, index=17)
    partner_name = st.selectbox("一緒に働いた社員", staff_options)
    memo = st.text_area("備考", placeholder="必要なら入力")

    submitted = st.form_submit_button("勤務登録")

    if submitted:
        if not site_name.strip():
            st.error("現場名を入力してください。")
        elif start_time >= end_time:
            st.error("終了時間は開始時間より後にしてください。")
        else:
            conn = get_connection()

            conn.execute("""
            INSERT INTO work_logs (
                user_id,
                site_name,
                work_date,
                start_time,
                end_time,
                partner_name,
                memo,
                status,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                st.session_state.user_id,
                site_name.strip(),
                work_date.strftime("%Y-%m-%d"),
                start_time,
                end_time,
                partner_name,
                memo.strip(),
                "pending",
                datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            ))

            conn.commit()
            conn.close()

            st.success("勤務情報を登録しました！")