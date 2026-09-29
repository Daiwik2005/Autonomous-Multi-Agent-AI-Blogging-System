import json
import os
import sqlite3
import unicodedata
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Iterator


DATABASE_PATH = Path(
    os.environ.get("TWEETY_DB_PATH", Path(__file__).with_name("tweety.sqlite3"))
)


def _connect() -> sqlite3.Connection:
    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(DATABASE_PATH, timeout=30)
    connection.row_factory = sqlite3.Row
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            topic TEXT NOT NULL,
            topic_key TEXT NOT NULL UNIQUE,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            tags TEXT NOT NULL,
            published_at TEXT NOT NULL
        )
        """
    )
    return connection


@contextmanager
def _database() -> Iterator[sqlite3.Connection]:
    connection = _connect()
    try:
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def _topic_key(topic: str) -> str:
    normalized = unicodedata.normalize("NFKC", topic).casefold()
    return " ".join(normalized.split())


def publish_post(
    title: str,
    content: str,
    tags: str = "AI, Agents, LangChain",
    topic: str | None = None,
) -> dict:
    cleaned_topic = (topic or title).strip()
    if not cleaned_topic:
        raise ValueError("A topic is required to publish a post.")

    published_at = datetime.now().astimezone()
    post = {
        "topic": cleaned_topic,
        "title": title.strip(),
        "date": f"{published_at:%B} {published_at.day}, {published_at:%Y}",
        "content": content.strip(),
        "tags": [tag.strip() for tag in tags.split(",") if tag.strip()],
    }
    try:
        with _database() as connection:
            connection.execute(
                """
                INSERT INTO posts (topic, topic_key, title, content, tags, published_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    post["topic"],
                    _topic_key(cleaned_topic),
                    post["title"],
                    post["content"],
                    json.dumps(post["tags"]),
                    published_at.isoformat(),
                ),
            )
    except sqlite3.IntegrityError as error:
        raise ValueError(f"The topic '{cleaned_topic}' has already been published.") from error
    return post


def get_posts() -> list[dict]:
    with _database() as connection:
        rows = connection.execute(
            "SELECT topic, title, content, tags, published_at FROM posts ORDER BY id DESC"
        ).fetchall()

    posts = []
    for row in rows:
        published_at = datetime.fromisoformat(row["published_at"])
        posts.append(
            {
                "topic": row["topic"],
                "title": row["title"],
                "date": f"{published_at:%B} {published_at.day}, {published_at:%Y}",
                "content": row["content"],
                "tags": json.loads(row["tags"]),
            }
        )
    return posts


def get_topics() -> list[str]:
    with _database() as connection:
        rows = connection.execute("SELECT topic FROM posts ORDER BY id DESC").fetchall()
    return [row["topic"] for row in rows]
