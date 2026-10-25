"""Состояние бота в SQLite: зоны, увиденные новости, отправленные сигналы.

Если хостинг стирает диск при перезапуске, бот просто начнёт с чистого листа:
зоны запишет молча, а новости возьмёт только за последние часы.
"""
from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path

from .config import MSK

SCHEMA = """
CREATE TABLE IF NOT EXISTS kv (key TEXT PRIMARY KEY, value TEXT);
CREATE TABLE IF NOT EXISTS zones (ticker TEXT PRIMARY KEY, zone TEXT, price REAL, updated_at TEXT);
CREATE TABLE IF NOT EXISTS moves (ticker TEXT, day TEXT, PRIMARY KEY (ticker, day));
CREATE TABLE IF NOT EXISTS news (
    id TEXT PRIMARY KEY, dedup TEXT, ticker TEXT, title TEXT, link TEXT, source TEXT,
    published TEXT, level INTEGER, reason TEXT, impact TEXT, created_at TEXT, sent INTEGER DEFAULT 0
);
CREATE INDEX IF NOT EXISTS news_dedup ON news (dedup);
CREATE INDEX IF NOT EXISTS news_created ON news (created_at);
CREATE TABLE IF NOT EXISTS macro_alerts (item TEXT PRIMARY KEY, last_sent TEXT);
"""


def now() -> datetime:
    return datetime.now(MSK)


class Storage:
    def __init__(self, path: Path):
        self.path = path
        self.db = sqlite3.connect(str(path), check_same_thread=False)
        self.db.row_factory = sqlite3.Row
        self.db.executescript(SCHEMA)
        self.db.commit()

    # --- kv
    def get(self, key: str, default=None):
        row = self.db.execute("SELECT value FROM kv WHERE key=?", (key,)).fetchone()
        return json.loads(row["value"]) if row else default

    def set(self, key: str, value) -> None:
        self.db.execute("INSERT OR REPLACE INTO kv (key, value) VALUES (?, ?)", (key, json.dumps(value, ensure_ascii=False)))
        self.db.commit()

    # --- зоны
    def get_zone(self, ticker: str) -> tuple[str, float] | None:
        row = self.db.execute("SELECT zone, price FROM zones WHERE ticker=?", (ticker,)).fetchone()
        return (row["zone"], row["price"]) if row else None

    def set_zone(self, ticker: str, zone: str, price: float) -> None:
        self.db.execute(
            "INSERT OR REPLACE INTO zones (ticker, zone, price, updated_at) VALUES (?, ?, ?, ?)",
            (ticker, zone, price, now().isoformat()),
        )
        self.db.commit()

    # --- резкие движения (не чаще раза в день)
    def move_alerted(self, ticker: str, day: str) -> bool:
        return self.db.execute("SELECT 1 FROM moves WHERE ticker=? AND day=?", (ticker, day)).fetchone() is not None

    def mark_move(self, ticker: str, day: str) -> None:
        self.db.execute("INSERT OR IGNORE INTO moves (ticker, day) VALUES (?, ?)", (ticker, day))
        self.db.commit()

    # --- новости
    def news_seen(self, news_id: str, dedup: str, within_hours: int = 48) -> bool:
        if self.db.execute("SELECT 1 FROM news WHERE id=?", (news_id,)).fetchone():
            return True
        since = (now() - timedelta(hours=within_hours)).isoformat()
        return self.db.execute("SELECT 1 FROM news WHERE dedup=? AND created_at>=?", (dedup, since)).fetchone() is not None

    def add_news(self, item: dict) -> None:
        self.db.execute(
            "INSERT OR IGNORE INTO news (id, dedup, ticker, title, link, source, published, level, reason, impact, created_at, sent) "
            "VALUES (:id, :dedup, :ticker, :title, :link, :source, :published, :level, :reason, :impact, :created_at, :sent)",
            {"sent": 0, "created_at": now().isoformat(), **item},
        )
        self.db.commit()

    def mark_news_sent(self, news_id: str) -> None:
        self.db.execute("UPDATE news SET sent=1 WHERE id=?", (news_id,))
        self.db.commit()

    def recent_news(self, hours: int = 24, min_level: int = 1) -> list[sqlite3.Row]:
        since = (now() - timedelta(hours=hours)).isoformat()
        return self.db.execute(
            "SELECT * FROM news WHERE created_at>=? AND level>=? ORDER BY level DESC, created_at DESC",
            (since, min_level),
        ).fetchall()

    # --- макро
    def macro_last_sent(self, item: str) -> datetime | None:
        row = self.db.execute("SELECT last_sent FROM macro_alerts WHERE item=?", (item,)).fetchone()
        return datetime.fromisoformat(row["last_sent"]) if row else None

    def mark_macro(self, item: str) -> None:
        self.db.execute("INSERT OR REPLACE INTO macro_alerts (item, last_sent) VALUES (?, ?)", (item, now().isoformat()))
        self.db.commit()
