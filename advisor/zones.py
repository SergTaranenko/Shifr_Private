"""Зоны цены относительно модели и правила смены зоны."""
from __future__ import annotations

BUY, HOLD, NEAR, SELL = "buy", "hold", "near", "sell"
ORDER = {BUY: 0, HOLD: 1, NEAR: 2, SELL: 3}
LABEL = {
    BUY: "зона покупки",
    HOLD: "держать",
    NEAR: "приближается к цене продажи",
    SELL: "цена продажи",
}
ICON = {BUY: "🟢", HOLD: "⚪", NEAR: "🟡", SELL: "🔴"}


def classify(price: float, lv: dict) -> str:
    if price <= lv["buy"]:
        return BUY
    if price >= lv["sell"]:
        return SELL
    if price >= lv["near"]:
        return NEAR
    return HOLD


def classify_with_hysteresis(price: float, lv: dict, prev: str | None, hyst_pct: float) -> str:
    """Смена зоны засчитывается, только если цена ушла за границу дальше чем на hyst_pct %.

    Так бот не дёргается, когда цена топчется прямо на границе.
    """
    raw = classify(price, lv)
    if prev is None or raw == prev:
        return raw
    h = hyst_pct / 100
    # граница, которую пересекли: между prev и raw
    if ORDER[raw] > ORDER[prev]:  # цена выросла
        bound = {HOLD: lv["buy"], NEAR: lv["near"], SELL: lv["sell"]}[_next_up(prev)]
        return raw if price >= bound * (1 + h) else prev
    bound = {BUY: lv["buy"], HOLD: lv["near"], NEAR: lv["sell"]}[_next_down(prev)]
    return raw if price <= bound * (1 - h) else prev


def _next_up(z: str) -> str:
    return {BUY: HOLD, HOLD: NEAR, NEAR: SELL}[z]


def _next_down(z: str) -> str:
    return {SELL: NEAR, NEAR: HOLD, HOLD: BUY}[z]


def transition_text(ticker: str, name: str, prev: str, new: str, price: float, lv: dict) -> str:
    up = ORDER[new] > ORDER[prev]
    arrow = "↗" if up else "↘"
    head = f"{ICON[new]} <b>{ticker}</b> {name}: {LABEL[prev]} {arrow} <b>{LABEL[new]}</b>"
    body = (
        f"Цена {price:,.2f} ₽ · справедливая {lv['fair']:,.0f} ₽ · покупка до {lv['buy']:,.0f} · "
        f"продажа от {lv['sell']:,.0f}"
    ).replace(",", " ")
    hint = {
        BUY: "Бумага заметно дешевле справедливой. Решение о покупке — за вами.",
        HOLD: "Цена вернулась в обычный диапазон.",
        NEAR: "До цены продажи меньше 5%. Хороший момент перепроверить тезис с Claude.",
        SELL: "Цена дошла до уровня продажи из модели. Проверьте тезис и решите, продавать ли.",
    }[new]
    return f"{head}\n{body}\n{hint}"
