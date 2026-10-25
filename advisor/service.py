"""Логика бота без Telegram: проверки котировок, новостей, макро, тексты сообщений."""
from __future__ import annotations

import asyncio
import html
import logging
from datetime import timedelta

import httpx

from . import market, news, zones
from .config import Config
from .giga import NewsJudge
from .levels import (diff_levels, drop_override, load_aliases, load_bundled, load_override, parse_workbook,
                     save_override, snapshot)
from .storage import Storage, now

log = logging.getLogger(__name__)

LEVEL_LABEL = {1: "полезно знать", 2: "может изменить модель", 3: "похоже на слом тезиса"}
LEVEL_ICON = {1: "🔹", 2: "🟠", 3: "🔴"}
ZONE_SHORT = {zones.BUY: "покупка", zones.HOLD: "держать", zones.NEAR: "близко к продаже", zones.SELL: "продажа"}
ASSUMPTION_NAMES = {
    "usdrub": "курс доллара", "gold_usd": "цена золота", "key_rate_2027": "ставка ЦБ 2027", "ofz10": "доходность ОФЗ",
    "p_peace": "вероятность мира", "t_peace": "срок до мира", "buy_disc": "граница зоны покупки",
    "sell_prem": "граница цены продажи", "ai_rf": "поправка ИИ на Россию", "ai_mkt": "рынок ИИ в 2030",
}


def esc(s) -> str:
    return html.escape(str(s or ""), quote=False)


def rub(x: float | None, d: int = 0) -> str:
    if x is None:
        return "—"
    return f"{x:,.{d}f}".replace(",", " ").replace(".", ",")


def pct(x: float | None) -> str:
    return "—" if x is None else f"{x:+.0%}"


def split_message(text: str, limit: int = 3900) -> list[str]:
    """Telegram ограничивает сообщение 4096 символами — режем по строкам."""
    parts, cur = [], ""
    for line in text.split("\n"):
        if len(cur) + len(line) + 1 > limit and cur:
            parts.append(cur)
            cur = ""
        cur += line + "\n"
    if cur.strip():
        parts.append(cur)
    return parts


class Advisor:
    def __init__(self, cfg: Config, storage: Storage | None = None, judge: NewsJudge | None = None):
        self.cfg = cfg
        self.storage = storage or Storage(cfg.db_path)
        self.judge = judge or NewsJudge(cfg)
        self.problems: list[str] = []
        self.aliases = load_aliases(cfg.find_file("aliases.json"))
        if not self.aliases:
            self.problems.append("нет файла aliases.json — новости по компаниям искать не по чему")
        feeds_path = cfg.find_file("feeds.json")
        if feeds_path is None:
            self.problems.append("нет файла feeds.json — беру ленты по умолчанию (РБК, Интерфакс, Google News)")
        self.feeds = news.load_feeds(feeds_path)
        self.matcher = news.Matcher(self.aliases)
        try:
            self.levels = self.select_model()
        except FileNotFoundError as e:
            self.problems.append(f"модель не найдена: {e}. Положите книгу в репозиторий как model/model.xlsx")
            self.levels = {"issuers": [], "assumptions": {}, "version": None, "_origin": "none"}
        for p in self.problems:
            log.warning(p)
        self.feed_status: dict[str, str] = {}
        self.http = httpx.AsyncClient()

    # ------------------------------------------------------------ какая модель действует
    def select_model(self) -> dict:
        """Главный источник — GitHub (папка data/ в репозитории).

        Если в GitHub появилась новая версия книги — действует она. Если вы прислали книгу в чат
        после последнего обновления GitHub — действует присланная, пока в GitHub не появится новая.
        """
        bundled = load_bundled(self.cfg.search_dirs())
        seen = self.storage.get("github_version_seen")
        override = load_override(self.cfg.data_dir)
        if bundled.get("version") != seen:
            self.storage.set("github_version_seen", bundled.get("version"))
            if override is not None and seen is not None:
                drop_override(self.cfg.data_dir)  # в GitHub новая модель — присланная в чат больше не нужна
                override = None
        if override is not None and override.get("version") != bundled.get("version"):
            return override
        return bundled

    def model_file(self) -> str | None:
        """Путь к Excel-книге действующей модели (чтобы прислать её в чат)."""
        return self.levels.get("_xlsx")

    def pending_announcement(self) -> tuple[str, str | None] | None:
        """Если действующая модель ещё не отправлялась владельцу — текст прогноза и путь к книге."""
        ver = self.levels.get("version")
        if not self.issuers() or (ver and ver == self.storage.get("announced_version")):
            return None
        prev = self.storage.get("announced_snapshot")
        return self.announcement_text(prev), self.model_file()

    def mark_announced(self) -> None:
        self.storage.set("announced_version", self.levels.get("version"))
        self.storage.set("announced_snapshot", snapshot(self.levels))

    def announcement_text(self, prev: dict | None) -> str:
        lv = self.levels
        origin = {"github": "из GitHub", "chat": "из присланной в чат книги"}.get(lv.get("_origin"), "")
        lines = [f"📘 <b>Действующий прогноз</b> {origin} · {esc(lv.get('source', ''))}"]
        if lv.get("_warning"):
            lines.append(f"⚠️ {esc(lv['_warning'])}")
        if prev:
            changes = diff_levels(prev, lv)
            if changes:
                lines.append("Что изменилось в справедливых ценах:")
                lines += [f"• {esc(c)}" for c in changes]
            else:
                lines.append("Справедливые цены не изменились.")
            pa, na = prev.get("assumptions", {}), lv.get("assumptions", {})
            ach = [k for k in na if k in pa and abs((na[k] or 0) - (pa[k] or 0)) > 1e-9]
            if ach:
                lines.append("Изменились допущения: " + ", ".join(esc(ASSUMPTION_NAMES.get(k, k)) for k in ach) + ".")
        lines.append("")
        lines.append(self.forecast_overview())
        lines.append("Подробно по каждой бумаге — /forecast или /forecast SBER.")
        return "\n".join(lines)

    # ------------------------------------------------------------ уровни
    def issuers(self) -> list[dict]:
        return self.levels["issuers"]

    def tickers(self) -> list[str]:
        return [i["ticker"] for i in self.issuers()]

    def issuer_for_key(self, key: str) -> dict:
        if key == "MACRO":
            a = self.levels.get("assumptions", {})
            m = self.aliases.get("MACRO", {})
            thesis = (
                f"Модель исходит из: средняя ключевая ставка в 2027 — {a.get('key_rate_2027', 0.13):.1%}; "
                f"мир и снятие санкций через {a.get('t_peace', 5):.0f} лет с вероятностью {a.get('p_peace', 0.5):.0%}; "
                f"курс {a.get('usdrub', 85):.0f} ₽/$; золото ${a.get('gold_usd', 3800):,.0f}.".replace(",", " ")
            )
            return {"ticker": "МАКРО", "name": m.get("name", "Макро и геополитика"), "thesis": thesis,
                    "breaks": m.get("breaks", []), "watch": m.get("watch", [])}
        for it in self.issuers():
            if it["ticker"] == key:
                return it
        return {"ticker": key, "name": key, "thesis": "", "breaks": [], "watch": []}

    def update_levels_from_file(self, data: bytes, filename: str) -> str:
        new = parse_workbook(data)
        new["source"] = filename
        prev = self.storage.get("announced_snapshot") or snapshot(self.levels)
        save_override(new, data, self.cfg.data_dir)
        self.levels = load_override(self.cfg.data_dir)
        # зоны пересчитаем заново, без сигналов о «смене»
        for t in self.tickers():
            self.storage.db.execute("DELETE FROM zones WHERE ticker=?", (t,))
        self.storage.db.commit()
        text = self.announcement_text(prev)
        self.mark_announced()
        return (
            f"✅ Принял книгу «{esc(filename)}» ({len(new['issuers'])} бумаг). Она действует, пока в GitHub не появится новая версия.\n"
            "Чтобы модель не потерялась, положите этот же файл в репозиторий: model/model.xlsx.\n\n" + text
        )

    # ------------------------------------------------------------ прогноз
    def forecast_overview(self, prices: dict | None = None) -> str:
        prices = prices or (self.storage.get("last_quotes") or {}).get("prices", {})
        rows = [f"{'Бумага':<6}{'Справ.':>8}{'Цена':>8}{'Потенц.':>8}"]
        for lv in self.issuers():
            p = (prices.get(lv["ticker"]) or {}).get("price")
            rows.append(
                f"{lv['ticker']:<6}{rub(lv['fair']):>8}{rub(p, 1 if p and p < 1000 else 0) if p else '—':>8}"
                f"{pct(lv['fair'] / p - 1) if p else '—':>8}"
            )
        a = self.levels.get("assumptions", {})
        tail = ""
        if a:
            tail = (
                f"\nДопущения: ставка ЦБ 2027 {a.get('key_rate_2027', 0):.1%}; курс {a.get('usdrub', 0):.0f} ₽/$; "
                f"золото ${rub(a.get('gold_usd'))}; мир {a.get('p_peace', 0):.0%} через {a.get('t_peace', 0):.0f} лет; "
                f"ИИ по мультипликаторам лидеров × {a.get('ai_rf', 1):.1f}.".replace(".", ",").rstrip(",") + "."
            )
        return "<pre>" + esc("\n".join(rows)) + "</pre>" + tail

    def forecast_card(self, lv: dict, price: float | None) -> str:
        t = lv["ticker"]
        ref = " <i>(для справки, позиции нет)</i>" if not lv.get("qty") else ""
        head = f"<b>{esc(t)} · {esc(lv['name'])}</b>{ref} — справедливая <b>{rub(lv['fair'])} ₽</b>"
        if price:
            head += f" (цена {rub(price, 1 if price < 1000 else 0)} ₽, потенциал {pct(lv['fair'] / price - 1)}, {ZONE_SHORT[zones.classify(price, lv)]})"
        lines = [head, f"Покупка до {rub(lv['buy'])} · близко к продаже от {rub(lv['near'])} · продажа от {rub(lv['sell'])}"]
        comps = lv.get("components") or []
        if comps:
            s = f"база {rub(lv.get('base'))}"
            for n, v in comps:
                s += f" {'+' if v >= 0 else '−'} {esc(n)} {rub(abs(v))}"
            lines.append("Из чего: " + s)
        if lv.get("method"):
            lines.append(f"Метод: {esc(lv['method'])}")
        if lv.get("levers"):
            lines.append("Главные допущения: " + "; ".join(f"{esc(k)} — {esc(v)}" for k, v in lv["levers"]))
        if lv.get("thesis"):
            lines.append(f"Тезис: {esc(lv['thesis'])}")
        if lv.get("breaks"):
            lines.append("Слом тезиса: " + "; ".join(esc(b) for b in lv["breaks"]))
        return "\n".join(lines)

    async def forecast_text(self, ticker: str | None = None) -> str:
        try:
            prices = await self.fetch_prices()
        except Exception:  # noqa: BLE001
            prices = (self.storage.get("last_quotes") or {}).get("prices", {})
        items = self.issuers()
        if ticker:
            items = [i for i in items if i["ticker"] == ticker.upper()]
            if not items:
                return f"В модели нет бумаги {esc(ticker)}. Есть: {', '.join(self.tickers())}."
        head = f"📘 <b>Прогноз по модели</b> · обновлена {esc(self.levels.get('updated', ''))} · {esc(self.levels.get('source', ''))}"
        cards = [self.forecast_card(i, (prices.get(i["ticker"]) or {}).get("price")) for i in items]
        body = "\n\n".join(cards)
        if not ticker:
            body = self.forecast_overview(prices) + "\n\n" + body
        return head + "\n\n" + body + "\n\n<i>Это прогноз модели, а не рекомендация. Модель меняем вместе с Claude.</i>"

    # ------------------------------------------------------------ котировки
    async def fetch_prices(self) -> dict[str, dict]:
        if not self.tickers():
            return {}
        prices = await market.fetch_shares(self.http, self.tickers())
        self.storage.set("last_quotes", {"at": now().isoformat(), "prices": prices})
        return prices

    async def check_quotes(self, silent: bool = False) -> list[str]:
        prices = await self.fetch_prices()
        alerts = []
        day = now().strftime("%Y-%m-%d")
        for lv in self.issuers():
            t = lv["ticker"]
            q = prices.get(t)
            if not q:
                continue
            p = q["price"]
            prev = self.storage.get_zone(t)
            prev_zone = prev[0] if prev else None
            zone = zones.classify_with_hysteresis(p, lv, prev_zone, self.cfg.hysteresis_pct)
            if prev_zone is not None and zone != prev_zone and not silent:
                alerts.append(zones.transition_text(t, esc(lv["name"]), prev_zone, zone, p, lv))
            self.storage.set_zone(t, zone, p)
            if q.get("prev") and not silent:
                ch = p / q["prev"] - 1
                if abs(ch) * 100 >= self.cfg.move_alert_pct and not self.storage.move_alerted(t, day):
                    self.storage.mark_move(t, day)
                    alerts.append(
                        f"⚡ <b>{t}</b> {esc(lv['name'])}: {ch:+.1%} за день, цена {rub(p, 2)} ₽.\n"
                        "Резкое движение — проверьте новости. Если причина в бизнесе компании, обсудите с Claude, меняет ли это модель."
                    )
        return alerts

    # ------------------------------------------------------------ новости
    async def _fetch_all_feeds(self) -> list[tuple[dict, list[dict]]]:
        sem = asyncio.Semaphore(6)
        feeds = news.feed_urls(self.feeds, self.aliases)

        async def one(f):
            async with sem:
                try:
                    raw = await news.fetch_feed(self.http, f["url"])
                    items = news.normalize_entries(raw, f["name"])
                    self.feed_status[f["name"]] = f"ok ({len(items)})"
                    return f, items
                except Exception as e:  # noqa: BLE001
                    self.feed_status[f["name"]] = f"ошибка: {e.__class__.__name__}"
                    return f, []

        return await asyncio.gather(*(one(f) for f in feeds))

    async def check_news(self) -> list[str]:
        baseline = not self.storage.get("news_initialized", False)
        results = await self._fetch_all_feeds()
        cutoff = now() - timedelta(hours=self.cfg.news_lookback_hours)
        candidates = []
        for f, items in results:
            for it in items:
                if it["published"] < cutoff:
                    continue
                keys = self.matcher.match(f"{it['title']} {it['summary']}")
                for key in keys:
                    dk = news.dedup_key(key, it["title"])
                    nid = f"{it['id']}:{key}"
                    if self.storage.news_seen(nid, dk):
                        continue
                    candidates.append((key, it, nid, dk))
        # одна и та же новость могла прийти из нескольких лент
        uniq, seen_dk = [], set()
        for c in candidates:
            if c[3] not in seen_dk:
                seen_dk.add(c[3])
                uniq.append(c)

        alerts = []
        calls = 0
        for key, it, nid, dk in sorted(uniq, key=lambda c: c[1]["published"]):
            row = {"id": nid, "dedup": dk, "ticker": key, "title": it["title"], "link": it["link"],
                   "source": it["source"], "published": it["published"].isoformat()}
            if baseline:
                self.storage.add_news({**row, "level": -1, "reason": "до первого запуска", "impact": ""})
                continue
            issuer = self.issuer_for_key(key)
            if calls < self.cfg.gigachat_max_calls or not self.judge.enabled:
                res = await self.judge.judge(issuer, it)
                calls += 1 if self.judge.enabled else 0
            else:
                res = {"relevant": True, "level": news.heuristic_level(it["title"]), "reason": "оценка по ключевым словам (лимит GigaChat на этот запуск)",
                       "impact": "", "by": "rules"}
            level = res["level"] if res["relevant"] else 0
            self.storage.add_news({**row, "level": level, "reason": res["reason"], "impact": res["impact"]})
            if level >= 2:
                alerts.append(self.news_alert_text(issuer, it, level, res))
                self.storage.mark_news_sent(nid)
        if baseline:
            self.storage.set("news_initialized", True)
        self.storage.set("last_news_check", now().isoformat())
        return alerts

    def news_alert_text(self, issuer: dict, it: dict, level: int, res: dict) -> str:
        t = issuer["ticker"]
        lines = [
            f"{LEVEL_ICON[level]} <b>{esc(t)}</b> · {LEVEL_LABEL[level]}",
            f"<a href=\"{esc(it['link'])}\">{esc(it['title'])}</a>",
            f"<i>{esc(it['source'])}, {it['published'].strftime('%d.%m %H:%M')}</i>",
        ]
        if res.get("reason"):
            lines.append(f"Почему: {esc(res['reason'])}")
        if res.get("impact"):
            lines.append(f"Что в модели: {esc(res['impact'])}")
        lines.append(f"→ Обсудить с Claude: «Новость по {esc(t)}: {esc(it['title'])}. Как это меняет модель?»")
        return "\n".join(lines)

    # ------------------------------------------------------------ макро
    async def macro_values(self) -> dict:
        out = {}
        try:
            out["usdrub"] = await market.fetch_usdrub(self.http)
        except Exception as e:  # noqa: BLE001
            out["usdrub_err"] = e.__class__.__name__
        try:
            g = await market.fetch_gold_rub_per_gram(self.http)
            if out.get("usdrub"):
                out["gold_usd"] = market.gold_usd_per_oz(g, out["usdrub"])
        except Exception as e:  # noqa: BLE001
            out["gold_err"] = e.__class__.__name__
        return out

    async def check_macro(self) -> list[str]:
        a = self.levels.get("assumptions", {})
        vals = await self.macro_values()
        alerts = []
        items = [
            ("usdrub", "Курс доллара", "₽", "Полюс (выручка в долларах), газовые опционы Газпрома, экспортёры"),
            ("gold_usd", "Золото", "$/унц", "Полюс"),
        ]
        for key, name, unit, who in items:
            fact, model = vals.get(key), a.get(key)
            if not fact or not model:
                continue
            dev = fact / model - 1
            last = self.storage.macro_last_sent(key)
            if abs(dev) * 100 >= self.cfg.macro_alert_pct and (last is None or now() - last > timedelta(days=7)):
                self.storage.mark_macro(key)
                alerts.append(
                    f"📊 <b>{name}</b>: {rub(fact, 1 if key == 'usdrub' else 0)} {unit} — на {dev:+.0%} от допущения модели "
                    f"({rub(model, 0)} {unit}).\nЗатрагивает: {who}. Стоит обсудить с Claude, не пора ли поменять допущение."
                )
        return alerts

    # ------------------------------------------------------------ тексты
    async def status_text(self) -> str:
        try:
            prices = await self.fetch_prices()
            when = now()
            note = ""
        except Exception as e:  # noqa: BLE001
            saved = self.storage.get("last_quotes") or {}
            prices = saved.get("prices", {})
            when = None
            note = f"\n⚠️ Биржа не ответила ({e.__class__.__name__}), показываю последние сохранённые цены."
        rows = [f"{'Бумага':<6}{'Цена':>9}{'Справ.':>9}{'Потенц.':>8}  Зона"]
        tot_now = tot_fair = 0.0
        for lv in self.issuers():
            t = lv["ticker"]
            p = (prices.get(t) or {}).get("price")
            if p is None:
                rows.append(f"{t:<6}{'—':>9}{rub(lv['fair']):>9}")
                continue
            z = zones.classify(p, lv)
            up = lv["fair"] / p - 1
            rows.append(f"{t:<6}{rub(p, 1 if p < 1000 else 0):>9}{rub(lv['fair']):>9}{pct(up):>8}  {ZONE_SHORT[z]}")
            q = lv.get("qty") or 0
            tot_now += q * p
            tot_fair += q * lv["fair"]
        head = "📋 <b>Бумаги против модели</b>"
        if when:
            head += f" · {when.strftime('%d.%m %H:%M')} МСК, задержка биржи ~15 мин"
        body = "<pre>" + esc("\n".join(rows)) + "</pre>"
        port = ""
        if tot_now:
            port = f"\nАкции в портфелях: {rub(tot_now)} ₽ · по справедливым ценам {rub(tot_fair)} ₽ ({pct(tot_fair / tot_now - 1)})."
        src = f"\n<i>Модель: {esc(self.levels.get('source', 'levels.json'))}, обновлена {esc(self.levels.get('updated', ''))}</i>"
        return head + "\n" + body + port + note + src

    def _days(self) -> str:
        names = ["воскресеньям", "понедельникам", "вторникам", "средам", "четвергам", "пятницам", "субботам"]
        return ", ".join(names[d % 7] for d in self.cfg.forecast_days)

    def levels_text(self) -> str:
        rows = [f"{'Бумага':<6}{'Справ.':>9}{'Покупка≤':>10}{'Продажа≥':>10}"]
        for lv in self.issuers():
            rows.append(f"{lv['ticker']:<6}{rub(lv['fair']):>9}{rub(lv['buy']):>10}{rub(lv['sell']):>10}")
        a = self.levels.get("assumptions", {})
        tail = ""
        if a:
            tail = (
                f"\nДопущения: ставка ЦБ 2027 {a.get('key_rate_2027', 0):.1%}, курс {a.get('usdrub', 0):.0f} ₽/$, "
                f"золото ${rub(a.get('gold_usd'))}, мир {a.get('p_peace', 0):.0%} через {a.get('t_peace', 0):.0f} лет."
            )
        return "🎯 <b>Уровни из модели</b>\n<pre>" + esc("\n".join(rows)) + "</pre>" + tail + \
            "\n<i>Подробный прогноз — /forecast. Модель обновляется через GitHub: model/model.xlsx.</i>"

    def news_text(self, hours: int = 24, min_level: int = 1, limit: int = 15) -> str:
        rows = self.storage.recent_news(hours, min_level)
        if not rows:
            return f"За последние {hours} ч важных новостей по вашим бумагам нет."
        lines = [f"📰 <b>Новости за {hours} ч</b> (важные сверху)"]
        for r in rows[:limit]:
            lvl = max(1, min(3, r["level"]))
            lines.append(f"{LEVEL_ICON[lvl]} <b>{esc(r['ticker'])}</b> <a href=\"{esc(r['link'])}\">{esc(r['title'])}</a> — <i>{esc(r['source'])}</i>")
        if len(rows) > limit:
            lines.append(f"…и ещё {len(rows) - limit}.")
        return "\n".join(lines)

    async def digest_text(self) -> str:
        parts = [f"🗓 <b>Итоги дня, {now().strftime('%d.%m.%Y')}</b>", await self.status_text()]
        vals = await self.macro_values()
        a = self.levels.get("assumptions", {})
        if vals.get("usdrub") or vals.get("gold_usd"):
            m = []
            if vals.get("usdrub"):
                m.append(f"курс {rub(vals['usdrub'], 1)} ₽ (в модели {rub(a.get('usdrub'))})")
            if vals.get("gold_usd"):
                m.append(f"золото ${rub(vals['gold_usd'])} (в модели ${rub(a.get('gold_usd'))})")
            parts.append("💱 " + ", ".join(m))
        parts.append(self.news_text(24, 1, 12))
        return "\n\n".join(parts)

    async def health_text(self) -> str:
        lines = ["🩺 <b>Проверка бота</b>"]
        try:
            p = await market.fetch_shares(self.http, (self.tickers() or ["SBER"])[:2])
            sample = ", ".join(f"{k} {v['price']}" for k, v in p.items())
            lines.append(f"Мосбиржа: ok ({sample})")
        except Exception as e:  # noqa: BLE001
            lines.append(f"Мосбиржа: ошибка {e.__class__.__name__}")
        vals = await self.macro_values()
        lines.append(f"Курс доллара: {rub(vals.get('usdrub'), 2) if vals.get('usdrub') else 'ошибка ' + vals.get('usdrub_err', '')}")
        lines.append(f"Золото: {('$' + rub(vals.get('gold_usd'))) if vals.get('gold_usd') else 'ошибка ' + vals.get('gold_err', '')}")
        await self._fetch_all_feeds()
        ok = sum(1 for v in self.feed_status.values() if v.startswith("ok"))
        lines.append(f"Ленты новостей: работают {ok} из {len(self.feed_status)}")
        bad = [f"  • {esc(k)}: {esc(v)}" for k, v in self.feed_status.items() if not v.startswith("ok")]
        lines += bad[:10]
        lines.append(f"GigaChat: {esc(await self.judge.ping())}")
        origin = {"github": "из GitHub", "chat": "присланная в чат"}.get(self.levels.get("_origin"), "")
        lines.append(f"Модель: {len(self.issuers())} бумаг, {origin}, файл {esc(self.levels.get('source', 'levels.json'))}, версия {esc(self.levels.get('version', ''))}")
        if self.levels.get("_where"):
            lines.append(f"Папка модели на сервере: {esc(self.levels['_where'])}")
        if self.levels.get("_warning"):
            lines.append(f"⚠️ {esc(self.levels['_warning'])}")
        for p in self.problems:
            lines.append(f"⚠️ {esc(p)}")
        lines.append(f"Данные бота: {esc(self.cfg.data_dir)}")
        lines.append(
            "Расписание: котировки в " + ", ".join(t.strftime("%H:%M") for t in self.cfg.quote_times)
            + f"; новости каждые {self.cfg.news_interval_min} мин; макро в {self.cfg.macro_time.strftime('%H:%M')}; итоги дня в {self.cfg.digest_time.strftime('%H:%M')}"
            + (f"; прогноз по {self._days()} в {self.cfg.forecast_time.strftime('%H:%M')}" if self.cfg.forecast_days else "") + " (МСК)"
        )
        return "\n".join(lines)
