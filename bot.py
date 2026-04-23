import logging
import os
import random
import re

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    Application,
    CommandHandler,
    ConversationHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
    ContextTypes,
)

import shaman_cipher_36

# ─── Logging ──────────────────────────────────────────────────────────
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# ─── States ───────────────────────────────────────────────────────────
CHECK_PASSWORD, MENU = range(2)

CORRECT_PASSWORD = "7788"
CIPHER_LETTERS = ["Г", "П", "М"]

# ─── Helpers ──────────────────────────────────────────────────────────

def extract_tasks(description: str) -> list[str]:
    """Извлекает пронумерованные подзадания из многострочного описания."""
    pattern = r'(?:^|\n)\s*(\d+)\.\s*(.+?)(?=\n\s*\d+\.|$)'
    matches = re.findall(pattern, description, re.DOTALL)
    tasks = [text.strip() for _, text in matches]
    return tasks


def build_ice_cream_keyboard(page: int = 0, per_page: int = 12) -> InlineKeyboardMarkup:
    """Строит Inline-клавиатуру с пагинацией для 36 вкусов."""
    flavors = shaman_cipher_36.ICE_CREAM_FLAVORS
    total_pages = (len(flavors) + per_page - 1) // per_page

    start = page * per_page
    end = min(start + per_page, len(flavors))

    buttons = []
    for fid, name, _, _, _ in flavors[start:end]:
        buttons.append([InlineKeyboardButton(name, callback_data=f"flavor:{fid}")])

    # Кнопки пагинации
    nav_buttons = []
    if page > 0:
        nav_buttons.append(InlineKeyboardButton("⬅️ Назад", callback_data=f"page:{page - 1}"))
    nav_buttons.append(InlineKeyboardButton(f"📄 {page + 1}/{total_pages}", callback_data="noop"))
    if page < total_pages - 1:
        nav_buttons.append(InlineKeyboardButton("Вперёд ➡️", callback_data=f"page:{page + 1}"))

    if nav_buttons:
        buttons.append(nav_buttons)

    buttons.append([InlineKeyboardButton("❌ Закрыть меню", callback_data="close")])

    return InlineKeyboardMarkup(buttons)


# ─── Handlers ─────────────────────────────────────────────────────────

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Приветствие и запрос пароля."""
    await update.message.reply_text(
        "👋 Привет!\n\n"
        "Это бот «Ледник Шамана». Для доступа к функциям введите пароль:"
    )
    return CHECK_PASSWORD


async def check_password(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Проверка пароля."""
    text = update.message.text.strip()
    if text == CORRECT_PASSWORD:
        reply_markup = ReplyKeyboardMarkup(
            [["🔐 Шифр", "🍦 Мороженое"]],
            resize_keyboard=True,
            one_time_keyboard=False,
        )
        await update.message.reply_text(
            "✅ Пароль верный! Добро пожаловать.\n\n"
            "Выберите действие с помощью кнопок ниже:",
            reply_markup=reply_markup,
        )
        return MENU
    else:
        await update.message.reply_text("❌ Неверный пароль. Попробуйте ещё раз:")
        return CHECK_PASSWORD


async def menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработка кнопок основного меню."""
    text = update.message.text.strip()

    if text == "🔐 Шифр":
        letter = random.choice(CIPHER_LETTERS)
        number = random.randint(1, 20)
        cipher = f"{letter}{number}"
        await update.message.reply_text(
            f"🔐 Ваш шифр: <b>{cipher}</b>\n\n"
            f"Буква: {letter}\n"
            f"Число: {number}\n\n"
            f"Используйте его по назначению 🧊",
            parse_mode="HTML",
        )

    elif text == "🍦 Мороженое":
        markup = build_ice_cream_keyboard(page=0)
        await update.message.reply_text(
            "🍦 Выберите вкус мороженого из списка ниже:\n"
            "(1 страница из 3)",
            reply_markup=markup,
        )

    else:
        await update.message.reply_text(
            "Используйте кнопки меню: 🔐 Шифр или 🍦 Мороженое"
        )


async def ice_cream_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработка Inline-кнопок мороженого."""
    query = update.callback_query
    await query.answer()
    data = query.data

    if data.startswith("page:"):
        page = int(data.split(":")[1])
        markup = build_ice_cream_keyboard(page=page)
        total_pages = (len(shaman_cipher_36.ICE_CREAM_FLAVORS) + 11) // 12
        await query.edit_message_text(
            f"🍦 Выберите вкус мороженого из списка ниже:\n"
            f"({page + 1} страница из {total_pages})",
            reply_markup=markup,
        )
        return

    if data == "close":
        await query.delete_message()
        return

    if data.startswith("flavor:"):
        fid = int(data.split(":")[1])
        flavor = shaman_cipher_36.FLAVORS_BY_ID.get(fid)
        if not flavor:
            await query.edit_message_text("Ошибка: вкус не найден.")
            return

        fid_val, name, task_type, description, min_rank = flavor
        tasks = extract_tasks(description)

        if tasks:
            chosen_task = random.choice(tasks)
        else:
            chosen_task = "Подзадания не найдены."

        # Отправляем результат новым сообщением (чтобы меню осталось или удалилось)
        await query.delete_message()
        await query.message.chat.send_message(
            f"🍦 <b>{name}</b>\n"
            f"{task_type}\n\n"
            f"🎯 <b>Ваше случайное задание:</b>\n"
            f"{chosen_task}",
            parse_mode="HTML",
        )


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Сброс состояния."""
    await update.message.reply_text(
        "Сессия завершена. Отправьте /start для нового входа.",
        reply_markup=ReplyKeyboardRemove(),
    )
    return ConversationHandler.END


# ─── Main ─────────────────────────────────────────────────────────────

def main() -> None:
    token = os.getenv("TELEGRAM_BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")
    if not token or token == "YOUR_BOT_TOKEN_HERE":
        logger.error("Не задан TELEGRAM_BOT_TOKEN! Установите переменную окружения.")
        raise SystemExit(1)

    application = Application.builder().token(token).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            CHECK_PASSWORD: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, check_password),
            ],
            MENU: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, menu_handler),
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    application.add_handler(conv_handler)
    application.add_handler(CallbackQueryHandler(ice_cream_callback))

    logger.info("Бот запущен. Нажмите Ctrl+C для остановки.")
    application.run_polling()


if __name__ == "__main__":
    main()
