import streamlit as st
from database import get_connection


def login():
    if "user_id" in st.session_state:
        return True

    st.title("🦈 SHARK CREW")
    st.subheader("ログイン")

    username = st.text_input("ID")
    password = st.text_input("パスワード", type="password")

    if st.button("ログイン"):
        conn = get_connection()
        cur = conn.cursor()

        cur.execute(
            """
            SELECT *
            FROM users
            WHERE username = %s
            AND password = %s
            AND is_active = 1
            """,
            (
                username.strip().lower(),
                password.strip()
            )
        )

        user = cur.fetchone()

        cur.close()
        conn.close()

        if user:
            st.session_state.user_id = user["id"]
            st.session_state.username = user["username"]
            st.session_state.display_name = user["display_name"]
            st.session_state.role = user["role"]
            st.rerun()
        else:
            st.error("IDまたはパスワードが違います")

    st.stop()