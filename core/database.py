import sqlite3
from pathlib import Path


DB_PATH = (
    Path(__file__).resolve().parent.parent
    / "data"
    / "myself.db"
)


def get_connection():
    DB_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    return sqlite3.connect(DB_PATH)


def _column_exists(
    cursor,
    table_name: str,
    column_name: str,
) -> bool:

    cursor.execute(
        f"PRAGMA table_info({table_name})"
    )

    columns = cursor.fetchall()

    return any(
        column[1] == column_name
        for column in columns
    )


def init_database():
    """
    初始化数据库。

    同时兼容旧版 v0.1 数据库：
    如果缺少新字段，就自动 ALTER TABLE 添加。
    """

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS training_samples (
            id INTEGER PRIMARY KEY AUTOINCREMENT,

            user_message TEXT NOT NULL,

            model_response TEXT,

            rating TEXT NOT NULL,

            corrected_response TEXT,

            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    # =========================
    # v0.2 migration
    # =========================

    new_columns = {
        "source": "TEXT DEFAULT 'chat'",
        "scene": "TEXT",
        "relationship": "TEXT",
        "style_tags": "TEXT",
    }

    for column_name, column_type in new_columns.items():

        if not _column_exists(
            cursor,
            "training_samples",
            column_name,
        ):

            cursor.execute(
                f"""
                ALTER TABLE training_samples
                ADD COLUMN {column_name} {column_type}
                """
            )

    conn.commit()
    conn.close()


def save_sample(
    user_message: str,
    model_response: str | None,
    rating: str,
    corrected_response: str | None = None,
    source: str = "chat",
    scene: str | None = None,
    relationship: str | None = None,
    style_tags: str | None = None,
):
    """
    保存人格训练候选样本。
    """

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO training_samples (
            user_message,
            model_response,
            rating,
            corrected_response,
            source,
            scene,
            relationship,
            style_tags
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            user_message,
            model_response,
            rating,
            corrected_response,
            source,
            scene,
            relationship,
            style_tags,
        ),
    )

    conn.commit()
    conn.close()


def get_interview_dimension_counts():
    """
    统计每个人格维度目前已经有多少条 Interview 数据。
    """

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT
            scene,
            COUNT(*)
        FROM training_samples
        WHERE source = 'interview'
        GROUP BY scene
        """
    )

    rows = cursor.fetchall()

    conn.close()

    return {
        scene: count
        for scene, count in rows
        if scene is not None
    }