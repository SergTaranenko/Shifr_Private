"""Котировки Мосбиржи (ISS, бесплатно, задержка ~15 минут), курс доллара и золото."""
from __future__ import annotations

import xml.etree.ElementTree as ET
from datetime import datetime, timedelta

import httpx

from .config import MSK

ISS = "https://iss.moex.com/iss"
UA = {"User-Agent": "portfolio-advisor-bot/1.0"}
TROY_OZ_G = 31.1034768


def shares_url(tickers: list[str]) -> str:
    return (
        f"{ISS}/engines/stock/markets/shares/boards/TQBR/securities.json"
        f"?securities={','.join(tickers)}&iss.meta=off&iss.only=marketdata,securities"
        "&marketdata.columns=SECID,LAST,LCURRENTPRICE,MARKETPRICE,UPDATETIME,SYSTIME"
        "&securities.columns=SECID,PREVPRICE,SHORTNAME"
    )


def _table(block: dict) -> list[dict]:
    cols = block.get("columns", [])
    return [dict(zip(cols, row)) for row in block.get("data", [])]


def parse_shares(payload: dict) -> dict[str, dict]:
    """{тикер: {price, prev, time}}. Если сделки сегодня не было — берём последнюю известную цену."""
    md = {r["SECID"]: r for r in _table(payload.get("marketdata", {}))}
    sec = {r["SECID"]: r for r in _table(payload.get("securities", {}))}
    out = {}
    for t in set(md) | set(sec):
        m, s = md.get(t, {}), sec.get(t, {})
        price = m.get("LAST") or m.get("LCURRENTPRICE") or m.get("MARKETPRICE") or s.get("PREVPRICE")
        if price is None:
            continue
        out[t] = {
            "price": float(price),
            "prev": float(s["PREVPRICE"]) if s.get("PREVPRICE") else None,
            "time": m.get("UPDATETIME") or "",
            "systime": m.get("SYSTIME") or "",
        }
    return out


async def fetch_shares(client: httpx.AsyncClient, tickers: list[str]) -> dict[str, dict]:
    r = await client.get(shares_url(tickers), headers=UA, timeout=20)
    r.raise_for_status()
    return parse_shares(r.json())


# --------------------------------------------------------------- макро
def parse_cbr_daily_xml(text: str) -> float:
    root = ET.fromstring(text)
    for v in root.findall("Valute"):
        if v.findtext("CharCode") == "USD":
            nominal = float(v.findtext("Nominal").replace(",", "."))
            return float(v.findtext("Value").replace(",", ".")) / nominal
    raise ValueError("USD не найден в ответе ЦБ")


async def fetch_usdrub(client: httpx.AsyncClient) -> float:
    try:
        r = await client.get("https://www.cbr-xml-daily.ru/daily_json.js", headers=UA, timeout=15)
        r.raise_for_status()
        return float(r.json()["Valute"]["USD"]["Value"])
    except Exception:  # noqa: BLE001 — запасной источник: сам ЦБ
        r = await client.get("https://www.cbr.ru/scripts/XML_daily.asp", headers=UA, timeout=15)
        r.raise_for_status()
        return parse_cbr_daily_xml(r.content.decode("windows-1251", errors="replace"))


def parse_moex_gold(payload: dict) -> float:
    md = _table(payload.get("marketdata", {}))
    for row in md:
        p = row.get("LAST") or row.get("MARKETPRICETODAY") or row.get("WAPRICE")
        if p:
            return float(p)
    sec = _table(payload.get("securities", {}))
    for row in sec:
        if row.get("PREVPRICE"):
            return float(row["PREVPRICE"])
    raise ValueError("нет цены GLDRUB_TOM")


def parse_cbr_metals_xml(text: str) -> float:
    root = ET.fromstring(text)
    recs = [r for r in root.findall("Record") if r.get("Code") == "1"]
    if not recs:
        raise ValueError("нет цены золота в ответе ЦБ")
    return float(recs[-1].findtext("Buy").replace(",", "."))


async def fetch_gold_rub_per_gram(client: httpx.AsyncClient) -> float:
    try:
        url = f"{ISS}/engines/currency/markets/selt/boards/CETS/securities/GLDRUB_TOM.json?iss.meta=off&iss.only=marketdata,securities"
        r = await client.get(url, headers=UA, timeout=15)
        r.raise_for_status()
        return parse_moex_gold(r.json())
    except Exception:  # noqa: BLE001 — запасной источник: учётная цена ЦБ
        today = datetime.now(MSK)
        d1, d2 = (today - timedelta(days=10)).strftime("%d/%m/%Y"), today.strftime("%d/%m/%Y")
        r = await client.get(f"https://www.cbr.ru/scripts/xml_metall.asp?date_req1={d1}&date_req2={d2}", headers=UA, timeout=15)
        r.raise_for_status()
        return parse_cbr_metals_xml(r.content.decode("windows-1251", errors="replace"))


def gold_usd_per_oz(rub_per_gram: float, usdrub: float) -> float:
    return rub_per_gram * TROY_OZ_G / usdrub
