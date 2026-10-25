"""Оценка новостей через GigaChat. Модель справедливой стоимости бот не меняет —
GigaChat только решает, насколько новость важна для тезиса.
"""
from __future__ import annotations

import asyncio
import json
import logging
import re

from .config import Config
from .news import heuristic_level

log = logging.getLogger(__name__)

SYSTEM = (
    "Ты помощник долгосрочного инвестора на российском рынке акций. "
    "Ты оцениваешь, насколько новость важна для инвестиционного тезиса по компании. "
    "Ты не даёшь советов купить или продать. Отвечай строго одним JSON-объектом без пояснений."
)

PROMPT = """Компания: {name} ({ticker}).
Тезис инвестора: {thesis}
Условия слома тезиса: {breaks}
Что важно отслеживать: {watch}

Новость ({source}, {date}):
{title}
{summary}

Оцени новость:
- relevant: true, если новость действительно про эту компанию или прямо влияет на её бизнес; false, если совпало только слово.
- level: 0 — шум (движение котировок, мнения без фактов, повтор); 1 — полезно знать; 2 — может изменить вводные модели (прибыль, дивиденды, долг, прогноз компании, налоги, крупные сделки, регулирование, ставка ЦБ); 3 — похоже на одно из условий слома тезиса.
- reason: одно короткое предложение, почему такой уровень.
- impact: какую вводную модели это может затронуть (пустая строка, если никакую).

Ответ строго в формате:
{{"relevant": true, "level": 1, "reason": "...", "impact": "..."}}"""


def extract_json(text: str) -> dict:
    """GigaChat иногда оборачивает JSON в ```json ... ``` или добавляет текст — достаём первый объект."""
    m = re.search(r"\{.*\}", text or "", re.DOTALL)
    if not m:
        raise ValueError("в ответе нет JSON")
    data = json.loads(m.group(0))
    level = int(data.get("level", 1))
    return {
        "relevant": bool(data.get("relevant", True)),
        "level": max(0, min(3, level)),
        "reason": str(data.get("reason", "")).strip()[:300],
        "impact": str(data.get("impact", "")).strip()[:200],
    }


class NewsJudge:
    def __init__(self, cfg: Config):
        self.cfg = cfg
        self.client = None
        self.last_error = ""
        if cfg.gigachat_credentials:
            try:
                from gigachat import GigaChat

                kw = dict(
                    credentials=cfg.gigachat_credentials,
                    scope=cfg.gigachat_scope,
                    model=cfg.gigachat_model,
                    verify_ssl_certs=cfg.gigachat_verify_ssl,
                    timeout=40,
                )
                if cfg.gigachat_ca_bundle:
                    kw["ca_bundle_file"] = cfg.gigachat_ca_bundle
                self.client = GigaChat(**kw)
            except Exception as e:  # noqa: BLE001
                self.last_error = f"GigaChat не запустился: {e}"
                log.exception("GigaChat init failed")

    @property
    def enabled(self) -> bool:
        return self.client is not None

    async def _ask(self, user_text: str) -> str:
        from gigachat.models import Chat, Messages, MessagesRole

        chat = Chat(
            messages=[
                Messages(role=MessagesRole.SYSTEM, content=SYSTEM),
                Messages(role=MessagesRole.USER, content=user_text),
            ],
            temperature=0.1,
            max_tokens=300,
        )
        resp = await self.client.achat(chat)
        return resp.choices[0].message.content

    async def judge(self, issuer: dict, item: dict) -> dict:
        text = f"{item['title']}. {item.get('summary', '')}"
        if self.client is None:
            return {"relevant": True, "level": heuristic_level(text), "reason": "оценка по ключевым словам (GigaChat не подключён)",
                    "impact": "", "by": "rules"}
        prompt = PROMPT.format(
            name=issuer.get("name", ""),
            ticker=issuer.get("ticker", ""),
            thesis=issuer.get("thesis") or "—",
            breaks="; ".join(issuer.get("breaks", [])) or "—",
            watch="; ".join(issuer.get("watch", [])) or "—",
            source=item.get("source", ""),
            date=item["published"].strftime("%d.%m.%Y %H:%M"),
            title=item["title"],
            summary=item.get("summary", "")[:600],
        )
        try:
            answer = await self._ask(prompt)
            res = extract_json(answer)
            res["by"] = "gigachat"
            self.last_error = ""
            return res
        except Exception as e:  # noqa: BLE001
            self.last_error = f"{e.__class__.__name__}: {e}"[:300]
            log.warning("GigaChat judge failed: %s", self.last_error)
            return {"relevant": True, "level": heuristic_level(text), "reason": "оценка по ключевым словам (GigaChat не ответил)",
                    "impact": "", "by": "rules"}

    async def ping(self) -> str:
        if self.client is None:
            return self.last_error or "не подключён (нет GIGACHAT_CREDENTIALS)"
        try:
            ans = await asyncio.wait_for(self._ask("Ответь одним словом: работает"), timeout=45)
            return f"работает ({self.cfg.gigachat_model}): {ans.strip()[:40]}"
        except Exception as e:  # noqa: BLE001
            return f"ошибка: {e.__class__.__name__}: {str(e)[:200]}"
