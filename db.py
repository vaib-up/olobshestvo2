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
    cur.execute(
        "CREATE INDEX IF NOT EXISTS idx_theory_history_user ON theory_history(user_id, ts DESC)"
    )

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS helper_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            topic TEXT NOT NULL,
            answer TEXT NOT NULL,
            ts INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    cur.execute(
        "CREATE INDEX IF NOT EXISTS idx_helper_history_user ON helper_history(user_id, ts DESC)"
    )

    # Участники общего рейтинга
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS leaderboard_users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            display_name TEXT NOT NULL,
            rating_opt_in INTEGER NOT NULL DEFAULT 0,
            opted_in_at TIMESTAMP NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    cur.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_leaderboard_opt_in
        ON leaderboard_users(rating_opt_in, user_id)
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
        SELECT COUNT(*) as tests_count, SUM(score) as sum_score, SUM(total) as sum_total
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


def save_error(
    user_id: int,
    test_id: str,
    question_text: str,
    correct_answer: str,
    user_answer: str,
    topic: str = None,
):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO user_errors (user_id, test_id, question_text, correct_answer, user_answer, topic)
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


# ── Leaderboard ─────────────────────────────────────────────────────────────

def upsert_leaderboard_user(user_id: int, username: str | None, display_name: str):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO leaderboard_users (user_id, username, display_name, updated_at)
        VALUES (?, ?, ?, CURRENT_TIMESTAMP)
        ON CONFLICT(user_id) DO UPDATE SET
            username = excluded.username,
            display_name = excluded.display_name,
            updated_at = CURRENT_TIMESTAMP
        """,
        (user_id, username, display_name),
    )
    conn.commit()
    conn.close()


def set_leaderboard_consent(
    user_id: int,
    consent: bool,
    username: str | None = None,
    display_name: str | None = None,
):
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("SELECT user_id FROM leaderboard_users WHERE user_id = ?", (user_id,))
    exists = cur.fetchone()

    if exists:
        if display_name is not None and username is not None:
            cur.execute(
                """
                UPDATE leaderboard_users
                SET username = ?,
                    display_name = ?,
                    rating_opt_in = ?,
                    opted_in_at = CASE
                        WHEN ? = 1 THEN COALESCE(opted_in_at, CURRENT_TIMESTAMP)
                        ELSE NULL
                    END,
                    updated_at = CURRENT_TIMESTAMP
                WHERE user_id = ?
                """,
                (username, display_name, int(consent), int(consent), user_id),
            )
        elif display_name is not None:
            cur.execute(
                """
                UPDATE leaderboard_users
                SET display_name = ?,
                    rating_opt_in = ?,
                    opted_in_at = CASE
                        WHEN ? = 1 THEN COALESCE(opted_in_at, CURRENT_TIMESTAMP)
                        ELSE NULL
                    END,
                    updated_at = CURRENT_TIMESTAMP
                WHERE user_id = ?
                """,
                (display_name, int(consent), int(consent), user_id),
            )
        elif username is not None:
            cur.execute(
                """
                UPDATE leaderboard_users
                SET username = ?,
                    rating_opt_in = ?,
                    opted_in_at = CASE
                        WHEN ? = 1 THEN COALESCE(opted_in_at, CURRENT_TIMESTAMP)
                        ELSE NULL
                    END,
                    updated_at = CURRENT_TIMESTAMP
                WHERE user_id = ?
                """,
                (username, int(consent), int(consent), user_id),
            )
        else:
            cur.execute(
                """
                UPDATE leaderboard_users
                SET rating_opt_in = ?,
                    opted_in_at = CASE
                        WHEN ? = 1 THEN COALESCE(opted_in_at, CURRENT_TIMESTAMP)
                        ELSE NULL
                    END,
                    updated_at = CURRENT_TIMESTAMP
                WHERE user_id = ?
                """,
                (int(consent), int(consent), user_id),
            )
    else:
        cur.execute(
            """
            INSERT INTO leaderboard_users (
                user_id,
                username,
                display_name,
                rating_opt_in,
                opted_in_at,
                created_at,
                updated_at
            )
            VALUES (?, ?, ?, ?, CASE WHEN ? = 1 THEN CURRENT_TIMESTAMP ELSE NULL END, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            """,
            (
                user_id,
                username,
                display_name or f"User {user_id}",
                int(consent),
                int(consent),
            ),
        )

    conn.commit()
    conn.close()


def get_leaderboard(limit: int = 10):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT
            lu.user_id,
            lu.username,
            lu.display_name,
            COALESCE(SUM(fa.score), 0) AS sum_score,
            COALESCE(SUM(fa.total), 0) AS sum_total,
            COUNT(fa.id) AS tests_count,
            lu.opted_in_at
        FROM leaderboard_users lu
        LEFT JOIN first_attempts fa ON fa.user_id = lu.user_id
        WHERE lu.rating_opt_in = 1
        GROUP BY lu.user_id, lu.username, lu.display_name, lu.opted_in_at
        ORDER BY sum_score DESC,
                 CASE
                     WHEN COALESCE(SUM(fa.total), 0) = 0 THEN 0
                     ELSE 1.0 * SUM(fa.score) / SUM(fa.total)
                 END DESC,
                 tests_count DESC,
                 lu.opted_in_at ASC,
                 lu.user_id ASC
        LIMIT ?
        """,
        (limit,),
    )
    rows = cur.fetchall()
    conn.close()

    result = []
    for idx, row in enumerate(rows, start=1):
        result.append(
            {
                "place": idx,
                "user_id": row[0],
                "username": row[1],
                "display_name": row[2],
                "sum_score": row[3],
                "sum_total": row[4],
                "tests_count": row[5],
                "opted_in_at": row[6],
            }
        )
    return result


def get_user_leaderboard_entry(user_id: int):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT
            lu.user_id,
            lu.username,
            lu.display_name,
            lu.rating_opt_in,
            lu.opted_in_at,
            COALESCE(SUM(fa.score), 0) AS sum_score,
            COALESCE(SUM(fa.total), 0) AS sum_total,
            COUNT(fa.id) AS tests_count
        FROM leaderboard_users lu
        LEFT JOIN first_attempts fa ON fa.user_id = lu.user_id
        WHERE lu.user_id = ?
        GROUP BY lu.user_id, lu.username, lu.display_name, lu.rating_opt_in, lu.opted_in_at
        """,
        (user_id,),
    )
    row = cur.fetchone()

    if row is None:
        conn.close()
        return None

    cur.execute(
        """
        WITH ranked AS (
            SELECT
                lu.user_id,
                COALESCE(SUM(fa.score), 0) AS sum_score,
                COALESCE(SUM(fa.total), 0) AS sum_total,
                COUNT(fa.id) AS tests_count,
                lu.opted_in_at,
                ROW_NUMBER() OVER (
                    ORDER BY COALESCE(SUM(fa.score), 0) DESC,
                             CASE
                                 WHEN COALESCE(SUM(fa.total), 0) = 0 THEN 0
                                 ELSE 1.0 * SUM(fa.score) / SUM(fa.total)
                             END DESC,
                             COUNT(fa.id) DESC,
                             lu.opted_in_at ASC,
                             lu.user_id ASC
                ) AS place
            FROM leaderboard_users lu
            LEFT JOIN first_attempts fa ON fa.user_id = lu.user_id
            WHERE lu.rating_opt_in = 1
            GROUP BY lu.user_id, lu.opted_in_at
        )
        SELECT place
        FROM ranked
        WHERE user_id = ?
        """,
        (user_id,),
    )
    place_row = cur.fetchone()
    conn.close()

    return {
        "user_id": row[0],
        "username": row[1],
        "display_name": row[2],
        "rating_opt_in": bool(row[3]),
        "opted_in_at": row[4],
        "sum_score": row[5],
        "sum_total": row[6],
        "tests_count": row[7],
        "place": place_row[0] if place_row else None,
    }


# ── Mine progress ───────────────────────────────────────────────────────────

def get_mine_progress(user_id: int) -> dict | None:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM mine_progress WHERE user_id = ?", (user_id,))
    row = cur.fetchone()
    conn.close()

    if row is None:
        return None

    keys = [
        "user_id",
        "gold",
        "gems",
        "idle_accum",
        "unlocked_horizons",
        "completed_tasks",
        "unlocked_vseross",
        "completed_vseross",
        "unlocked_secret",
        "completed_secret",
        "total_answers",
        "correct_answers",
        "updated_at",
    ]
    d = dict(zip(keys, row))
    for f in (
        "unlocked_horizons",
        "completed_tasks",
        "unlocked_vseross",
        "completed_vseross",
        "unlocked_secret",
        "completed_secret",
    ):
        d[f] = json.loads(d[f])
    return d


def save_mine_progress(user_id: int, data: dict):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO mine_progress (
            user_id, gold, gems, idle_accum,
            unlocked_horizons, completed_tasks,
            unlocked_vseross, completed_vseross,
            unlocked_secret, completed_secret,
            total_answers, correct_answers, updated_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        ON CONFLICT(user_id) DO UPDATE SET
            gold = excluded.gold,
            gems = excluded.gems,
            idle_accum = excluded.idle_accum,
            unlocked_horizons = excluded.unlocked_horizons,
            completed_tasks = excluded.completed_tasks,
            unlocked_vseross = excluded.unlocked_vseross,
            completed_vseross = excluded.completed_vseross,
            unlocked_secret = excluded.unlocked_secret,
            completed_secret = excluded.completed_secret,
            total_answers = excluded.total_answers,
            correct_answers = excluded.correct_answers,
            updated_at = CURRENT_TIMESTAMP
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


# ── Вспомогательная функция — работает для обеих таблиц ──────────────────

def _get_history(table: str, user_id: int, limit: int = 10) -> list[dict]:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        f"SELECT topic, answer, ts FROM {table} WHERE user_id = ? ORDER BY ts DESC LIMIT ?",
        (user_id, limit),
    )
    rows = cur.fetchall()
    conn.close()
    return [{"topic": r[0], "answer": r[1], "ts": r[2]} for r in rows]


def _save_history_item(table: str, user_id: int, topic: str, answer: str, ts: int):
    conn = get_conn()
    cur = conn.cursor()

    cur.execute(
        f"DELETE FROM {table} WHERE user_id = ? AND lower(topic) = lower(?)",
        (user_id, topic),
    )
    cur.execute(
        f"INSERT INTO {table} (user_id, topic, answer, ts) VALUES (?, ?, ?, ?)",
        (user_id, topic, answer, ts),
    )
    cur.execute(
        f"""
        DELETE FROM {table}
        WHERE user_id = ?
          AND id NOT IN (
              SELECT id FROM {table}
              WHERE user_id = ?
              ORDER BY ts DESC
              LIMIT 10
          )
        """,
        (user_id, user_id),
    )
    conn.commit()
    conn.close()


# ── Theory history (Шахта) ─────────────────────────────────────────────

def get_theory_history(user_id: int, limit: int = 10) -> list[dict]:
    return _get_history("theory_history", user_id, limit)


def save_theory_history_item(user_id: int, topic: str, answer: str, ts: int):
    _save_history_item("theory_history", user_id, topic, answer, ts)


# ── Helper history (Помощник) ───────────────────────────────────────────

def get_helper_history(user_id: int, limit: int = 10) -> list[dict]:
    return _get_history("helper_history", user_id, limit)


def save_helper_history_item(user_id: int, topic: str, answer: str, ts: int):
    _save_history_item("helper_history", user_id, topic, answer, ts)