from datetime import datetime

import psycopg2
import psycopg2.extras
import streamlit as st


CREW_USERS_TABLE = "crew_users"
CREW_WORK_LOGS_TABLE = "crew_work_logs"


def get_connection():
    database_url = st.secrets["DATABASE_URL"]

    return psycopg2.connect(
        database_url,
        cursor_factory=psycopg2.extras.RealDictCursor,
    )


def add_column_if_not_exists(conn, table, column, definition):
    cur = conn.cursor()

    cur.execute(
        """
        SELECT column_name
        FROM information_schema.columns
        WHERE table_schema = current_schema()
          AND table_name = %s
          AND column_name = %s
        """,
        (table, column),
    )

    if not cur.fetchone():
        cur.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")

    cur.close()


def init_db():
    """CREW専用テーブルだけを作成・更新する。

    在庫SHARKが使う users / work_logs は参照も変更もしない。
    """
    conn = get_connection()
    cur = conn.cursor()

    try:
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS crew_users (
                id BIGSERIAL PRIMARY KEY,
                username TEXT NOT NULL UNIQUE,
                password TEXT NOT NULL,
                display_name TEXT NOT NULL,
                role TEXT NOT NULL DEFAULT 'part_time',
                is_active BOOLEAN NOT NULL DEFAULT TRUE,
                phone TEXT,
                memo TEXT,
                created_at TEXT NOT NULL
            )
            """
        )

        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS staff_members (
                id BIGSERIAL PRIMARY KEY,
                name TEXT NOT NULL UNIQUE,
                is_active INTEGER NOT NULL DEFAULT 1,
                created_at TEXT NOT NULL
            )
            """
        )

        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS crew_work_logs (
                id BIGSERIAL PRIMARY KEY,
                user_id BIGINT NOT NULL REFERENCES crew_users(id),
                site_name TEXT NOT NULL,
                work_date TEXT NOT NULL,
                start_time TEXT NOT NULL,
                end_time TEXT NOT NULL,
                partner_name TEXT NOT NULL,
                memo TEXT,
                amount INTEGER,
                status TEXT NOT NULL DEFAULT 'pending',
                checked_by BIGINT REFERENCES crew_users(id),
                checked_at TEXT,
                created_at TEXT NOT NULL
            )
            """
        )

        # 旧CREW版で作られた途中状態にも安全に追従する。
        add_column_if_not_exists(conn, CREW_USERS_TABLE, "phone", "TEXT")
        add_column_if_not_exists(conn, CREW_USERS_TABLE, "memo", "TEXT")
        add_column_if_not_exists(
            conn,
            CREW_USERS_TABLE,
            "is_active",
            "BOOLEAN NOT NULL DEFAULT TRUE",
        )

        cur.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_crew_work_logs_status
            ON crew_work_logs(status)
            """
        )
        cur.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_crew_work_logs_work_date
            ON crew_work_logs(work_date)
            """
        )

        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        admin_users = [
            ("y.suga", "5744", "壽賀 洋佑"),
            ("s.shota", "3074", "鮫島 昇汰"),
            ("k.wakasugi", "8147", "若杉 洸太"),
        ]

        for username, password, display_name in admin_users:
            cur.execute(
                """
                INSERT INTO crew_users (
                    username,
                    password,
                    display_name,
                    role,
                    created_at
                )
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (username) DO NOTHING
                """,
                (username, password, display_name, "admin", now),
            )

        initial_staff = [
            "壽賀 洋佑",
            "鮫島 昇汰",
            "若杉 洸太",
        ]

        for staff_name in initial_staff:
            cur.execute(
                """
                INSERT INTO staff_members (
                    name,
                    created_at
                )
                VALUES (%s, %s)
                ON CONFLICT (name) DO NOTHING
                """,
                (staff_name, now),
            )

        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        cur.close()
        conn.close()
