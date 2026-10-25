"""Telegram: команды, расписание, приём Excel-книги с моделью."""
from __future__ import annotations

import logging
from functools import wraps

from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

from .config import Config
from .levels import ModelFileError
from .service import Advisor, split_message

log = logging.getLogger(__name__)

HELP = """Я слежу за котировками и новостями по вашим бумагам, сигналю о важном и присылаю прогноз из модели. Модель я не меняю — её вы обновляете вместе с Claude и кладёте в GitHub.

<b>Команды</b>
/forecast — прогноз по всем бумагам: справедливые цены, из чего они складываются, допущения, тезисы
/forecast SBER — прогноз по одной бумаге
/model — прислать Excel-книгу действующей модели
/status — цены против справедливых, зоны, портфель
/levels — уровни покупки и продажи из модели
/news — важные новости за сутки
/digest — итоги дня сейчас
/check — проверить котировки сейчас
/checknews — проверить новости сейчас
/macro — курс и золото против допущений модели
/health — что работает, а что нет

<b>Когда я пишу сам</b>
• бумага сменила зону: покупка / держать / близко к продаже / продажа
• цена за день изменилась больше чем на 5%
• новость может изменить модель или похожа на слом тезиса
• курс или золото ушли от допущений модели больше чем на 10%
• итоги дня — вечером
• прогноз целиком — раз в неделю и каждый раз, когда модель обновилась

<b>Обновить модель</b> — положите новую книгу в репозиторий как model/model.xlsx: хостинг перезапустит меня, и я пришлю новый прогноз.
Можно и прислать книгу сюда — она будет действовать, пока в GitHub не появится новая версия."""


def owner_only(fn):
    @wraps(fn)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        app_owner = owner_id(context)
        chat = update.effective_chat
        if app_owner is None or chat is None or chat.id != app_owner:
            if update.effective_message:
                await update.effective_message.reply_text("Это личный бот.")
            return
        return await fn(update, context)

    return wrapper


def owner_id(context) -> int | None:
    cfg: Config = context.application.bot_data["cfg"]
    if cfg.owner_chat_id:
        return cfg.owner_chat_id
    adv: Advisor = context.application.bot_data["advisor"]
    return adv.storage.get("owner_chat_id")


async def send(context, text: str) -> None:
    chat_id = owner_id(context)
    if not chat_id:
        log.warning("владелец не задан — сообщение не отправлено")
        return
    for part in split_message(text):
        await context.bot.send_message(chat_id, part, parse_mode=ParseMode.HTML, disable_web_page_preview=True)


async def reply(update: Update, text: str) -> None:
    for part in split_message(text):
        await update.effective_message.reply_text(part, parse_mode=ParseMode.HTML, disable_web_page_preview=True)


def problems_note(adv: Advisor) -> str:
    if not adv.problems:
        return ""
    from .service import esc

    return "\n\n⚠️ <b>Что не так с файлами на сервере</b>\n" + "\n".join(f"• {esc(p)}" for p in adv.problems)


async def send_model_file(bot, chat_id: int, adv: Advisor, caption: str = "Книга действующей модели") -> bool:
    path = adv.model_file()
    if not path:
        return False
    with open(path, "rb") as fh:
        await bot.send_document(chat_id, fh, filename=adv.levels.get("source") or "model.xlsx", caption=caption)
    return True


async def announce_if_pending(bot, adv: Advisor, chat_id: int | None) -> None:
    """Прислать прогноз, если действующая модель владельцу ещё не отправлялась (после обновления в GitHub)."""
    if not chat_id:
        return
    pending = adv.pending_announcement()
    if not pending:
        return
    text, _ = pending
    try:
        await adv.fetch_prices()
        text, _ = adv.pending_announcement() or (text, None)
    except Exception:  # noqa: BLE001
        pass
    for part in split_message(text):
        await bot.send_message(chat_id, part, parse_mode=ParseMode.HTML, disable_web_page_preview=True)
    await send_model_file(bot, chat_id, adv, "Книга модели, по которой я теперь считаю зоны")
    adv.mark_announced()


# ------------------------------------------------------------------ команды
async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cfg: Config = context.application.bot_data["cfg"]
    adv: Advisor = context.application.bot_data["advisor"]
    chat_id = update.effective_chat.id
    if not cfg.owner_chat_id and not adv.storage.get("owner_chat_id"):
        adv.storage.set("owner_chat_id", chat_id)
        await reply(
            update,
            f"Готово, я запомнил вас как владельца. Ваш chat id: <code>{chat_id}</code>.\n"
            "Надёжнее прописать его в настройках хостинга как OWNER_CHAT_ID — тогда он не потеряется при перезапуске.\n\n" + HELP + problems_note(adv),
        )
        await announce_if_pending(context.bot, adv, chat_id)
        return
    if owner_id(context) != chat_id:
        await reply(update, "Это личный бот.")
        return
    await reply(update, HELP + problems_note(adv))
    await announce_if_pending(context.bot, adv, chat_id)


@owner_only
async def cmd_help(update, context):
    await reply(update, HELP)


@owner_only
async def cmd_forecast(update, context):
    adv: Advisor = context.application.bot_data["advisor"]
    ticker = context.args[0] if context.args else None
    await reply(update, await adv.forecast_text(ticker))


@owner_only
async def cmd_model(update, context):
    adv: Advisor = context.application.bot_data["advisor"]
    if not await send_model_file(context.bot, update.effective_chat.id, adv):
        await reply(update, "Книги модели у меня нет — работаю по data/levels.json. Положите книгу в репозиторий как model/model.xlsx.")


@owner_only
async def cmd_status(update, context):
    await reply(update, await context.application.bot_data["advisor"].status_text())


@owner_only
async def cmd_levels(update, context):
    await reply(update, context.application.bot_data["advisor"].levels_text())


@owner_only
async def cmd_news(update, context):
    await reply(update, context.application.bot_data["advisor"].news_text(24, 1))


@owner_only
async def cmd_digest(update, context):
    await reply(update, await context.application.bot_data["advisor"].digest_text())


@owner_only
async def cmd_check(update, context):
    adv: Advisor = context.application.bot_data["advisor"]
    try:
        alerts = await adv.check_quotes()
    except Exception as e:  # noqa: BLE001
        await reply(update, f"Биржа не ответила: {e.__class__.__name__}. Попробую в следующий раз по расписанию.")
        return
    await reply(update, "\n\n".join(alerts) if alerts else "Смен зон нет.")
    await reply(update, await adv.status_text())


@owner_only
async def cmd_checknews(update, context):
    adv: Advisor = context.application.bot_data["advisor"]
    await reply(update, "Проверяю ленты, это может занять минуту…")
    alerts = await adv.check_news()
    await reply(update, "\n\n".join(alerts) if alerts else "Новых важных новостей нет. Всё, что полезно знать, — в /news.")


@owner_only
async def cmd_macro(update, context):
    adv: Advisor = context.application.bot_data["advisor"]
    vals = await adv.macro_values()
    a = adv.levels.get("assumptions", {})
    from .service import rub

    lines = ["💱 <b>Макро против допущений модели</b>"]
    if vals.get("usdrub"):
        lines.append(f"Курс: {rub(vals['usdrub'], 2)} ₽ (в модели {rub(a.get('usdrub'))} ₽, {vals['usdrub'] / a['usdrub'] - 1:+.0%})" if a.get("usdrub") else f"Курс: {rub(vals['usdrub'], 2)} ₽")
    if vals.get("gold_usd"):
        lines.append(f"Золото: ${rub(vals['gold_usd'])} (в модели ${rub(a.get('gold_usd'))}, {vals['gold_usd'] / a['gold_usd'] - 1:+.0%})" if a.get("gold_usd") else f"Золото: ${rub(vals['gold_usd'])}")
    if len(lines) == 1:
        lines.append("Источники курса и золота не ответили, попробуйте позже.")
    await reply(update, "\n".join(lines))


@owner_only
async def cmd_health(update, context):
    await reply(update, "Проверяю источники, это займёт до минуты…")
    await reply(update, await context.application.bot_data["advisor"].health_text())


@owner_only
async def on_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    adv: Advisor = context.application.bot_data["advisor"]
    doc = update.effective_message.document
    name = doc.file_name or "model.xlsx"
    if not name.lower().endswith((".xlsx", ".xlsm")):
        await reply(update, "Пришлите Excel-книгу модели (.xlsx).")
        return
    f = await doc.get_file()
    data = bytes(await f.download_as_bytearray())
    try:
        msg = adv.update_levels_from_file(data, name)
    except ModelFileError as e:
        await reply(update, f"Не получилось прочитать модель: {e}.")
        return
    await reply(update, msg)
    try:
        await adv.check_quotes(silent=True)
        await reply(update, await adv.status_text())
    except Exception as e:  # noqa: BLE001
        await reply(update, f"Модель сохранена, но биржа сейчас не ответила ({e.__class__.__name__}). Зоны пересчитаю по расписанию.")


# ------------------------------------------------------------------ задания по расписанию
async def job_quotes(context: ContextTypes.DEFAULT_TYPE):
    adv: Advisor = context.application.bot_data["advisor"]
    try:
        alerts = await adv.check_quotes()
    except Exception:
        log.exception("quotes job failed")
        return
    if alerts:
        await send(context, "\n\n".join(alerts))


async def job_news(context: ContextTypes.DEFAULT_TYPE):
    adv: Advisor = context.application.bot_data["advisor"]
    try:
        alerts = await adv.check_news()
    except Exception:
        log.exception("news job failed")
        return
    for a in alerts:
        await send(context, a)


async def job_macro(context: ContextTypes.DEFAULT_TYPE):
    adv: Advisor = context.application.bot_data["advisor"]
    try:
        alerts = await adv.check_macro()
    except Exception:
        log.exception("macro job failed")
        return
    if alerts:
        await send(context, "\n\n".join(alerts))


async def job_forecast(context: ContextTypes.DEFAULT_TYPE):
    adv: Advisor = context.application.bot_data["advisor"]
    chat_id = owner_id(context)
    if not chat_id:
        return
    try:
        await send(context, await adv.forecast_text())
        await send_model_file(context.bot, chat_id, adv, "Книга модели — еженедельная копия")
    except Exception:
        log.exception("forecast job failed")


async def job_digest(context: ContextTypes.DEFAULT_TYPE):
    adv: Advisor = context.application.bot_data["advisor"]
    try:
        await send(context, await adv.digest_text())
    except Exception:
        log.exception("digest job failed")


async def on_startup(app: Application):
    adv: Advisor = app.bot_data["advisor"]
    cfg: Config = app.bot_data["cfg"]
    # первая проверка котировок — молча, чтобы запомнить текущие зоны
    try:
        await adv.check_quotes(silent=True)
    except Exception:
        log.exception("startup quotes failed")
    # если модель в GitHub обновилась — прислать новый прогноз
    try:
        await announce_if_pending(app.bot, adv, cfg.owner_chat_id or adv.storage.get("owner_chat_id"))
    except Exception:
        log.exception("startup announcement failed")


def build_app(cfg: Config, advisor: Advisor | None = None) -> Application:
    if not cfg.telegram_token:
        raise SystemExit("Не задан TELEGRAM_TOKEN — токен бота от @BotFather.")
    app = Application.builder().token(cfg.telegram_token).post_init(on_startup).build()
    app.bot_data["cfg"] = cfg
    app.bot_data["advisor"] = advisor or Advisor(cfg)

    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("help", cmd_help))
    app.add_handler(CommandHandler("forecast", cmd_forecast))
    app.add_handler(CommandHandler("model", cmd_model))
    app.add_handler(CommandHandler("status", cmd_status))
    app.add_handler(CommandHandler("levels", cmd_levels))
    app.add_handler(CommandHandler("news", cmd_news))
    app.add_handler(CommandHandler("digest", cmd_digest))
    app.add_handler(CommandHandler("check", cmd_check))
    app.add_handler(CommandHandler("checknews", cmd_checknews))
    app.add_handler(CommandHandler("macro", cmd_macro))
    app.add_handler(CommandHandler("health", cmd_health))
    app.add_handler(MessageHandler(filters.Document.ALL, on_document))

    jq = app.job_queue
    for t in cfg.quote_times:
        jq.run_daily(job_quotes, time=t, name=f"quotes-{t.strftime('%H%M')}")
    jq.run_repeating(job_news, interval=cfg.news_interval_min * 60, first=90, name="news")
    jq.run_daily(job_macro, time=cfg.macro_time, name="macro")
    jq.run_daily(job_digest, time=cfg.digest_time, name="digest")
    if cfg.forecast_days:
        jq.run_daily(job_forecast, time=cfg.forecast_time, days=cfg.forecast_days, name="forecast")
    return app
