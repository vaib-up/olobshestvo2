import sqlite3
import json
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
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS first_attempts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            test_id TEXT NOT NULL,
            score INTEGER NOT NULL,
            total INTEGER NOT NULL,
            finished_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id, test_id)
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS mine_progress (
            user_id INTEGER PRIMARY KEY,
            gold INTEGER NOT NULL DEFAULT 0,
            gems INTEGER NOT NULL DEFAULT 0,
            idle_accum REAL NOT NULL DEFAULT 0,
            unlocked_horizons TEXT NOT NULL DEFAULT '[]',
            completed_tasks TEXT NOT NULL DEFAULT '[]',
            unlocked_vseross TEXT NOT NULL DEFAULT '[]',
            completed_vseross TEXT NOT NULL DEFAULT '[]',
            unlocked_secret TEXT NOT NULL DEFAULT '[]',
            completed_secret TEXT NOT NULL DEFAULT '[]',
            total_answers INTEGER NOT NULL DEFAULT 0,
            correct_answers INTEGER NOT NULL DEFAULT 0,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS theory_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            topic TEXT NOT NULL,
            answer TEXT NOT NULL,
            ts INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    # Индекс для быстрой выборки последних записей пользователя
    cur.execute(
        "CREATE INDEX IF NOT EXISTS idx_theory_history_user ON theory_history(user_id, ts DESC)"
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


# ── Mine progress ────────────────────────────────────────────────────────────

def get_mine_progress(user_id: int) -> dict | None:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM mine_progress WHERE user_id = ?", (user_id,))
    row = cur.fetchone()
    conn.close()
    if row is None:
        return None
    keys = [
        "user_id", "gold", "gems", "idle_accum",
        "unlocked_horizons", "completed_tasks",
        "unlocked_vseross", "completed_vseross",
        "unlocked_secret", "completed_secret",
        "total_answers", "correct_answers", "updated_at"
    ]
    d = dict(zip(keys, row))
    for f in ("unlocked_horizons", "completed_tasks",
              "unlocked_vseross", "completed_vseross",
              "unlocked_secret", "completed_secret"):
        d[f] = json.loads(d[f])
    return d


def save_mine_progress(user_id: int, data: dict):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO mine_progress
            (user_id, gold, gems, idle_accum,
             unlocked_horizons, completed_tasks,
             unlocked_vseross, completed_vseross,
             unlocked_secret, completed_secret,
             total_answers, correct_answers, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        ON CONFLICT(user_id) DO UPDATE SET
            gold              = excluded.gold,
            gems              = excluded.gems,
            idle_accum        = excluded.idle_accum,
            unlocked_horizons = excluded.unlocked_horizons,
            completed_tasks   = excluded.completed_tasks,
            unlocked_vseross  = excluded.unlocked_vseross,
            completed_vseross = excluded.completed_vseross,
            unlocked_secret   = excluded.unlocked_secret,
            completed_secret  = excluded.completed_secret,
            total_answers     = excluded.total_answers,
            correct_answers   = excluded.correct_answers,
            updated_at        = CURRENT_TIMESTAMP
        """,
        (
            user_id,
            data.get("gold", 0),
            data.get("gems", 0),
            data.get("idle_accum", 0),
            json.dumps(data.get("unlocked_horizons", []), ensure_ascii=False),
            json.dumps(data.get("completed_tasks", []), ensure_ascii=False),
            json.dumps(data.get("unlocked_vseross", []), ensure_ascii=False),
            json.dumps(data.get("completed_vseross", []), ensure_ascii=False),
            json.dumps(data.get("unlocked_secret", []), ensure_ascii=False),
            json.dumps(data.get("completed_secret", []), ensure_ascii=False),
            data.get("total_answers", 0),
            data.get("correct_answers", 0),
        ),
    )
    conn.commit()
    conn.close()


# ── Theory history ───────────────────────────────────────────────────────────

def get_theory_history(user_id: int, limit: int = 10) -> list[dict]:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT topic, answer, ts
        FROM theory_history
        WHERE user_id = ?
        ORDER BY ts DESC
        LIMIT ?
        """,
        (user_id, limit),
    )
    rows = cur.fetchall()
    conn.close()
    return [{"topic": r[0], "answer": r[1], "ts": r[2]} for r in rows]


def save_theory_history_item(user_id: int, topic: str, answer: str, ts: int):
    conn = get_conn()
    cur = conn.cursor()
    # Удаляем предыдущую запись с тем же topic у этого пользователя (дедупликация)
    cur.execute(
        "DELETE FROM theory_history WHERE user_id = ? AND lower(topic) = lower(?)",
        (user_id, topic),
    )
    # Вставляем новую
    cur.execute(
        "INSERT INTO theory_history (user_id, topic, answer, ts) VALUES (?, ?, ?, ?)",
        (user_id, topic, answer, ts),
    )
    # Оставляем только последние 10 записей пользователя
    cur.execute(
        """
        DELETE FROM theory_history
        WHERE user_id = ? AND id NOT IN (
            SELECT id FROM theory_history
            WHERE user_id = ?
            ORDER BY ts DESC
            LIMIT 10
        )
        """,
        (user_id, user_id),
    )
    conn.commit()
    conn.close()
