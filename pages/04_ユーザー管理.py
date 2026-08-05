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

cur.execute("SELECT COUNT(*) AS count FROM crew_users")
total_count = cur.fetchone()["count"]

cur.execute("SELECT COUNT(*) AS count FROM crew_users WHERE role = 'admin'")
admin_count = cur.fetchone()["count"]

cur.execute("SELECT COUNT(*) AS count FROM crew_users WHERE role = 'part_time'")
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
                INSERT INTO crew_users (
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
FROM crew_users
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

    icon = "🟢" if user["is_active"] else "🔴"
    status_text = "有効" if user["is_active"] else "無効"
    role_icon = "👑" if user["role"] == "admin" else "👷"

    with st.expander(f'{icon} {user["display_name"]} / {user["username"]} / {status_text}'):

        st.markdown(f"""
**ID**：{user["username"]}  
**権限**：{role_icon} {user["role"]}  
**状態**：{status_text}  
**登録日**：{user["created_at"]}
""")

        st.divider()

        new_display_name = st.text_input(
            "表示名",
            value=user["display_name"],
            key=f"display_{user['id']}"
        )

        new_username = st.text_input(
            "ログインID",
            value=user["username"],
            key=f"username_{user['id']}"
        )

        new_role = st.selectbox(
            "権限",
            ["part_time", "admin"],
            index=["part_time", "admin"].index(user["role"]),
            key=f"role_{user['id']}"
        )

        phone = st.text_input(
            "電話番号",
            value=user.get("phone", "") or "",
            key=f"phone_{user['id']}"
        )

        memo = st.text_area(
            "メモ",
            value=user.get("memo", "") or "",
            key=f"memo_{user['id']}"
        )

        col1, col2, col3 = st.columns(3)

        with col1:
            if st.button("更新", key=f"update_{user['id']}"):
                cur.execute("""
                UPDATE crew_users
                SET
                    display_name = %s,
                    username = %s,
                    role = %s,
                    phone = %s,
                    memo = %s
                WHERE id = %s
                """, (
                    new_display_name.strip(),
                    new_username.strip().lower(),
                    new_role,
                    phone.strip(),
                    memo.strip(),
                    user["id"]
                ))

                conn.commit()
                st.success("更新しました")
                st.rerun()

        with col2:
            if user["is_active"]:
                if st.button("非表示", key=f"off_{user['id']}"):
                    cur.execute("""
                    UPDATE crew_users
                    SET is_active = FALSE
                    WHERE id = %s
                    """, (
                        user["id"],
                    ))

                    conn.commit()
                    st.rerun()
            else:
                if st.button("再表示", key=f"on_{user['id']}"):
                    cur.execute("""
                    UPDATE crew_users
                    SET is_active = TRUE
                    WHERE id = %s
                    """, (
                        user["id"],
                    ))

                    conn.commit()
                    st.rerun()

        with col3:
            if st.button("パスワード変更", key=f"pass_open_{user['id']}"):
                st.session_state[f"pass_change_{user['id']}"] = True

        if st.session_state.get(f"pass_change_{user['id']}", False):
            new_password = st.text_input(
                "新しいパスワード",
                type="password",
                key=f"new_pass_{user['id']}"
            )

            if st.button("パスワード更新", key=f"pass_update_{user['id']}"):
                if not new_password.strip():
                    st.error("パスワードを入力してください。")
                else:
                    cur.execute("""
                    UPDATE crew_users
                    SET password = %s
                    WHERE id = %s
                    """, (
                        new_password.strip(),
                        user["id"]
                    ))

                    conn.commit()
                    st.success("パスワードを変更しました")
                    st.session_state[f"pass_change_{user['id']}"] = False
                    st.rerun()

cur.close()
conn.close()
