import sqlite3
from pathlib import Path
from datetime import datetime

DB_PATH = Path("data") / "shark_crew.db"


def get_connection():
    """
    DB接続を返す関数
    """
    DB_PATH.parent.mkdir(exist_ok=True)

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    return conn


def init_db():
    """
    SHARK CREW用のDBと初期データを作成
    """
    conn = get_connection()

    # =====================
    # ユーザー
    # role:
    # part_time → 勤務入力だけ
    # admin     → 全部
    # =====================
    conn.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
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
    # バイト入力画面でプルダウン表示
    # =====================
    conn.execute("""
    CREATE TABLE IF NOT EXISTS staff_members (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL UNIQUE,
        is_active INTEGER NOT NULL DEFAULT 1,
        created_at TEXT NOT NULL
    )
    """)

    # =====================
    # 勤務ログ
    # バイト入力 → admin確認 → CSV出力
    # =====================
    conn.execute("""
    CREATE TABLE IF NOT EXISTS work_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        site_name TEXT NOT NULL,
        work_date TEXT NOT NULL,
        start_time TEXT NOT NULL,
        end_time TEXT NOT NULL,
        partner_name TEXT NOT NULL,
        memo TEXT,
        amount INTEGER,
        status TEXT NOT NULL DEFAULT 'pending',
        checked_by INTEGER,
        checked_at TEXT,
        created_at TEXT NOT NULL,
        FOREIGN KEY (user_id) REFERENCES users(id),
        FOREIGN KEY (checked_by) REFERENCES users(id)
    )
    """)

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # =====================
    # 初期ユーザー
    # =====================
    conn.execute("""
    INSERT OR IGNORE INTO users (
        username,
        password,
        display_name,
        role,
        created_at
    )
    VALUES (?, ?, ?, ?, ?)
    """, (
        "suga",
        "0227",
        "壽賀 洋佑",
        "admin",
        now
    ))

    conn.execute("""
    INSERT OR IGNORE INTO users (
        username,
        password,
        display_name,
        role,
        created_at
    )
    VALUES (?, ?, ?, ?, ?)
    """, (
        "baito01",
        "1234",
        "バイト01",
        "part_time",
        now
    ))

    # =====================
    # 初期社員
    # =====================
    initial_staff = [
        "壽賀 洋佑",
        "鮫島昇汰",
        "若杉洸太",
    ]

    for staff_name in initial_staff:
        conn.execute("""
        INSERT OR IGNORE INTO staff_members (
            name,
            created_at
        )
        VALUES (?, ?)
        """, (
            staff_name,
            now
        ))

    conn.commit()
    conn.close()