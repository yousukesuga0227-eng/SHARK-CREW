import streamlit as st
import psycopg2
import psycopg2.extras
from datetime import datetime


def get_connection():
    """
    Supabase PostgreSQLへ接続する関数
    Streamlit CloudのSecretsに DATABASE_URL を設定しておく
    """
    database_url = st.secrets["DATABASE_URL"]

    conn = psycopg2.connect(
        database_url,
        cursor_factory=psycopg2.extras.RealDictCursor
    )

    return conn


def init_db():
    """
    Supabase側にテーブルが無ければ作成し、
    初期adminと初期社員を投入する
    """
    conn = get_connection()
    cur = conn.cursor()

    # =====================
    # ユーザー
    # =====================
    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id BIGSERIAL PRIMARY KEY,
        username TEXT NOT NULL UNIQUE,
        password TEXT NOT NULL,
        display_name TEXT NOT NULL,
        role TEXT NOT NULL DEFAULT 'part_time',
        is_active INTEGER NOT NULL DEFAULT 1,
        created_at TEXT NOT NULL
    )
    """)

    # =====================
    # 一緒に働いた社員
    # =====================
    cur.execute("""
    CREATE TABLE IF NOT EXISTS staff_members (
        id BIGSERIAL PRIMARY KEY,
        name TEXT NOT NULL UNIQUE,
        is_active INTEGER NOT NULL DEFAULT 1,
        created_at TEXT NOT NULL
    )
    """)

    # =====================
    # 勤務ログ
    # =====================
    cur.execute("""
    CREATE TABLE IF NOT EXISTS work_logs (
        id BIGSERIAL PRIMARY KEY,
        user_id BIGINT NOT NULL REFERENCES users(id),
        site_name TEXT NOT NULL,
        work_date TEXT NOT NULL,
        start_time TEXT NOT NULL,
        end_time TEXT NOT NULL,
        partner_name TEXT NOT NULL,
        memo TEXT,
        amount INTEGER,
        status TEXT NOT NULL DEFAULT 'pending',
        checked_by BIGINT REFERENCES users(id),
        checked_at TEXT,
        created_at TEXT NOT NULL
    )
    """)

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    admin_users = [
        ("y.suga", "5744", "壽賀 洋佑"),
        ("s.shota", "3074", "鮫島 昇汰"),
        ("k.wakasugi", "8147", "若杉 洸太"),
    ]

    for username, password, display_name in admin_users:
        cur.execute("""
        INSERT INTO users (
            username,
            password,
            display_name,
            role,
            created_at
        )
        VALUES (%s, %s, %s, %s, %s)
        ON CONFLICT (username) DO NOTHING
        """, (
            username,
            password,
            display_name,
            "admin",
            now
        ))

    initial_staff = [
        "壽賀 洋佑",
        "鮫島 昇汰",
        "若杉 洸太",
    ]

    for staff_name in initial_staff:
        cur.execute("""
        INSERT INTO staff_members (
            name,
            created_at
        )
        VALUES (%s, %s)
        ON CONFLICT (name) DO NOTHING
        """, (
            staff_name,
            now
        ))

    conn.commit()
    cur.close()
    conn.close()