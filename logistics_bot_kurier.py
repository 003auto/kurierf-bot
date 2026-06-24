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
        "duties": "• Доставка заказов пешком в пределах района\n• Приём и передача посылок получателю\n• Подтверждение доставки через приложение",
        "requirements": "• Без опыта — обучаем\n• Смартфон с навигацией\n• Ответственность и пунктуальность",
        "conditions": "• 3 500–6 000 ₽ за смену\n• Выплаты каждую неделю\n• Гибкий выбор смен\n• Оформление с первого дня",
    },
    "v2": {
        "icon": "🚴",
        "title": "Курьер на велосипеде / самокате",
        "salary": "4 000–7 000 ₽ за смену",
        "schedule": "Гибкий, смены 8–10 часов",
        "duties": "• Доставка заказов на велосипеде или самокате\n• Работа по оптимизированным маршрутам\n• Подтверждение доставки через приложение",
        "requirements": "• Велосипед или самокат — свой или компании\n• Уверенное вождение в городе\n• Смартфон с навигацией",
        "conditions": "• 4 000–7 000 ₽ за смену, в пиковые дни выше\n• Выплаты каждую неделю\n• Гибкий выбор смен\n• Оформление с первого дня",
    },
    "v3": {
        "icon": "🏍",
        "title": "Курьер на мотоцикле",
        "salary": "5 500–9 500 ₽ за смену",
        "schedule": "Гибкий, смены 8–10 часов",
        "duties": "• Быстрая доставка заказов на мотоцикле\n• Работа по приоритетным маршрутам\n• Подтверждение доставки через приложение",
        "requirements": "• Водительское удостоверение кат. A\n• Опыт езды в городе от 1 года\n• Смартфон с навигацией",
        "conditions": "• 5 500–9 500 ₽ за смену\n• Компенсация топлива\n• Выплаты каждую неделю\n• Оформление с первого дня",
    },
    "v4": {
        "icon": "🚗",
        "title": "Курьер на автомобиле",
        "salary": "5 000–9 000 ₽ за смену",
        "schedule": "Гибкий, смены 8–10 часов",
        "duties": "• Доставка заказов на автомобиле по нескольким точкам\n• Работа по оптимизированным маршрутам\n• Подтверждение доставки через приложение",
        "requirements": "• Водительское удостоверение кат. B\n• Опыт вождения в городе от 1 года\n• Смартфон с навигацией",
        "conditions": "• 5 000–9 000 ₽ за смену\n• Свой транспорт с компенсацией топлива или авто компании\n• Выплаты каждую неделю\n• Оформление с первого дня",
    },
    "v5": {
        "icon": "🚐",
        "title": "Курьер на микроавтобусе / Газели",
        "salary": "6 000–11 000 ₽ за смену",
        "schedule": "Гибкий, смены 8–12 часов",
        "duties": "• Доставка крупных и объёмных грузов\n• Погрузка и разгрузка на точках\n• Работа по маршрутным листам",
        "requirements": "• Водительское удостоверение кат. B или C\n• Опыт вождения от 2 лет\n• Готовность к физическим нагрузкам",
        "conditions": "• 6 000–11 000 ₽ за смену\n• Транспорт компании или компенсация\n• Выплаты каждую неделю\n• Оформление с первого дня",
    },
    "v6": {
        "icon": "🚛",
        "title": "Курьер на грузовом автомобиле",
        "salary": "7 000–13 000 ₽ за смену",
        "schedule": "Гибкий, смены 8–12 часов",
        "duties": "• Доставка крупногабаритных грузов на большегрузном транспорте\n• Оформление сопроводительных документов\n• Контроль сохранности груза",
        "requirements": "• Водительское удостоверение кат. C или CE\n• Опыт вождения грузового транспорта от 2 лет\n• Знание транспортного документооборота",
        "conditions": "• 7 000–13 000 ₽ за смену\n• Транспорт компании\n• Выплаты каждую неделю\n• Оформление с первого дня",
    },
}

CITIES = [
    "Москва и Московская область",
    "Санкт-Петербург и Ленинградская область",
    "Екатеринбург и Свердловская область",
    "Новосибирск и Новосибирская область",
    "Краснодар и Краснодарский край",
    "Другой регион",
]

QUIZ_QUESTIONS = [
    {
        "text": "Шаг 2 из 4\n\n<b>Укажите ваш возраст:</b>",
        "key": "age",
        "options": [
            ("До 18 лет", "до 18"),
            ("18–25 лет", "18–25"),
            ("26–35 лет", "26–35"),
            ("36–45 лет", "36–45"),
            ("45+ лет", "45+"),
        ]
    },
    {
        "text": "Шаг 3 из 4\n\n<b>Вы работали курьером раньше?</b>",
        "key": "experience",
        "options": [
            ("Да, есть опыт", "да"),
            ("Нет, первый раз", "нет"),
        ]
    },
    {
        "text": "Шаг 4 из 4\n\n<b>Когда готовы приступить к работе?</b>",
        "key": "start",
        "options": [
            ("Готов прямо сейчас", "сейчас"),
            ("Через неделю", "через неделю"),
            ("В течение месяца", "в течение месяца"),
        ]
    },
]

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main_keyboard():
    return InlineKeyboardMarkup(
        [[InlineKeyboardButton(f"{v['icon']} {v['title']}", callback_data=k)]
         for k, v in VACANCIES.items()] +
        [[InlineKeyboardButton("🏢 О компании", callback_data="about")]]
    )


def city_keyboard(vac_id):
    buttons = [
        [InlineKeyboardButton(city, callback_data=f"city_{vac_id}_{i}")]
        for i, city in enumerate(CITIES)
    ]
    return InlineKeyboardMarkup(buttons)


def quiz_keyboard(vac_id, question_index):
    question = QUIZ_QUESTIONS[question_index]
    buttons = [
        [InlineKeyboardButton(label, callback_data=f"quiz_{vac_id}_{question_index}_{value}")]
        for label, value in question["options"]
    ]
    return InlineKeyboardMarkup(buttons)


def build_hr_message(vac_id, answers):
    vac = VACANCIES[vac_id]
    text = (
        f"Привет! Хочу узнать подробнее о вакансии «{vac['title']}».\n\n"
        f"Город: {answers.get('city', '—')}\n"
        f"Возраст: {answers.get('age', '—')}\n"
        f"Опыт курьера: {answers.get('experience', '—')}\n"
        f"Готов приступить: {answers.get('start', '—')}"
    )
    return quote(text, safe="")


async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    ctx.user_data.clear()
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

    if data == "about":
        await query.edit_message_text(
            COMPANY_ABOUT,
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("← Все вакансии", callback_data="back")]
            ])
        )
        return

    if data == "back":
        ctx.user_data.clear()
        await query.edit_message_text(
            f"Актуальные вакансии <b>{COMPANY_NAME}</b>. Выберите интересующую:",
            parse_mode="HTML",
            reply_markup=main_keyboard()
        )
        return

    # Вибір вакансії — карточка + вибір міста
    if data in VACANCIES:
        vac = VACANCIES[data]
        ctx.user_data["vac_id"] = data
        ctx.user_data["answers"] = {}
        await query.edit_message_text(
            f"{vac['icon']} <b>{vac['title']}</b>\n"
            f"💰 {vac['salary']}  |  🕐 {vac['schedule']}\n\n"
            f"<b>Обязанности:</b>\n{vac['duties']}\n\n"
            f"<b>Требования:</b>\n{vac['requirements']}\n\n"
            f"<b>Условия:</b>\n{vac['conditions']}\n\n"
            "—\n\n"
            "Шаг 1 из 4\n\n<b>Выберите ваш город / регион:</b>",
            parse_mode="HTML",
            reply_markup=city_keyboard(data)
        )
        return

    # Вибір міста
    if data.startswith("city_"):
        parts = data.split("_", 2)
        _, vac_id, city_idx = parts
        city = CITIES[int(city_idx)]
        ctx.user_data["vac_id"] = vac_id
        if "answers" not in ctx.user_data:
            ctx.user_data["answers"] = {}
        ctx.user_data["answers"]["city"] = city
        await query.edit_message_text(
            QUIZ_QUESTIONS[0]["text"],
            parse_mode="HTML",
            reply_markup=quiz_keyboard(vac_id, 0)
        )
        return

    # Квіз
    if data.startswith("quiz_"):
        parts = data.split("_", 3)
        _, vac_id, q_idx_str, answer = parts
        q_idx = int(q_idx_str)

        if "answers" not in ctx.user_data:
            ctx.user_data["answers"] = {}

        ctx.user_data["answers"][QUIZ_QUESTIONS[q_idx]["key"]] = answer
        ctx.user_data["vac_id"] = vac_id

        next_q = q_idx + 1

        if next_q < len(QUIZ_QUESTIONS):
            await query.edit_message_text(
                QUIZ_QUESTIONS[next_q]["text"],
                parse_mode="HTML",
                reply_markup=quiz_keyboard(vac_id, next_q)
            )
            return

        # Фінал
        vac = VACANCIES[vac_id]
        hr_text = build_hr_message(vac_id, ctx.user_data["answers"])
        await query.edit_message_text(
            f"Отлично! 🎉\n\n"
            f"Вы выбрали: <b>{vac['icon']} {vac['title']}</b>\n"
            f"Заработок: <b>{vac['salary']}</b>\n"
            f"Регион: <b>{ctx.user_data['answers'].get('city', '—')}</b>\n\n"
            "Остался один шаг — напишите нашему менеджеру Константину, "
            "и он свяжется с вами в течение 15 минут 👇",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("✉️ Написать Константину", url=f"https://t.me/{HR_USERNAME}?text={hr_text}")],
                [InlineKeyboardButton("← Все вакансии", callback_data="back")],
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
