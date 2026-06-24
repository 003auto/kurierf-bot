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

# Вопросы квиза
QUIZ_QUESTIONS = [
    {
        "text": "Шаг 1 из 3\n\n<b>Укажите ваш возраст:</b>",
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
        "text": "Шаг 2 из 3\n\n<b>Вы работали курьером раньше?</b>",
        "key": "experience",
        "options": [
            ("Да, есть опыт", "да"),
            ("Нет, первый раз", "нет"),
        ]
    },
    {
        "text": "Шаг 3 из 3\n\n<b>Когда готовы приступить к работе?</b>",
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


def quiz_keyboard(vac_id, question_index):
    question = QUIZ_QUESTIONS[question_index]
    buttons = [
        [InlineKeyboardButton(label, callback_data=f"quiz_{vac_id}_{question_index}_{value}")]
        for label, value in question["options"]
    ]
    return InlineKeyboardMarkup(buttons)


def build_hr_message(vac_id, answers):
    vac = VACANCIES[vac_id]
    age = answers.get("age", "—")
    experience = answers.get("experience", "—")
    start = answers.get("start", "—")
    text = (
        f"Привет! Хочу узнать подробнее о вакансии «{vac['title']}».\n\n"
        f"Возраст: {age}\n"
        f"Опыт курьера: {experience}\n"
        f"Готов приступить: {start}"
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
        ctx.user_data.clear()
        await query.edit_message_text(
            f"Актуальные вакансии <b>{COMPANY_NAME}</b>. Выберите интересующую:",
            parse_mode="HTML",
            reply_markup=main_keyboard()
        )
        return

    # Выбор вакансии — показываем карточку + первый вопрос квиза
    if data in VACANCIES:
        vac = VACANCIES[data]
        ctx.user_data["vac_id"] = data
        ctx.user_data["answers"] = {}
        await query.edit_message_text(
            f"{vac['icon']} <b>{vac['title']}</b>\n"
            f"💰 {vac['salary']}  |  📍 {vac['location']}  |  🕐 {vac['schedule']}\n\n"
            f"<b>Обязанности:</b>\n{vac['duties']}\n\n"
            f"<b>Требования:</b>\n{vac['requirements']}\n\n"
            f"<b>Условия:</b>\n{vac['conditions']}\n\n"
            "—\n\n"
            "Ответьте на 3 быстрых вопроса, чтобы мы могли подобрать для вас лучшие условия 👇\n\n"
            + QUIZ_QUESTIONS[0]["text"],
            parse_mode="HTML",
            reply_markup=quiz_keyboard(data, 0)
        )
        return

    # Ответ на вопрос квиза
    if data.startswith("quiz_"):
        parts = data.split("_", 3)
        # quiz_{vac_id}_{question_index}_{value}
        _, vac_id, q_idx_str, answer = parts
        q_idx = int(q_idx_str)

        if "answers" not in ctx.user_data:
            ctx.user_data["answers"] = {}

        key = QUIZ_QUESTIONS[q_idx]["key"]
        ctx.user_data["answers"][key] = answer
        ctx.user_data["vac_id"] = vac_id

        next_q = q_idx + 1

        # Ещё есть вопросы
        if next_q < len(QUIZ_QUESTIONS):
            await query.edit_message_text(
                QUIZ_QUESTIONS[next_q]["text"],
                parse_mode="HTML",
                reply_markup=quiz_keyboard(vac_id, next_q)
            )
            return

        # Квиз завершён — показываем финал
        vac = VACANCIES[vac_id]
        hr_text = build_hr_message(vac_id, ctx.user_data["answers"])
        await query.edit_message_text(
            f"Отлично! 🎉\n\n"
            f"Вы выбрали: <b>{vac['icon']} {vac['title']}</b>\n"
            f"Заработок: <b>{vac['salary']}</b>\n\n"
            "Ваши ответы сохранены. Осталось один шаг — напишите нашему менеджеру Константину, "
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
