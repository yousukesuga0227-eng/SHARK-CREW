import streamlit as st
from datetime import datetime
from database import get_connection, init_db
from auth import login

st.set_page_config(
    page_title="ユーザー管理",
    page_icon="👥",
    layout="wide"
)

init_db()
login()

if st.session_state.role != "admin":
    st.error("管理者専用ページです。")
    st.stop()

conn = get_connection()
cur = conn.cursor()

cur.execute("SELECT COUNT(*) AS count FROM users")
total_count = cur.fetchone()["count"]

cur.execute("SELECT COUNT(*) AS count FROM users WHERE role = 'admin'")
admin_count = cur.fetchone()["count"]

cur.execute("SELECT COUNT(*) AS count FROM users WHERE role = 'part_time'")
part_count = cur.fetchone()["count"]

st.title("👥 ユーザー管理")

col1, col2, col3 = st.columns(3)
col1.metric("👥 全ユーザー", total_count)
col2.metric("👑 管理者", admin_count)
col3.metric("👷 バイト", part_count)

st.divider()

if "add_user_form_key" not in st.session_state:
    st.session_state.add_user_form_key = 0

st.subheader("➕ 新規ユーザー登録")

with st.form(f"add_user_{st.session_state.add_user_form_key}"):
    display_name = st.text_input("表示名")
    username = st.text_input("ログインID")
    password = st.text_input("パスワード", type="password")
    password_check = st.text_input("パスワード確認", type="password")

    submit = st.form_submit_button("登録")

    if submit:
        display_name = display_name.strip()
        username = username.strip().lower()
        password = password.strip()
        password_check = password_check.strip()

        if not display_name or not username or not password or not password_check:
            st.error("未入力があります。")
        elif password != password_check:
            st.error("パスワードが一致しません。")
        else:
            try:
                cur.execute("""
                INSERT INTO users (
                    username,
                    password,
                    display_name,
                    role,
                    created_at
                )
                VALUES (%s, %s, %s, %s, %s)
                """, (
                    username,
                    password,
                    display_name,
                    "part_time",
                    datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                ))

                conn.commit()

                st.success(f"✅ 登録しました：{display_name} / ID：{username}")
                st.session_state.add_user_form_key += 1
                st.rerun()

            except Exception:
                conn.rollback()
                st.error("同じIDがすでに存在します。")

st.divider()

st.subheader("👤 登録ユーザー")

keyword = st.text_input("🔍 名前・ID検索").strip()

cur.execute("""
SELECT *
FROM users
WHERE display_name ILIKE %s
OR username ILIKE %s
ORDER BY
    CASE WHEN role = 'admin' THEN 0 ELSE 1 END,
    display_name ASC
""", (
    f"%{keyword}%",
    f"%{keyword}%"
))

users = cur.fetchall()

if not users:
    st.info("該当するユーザーはいません。")

for user in users:
    st.markdown("---")

    col1, col2 = st.columns([4, 1])

    with col1:
        icon = "🟢" if user["is_active"] else "🔴"
        status_text = "有効" if user["is_active"] else "無効"
        role_icon = "👑" if user["role"] == "admin" else "👷"

        st.markdown(f"""
### {icon} {user["display_name"]}

**ID**：{user["username"]}  
**権限**：{role_icon} {user["role"]}  
**状態**：{status_text}  
**登録日**：{user["created_at"]}
""")

    with col2:
        if user["role"] == "admin":
            st.info("管理者")
        else:
            if user["is_active"]:
                if st.button("無効化", key=f"off_{user['id']}"):
                    cur.execute("""
                    UPDATE users
                    SET is_active = 0
                    WHERE id = %s
                    """, (
                        user["id"],
                    ))

                    conn.commit()
                    st.rerun()
            else:
                if st.button("有効化", key=f"on_{user['id']}"):
                    cur.execute("""
                    UPDATE users
                    SET is_active = 1
                    WHERE id = %s
                    """, (
                        user["id"],
                    ))

                    conn.commit()
                    st.rerun()

cur.close()
conn.close()