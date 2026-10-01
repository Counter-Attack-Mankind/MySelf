import sqlite3
from contextlib import contextmanager
from pathlib import Path


DB_PATH = Path(__file__).resolve().parent.parent / "data" / "myself.db"

EXPECTED_COLUMNS = {
    "training_samples": {
        "id", "user_message", "model_response", "rating", "corrected_response", "created_at"
    },
    "interview_sessions": {"id", "status", "started_at", "ended_at"},
    "interview_turns": {
        "id", "session_id", "turn_index", "parent_turn_id", "question_text", "answer_text",
        "question_strategy", "life_domain", "relationship", "task_type", "communication_goal",
        "emotion_tone", "created_at", "answered_at",
    },
    "style_observations": {"id", "turn_id", "observation_text", "confidence", "created_at"},
}


@contextmanager
def get_connection():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        with conn:
            yield conn
    finally:
        conn.close()


def init_database():
    with get_connection() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS training_samples (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_message TEXT NOT NULL,
                model_response TEXT NOT NULL,
                rating TEXT NOT NULL CHECK (rating IN ('good', 'normal', 'bad', 'corrected')),
                corrected_response TEXT,
                created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS interview_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                status TEXT NOT NULL CHECK (status IN ('active', 'completed', 'cancelled')),
                started_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                ended_at DATETIME
            );

            CREATE TABLE IF NOT EXISTS interview_turns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id INTEGER NOT NULL,
                turn_index INTEGER NOT NULL,
                parent_turn_id INTEGER,
                question_text TEXT NOT NULL,
                answer_text TEXT NOT NULL,
                question_strategy TEXT,
                life_domain TEXT,
                relationship TEXT,
                task_type TEXT,
                communication_goal TEXT,
                emotion_tone TEXT,
                created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                answered_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (session_id) REFERENCES interview_sessions(id) ON DELETE CASCADE,
                FOREIGN KEY (parent_turn_id) REFERENCES interview_turns(id) ON DELETE SET NULL,
                UNIQUE (session_id, turn_index)
            );

            CREATE TABLE IF NOT EXISTS style_observations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                turn_id INTEGER NOT NULL,
                observation_text TEXT NOT NULL,
                confidence REAL NOT NULL DEFAULT 0.2,
                created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (turn_id) REFERENCES interview_turns(id) ON DELETE CASCADE
            );
            """
        )
        _check_schema(conn)


def _check_schema(conn):
    for table_name, expected in EXPECTED_COLUMNS.items():
        actual = {row[1] for row in conn.execute(f"PRAGMA table_info({table_name})")}
        if actual != expected:
            raise RuntimeError(
                f"数据库表 {table_name} 与当前代码不兼容。请删除 {DB_PATH} 后重新启动。"
            )


def save_training_sample(
    user_message: str,
    model_response: str,
    rating: str,
    corrected_response: str | None = None,
):
    with get_connection() as conn:
        cursor = conn.execute(
            """
            INSERT INTO training_samples (user_message, model_response, rating, corrected_response)
            VALUES (?, ?, ?, ?)
            """,
            (user_message, model_response, rating, corrected_response),
        )
        return cursor.lastrowid


def create_interview_session():
    with get_connection() as conn:
        cursor = conn.execute("INSERT INTO interview_sessions (status) VALUES ('active')")
        return cursor.lastrowid


def finish_interview_session(session_id: int, status: str):
    with get_connection() as conn:
        conn.execute(
            "UPDATE interview_sessions SET status = ?, ended_at = CURRENT_TIMESTAMP WHERE id = ?",
            (status, session_id),
        )


def save_interview_turn(
    session_id: int,
    turn_index: int,
    question_text: str,
    answer_text: str,
    parent_turn_id: int | None = None,
    question_strategy: str | None = None,
    life_domain: str | None = None,
    relationship: str | None = None,
    task_type: str | None = None,
    communication_goal: str | None = None,
    emotion_tone: str | None = None,
):
    with get_connection() as conn:
        cursor = conn.execute(
            """
            INSERT INTO interview_turns (
                session_id, turn_index, parent_turn_id, question_text, answer_text,
                question_strategy, life_domain, relationship, task_type,
                communication_goal, emotion_tone
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                session_id, turn_index, parent_turn_id, question_text, answer_text,
                question_strategy, life_domain, relationship, task_type,
                communication_goal, emotion_tone,
            ),
        )
        return cursor.lastrowid


def save_style_observation(turn_id: int, observation_text: str, confidence: float = 0.2):
    with get_connection() as conn:
        cursor = conn.execute(
            """
            INSERT INTO style_observations (turn_id, observation_text, confidence)
            VALUES (?, ?, ?)
            """,
            (turn_id, observation_text, confidence),
        )
        return cursor.lastrowid


def get_interview_dimension_counts():
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT communication_goal, COUNT(*)
            FROM interview_turns
            WHERE communication_goal IS NOT NULL
            GROUP BY communication_goal
            """
        ).fetchall()
    return dict(rows)
