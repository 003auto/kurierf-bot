import logging
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from urllib.parse import quote
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

BOT_TOKEN = os.getenv("BOT_TOKEN", "ВСТАВИТИ_ТОКЕН")
HR_USERNAME = "Vormilov"

COMPANY_NAME = "КурьерРФ"
COMPANY_ABOUT = (
    "<b>О компании КурьерРФ</b>\n\n"
    "КурьерРФ — федеральная курьерская служба с многолетней историей. "
    "Мы начинали с нескольких городов, а сегодня работаем во всех крупных городах России: "
    "Москва, Санкт-Петербург, Екатеринбург, Новосибирск, Казань, Краснодар, "
    "Нижний Новгород и десятки региональных центров.\n\n"
    "В нашем штате более 5 000 курьеров по всей стране. "
    "Ежедневно мы выполняем тысячи доставок — от небольших посылок до крупногабаритных грузов.\n\n"
    "<b>Почему выбирают нас:</b>\n"
    "• Стабильные выплаты каждую неделю без задержек\n"
    "• Гибкий график — сам выбираешь смены\n"
    "• Официальное оформление с первого дня\n"
    "• Собственный транспорт компании для тех, у кого нет своего\n"
    "• Поддержка и обучение на старте — выходишь на маршрут уже через день"
)

VACANCIES = {
    "v1": {"icon": "🚶", "title": "Пеший курьер", "salary": "3 500–6 000 ₽ за смену"},
    "v2": {"icon": "🚴", "title": "Курьер на велосипеде / самокате / СИМ", "salary": "4 500–8 000 ₽ за смену"},
    "v3": {"icon": "🚗", "title": "Курьер на авто / мото", "salary": "5 000–9 000 ₽ за смену"},
}

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main_keyboard():
    return InlineKeyboardMarkup(
        [[InlineKeyboardButton(f"{v['icon']} {v['title']}", callback_data=f"vac_{k}")]
         for k, v in VACANCIES.items()] +
        [[InlineKeyboardButton("🏢 О компании", callback_data="about")]]
    )


def age_keyboard(vac_id):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("до 18", callback_data=f"age_до18_{vac_id}"),
         InlineKeyboardButton("18–25", callback_data=f"age_18-25_{vac_id}")],
        [InlineKeyboardButton("26–35", callback_data=f"age_26-35_{vac_id}"),
         InlineKeyboardButton("36–45", callback_data=f"age_36-45_{vac_id}")],
        [InlineKeyboardButton("45+", callback_data=f"age_45+_{vac_id}")],
    ])


def exp_keyboard(vac_id, age):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ Да", callback_data=f"exp_да_{vac_id}_{age}"),
         InlineKeyboardButton("❌ Нет", callback_data=f"exp_нет_{vac_id}_{age}")],
    ])


def start_keyboard(vac_id, age, exp):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🟢 Готов сейчас", callback_data=f"when_сейчас_{vac_id}_{age}_{exp}")],
        [InlineKeyboardButton("📅 Через неделю", callback_data=f"when_через_неделю_{vac_id}_{age}_{exp}")],
        [InlineKeyboardButton("💬 Есть вопросы", callback_data=f"when_есть_вопросы_{vac_id}_{age}_{exp}")],
    ])


async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    await update.message.reply_text(
        f"Здравствуйте, {user.first_name}! 👋\n\n"
        f"Вы обратились в HR-отдел компании <b>{COMPANY_NAME}</b>.\n\n"
        "Федеральная курьерская служба.\n"
        "Более 5 000 курьеров по всей России.\n\n"
        "Выберите интересующую вакансию:",
        parse_mode="HTML",
        reply_markup=main_keyboard()
    )


async def handle(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    # О компании
    if data == "about":
        await query.edit_message_text(
            COMPANY_ABOUT,
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("← Все вакансии", callback_data="back")]
            ])
        )
        return

    # Назад
    if data == "back":
        await query.edit_message_text(
            f"Актуальные вакансии <b>{COMPANY_NAME}</b>. Выберите интересующую:",
            parse_mode="HTML",
            reply_markup=main_keyboard()
        )
        return

    # Выбор вакансии → Вопрос 1: Возраст
    if data.startswith("vac_"):
        vac_id = data.split("_")[1]
        vac = VACANCIES.get(vac_id)
        await query.edit_message_text(
            f"{vac['icon']} <b>{vac['title']}</b> — {vac['salary']}\n\n"
            "Отлично! Пара быстрых вопросов, чтобы менеджер был готов к разговору.\n\n"
            "<b>Вопрос 1 из 3</b>\nСколько вам лет?",
            parse_mode="HTML",
            reply_markup=age_keyboard(vac_id)
        )
        return

    # Ответ на возраст → Вопрос 2: Опыт
    if data.startswith("age_"):
        parts = data.split("_", 2)
        age = parts[1]
        vac_id = parts[2]
        await query.edit_message_text(
            "<b>Вопрос 2 из 3</b>\nВы работали курьером раньше?",
            parse_mode="HTML",
            reply_markup=exp_keyboard(vac_id, age)
        )
        return

    # Ответ на опыт → Вопрос 3: Когда начать
    if data.startswith("exp_"):
        parts = data.split("_", 3)
        exp = parts[1]
        vac_id = parts[2]
        age = parts[3]
        await query.edit_message_text(
            "<b>Вопрос 3 из 3</b>\nКогда готовы приступить к работе?\n\n"
            "После ответа вас переключат к менеджеру Константину 👇",
            parse_mode="HTML",
            reply_markup=start_keyboard(vac_id, age, exp)
        )
        return

    # Ответ на когда → Финал
    if data.startswith("when_"):
        parts = data.split("_", 4)
        when = parts[1]
        vac_id = parts[2]
        age = parts[3]
        exp = parts[4]
        vac = VACANCIES.get(vac_id)

        exp_text = "есть опыт курьера" if exp == "да" else "без опыта"
        when_text = {
            "сейчас": "готов сейчас",
            "через_неделю": "через неделю",
            "есть_вопросы": "есть вопросы",
        }.get(when, when)

        msg = quote(
            f"Привет! Интересует вакансия: {vac['title']}\n"
            f"Возраст: {age}\n"
            f"Опыт: {exp_text}\n"
            f"Готов начать: {when_text}",
            safe=""
        )

        await query.edit_message_text(
            f"✅ Спасибо за ответы!\n\n"
            f"Вакансия: <b>{vac['title']}</b>\n"
            f"💰 {vac['salary']}\n\n"
            "Нажмите кнопку ниже — менеджер Константин уже будет знать о вас всё нужное 👇",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("✉️ Написать Константину", url=f"https://t.me/{HR_USERNAME}?text={msg}")],
                [InlineKeyboardButton("← В начало", callback_data="back")],
            ])
        )
        return


def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(handle))
    logger.info("Бот запущено")
    app.run_polling()


if __name__ == "__main__":
    main()
