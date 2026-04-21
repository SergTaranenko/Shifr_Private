# -*- coding: utf-8 -*-
"""
Бот «12 рангов» v3 — Избыточные дела.
Сверх нормы: супернаграда, погашение долга, перенос вперёд.
"""

import os
import json
import random
import logging
import ssl
import uuid
import importlib
from datetime import datetime, timedelta, date
from pathlib import Path
from io import BytesIO

import pytz
import aiohttp
from telegram import Update
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    filters, ContextTypes
)

from core_config import (
    RANK_SCHEDULE, LANDSCAPE,
    HUNGER_WARNING, HUNGER_RIOT, DOPAMINE_START, DOPAMINE_END,
    WAKEUP_HOUR, WAKEUP_MINUTE, REPORT_HOUR, REPORT_MINUTE,
    PENALTY_TEXTS, DISASTER_TEXTS, TRIED_TEXTS,
)

from ice_cream_rewards import get_reward, get_all_available, get_total_count
from ice_cream_cipher import get_cipher

# ========== ОКРУЖЕНИЕ ==========
BOT_TOKEN = os.environ.get("BOT_TOKEN")
GIGACHAT_AUTH = os.environ.get("GIGACHAT_AUTH")
DATA_DIR = Path("/app/data")
TIMEZONE = pytz.timezone("Europe/Moscow")

GIGACHAT_OAUTH_URL = "https://ngw.devices.sberbank.ru:9443/api/v2/oauth"
GIGACHAT_API_URL = "https://gigachat.devices.sberbank.ru/api/v1"

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ========== GIGACHAT ==========
class GigaChatAPI:
    def __init__(self):
        self.token_cache = {"token": None, "expires": None}

    async def get_token(self):
        if self.token_cache["token"] and self.token_cache["expires"]:
            if datetime.now().timestamp() < self.token_cache["expires"] - 60:
                return self.token_cache["token"]
        if not GIGACHAT_AUTH:
            return None
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    GIGACHAT_OAUTH_URL,
                    headers={
                        "Content-Type": "application/x-www-form-urlencoded",
                        "Accept": "application/json",
                        "RqUID": str(uuid.uuid4()),
                        "Authorization": f"Basic {GIGACHAT_AUTH}"
                    },
                    data="scope=GIGACHAT_API_PERS",
                    ssl=ssl_context
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        self.token_cache["token"] = data["access_token"]
                        self.token_cache["expires"] = data["expires_at"] / 1000
                        return data["access_token"]
        except Exception as e:
            logger.error(f"GigaChat auth error: {e}")
        return None

    async def generate_image(self, prompt: str):
        token = await self.get_token()
        if not token:
            return None
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        try:
            timeout = aiohttp.ClientTimeout(total=90)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.post(
                    f"{GIGACHAT_API_URL}/chat/completions",
                    headers={
                        "Content-Type": "application/json",
                        "Accept": "application/json",
                        "Authorization": f"Bearer {token}"
                    },
                    json={
                        "model": "GigaChat-Max",
                        "messages": [{"role": "user", "content": prompt}],
                        "function_call": "auto"
                    },
                    ssl=ssl_context
                ) as resp:
                    if resp.status != 200:
                        return None
                    data = await resp.json()
                    content = data["choices"][0]["message"]["content"]
                    if "<img src=\"" in content:
                        start = content.find("<img src=\"") + 10
                        end = content.find("\"", start)
                        file_id = content[start:end]
                        async with session.get(
                            f"{GIGACHAT_API_URL}/files/{file_id}/content",
                            headers={"Authorization": f"Bearer {token}"},
                            ssl=ssl_context
                        ) as img_resp:
                            if img_resp.status == 200:
                                return await img_resp.read()
        except Exception as e:
            logger.error(f"Image generation error: {e}")
        return None

gigachat = GigaChatAPI()

# ========== DATA ==========
def load_data():
    file_path = DATA_DIR / "stoyanka_data.json"
    default = {
        "user_id": None,
        "current_date": None,
        "morning_done": False,
        "waiting_for_plans": False,
        "plans_confirmed": None,
        "last_feed_time": None,
        "hunger_notified": False,
        "last_dopamine_hour": None,
        "goodnight_sent": False,
        "keeper_streak": 0,
        "waiting_for_keeper": False,
        "total_keeper_success": 0,
        "superhero_morning_flag": False,
        "deeds_by_rank": [0] * 12,
        "total_deeds": 0,
        "announced_ranks": [],
        "tasted_flavors": [],
        "collected_artifacts": [],
        "rewards_used": 0,
        # Новые поля для избыточных дел
        "debt_paid": [0] * 12,       # виртуальные дела, купленные за избыток
        "carry_over": [0] * 12,      # перенос В ранг (уменьшает требование)
        "excess_spent_total": 0,     # сколько всего потрачено избытка
    }
    try:
        if file_path.exists():
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                for key in default:
                    if key not in data:
                        data[key] = default[key]
                return data
        return default
    except Exception as e:
        logger.error(f"Load error: {e}")
        return default

def save_data(data):
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    file_path = DATA_DIR / "stoyanka_data.json"
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def load_commandments():
    file_path = Path(__file__).parent / "commandments.json"
    try:
        if file_path.exists():
            with open(file_path, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception as e:
        logger.error(f"Commandments load error: {e}")
    return []

def now_msk():
    return datetime.now(TIMEZONE)

def today_str():
    return now_msk().strftime("%Y-%m-%d")

def get_hunger_hours(data):
    last = data.get("last_feed_time")
    if not last:
        return 0
    last_dt = datetime.fromisoformat(last)
    return (now_msk() - last_dt).total_seconds() / 3600

def get_hunger_mode(data):
    hours = get_hunger_hours(data)
    if hours < HUNGER_WARNING:
        return "good"
    elif hours < HUNGER_RIOT:
        return "bad"
    return "riot"

# ========== ИЗБЫТОК И ДОЛГИ ==========
def get_rank_adjusted(rank_num, data):
    """Требование ранга с учётом переноса."""
    req = RANK_SCHEDULE[rank_num]["deeds_required"]
    carry_in = data.get("carry_over", [0]*12)[rank_num-1]
    return max(0, req - carry_in)

def get_rank_effective_done(rank_num, data):
    """Фактически зачтённые дела ранга (физические + погашенные)."""
    return data["deeds_by_rank"][rank_num-1] + data.get("debt_paid", [0]*12)[rank_num-1]

def get_rank_debt(data, rank_num):
    """Сколько не хватает до закрытия ранга."""
    adj = get_rank_adjusted(rank_num, data)
    done = get_rank_effective_done(rank_num, data)
    return max(0, adj - done)

def get_rank_excess(data, rank_num):
    """Сколько избыточных дел в конкретном ранге."""
    adj = get_rank_adjusted(rank_num, data)
    done = get_rank_effective_done(rank_num, data)
    return max(0, done - adj)

def get_excess_pool(data):
    """Общий банк нераспределённого избытка."""
    total_earned = 0
    for r in range(1, 13):
        total_earned += get_rank_excess(data, r)
    spent = data.get("excess_spent_total", 0)
    return max(0, total_earned - spent)

# ========== РАНГИ ==========
def get_current_rank(for_date=None):
    check = for_date or date.today()
    if check < RANK_SCHEDULE[1]["start"]:
        return 0
    for rank_num in range(1, 13):
        sched = RANK_SCHEDULE[rank_num]
        if sched["start"] <= check <= sched["end"]:
            return rank_num
    return 13

def get_rank_announcement(for_date=None):
    check = for_date or date.today()
    for rank_num in range(1, 13):
        sched = RANK_SCHEDULE[rank_num]
        ann = sched.get("announcement")
        if ann and check == ann:
            return True, rank_num
    return False, None

def get_epoch(rank_num):
    return RANK_SCHEDULE[rank_num]["epoch"]

def get_rank_name(rank_num):
    return RANK_SCHEDULE[rank_num]["name"]

def get_adjusted_requirements(data):
    """Полный отчёт по всем рангам."""
    result = {}
    for r in range(1, 13):
        req = RANK_SCHEDULE[r]["deeds_required"]
        carry_in = data.get("carry_over", [0]*12)[r-1]
        debt_paid = data.get("debt_paid", [0]*12)[r-1]
        adjusted = max(0, req - carry_in)
        raw_done = data["deeds_by_rank"][r-1]
        eff_done = raw_done + debt_paid
        result[r] = {
            "required": req,
            "adjusted": adjusted,
            "raw_done": raw_done,
            "eff_done": eff_done,
            "carry_in": carry_in,
            "debt_paid": debt_paid,
            "debt": max(0, adjusted - eff_done),
            "excess": max(0, eff_done - adjusted),
        }
    return result

def add_deed(data, rank_num):
    if rank_num < 1 or rank_num > 12:
        return False, "Вне расписания.", 0

    data["deeds_by_rank"][rank_num - 1] += 1
    data["total_deeds"] += 1

    adj = get_rank_adjusted(rank_num, data)
    eff = get_rank_effective_done(rank_num, data)

    epoch = get_epoch(rank_num)
    bonus = 12 if epoch == "ppn" else 10
    if rank_num <= 2:
        bonus = 6
    elif rank_num >= 11:
        bonus = 16

    if eff > adj:
        pool = get_excess_pool(data)
        msg = (
            f"⚡ Ранг «{get_rank_name(rank_num)}» выполнен на {eff}/{adj}!\n"
            f"💰 Банк избыточных дел: {pool}\n\n"
            f"Что делать с избытком?\n"
            f"/reward — супернаграда для себя (1 дело)\n"
            f"/paydebt [ранг] [кол-во] — погасить долг прошлого ранга\n"
            f"/carry [ранг] [кол-во] — перенести в следующий ранг\n"
            f"/balance — проверить все долги и переносы"
        )
        return True, msg, bonus
    else:
        remaining = adj - eff
        msg = f"⚒️ Артефакт получен. Осталось: {remaining} до завершения ранга."
        return True, msg, bonus

# ========== МОДУЛИ РАНГОВ ==========
def get_rank_module(rank_num: int):
    try:
        return importlib.import_module(f"ranks.rank_{rank_num:02d}")
    except ImportError:
        return None

def get_rank_artifact(rank_num: int, ritual: bool = False):
    mod = get_rank_module(rank_num)
    if mod:
        if ritual and hasattr(mod, "RITUALS") and mod.RITUALS:
            return random.choice(mod.RITUALS)
        if hasattr(mod, "ARTIFACTS") and mod.ARTIFACTS:
            return random.choice(mod.ARTIFACTS)
    epoch = get_epoch(rank_num)
    return {
        "name": "Каменный обломок",
        "material": "известняк",
        "desc": "Обычный камень с местных склонов",
        "prompt": f"Limestone flake from {epoch} archaeological site, photorealistic, 8k"
    }

def get_artifact_image_prompt(artifact: dict, rank_num: int):
    epoch = get_epoch(rank_num)
    ls = LANDSCAPE[epoch]
    if epoch == "natufian":
        return (
            f"Extreme close-up of {artifact['name']} made of {artifact['material']} "
            f"from Natufian Levant, 11000 BC, lying on reindeer hide, "
            f"firelight, {ls['ground']}, photorealistic, 8k, archaeological artifact photography"
        )
    else:
        return (
            f"Extreme close-up of {artifact['name']} made of {artifact['material']} "
            f"from PPN Anatolia, 7500 BC, lying on stone altar, "
            f"dust, {ls['ground']}, photorealistic, 8k, archaeological artifact photography"
        )

def get_rank_tried_text(rank_num: int):
    epoch = get_epoch(rank_num) if 1 <= rank_num <= 12 else "natufian"
    mod = get_rank_module(rank_num)
    if mod and hasattr(mod, "get_tried_text"):
        return mod.get_tried_text()
    return random.choice(TRIED_TEXTS[epoch])

def get_rank_penalty_text(rank_num: int):
    epoch = get_epoch(rank_num) if 1 <= rank_num <= 12 else "natufian"
    mod = get_rank_module(rank_num)
    if mod and hasattr(mod, "get_penalty_text"):
        return mod.get_penalty_text()
    return random.choice(PENALTY_TEXTS[epoch])

# ========== ПРОМПТЫ ==========
def get_sunrise_prompt(rank_num: int):
    epoch = get_epoch(rank_num)
    ls = LANDSCAPE[epoch]
    if epoch == "natufian":
        return (
            f"Early Natufian morning in the Levant, 12000 BC, {ls['ground']}, "
            f"{ls['trees']}, wild wheat fields, semi-subterranean round stone huts, "
            f"first sunlight, Mediterranean light, photorealistic, 8k"
        )
    else:
        return (
            f"Early PPN morning in Anatolia, 8000 BC, {ls['ground']}, "
            f"workers building stone rectangular houses, {ls['trees']}, "
            f"first agricultural fields, photorealistic, 8k"
        )

def get_night_prompt(rank_num: int):
    epoch = get_epoch(rank_num)
    ls = LANDSCAPE[epoch]
    if epoch == "natufian":
        return (
            f"Night in Natufian camp, Levant, 11500 BC, clear starry sky, "
            f"embers in fire pit inside stone hut, {ls['animals']} sounds, "
            f"photorealistic, 8k, Mediterranean night"
        )
    else:
        return (
            f"Night in PPN settlement, Anatolia, 7500 BC, stone plastered houses, "
            f"fire pits, distant ritual T-pillars, {ls['animals']} silhouettes, "
            f"photorealistic, 8k"
        )

# ========== ХЕНДЛЕРЫ ==========
async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    data = load_data()
    data["user_id"] = user_id
    data["current_date"] = today_str()
    if not data["last_feed_time"]:
        data["last_feed_time"] = now_msk().isoformat()
    save_data(data)

    rank = get_current_rank()
    if rank == 0:
        await update.message.reply_text("⏳ Бот стартует 21 апреля 2026.")
        return
    if rank == 13:
        await update.message.reply_text("🏁 Траектория завершена.")
        return

    sched = RANK_SCHEDULE[rank]
    reqs = get_adjusted_requirements(data)
    info = reqs[rank]
    collected = len(data.get("collected_artifacts", []))
    pool = get_excess_pool(data)

    schedule_lines = []
    for r in range(1, 13):
        s = RANK_SCHEDULE[r]
        line = f"{r}. {s['name']} — {s['start'].strftime('%d.%m')}-{s['end'].strftime('%d.%m')}, {s['deeds_required']} артеф."
        if r == rank:
            line = f"👉 {line} (сейчас)"
        schedule_lines.append(line)

    msg = (
        f"⚒️ 12 РАНГОВ: от Падальщика до Созидателя\n\n"
        f"Текущий: {rank} — «{sched['name']}»\n"
        f"Эпоха: {'Натуф' if sched['epoch'] == 'natufian' else 'Анатолия'}\n"
        f"Артефактов: {info['eff_done']}/{info['adjusted']} (база {info['required']})\n"
        f"В коллекции: {collected} шт.\n"
        f"💰 Банк избыточных дел: {pool}\n"
        f"Всего дел: {data['total_deeds']}/174\n\n"
        f"📅 Расписание:\n" + "\n".join(schedule_lines) + "\n\n"
        f"Команды:\n/done — Получить артефакт\n/tried — Пытался, +4ч\n"
        f"/penalty — Неудача, -1ч\n/penalty20 — Катастрофа, -20ч\n"
        f"/balance — Долги и избыток\n/reward — Супернаграда (1 избыток)\n"
        f"/paydebt [ранг] [кол-во] — Погасить долг\n/carry [ранг] [кол-во] — Перенести вперёд\n"
        f"/collection — Музей артефактов\n/menu — Ледник Шамана\n"
        f"/taste [вкус] — Толкование шамана\n/status — Проверить прогресс"
    )
    await update.message.reply_text(msg)

async def cmd_done(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = load_data()
    rank = get_current_rank()
    if rank < 1 or rank > 12:
        await update.message.reply_text("Вне периода активности.")
        return
    if data.get("waiting_for_plans"):
        await update.message.reply_text("Сначала ответь на утренний вопрос (есть/нет).")
        return

    success, msg, bonus = add_deed(data, rank)
    if not success:
        await update.message.reply_text(msg)
        return

    # Ритуальный каждый 5-й в ранге
    deeds_in_rank = data["deeds_by_rank"][rank - 1]
    is_ritual = (deeds_in_rank % 5 == 0) and (deeds_in_rank > 0)
    if is_ritual:
        bonus = 18

    current_hunger = get_hunger_hours(data)
    new_hunger = current_hunger - bonus
    new_feed_time = now_msk() - timedelta(hours=new_hunger)
    data["last_feed_time"] = new_feed_time.isoformat()
    data["hunger_notified"] = False

    artifact = get_rank_artifact(rank, ritual=is_ritual)
    data["collected_artifacts"].append({
        "rank": rank,
        "name": artifact["name"],
        "material": artifact["material"],
        "ritual": is_ritual,
        "date": today_str()
    })

    ritual_tag = "⚡ РИТУАЛЬНЫЙ АРТЕФАКТ!\n" if is_ritual else ""
    text = (
        f"{ritual_tag}⚒️ Получен: **{artifact['name']}**\n"
        f"📦 Материал: {artifact['material']}\n"
        f"📝 {artifact['desc']}\n"
        f"⏳ +{bonus}ч сытости\n"
        f"{msg}"
    )
    await update.message.reply_text(text, parse_mode="Markdown")

    img_prompt = get_artifact_image_prompt(artifact, rank)
    img_data = await gigachat.generate_image(img_prompt)
    if img_data:
        await context.bot.send_photo(chat_id=update.effective_user.id, photo=BytesIO(img_data))

    save_data(data)

async def cmd_balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = load_data()
    reqs = get_adjusted_requirements(data)
    pool = get_excess_pool(data)

    lines = [f"📊 БАЛАНС ДЕЛ\n\n💰 Избыточный банк: {pool} дел\n"]

    # Долги
    debt_lines = []
    for r in range(1, 13):
        info = reqs[r]
        if info["debt"] > 0:
            debt_lines.append(f"  📉 Ранг {r}: «{get_rank_name(r)}» — не хватает {info['debt']} (сделано {info['raw_done']}/{info['adjusted']})")
    if debt_lines:
        lines.append("\n📉 Долги:")
        lines.extend(debt_lines)
    else:
        lines.append("\n✅ Долгов нет.")

    # Переносы
    carry_lines = []
    for r in range(1, 13):
        c = data.get("carry_over", [0]*12)[r-1]
        if c > 0:
            carry_lines.append(f"  📦 Ранг {r}: «{get_rank_name(r)}» — перенос +{c} (требование {RANK_SCHEDULE[r]['deeds_required']} → {max(0, RANK_SCHEDULE[r]['deeds_required'] - c)})")
    if carry_lines:
        lines.append("\n📦 Переносы в ранги:")
        lines.extend(carry_lines)
    else:
        lines.append("\n📦 Переносов нет.")

    # Погашения
    paid_lines = []
    for r in range(1, 13):
        p = data.get("debt_paid", [0]*12)[r-1]
        if p > 0:
            paid_lines.append(f"  ✅ Ранг {r}: погашено виртуально {p} дел")
    if paid_lines:
        lines.append("\n✅ Погашено из избытка:")
        lines.extend(paid_lines)

    lines.append(f"\n🎁 Супернаград активировано: {data.get('rewards_used', 0)}")

    await update.message.reply_text("\n".join(lines))

async def cmd_reward(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = load_data()
    pool = get_excess_pool(data)
    if pool < 1:
        await update.message.reply_text(f"❌ Недостаточно избыточных дел. Банк: {pool}")
        return

    data["excess_spent_total"] = data.get("excess_spent_total", 0) + 1
    data["rewards_used"] = data.get("rewards_used", 0) + 1
    save_data(data)

    new_pool = get_excess_pool(data)
    await update.message.reply_text(
        f"🎁 Супернаграда активирована.\n"
        f"Ты знаешь, что это.\n"
        f"Всего наград: {data['rewards_used']}\n"
        f"💰 Банк: {new_pool}"
    )

async def cmd_paydebt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = load_data()
    if not context.args or len(context.args) < 1:
        await update.message.reply_text("Укажи ранг: /paydebt [ранг] [кол-во=1]")
        return

    try:
        target_rank = int(context.args[0])
        amount = int(context.args[1]) if len(context.args) > 1 else 1
    except ValueError:
        await update.message.reply_text("Числами, пожалуйста: /paydebt 1 2")
        return

    if target_rank < 1 or target_rank > 12:
        await update.message.reply_text("Ранг 1–12.")
        return

    pool = get_excess_pool(data)
    if amount > pool:
        await update.message.reply_text(f"❌ Недостаточно избытка. Банк: {pool}")
        return

    debt = get_rank_debt(data, target_rank)
    if amount > debt:
        await update.message.reply_text(f"❌ Долг ранга {target_rank} только {debt}. Нельзя погасить больше.")
        return

    data["debt_paid"][target_rank - 1] += amount
    data["excess_spent_total"] += amount
    save_data(data)

    new_pool = get_excess_pool(data)
    await update.message.reply_text(
        f"✅ Долг ранга {target_rank} «{get_rank_name(target_rank)}» погашен на {amount}!\n"
        f"Теперь: {get_rank_effective_done(target_rank, data)}/{get_rank_adjusted(target_rank, data)}\n"
        f"💰 Банк: {new_pool}"
    )

async def cmd_carry(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = load_data()
    if not context.args or len(context.args) < 1:
        await update.message.reply_text("Укажи ранг и количество: /carry [ранг] [кол-во=1]")
        return

    try:
        target_rank = int(context.args[0])
        amount = int(context.args[1]) if len(context.args) > 1 else 1
    except ValueError:
        await update.message.reply_text("Числами: /carry 3 2")
        return

    if target_rank < 1 or target_rank > 12:
        await update.message.reply_text("Ранг 1–12.")
        return

    pool = get_excess_pool(data)
    if amount > pool:
        await update.message.reply_text(f"❌ Недостаточно избытка. Банк: {pool}")
        return

    # Проверка: нельзя перенести больше, чем требование ранга
    current_req = get_rank_adjusted(target_rank, data)
    if amount > current_req:
        await update.message.reply_text(f"❌ Нельзя перенести больше требования ранга ({current_req}).")
        return

    data["carry_over"][target_rank - 1] += amount
    data["excess_spent_total"] += amount
    save_data(data)

    new_req = get_rank_adjusted(target_rank, data)
    new_pool = get_excess_pool(data)
    await update.message.reply_text(
        f"📦 Перенос в ранг {target_rank} «{get_rank_name(target_rank)}»: +{amount}\n"
        f"Требование: {RANK_SCHEDULE[target_rank]['deeds_required']} → {new_req}\n"
        f"💰 Банк: {new_pool}"
    )

async def cmd_collection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = load_data()
    collected = data.get("collected_artifacts", [])
    if not collected:
        await update.message.reply_text("🏛️ Музей пуст. Начни собирать артефакты командой /done")
        return

    by_rank = {r: [] for r in range(1, 13)}
    for art in collected:
        by_rank[art["rank"]].append(art)

    lines = [f"🏛️ КОЛЛЕКЦИЯ АРТЕФАКТОВ ({len(collected)} шт.)\n"]
    for r in range(1, 13):
        arts = by_rank[r]
        if not arts:
            continue
        name = get_rank_name(r)
        unique = {a["name"] for a in arts}
        ritual_count = sum(1 for a in arts if a["ritual"])
        lines.append(f"\n📜 Ранг {r}: «{name}» — {len(arts)} шт. (уникальных: {len(unique)}, ритуальных: {ritual_count})")
        for a in arts[-3:]:
            tag = "⚡" if a["ritual"] else "•"
            lines.append(f"  {tag} {a['name']} ({a['material']})")

    await update.message.reply_text("\n".join(lines))

async def cmd_tried(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = load_data()
    rank = get_current_rank()
    if rank < 1 or rank > 12:
        await update.message.reply_text("Вне периода активности.")
        return

    current_hunger = get_hunger_hours(data)
    new_hunger = current_hunger - 4
    new_feed_time = now_msk() - timedelta(hours=new_hunger)
    data["last_feed_time"] = new_feed_time.isoformat()
    save_data(data)

    text = get_rank_tried_text(rank)
    await update.message.reply_text(text)

async def cmd_penalty(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = load_data()
    rank = get_current_rank()
    if rank < 1 or rank > 12:
        await update.message.reply_text("Вне периода активности.")
        return

    current_hunger = get_hunger_hours(data)
    new_hunger = current_hunger + 1
    new_feed_time = now_msk() - timedelta(hours=new_hunger)
    data["last_feed_time"] = new_feed_time.isoformat()
    save_data(data)

    text = get_rank_penalty_text(rank)
    await update.message.reply_text(text)

async def cmd_penalty20(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = load_data()
    rank = get_current_rank()
    if rank < 1 or rank > 12:
        await update.message.reply_text("Вне периода активности.")
        return

    current_hunger = get_hunger_hours(data)
    new_hunger = current_hunger + 20
    new_feed_time = now_msk() - timedelta(hours=new_hunger)
    data["last_feed_time"] = new_feed_time.isoformat()
    save_data(data)

    epoch = get_epoch(rank) if 1 <= rank <= 12 else "natufian"
    await update.message.reply_text(random.choice(DISASTER_TEXTS[epoch]))

async def cmd_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = load_data()
    rank = get_current_rank()
    hours = get_hunger_hours(data)

    if rank == 0:
        await update.message.reply_text("⏳ Старт 21 апреля 2026.")
        return
    if rank == 13:
        await update.message.reply_text("🏁 Траектория завершена.")
        return

    reqs = get_adjusted_requirements(data)
    info = reqs[rank]
    mode = get_hunger_mode(data)
    collected = len(data.get("collected_artifacts", []))
    pool = get_excess_pool(data)

    if mode == "good":
        hunger_status = f"✅ До кризиса: {HUNGER_WARNING - hours:.1f} ч."
        emoji = "😊"
    elif mode == "bad":
        hunger_status = f"⚠️ До бунта: {HUNGER_RIOT - hours:.1f} ч."
        emoji = "😟"
    else:
        overtime = hours - HUNGER_RIOT
        hunger_status = f"🔥 БУНТ! Без дела {overtime:.1f} ч.!"
        emoji = "😡"

    progress_lines = []
    for r in range(1, 13):
        i = reqs[r]
        status = ""
        if r < rank:
            status = " ✅" if i["debt"] == 0 else " 📉"
        elif r == rank:
            status = f" → {i['eff_done']}/{i['adjusted']}"
        else:
            status = f" ({i['required']} арт., перенос: -{i['carry_in']})"
        progress_lines.append(f"{r}. {RANK_SCHEDULE[r]['name']}{status}")

    msg = (
        f"📊 СТАТУС — {emoji}\n\n"
        f"Ранг {rank}: «{get_rank_name(rank)}»\n"
        f"Артефактов: {info['eff_done']}/{info['adjusted']}\n"
        f"В коллекции: {collected} шт.\n"
        f"💰 Банк избыточных дел: {pool}\n"
        f"Всего дел: {data['total_deeds']}/174\n"
        f"⏱️ Без дела: {hours:.1f} ч.\n"
        f"{hunger_status}\n\n"
        f"📈 Прогресс:\n" + "\n".join(progress_lines)
    )
    await update.message.reply_text(msg)

# ========== ЛЕДНИК ШАМАНА ==========
async def cmd_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = load_data()
    rank = get_current_rank()
    if rank < 1 or rank > 12:
        await update.message.reply_text("Вне периода активности.")
        return

    available = get_all_available(rank)
    lines = [f"{f[0]} — {f[1]}" for f in available]
    tasted = data.get("tasted_flavors", [])
    tasted_count = len(set(tasted))

    await update.message.reply_text(
        f"🍦 ЛЕДНИК ШАМАНА\n"
        f"Открыто: {len(available)}/{get_total_count()} вкусов\n"
        f"Попробовано: {tasted_count}/{get_total_count()}\n\n"
        + "\n".join(lines)
        + "\n\nРасшифровка: /taste [вкус]"
    )

async def cmd_taste(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = load_data()
    rank = get_current_rank()
    if rank < 1 or rank > 12:
        await update.message.reply_text("Вне периода активности.")
        return
    if not context.args:
        await update.message.reply_text("Укажи вкус: /taste пломбирное")
        return

    flavor_name = " ".join(context.args)
    cipher, error = get_cipher(flavor_name, rank)
    if error:
        await update.message.reply_text(error)
        return

    key = flavor_name.lower().strip()
    if key not in data.get("tasted_flavors", []):
        data.setdefault("tasted_flavors", []).append(key)
        save_data(data)

    await update.message.reply_text(
        f"🔮 Шаман шепчет про «{flavor_name}»:\n\n{cipher}"
    )

# ========== ТЕКСТ ==========
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.lower().strip()
    data = load_data()
    if not data.get("user_id"):
        data["user_id"] = update.effective_user.id
        save_data(data)

    if data.get("waiting_for_keeper"):
        if text in ["сдержал", "yes", "конечно", "выполнено"]:
            data["keeper_streak"] = data.get("keeper_streak", 0) + 1
            data["total_keeper_success"] = data.get("total_keeper_success", 0) + 1
            data["waiting_for_keeper"] = False
            save_data(data)
            await update.message.reply_text(
                f"✅ Зафиксировано.\n🔥 Серия: {data['keeper_streak']} дней"
            )
            return
        elif text in ["сорвал", "no", "не выполнено"]:
            old = data.get("keeper_streak", 0)
            data["keeper_streak"] = 0
            data["waiting_for_keeper"] = False
            save_data(data)
            await update.message.reply_text(
                f"❌ Соглашение не выдержано. Серия сброшена (было: {old})."
            )
            return
        else:
            await update.message.reply_text("Ответь: 'сдержал' или 'сорвал'")
            return

    if data.get("waiting_for_plans"):
        if any(w in text for w in ["есть", "да", "готов", "yes"]):
            data["plans_confirmed"] = True
            data["morning_done"] = True
            data["superhero_morning_flag"] = True
            data["waiting_for_plans"] = False
            save_data(data)
            await update.message.reply_text("✅ Отлично, Мастер! План есть — племя будет сыто.")
            rank = get_current_rank()
            if 1 <= rank <= 12:
                img = await gigachat.generate_image(get_sunrise_prompt(rank))
                if img:
                    await context.bot.send_photo(
                        chat_id=update.effective_user.id,
                        photo=BytesIO(img),
                        caption="🌅 Рассвет. День обещает быть плодотворным."
                    )
        elif any(w in text for w in ["нет", "нету", "не", "no"]):
            data["plans_confirmed"] = False
            data["morning_done"] = True
            data["waiting_for_plans"] = False
            save_data(data)
            g1, g2 = f"G{random.randint(1,20)}", f"G{random.randint(21,40)}"
            p1, m1 = f"P{random.randint(1,20)}", f"M{random.randint(1,20)}"
            tasks = random.sample([g1, g2, p1, m1], 4)
            msg = "⚒️ Твои цели на сегодня:\n" + "\n".join(f"• `{t}`" for t in tasks)
            await update.message.reply_text(msg, parse_mode="Markdown")
        else:
            await update.message.reply_text("Ответь просто: 'есть' или 'нет'")
        return

    if any(w in text for w in ["сделал", "готово", "сделала"]):
        await cmd_done(update, context)
    elif any(w in text for w in ["попробовал", "старался", "пыт"]):
        await cmd_tried(update, context)
    elif "неудач" in text or "плохо" in text:
        await cmd_penalty(update, context)

# ========== ТАЙМЕР ==========
async def main_timer(context: ContextTypes.DEFAULT_TYPE):
    data = load_data()
    user_id = data.get("user_id")
    if not user_id:
        return

    now = now_msk()
    h, m = now.hour, now.minute
    wd = now.weekday()
    today = date.today()

    if data.get("current_date") != today_str():
        data["current_date"] = today_str()
        data["morning_done"] = False
        data["waiting_for_plans"] = False
        data["waiting_for_keeper"] = False
        data["hunger_notified"] = False
        data["last_dopamine_hour"] = None
        data["goodnight_sent"] = False
        data["superhero_morning_flag"] = False
        save_data(data)

    rank = get_current_rank(today)

    if h == 9 and m == 0:
        is_ann, ann_rank = get_rank_announcement(today)
        if is_ann and ann_rank not in data.get("announced_ranks", []):
            data.setdefault("announced_ranks", []).append(ann_rank)
            save_data(data)
            sched = RANK_SCHEDULE[ann_rank]
            holiday = sched.get("holiday_end")
            start = sched["start"]
            if holiday and holiday >= today:
                msg = (
                    f"🎉 Объявлен ранг {ann_rank}: «{sched['name']}»!\n\n"
                    f"Праздник до {holiday.strftime('%d.%m')}. "
                    f"Фактически начинается {start.strftime('%d.%m')}. "
                    f"Требуется артефактов: {sched['deeds_required']}."
                )
            else:
                msg = (
                    f"🎉 Сегодня начинается ранг {ann_rank}: «{sched['name']}»!\n"
                    f"Требуется артефактов: {sched['deeds_required']}."
                )
            await context.bot.send_message(chat_id=user_id, text=msg)

    if h == WAKEUP_HOUR and m == WAKEUP_MINUTE:
        if not data.get("morning_done"):
            if data.get("waiting_for_keeper"):
                data["waiting_for_keeper"] = False
                save_data(data)

            commandments = load_commandments()
            if commandments:
                short_list = "\n".join([f"{c['id']}. {c['short']}" for c in commandments])
                txt = f"📜 ЗАПОВЕДИ ДНЯ:\n\n{short_list}\n\n🌅 Ты начертил 4 дела на бересте? (есть/нет)"
            else:
                txt = "⚒️ Вставай. У тебя есть 4 дела на сегодня? (есть/нет)"

            await context.bot.send_message(chat_id=user_id, text=txt)
            data["waiting_for_plans"] = True
            save_data(data)

    if h == 21 and m == 0:
        if not data.get("waiting_for_keeper"):
            rank_name = get_rank_name(rank) if 1 <= rank <= 12 else "Старейшина"
            await context.bot.send_message(
                chat_id=user_id,
                text=f"🌙 Вечер у костра. {rank_name} спрашивает: ты сдержал сегодня соглашение? (сдержал/сорвал)"
            )
            data["waiting_for_keeper"] = True
            save_data(data)

    if h == 4 and m == 0 and wd < 5:
        data["superhero_morning_flag"] = False
        save_data(data)
        await context.bot.send_message(chat_id=user_id, text="🌑 Рассвет у костра. Племя ещё спит, а ты можешь взять кремнёвое орудие мысли. Сегодня не нужен подвиг. Достаточно 15 минут у огня знаний. Открой свиток диссертации. Исправь 1 абзац. Выпиши 1 мысль. Супергерой просыпается с малого удара.")

    if h == 9 and m == 0 and wd < 5:
        await context.bot.send_message(chat_id=user_id, text="⚒️ Дневная смена племени. Сейчас главное — ремесло, добыча, порядок в лагере. Делай рабочие дела крепко и спокойно. Если будет окно — можно на пару минут открыть мешок Мультимиллионера: цифры, идея, деньги, стратегия.")

    if h == 18 and m == 0 and wd < 5:
        await context.bot.send_message(chat_id=user_id, text="🏕️ Костёр семьи уже горит. Пора возвращаться в лагерь не только телом, но и сердцем. Сегодня роль — Добрый Папа: тепло, внимание, дом, разговор, забота. Не нужен идеал. Нужно одно живое доброе действие.")

    if h == 21 and m == 30 and wd < 5:
        if data.get("superhero_morning_flag"):
            msg = "🔥 Ночная мастерская открыта. Если есть искра — выходит Мультимиллионер. Один денежный шаг: идея, таблица, план, контроль, стратегия. Не строй империю за ночь. Положи один слиток в будущее."
        else:
            msg = "🦶 След охотника не найден. Утренний выход Супергероя пропущен. Значит, этой ночью сначала не золото, а знание. Открой диссертацию хотя бы на 15 минут. Сначала копьё героя, потом сундук Мультимиллионера."
        await context.bot.send_message(chat_id=user_id, text=msg)

    if h == 8 and m == 0 and wd == 5:
        await context.bot.send_message(chat_id=user_id, text="📜 День большой охоты. Сегодня племя ждёт от тебя не суеты, а глубокого прохода в пещеры знания. Суббота — день Супергероя. Не обязательно тащить весь мамонт целиком. Но нужно сделать настоящий заход: текст, таблица, правка, источники. Сегодня ты добываешь не мясо, а будущее имя.")

    if h == 9 and m == 0 and wd == 6:
        await context.bot.send_message(chat_id=user_id, text="💰 Утро Мультимиллионера. Один денежный шаг сегодня важнее десяти фантазий.")

    if h == 15 and m == 0 and wd == 6:
        await context.bot.send_message(chat_id=user_id, text="🌿 Воскресный очаг зовёт. После обеда главное — семья, тепло и присутствие.")

    mode = get_hunger_mode(data)
    if mode == "riot" and m in [0, 30]:
        await context.bot.send_message(chat_id=user_id, text=random.choice([
            "🔥 БУНТ! Охотники без оружия уже 24 часа!",
            "🔥 Племя теряет терпение! Где дела?!",
            "🔥 Кризис! Мастерская пустует слишком долго!"
        ]))
    elif mode == "bad" and not data.get("hunger_notified"):
        data["hunger_notified"] = True
        save_data(data)
        await context.bot.send_message(chat_id=user_id, text="⚠️ Дела затягиваются. Племя нервничает. Действуй!")

    if m == 55 and DOPAMINE_START <= h <= DOPAMINE_END and h % 2 != 0:
        if data.get("last_dopamine_hour") != h:
            data["last_dopamine_hour"] = h
            save_data(data)
            if 1 <= rank <= 12:
                reward_text = get_reward(rank)
            else:
                reward_text = "🍦 Классическое — лёд из колодца."
            await context.bot.send_message(chat_id=user_id, text=reward_text)
            commandments = load_commandments()
            if commandments:
                cmd = random.choice(commandments)
                await context.bot.send_message(
                    chat_id=user_id,
                    text=f"📜 {cmd['id']}. {cmd['short']} — {cmd['full']}"
                )

    if h == 23 and m == 0 and not data.get("goodnight_sent"):
        if mode == "good":
            data["goodnight_sent"] = True
            save_data(data)
            if 1 <= rank <= 12:
                img = await gigachat.generate_image(get_night_prompt(rank))
            else:
                img = None
            if img:
                await context.bot.send_photo(
                    chat_id=user_id,
                    photo=BytesIO(img),
                    caption="🌙 Спокойной ночи, Делатель. День прожит."
                )
            else:
                await context.bot.send_message(chat_id=user_id, text="🌙 Спокойной ночи, Делатель.")

    if wd == 0 and h == REPORT_HOUR and m == REPORT_MINUTE:
        reqs = get_adjusted_requirements(data)
        current = get_current_rank()
        info = reqs[current] if 1 <= current <= 12 else {"done": 0, "adjusted": 0}
        collected = len(data.get("collected_artifacts", []))
        await context.bot.send_message(
            chat_id=user_id,
            text=(
                f"📊 НЕДЕЛЬНЫЙ ОТЧЁТ\n\n"
                f"Ранг {current}: «{get_rank_name(current)}»\n"
                f"Прогресс ранга: {info['eff_done']}/{info['adjusted']}\n"
                f"Артефактов в коллекции: {collected}\n"
                f"Всего дел: {data['total_deeds']}/174"
            )
        )

    if today == date(2026, 12, 31) and h == 12 and m == 0:
        collected = len(data.get("collected_artifacts", []))
        await context.bot.send_message(
            chat_id=user_id,
            text=(
                "🏁 ТРАЕКТОРИЯ ЗАВЕРШЕНА.\n\n"
                "Ты прошёл путь от Падальщика у края до Созидателя места. "
                f"{collected} артефактов. 2 эпохи. 1 жизнь.\n\n"
                "🎉 Праздник до 1 января. Бот останавливается."
            )
        )

# ========== MAIN ==========
def main():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if not BOT_TOKEN:
        logger.error("No BOT_TOKEN!")
        return

    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("done", cmd_done))
    app.add_handler(CommandHandler("tried", cmd_tried))
    app.add_handler(CommandHandler("penalty", cmd_penalty))
    app.add_handler(CommandHandler("penalty20", cmd_penalty20))
    app.add_handler(CommandHandler("status", cmd_status))
    app.add_handler(CommandHandler("collection", cmd_collection))
    app.add_handler(CommandHandler("menu", cmd_menu))
    app.add_handler(CommandHandler("taste", cmd_taste))
    app.add_handler(CommandHandler("balance", cmd_balance))
    app.add_handler(CommandHandler("reward", cmd_reward))
    app.add_handler(CommandHandler("paydebt", cmd_paydebt))
    app.add_handler(CommandHandler("carry", cmd_carry))

    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.job_queue.run_repeating(main_timer, interval=60, first=10)

    logger.info("Бот 12 рангов v3 (избыточные дела) запущен")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
