"""Настройки бота из переменных окружения (или файла .env рядом с main.py)."""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from datetime import time
from pathlib import Path
from zoneinfo import ZoneInfo

try:
    from dotenv import load_dotenv

    load_dotenv(Path(__file__).resolve().parent.parent / ".env")
except Exception:  # dotenv необязателен
    pass

MSK = ZoneInfo("Europe/Moscow")
APP_DIR = Path(__file__).resolve().parent.parent


def _env(name: str, default: str = "") -> str:
    return os.environ.get(name, default).strip()


def _times(value: str) -> list[time]:
    out = []
    for part in value.split(","):
        part = part.strip()
        if not part:
            continue
        hh, mm = part.split(":")
        out.append(time(int(hh), int(mm), tzinfo=MSK))
    return out


def _bool(value: str, default: bool) -> bool:
    if not value:
        return default
    return value.lower() in ("1", "true", "yes", "да", "on")


@dataclass
class Config:
    telegram_token: str = field(default_factory=lambda: _env("TELEGRAM_TOKEN") or _env("BOT_TOKEN"))
    owner_chat_id: int | None = field(default_factory=lambda: int(_env("OWNER_CHAT_ID")) if _env("OWNER_CHAT_ID") else None)

    gigachat_credentials: str = field(default_factory=lambda: _env("GIGACHAT_CREDENTIALS"))
    gigachat_model: str = field(default_factory=lambda: _env("GIGACHAT_MODEL", "GigaChat-2"))
    gigachat_scope: str = field(default_factory=lambda: _env("GIGACHAT_SCOPE", "GIGACHAT_API_PERS"))
    gigachat_verify_ssl: bool = field(default_factory=lambda: _bool(_env("GIGACHAT_VERIFY_SSL"), False))
    gigachat_ca_bundle: str = field(default_factory=lambda: _env("GIGACHAT_CA_BUNDLE"))
    gigachat_max_calls: int = field(default_factory=lambda: int(_env("GIGACHAT_MAX_CALLS_PER_RUN", "30")))

    data_dir: Path = field(default_factory=lambda: Path(_env("DATA_DIR", str(APP_DIR / "data"))))

    quote_times: list[time] = field(default_factory=lambda: _times(_env("QUOTE_TIMES", "10:05,14:05,18:05,22:05")))
    news_interval_min: int = field(default_factory=lambda: int(_env("NEWS_INTERVAL_MIN", "60")))
    digest_time: time = field(default_factory=lambda: _times(_env("DIGEST_TIME", "20:30"))[0])
    macro_time: time = field(default_factory=lambda: _times(_env("MACRO_TIME", "19:00"))[0])
    forecast_time: time = field(default_factory=lambda: _times(_env("FORECAST_TIME", "09:30"))[0])
    # дни недели для еженедельного прогноза: 0 — воскресенье, 1 — понедельник … 6 — суббота; пусто — не присылать
    forecast_days: tuple[int, ...] = field(
        default_factory=lambda: tuple(int(x) for x in _env("FORECAST_DAYS", "1").split(",") if x.strip())
    )

    move_alert_pct: float = field(default_factory=lambda: float(_env("MOVE_ALERT_PCT", "5")))
    macro_alert_pct: float = field(default_factory=lambda: float(_env("MACRO_ALERT_PCT", "10")))
    hysteresis_pct: float = field(default_factory=lambda: float(_env("ZONE_HYSTERESIS_PCT", "0.5")))
    news_lookback_hours: int = field(default_factory=lambda: int(_env("NEWS_LOOKBACK_HOURS", "12")))

    bundled_dir: Path = field(default_factory=lambda: APP_DIR / "data")

    @property
    def bundled_data(self) -> Path:
        """Папка data/ из репозитория GitHub: книга модели, levels.json, ленты, названия компаний."""
        return self.bundled_dir

    @property
    def db_path(self) -> Path:
        return self.data_dir / "state.db"


def load_config() -> Config:
    cfg = Config()
    cfg.data_dir.mkdir(parents=True, exist_ok=True)
    return cfg
