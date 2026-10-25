"""Новости: RSS деловых СМИ и Google News по каждой компании, поиск упоминаний, отсев повторов."""
from __future__ import annotations

import calendar
import hashlib
import html
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote

import feedparser
import httpx

from .config import MSK

UA = {"User-Agent": "Mozilla/5.0 (portfolio-advisor-bot/1.0)"}


def load_feeds(path: Path | None) -> dict:
    if path and path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    from .defaults import FEEDS

    return FEEDS


def feed_urls(feeds: dict, aliases: dict) -> list[dict]:
    """Список лент: общие деловые + поиск Google News по каждой компании."""
    out = [{"name": f["name"], "url": f["url"], "hint": None} for f in feeds.get("general", [])]
    if feeds.get("google_news", True):
        tmpl = feeds.get("google_news_template")
        for key, a in aliases.items():
            q = a.get("query")
            if q:
                out.append({"name": f"Google News: {q}", "url": tmpl.format(query=quote(q)), "hint": key})
    return out


_TAG = re.compile(r"<[^>]+>")
_SPACE = re.compile(r"\s+")


def clean(text: str) -> str:
    return _SPACE.sub(" ", html.unescape(_TAG.sub(" ", text or ""))).strip()


def normalize_entries(raw: bytes | str, source: str) -> list[dict]:
    parsed = feedparser.parse(raw)
    items = []
    for e in parsed.entries:
        title = clean(e.get("title", ""))
        if not title:
            continue
        src = source
        # у Google News заголовок вида «Новость - Источник»
        if source.startswith("Google News") and " - " in title:
            title, src_name = title.rsplit(" - ", 1)
            src = src_name.strip() or source
        link = e.get("link", "")
        tm = e.get("published_parsed") or e.get("updated_parsed")
        published = (
            datetime.fromtimestamp(calendar.timegm(tm), tz=timezone.utc).astimezone(MSK) if tm else datetime.now(MSK)
        )
        items.append(
            {
                "id": hashlib.sha1((e.get("id") or link or title).encode("utf-8")).hexdigest(),
                "title": title,
                "summary": clean(e.get("summary", ""))[:600],
                "link": link,
                "source": src,
                "published": published,
            }
        )
    return items


async def fetch_feed(client: httpx.AsyncClient, url: str) -> bytes:
    r = await client.get(url, headers=UA, timeout=20, follow_redirects=True)
    r.raise_for_status()
    return r.content


# --------------------------------------------------------------- поиск упоминаний
def _pattern(alias: str) -> str:
    return r"(?<!\w)" + re.escape(alias) + r"\w{0,3}(?!\w)"


class Matcher:
    """Находит, о каких компаниях новость. Окончания слов допускаются (до 3 букв)."""

    def __init__(self, aliases: dict):
        self.rules = []
        for key, a in aliases.items():
            ci = [_pattern(x) for x in a.get("aliases", [])]
            cs = [_pattern(x) for x in a.get("aliases_cs", [])]
            self.rules.append(
                (
                    key,
                    re.compile("|".join(ci), re.IGNORECASE) if ci else None,
                    re.compile("|".join(cs)) if cs else None,
                )
            )

    def match(self, text: str) -> list[str]:
        found = []
        for key, ci, cs in self.rules:
            if (ci and ci.search(text)) or (cs and cs.search(text)):
                found.append(key)
        return found


def dedup_key(ticker: str, title: str) -> str:
    norm = re.sub(r"[^\w]+", "", title.lower())[:70]
    return f"{ticker}:{norm}"


# --------------------------------------------------------------- запасная оценка без GigaChat
LEVEL3 = ["дефолт", "банкрот", "национализ", "арест актив", "отказ от дивиденд", "не будет выплачивать дивиденд",
          "приостанов", "делистинг", "уголовн", "атак", "авари", "пожар", "санкции против"]
LEVEL2 = ["дивиденд", "отчет", "отчёт", "мсфо", "рсбу", "прибыл", "выручк", "ebitda", "oibda", "гайденс", "прогноз",
          "допэмисс", "spo", "размещени", "выкуп", "байбек", "налог", "ндпи", "санкци", "сделк", "приобрет",
          "продаж", "ключев", "ставк", "контракт", "оферт", "мирн", "перемири", "сила байкала", "северный поток"]


def heuristic_level(text: str) -> int:
    t = text.lower()
    if any(w in t for w in LEVEL3):
        return 3
    if any(w in t for w in LEVEL2):
        return 2
    return 1
