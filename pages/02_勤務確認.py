import streamlit as st
from datetime import datetime
from database import get_connection, init_db
from auth import login

login()

if st.session_state.role != "admin":
    st.error("管理者専用ページです。")
    st.stop()

st.set_page_config(
    page_title="勤務確認",
    page_icon="📋",
    layout="wide"
)

init_db()
login()

if st.session_state.role != "admin":
    st.error("管理者専用ページです。")
    st.stop()

st.title("📋 勤務確認")
st.caption("未確認データに支給金額を入力して承認します")

conn = get_connection()

pending_count = conn.execute("""
SELECT COUNT(*) AS count
FROM work_logs
WHERE status = 'pending'
""").fetchone()["count"]

approved_count = conn.execute("""
SELECT COUNT(*) AS count
FROM work_logs
WHERE status = 'approved'
""").fetchone()["count"]

col1, col2 = st.columns(2)

with col1:
    if pending_count > 0:
        st.error(f"🚨 未承認：{pending_count} 件")
    else:
        st.success("🟢 未承認：0 件")

with col2:
    st.info(f"✅ 承認済：{approved_count} 件")

rows = conn.execute("""
SELECT
    work_logs.*,
    users.display_name,
    checked_user.display_name AS checked_name
FROM work_logs
LEFT JOIN users
ON users.id = work_logs.user_id
LEFT JOIN users AS checked_user
ON checked_user.id = work_logs.checked_by
ORDER BY
    CASE
        WHEN work_logs.status = 'pending' THEN 0
        ELSE 1
    END,
    work_logs.work_date DESC,
    work_logs.created_at DESC
""").fetchall()

if len(rows) == 0:
    st.info("勤務データはありません。")
    conn.close()
    st.stop()

for row in rows:
    st.markdown("---")

    st.subheader(f"👤 {row['display_name']}")

    col1, col2 = st.columns(2)

    with col1:
        st.write(f"**現場**：{row['site_name']}")
        st.write(f"**勤務日**：{row['work_date']}")
        st.write(f"**時間**：{row['start_time']} ～ {row['end_time']}")

    with col2:
        st.write(f"**一緒に働いた社員**：{row['partner_name']}")
        st.write(f"**備考**：{row['memo'] if row['memo'] else 'なし'}")

    if row["status"] == "approved":
        st.success("🟢 承認済み")
        st.write(f"**支給額**：{row['amount']:,} 円")
        st.write(f"**承認者**：{row['checked_name']}")
        st.write(f"**承認日時**：{row['checked_at']}")

    else:
        st.warning("🟡 未確認")

        amount = st.number_input(
            "支給金額",
            min_value=0,
            step=1000,
            value=0,
            key=f"amount_{row['id']}"
        )

        if st.button("承認する", key=f"approve_{row['id']}"):
            if amount <= 0:
                st.error("支給金額を入力してください。")
            else:
                conn.execute("""
                UPDATE work_logs
                SET
                    amount = ?,
                    status = 'approved',
                    checked_by = ?,
                    checked_at = ?
                WHERE id = ?
                """, (
                    amount,
                    st.session_state.user_id,
                    datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    row["id"]
                ))

                conn.commit()
                conn.close()

                st.success("承認しました！")
                st.rerun()

conn.close()