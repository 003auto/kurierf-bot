"""
Курьер РФ — HR-бот: 1 экран + кнопка в личку HR,
статистика по меткам (?start=метка), лиды через Telegram Business, рассылка.
Подробности: STATS_GUIDE.md
"""
import asyncio
import json
import logging
import os
import re
import sqlite3
from datetime import datetime, timedelta, timezone
from html import escape
from urllib.parse import quote

from telegram import (
    BusinessConnection, InlineKeyboardButton, InlineKeyboardMarkup, Update,
)
from telegram.error import Forbidden, RetryAfter, TelegramError
from telegram.ext import (
    Application, BusinessConnectionHandler, CallbackQueryHandler,
    CommandHandler, ContextTypes, MessageHandler, filters,
)

# ───────────────────────── Настройки ─────────────────────────
BOT_TOKEN = os.getenv("BOT_TOKEN", "ВСТАВИТЬ_ТОКЕН")
HR_USERNAME = os.getenv("HR_USERNAME", "ВСТАВИТЬ_USERNAME_ВАЛЕРИЯ").strip().lstrip("@")
ADMIN_IDS = {int(x) for x in re.findall(r"\d+", os.getenv("ADMIN_IDS", ""))}
DB_FILE = os.getenv("DB_FILE", "stats.db")          # Railway: /data/stats.db
DATA_FILE = os.getenv("DATA_FILE", "stats.json")    # старый JSON, только для миграции

HR_MESSAGE = "Здравствуйте! 👋 Хочу узнать подробнее о вакансии."
# tg://resolve открывает сразу чат (а не профиль) и вставляет текст в поле ввода
HR_LINK = f"tg://resolve?domain={HR_USERNAME}&text={quote(HR_MESSAGE, safe='')}"

MSK = timezone(timedelta(hours=3))
NO_LABEL = "direct"
LABEL_RE = re.compile(r"^[A-Za-z0-9_-]{1,64}$")

TEXT = (
    "Здравствуйте, {name}! 👋\n\n"
    "<b>Курьер РФ</b> — курьерская служба, специализирующаяся на срочной доставке "
    "документов и небольших посылок по России.\n\n"
    "<b>📋 Условия работы:</b>\n"
    "💰 Оплата: от 2 000 до 6 000 ₽ за заказ\n"
    "📍 Работа в вашем городе\n"
    "🕒 Гибкий график\n"
    "✅ Опыт работы не требуется\n"
    "📦 Доставка малогабаритных отправлений\n\n"
    "<b>📲 Хотите узнать подробнее о вакансии?</b>\n"
    "Наш HR-специалист Валерий расскажет об условиях сотрудничества, ответит на ваши "
    "вопросы и поможет с оформлением заявки.\n\n"
    "👇 Нажмите кнопку «Написать Валерию», чтобы обсудить все детали.\n\n"
)

ABOUT_TEXT = (
    "<b>🏢 О КОМПАНИИ</b>\n"
    "Курьер РФ — сервис, ориентированный на подбор курьеров для доставки документов "
    "и небольших посылок на территории России.\n"
    "Наша цель — сделать поиск работы в сфере доставки простым и удобным. Мы предлагаем "
    "соискателям возможность ознакомиться с доступными вакансиями, выбрать подходящий "
    "график и получить консультацию HR-специалиста.\n\n"
    "<b>📜 ИСТОРИЯ КОМПАНИИ</b>\n"
    "ООО «КУРЬЕР» зарегистрировано 9 ноября 2023 года в Москве. Основное направление "
    "деятельности организации — услуги почтовой связи. Среди дополнительных направлений — "
    "транспортные перевозки и подбор персонала.\n\n"
    "<b>📋 ЮРИДИЧЕСКАЯ ИНФОРМАЦИЯ</b>\n"
    "Полное название: ООО «КУРЬЕР»\n"
    "ИНН: 9717147317\n"
    "ОГРН: 1237700764135\n"
    "КПП: 771701001\n"
    "Дата регистрации: 09.11.2023\n"
    "Юридический адрес: 129626, г. Москва, проспект Мира, д. 102, корп. 1, помещ. 3/7"
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger("bot")


def hr_keyboard(label="✉️ Написать Валерию"):
    return InlineKeyboardMarkup([[InlineKeyboardButton(label, url=HR_LINK)]])


def main_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("✉️ Написать Валерию", url=HR_LINK)],
        [InlineKeyboardButton("🏢 О компании", callback_data="about")],
    ])


def about_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("✉️ Написать Валерию", url=HR_LINK)],
        [InlineKeyboardButton("← Вернуться к вакансии", callback_data="home")],
    ])


def is_admin(update: Update) -> bool:
    return bool(update.effective_user) and update.effective_user.id in ADMIN_IDS


# ───────────────────────── Хранилище (SQLite kv) ─────────────────────────
def _empty():
    return {
        "starts": {}, "leads": {},
        "today_starts": {}, "today_leads": {},
        "today_date": datetime.now(MSK).date().isoformat(),
        "today_counted": [], "user_source": {}, "counted": [],
        "hr_id": None,
    }


def _db():
    d = os.path.dirname(DB_FILE)
    if d:
        os.makedirs(d, exist_ok=True)
    conn = sqlite3.connect(DB_FILE)
    conn.execute("CREATE TABLE IF NOT EXISTS kv (key TEXT PRIMARY KEY, value TEXT NOT NULL)")
    return conn


def _load_data():
    data = _empty()
    with _db() as conn:
        row = conn.execute("SELECT value FROM kv WHERE key='data'").fetchone()
    if row:
        data.update(json.loads(row[0]))
        return data
    # Миграция: БД пустая, но есть старый JSON
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, encoding="utf-8") as f:
                data.update(json.load(f))
            logger.info("Миграция: перенесены данные из %s", DATA_FILE)
        except Exception as e:
            logger.error("Миграция из %s не удалась: %s", DATA_FILE, e)
    _save_data(data)
    return data


def _save_data(data=None):
    payload = json.dumps(data if data is not None else _DATA, ensure_ascii=False)
    with _db() as conn:  # транзакция: commit при успехе, rollback при ошибке
        conn.execute(
            "INSERT INTO kv(key, value) VALUES('data', ?) "
            "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
            (payload,),
        )


_DATA = _load_data()


# ───────────────────────── Счётчики ─────────────────────────
def roll_day():
    """Новый день по MSK → обнуляем только today_*."""
    today = datetime.now(MSK).date().isoformat()
    if _DATA["today_date"] != today:
        _DATA.update(today_date=today, today_starts={}, today_leads={}, today_counted=[])


def _inc(bucket, label):
    _DATA[bucket][label] = _DATA[bucket].get(label, 0) + 1


def track_start(user_id: int, label: str):
    roll_day()
    _inc("starts", label)
    _inc("today_starts", label)
    _DATA["user_source"][str(user_id)] = label  # последняя метка
    _save_data()


def track_lead(user_id: int) -> bool:
    """Засчитать лид. Только для тех, кто пришёл через бота."""
    uid = str(user_id)
    label = _DATA["user_source"].get(uid)
    if label is None:
        return False
    roll_day()
    changed = False
    if user_id not in _DATA["counted"]:
        _DATA["counted"].append(user_id)
        _inc("leads", label)
        changed = True
    if user_id not in _DATA["today_counted"]:
        _DATA["today_counted"].append(user_id)
        _inc("today_leads", label)
        changed = True
    if changed:
        _save_data()
    return changed


# ───────────────────────── Пользовательская часть ─────────────────────────
async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    label = ctx.args[0] if ctx.args and LABEL_RE.match(ctx.args[0]) else NO_LABEL
    track_start(user.id, label)
    await update.message.reply_text(
        TEXT.format(name=escape(user.first_name or "")),
        parse_mode="HTML",
        reply_markup=main_keyboard(),
        disable_web_page_preview=True,
    )


async def on_nav_button(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    if q.data == "about":
        text, kb = ABOUT_TEXT, about_keyboard()
    else:  # home
        text = TEXT.format(name=escape(q.from_user.first_name or ""))
        kb = main_keyboard()
    try:
        await q.edit_message_text(text, parse_mode="HTML", reply_markup=kb,
                                  disable_web_page_preview=True)
    except TelegramError as e:  # "message is not modified" при двойном клике
        logger.debug("nav: %s", e)


# ───────────────────────── Telegram Business ─────────────────────────
async def on_business_connection(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    bc: BusinessConnection = update.business_connection
    _DATA["hr_id"] = bc.user.id if bc.is_enabled else None
    _save_data()
    logger.info("Business connection: user=%s enabled=%s", bc.user.id, bc.is_enabled)


async def on_business_message(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    msg = update.business_message
    if not msg or not msg.from_user:
        return
    # hr_id мог не сохраниться (бот подключили до запуска) — достаём из подключения
    if _DATA.get("hr_id") is None:
        try:
            bc = await ctx.bot.get_business_connection(msg.business_connection_id)
            _DATA["hr_id"] = bc.user.id
            _save_data()
        except TelegramError as e:
            logger.warning("get_business_connection: %s", e)
    if msg.from_user.id == _DATA.get("hr_id"):
        return  # исходящее от HR — не лид
    if track_lead(msg.from_user.id):
        logger.info("Лид: user=%s", msg.from_user.id)


# ───────────────────────── Админка ─────────────────────────
def _table(starts: dict, leads: dict) -> str:
    labels = sorted(set(starts) | set(leads), key=lambda k: -starts.get(k, 0))
    if not labels:
        return "нет данных"
    w = max(5, max(len(l) for l in labels))
    lines = [f"{'метка':<{w}} {'старт':>6} {'личка':>6} {'CR':>6}"]
    ts = tl = 0
    for l in labels:
        s, d = starts.get(l, 0), leads.get(l, 0)
        ts, tl = ts + s, tl + d
        cr = f"{d / s * 100:.0f}%" if s else "—"
        lines.append(f"{l:<{w}} {s:>6} {d:>6} {cr:>6}")
    cr = f"{tl / ts * 100:.0f}%" if ts else "—"
    lines.append(f"{'ИТОГО':<{w}} {ts:>6} {tl:>6} {cr:>6}")
    return "\n".join(lines)


async def cmd_stats(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update):
        return
    roll_day()
    status = (f"✅ Business подключён (HR id {_DATA['hr_id']})" if _DATA.get("hr_id")
              else "❌ Business не подключён — личка не считается")
    text = (
        f"<b>📊 Сегодня ({_DATA['today_date']}, MSK)</b>\n"
        f"<pre>{escape(_table(_DATA['today_starts'], _DATA['today_leads']))}</pre>\n"
        f"<b>📈 За всё время</b>\n"
        f"<pre>{escape(_table(_DATA['starts'], _DATA['leads']))}</pre>\n"
        f"{status}"
    )
    await update.message.reply_text(text, parse_mode="HTML")


async def cmd_reset(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update):
        return
    await update.message.reply_text(
        "Что обнулить?",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("Только сегодня", callback_data="reset_today")],
            [InlineKeyboardButton("⚠️ Всё", callback_data="reset_all")],
            [InlineKeyboardButton("Отмена", callback_data="reset_cancel")],
        ]),
    )


async def cmd_broadcast(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update):
        return
    # берём текст как есть (с переносами строк), без самой команды
    parts = (update.message.text or "").split(maxsplit=1)
    text = parts[1].strip() if len(parts) > 1 else ""
    if not text:
        await update.message.reply_text("Использование: /broadcast <текст>")
        return
    recipients = _broadcast_targets()
    ctx.user_data["bc_text"] = text
    await update.message.reply_text(
        f"Получателей: <b>{len(recipients)}</b> (стартовали, но не написали HR)\n\n"
        f"Превью:\n—\n{escape(text)}\n—",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("✅ Отправить", callback_data="bc_send")],
            [InlineKeyboardButton("Отмена", callback_data="bc_cancel")],
        ]),
    )


def _broadcast_targets():
    counted = set(_DATA["counted"])
    hr = _DATA.get("hr_id")
    return [int(u) for u in _DATA["user_source"]
            if int(u) not in counted and int(u) != hr and int(u) not in ADMIN_IDS]


async def _run_broadcast(bot, admin_chat_id: int, text: str):
    sent = blocked = failed = 0
    kb = hr_keyboard("✉️ Связаться с менеджером")
    for uid in _broadcast_targets():
        for _ in range(2):
            try:
                await bot.send_message(uid, text, reply_markup=kb)
                sent += 1
                break
            except RetryAfter as e:
                await asyncio.sleep(e.retry_after + 1)
            except Forbidden:
                blocked += 1
                break
            except TelegramError as e:
                logger.warning("broadcast %s: %s", uid, e)
                failed += 1
                break
        await asyncio.sleep(0.05)  # ~20 сообщений/сек, ниже лимита Telegram
    await bot.send_message(
        admin_chat_id,
        f"📬 Рассылка завершена\n✅ Доставлено: {sent}\n🚫 Заблокировали бота: {blocked}\n⚠️ Ошибки: {failed}",
    )


async def on_admin_button(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    if not is_admin(update):
        await q.answer()
        return
    await q.answer()
    data = q.data
    if data == "reset_today":
        _DATA.update(today_starts={}, today_leads={}, today_counted=[])
        _save_data()
        await q.edit_message_text("✅ Сегодняшняя статистика обнулена")
    elif data == "reset_all":
        hr_id, users = _DATA.get("hr_id"), _DATA["user_source"]
        _DATA.clear()
        _DATA.update(_empty(), hr_id=hr_id, user_source=users)  # базу для рассылки не теряем
        _save_data()
        await q.edit_message_text("✅ Вся статистика обнулена (база пользователей для рассылки сохранена)")
    elif data == "reset_cancel" or data == "bc_cancel":
        ctx.user_data.pop("bc_text", None)
        await q.edit_message_text("Отменено")
    elif data == "bc_send":
        text = ctx.user_data.pop("bc_text", None)
        if not text:
            await q.edit_message_text("Нет текста для рассылки, запустите /broadcast заново")
            return
        await q.edit_message_text("🚀 Рассылка запущена, отчёт придёт по завершении")
        ctx.application.create_task(_run_broadcast(ctx.bot, q.message.chat_id, text))


async def cmd_chatid(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update):
        return
    await update.message.reply_text(f"chat_id: <code>{update.effective_chat.id}</code>", parse_mode="HTML")


# ───────────────────────── Запуск ─────────────────────────
def main():
    logger.info("HR link: %s", HR_LINK)
    logger.info("DB: %s | admins: %s", DB_FILE, ADMIN_IDS or "НЕ ЗАДАНЫ")
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("stats", cmd_stats))
    app.add_handler(CommandHandler("reset_stats", cmd_reset))
    app.add_handler(CommandHandler("broadcast", cmd_broadcast))
    app.add_handler(CommandHandler("chatid", cmd_chatid))
    app.add_handler(CallbackQueryHandler(on_nav_button, pattern=r"^(about|home)$"))
    app.add_handler(CallbackQueryHandler(on_admin_button, pattern=r"^(reset_|bc_)"))
    app.add_handler(BusinessConnectionHandler(on_business_connection))
    app.add_handler(MessageHandler(filters.UpdateType.BUSINESS_MESSAGE, on_business_message))
    # КРИТИЧНО: без business_connection / business_message Telegram не шлёт эти апдейты
    app.run_polling(allowed_updates=[
        "message", "callback_query", "business_connection", "business_message",
    ])


if __name__ == "__main__":
    main()
