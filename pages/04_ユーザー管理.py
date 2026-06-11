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

# 管理者のみ
if st.session_state.role != "admin":
    st.error("管理者専用ページです。")
    st.stop()

conn = get_connection()

admin_count = conn.execute("""
SELECT COUNT(*)
FROM users
WHERE role='admin'
""").fetchone()[0]

part_count = conn.execute("""
SELECT COUNT(*)
FROM users
WHERE role='part_time'
""").fetchone()[0]

total_count = conn.execute("""
SELECT COUNT(*)
FROM users
""").fetchone()[0]

st.title("👥 ユーザー管理")

col1, col2, col3 = st.columns(3)

col1.metric("👥 全ユーザー", total_count)
col2.metric("👑 管理者", admin_count)
col3.metric("👷 バイト", part_count)

st.divider()

admin_count = conn.execute("""
SELECT COUNT(*)
FROM users
WHERE role='admin'
""").fetchone()[0]

part_count = conn.execute("""
SELECT COUNT(*)
FROM users
WHERE role='part_time'
""").fetchone()[0]

total_count = conn.execute("""
SELECT COUNT(*)
FROM users
""").fetchone()[0]
if "add_user_form_key" not in st.session_state:
    st.session_state.add_user_form_key = 0

# ------------------------
# 新規登録
# ------------------------

st.subheader("➕ 新規ユーザー登録")

if "add_user_clear" in st.session_state:
    del st.session_state.add_user_clear

with st.form(f"add_user_{st.session_state.add_user_form_key}"):

    display_name = st.text_input("表示名")

    username = st.text_input("ログインID")

    password = st.text_input(
        "パスワード",
        type="password"
    )

    password_check = st.text_input(
    "パスワード(確認)",
    type="password"
)

    submit = st.form_submit_button("登録")

    if submit:

        if (
            display_name == ""
            or username == ""
            or password == ""
            or password_check == ""
        ):
            st.error("未入力があります")

        elif password != password_check:
            st.error("パスワードが一致しません")
            st.error("未入力があります")

        else:

            try:
                username = username.lower().strip()
                display_name = display_name.strip()
                password = password.strip()
                conn.execute(
                    """
                    INSERT INTO users (
                        username,
                        password,
                        display_name,
                        role,
                        created_at
                    )
                    VALUES
                    (?, ?, ?, ?, ?)
                    """,
                    (
                        username,
                        password,
                        display_name,
                        "part_time",
                        datetime.now().strftime(
                            "%Y-%m-%d %H:%M:%S"
                        )
                    )
                )

                conn.commit()

                st.success(
                    f"""
                ✅ 登録完了！

                表示名：
                {display_name}

                ID：
                {username}
                """
                )
                st.session_state.add_user_form_key += 1
                st.rerun()

            except Exception:

                st.error("同じIDがあります")

st.divider()

# ------------------------
# 一覧
# ------------------------

st.subheader("👤 登録ユーザー")

keyword = st.text_input(
    "🔍 名前・ID検索"
)

users = conn.execute(
    """
    SELECT *
    FROM users
    WHERE
        display_name LIKE ?
        OR
        username LIKE ?
    ORDER BY
        role DESC,
        display_name
    """,
    (
        f"%{keyword}%",
        f"%{keyword}%"
    )
).fetchall()

for user in users:

    col1, col2 = st.columns([4,1])

    with col1:

        icon = "🟢" if user["is_active"] else "🔴"

        status_text = "有効" if user["is_active"] else "無効"

        st.write(
            f"""
        {icon} **{user['display_name']}**

        ID：{user['username']}

        権限：{user['role']}

        状態：{status_text}
        """
        )

    with col2:

        if user["role"] != "admin":

            if user["is_active"]:

                if st.button(
                    "無効化",
                    key=f"off_{user['id']}"
                ):

                    conn.execute(
                        """
                        UPDATE users
                        SET is_active=0
                        WHERE id=?
                        """,
                        (
                            user["id"],
                        )
                    )

                    conn.commit()

                    st.rerun()

            else:

                if st.button(
                    "有効化",
                    key=f"on_{user['id']}"
                ):

                    conn.execute(
                        """
                        UPDATE users
                        SET is_active=1
                        WHERE id=?
                        """,
                        (
                            user["id"],
                        )
                    )

                    conn.commit()

                    st.rerun()

conn.close()