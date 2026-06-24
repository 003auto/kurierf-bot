import logging
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from urllib.parse import quote
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

BOT_TOKEN = os.getenv("BOT_TOKEN", "ВСТАВИТИ_ТОКЕН")
HR_USERNAME = "Vormilov"

COMPANY_NAME = "Курьер РФ"
COMPANY_ABOUT = (
    "<b>О компании Курьер РФ</b>\n\n"
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
    "v1": {
        "icon": "🚶",
        "title": "Пеший курьер",
        "salary": "3 500–6 000 ₽ за смену",
        "schedule": "Гибкий, смены 8–10 часов",
        "location": "Вся Россия",
        "duties": "• Доставка заказов пешком в пределах района\n• Приём и передача посылок получателю\n• Подтверждение доставки через приложение",
        "requirements": "• Без опыта — обучаем\n• Смартфон с навигацией\n• Ответственность и пунктуальность",
        "conditions": "• 3 500–6 000 ₽ за смену\n• Выплаты каждую неделю\n• Гибкий выбор смен\n• Оформление с первого дня",
    },
    "v2": {
        "icon": "🚴",
        "title": "Курьер на велосипеде / самокате / СИМ",
        "salary": "4 500–8 000 ₽ за смену",
        "schedule": "Гибкий, смены 8–10 часов",
        "location": "Вся Россия",
        "duties": "• Доставка заказов на личном или корпоративном транспорте\n• Работа по оптимизированным маршрутам\n• Подтверждение доставки через приложение",
        "requirements": "• Велосипед, самокат или СИМ — свой или компании\n• Уверенное вождение в городе\n• Смартфон с навигацией",
        "conditions": "• 4 500–8 000 ₽ за смену, в пиковые дни выше\n• Выплаты каждую неделю\n• Гибкий выбор смен\n• Оформление с первого дня",
    },
    "v3": {
        "icon": "🚗",
        "title": "Курьер на авто / мото",
        "salary": "5 000–9 000 ₽ за смену",
        "schedule": "Гибкий, смены 8–10 часов",
        "location": "Вся Россия",
        "duties": "• Доставка заказов на автомобиле или мотоцикле\n• Работа по маршрутам с несколькими точками\n• Подтверждение доставки через приложение",
        "requirements": "• Водительское удостоверение кат. B (авто) или A (мото)\n• Опыт вождения в городе\n• Смартфон с навигацией",
        "conditions": "• 5 000–9 000 ₽ за смену, при высокой загрузке больше\n• Свой транспорт с компенсацией топлива или транспорт компании\n• Выплаты каждую неделю\n• Оформление с первого дня",
    },
}

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main_keyboard():
    return InlineKeyboardMarkup(
        [[InlineKeyboardButton(f"{v['icon']} {v['title']}", callback_data=k)]
         for k, v in VACANCIES.items()] +
        [[InlineKeyboardButton("🏢 О компании", callback_data="about")]]
    )


def vacancy_keyboard(vac_id):
    vac = VACANCIES[vac_id]
    text = quote("Привет! Хочу узнать подробнее о вакансии", safe="")
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("✉️ Написать Константину", url=f"https://t.me/{HR_USERNAME}?text={text}")],
        [InlineKeyboardButton("← Все вакансии", callback_data="back")],
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

    if query.data == "about":
        await query.edit_message_text(
            COMPANY_ABOUT,
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("← Все вакансии", callback_data="back")]
            ])
        )
        return

    if query.data == "back":
        await query.edit_message_text(
            "Актуальные вакансии <b>ТрансРФ</b>. Выберите интересующую:",
            parse_mode="HTML",
            reply_markup=main_keyboard()
        )
        return

    vac = VACANCIES.get(query.data)
    if not vac:
        return

    await query.edit_message_text(
        f"{vac['icon']} <b>{vac['title']}</b>\n"
        f"💰 {vac['salary']}  |  📍 {vac['location']}  |  🕐 {vac['schedule']}\n\n"
        f"<b>Обязанности:</b>\n{vac['duties']}\n\n"
        f"<b>Требования:</b>\n{vac['requirements']}\n\n"
        f"<b>Условия:</b>\n{vac['conditions']}\n\n"
        "Остались вопросы или хотите откликнуться? Напишите нашему менеджеру Константину 👇",
        parse_mode="HTML",
        reply_markup=vacancy_keyboard(query.data)
    )


def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(handle))
    logger.info("Бот запущено")
    app.run_polling()


if __name__ == "__main__":
    main()
