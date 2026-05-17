import sqlite3
from pathlib import Path

DB_PATH = Path("stats.db")


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS user_errors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            test_id TEXT NOT NULL,
            question_text TEXT NOT NULL,
            correct_answer TEXT NOT NULL,
            user_answer TEXT NOT NULL,
            topic TEXT,
            made_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    conn.commit()
    conn.close()



def save_first_attempt(user_id: int, test_id: str, score: int, total: int):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO first_attempts (user_id, test_id, score, total)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(user_id, test_id) DO NOTHING
        """,
        (user_id, test_id, score, total),
    )
    conn.commit()
    conn.close()


def get_user_stats(user_id: int):
    conn = get_conn()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT 
            COUNT(*) as tests_count,
            SUM(score) as sum_score,
            SUM(total) as sum_total
        FROM first_attempts
        WHERE user_id = ?
        """,
        (user_id,),
    )
    tests_count, sum_score, sum_total = cur.fetchone()

    cur.execute(
        """
        SELECT test_id, score, total, finished_at
        FROM first_attempts
        WHERE user_id = ?
        ORDER BY finished_at
        """,
        (user_id,),
    )
    tests = cur.fetchall()

    conn.close()
    return tests_count or 0, sum_score or 0, sum_total or 0, tests

def save_error(user_id: int, test_id: str, question_text: str,
               correct_answer: str, user_answer: str, topic: str = None):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO user_errors
            (user_id, test_id, question_text, correct_answer, user_answer, topic)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (user_id, test_id, question_text, correct_answer, user_answer, topic),
    )
    conn.commit()
    conn.close()

def get_last_errors(user_id: int, limit: int = 10):
    """Возвращает последние N ошибок пользователя."""
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT question_text, correct_answer, user_answer, topic, made_at
        FROM user_errors
        WHERE user_id = ?
        ORDER BY made_at DESC
        LIMIT ?
        """,
        (user_id, limit),
    )
    rows = cur.fetchall()
    conn.close()
    return rows