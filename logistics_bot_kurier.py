import logging
import os
from urllib.parse import quote

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

BOT_TOKEN = os.getenv("BOT_TOKEN", "ВСТАВИТИ_ТОКЕН")
HR_USERNAME = "Vormilov"
HR_NAME = "Константину"

COMPANY_NAME = "Курьер РФ"

COMPANY_INTRO = (
    f"<b>{COMPANY_NAME}</b> — федеральная курьерская служба.\n"
    "Стабильные выплаты каждую неделю, гибкий график, обучение на старте.\n\n"
    "<b>Вакансии открыты в регионах:</b>\n"
    "📍 Крым\n"
    "📍 Донецк\n"
    "📍 Казань\n"
    "📍 Хабаровск\n"
    "📍 Владивосток\n"
    "📍 и другие города\n\n"
    "Шаг 1 из 2 — <b>выберите ваш регион:</b>"
)

REGIONS = [
    "Крым",
    "Донецк",
    "Казань",
    "Хабаровск",
    "Владивосток",
    "Другой город",
]

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

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def regions_keyboard():
    buttons = [
        InlineKeyboardButton(f"📍 {r}", callback_data=f"reg_{i}")
        for i, r in enumerate(REGIONS)
    ]
    # по 2 кнопки в ряд
    return InlineKeyboardMarkup([buttons[i:i + 2] for i in range(0, len(buttons), 2)])


def vacancies_keyboard(reg_idx):
    rows = [
        [InlineKeyboardButton(f"{v['icon']} {v['title']}", callback_data=f"vac_{key}_{reg_idx}")]
        for key, v in VACANCIES.items()
    ]
    rows.append([InlineKeyboardButton("← Сменить регион", callback_data="back")])
    return InlineKeyboardMarkup(rows)


def hr_link(vac_key, region):
    text = (
        f"Привет! Хочу узнать подробнее о вакансии «{VACANCIES[vac_key]['title']}».\n"
        f"Регион: {region}"
    )
    return f"https://t.me/{HR_USERNAME}?text={quote(text, safe='')}"


async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    await update.message.reply_text(
        f"Здравствуйте, {user.first_name}! 👋\n\n{COMPANY_INTRO}",
        parse_mode="HTML",
        reply_markup=regions_keyboard(),
    )


async def handle(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    # Назад на первый экран
    if data == "back":
        await query.edit_message_text(
            COMPANY_INTRO, parse_mode="HTML", reply_markup=regions_keyboard()
        )
        return

    # Шаг 1 → выбран регион, показываем вакансии
    if data.startswith("reg_"):
        reg_idx = int(data.split("_", 1)[1])
        await query.edit_message_text(
            f"Регион: <b>{REGIONS[reg_idx]}</b>\n\n"
            "Шаг 2 из 2 — <b>выберите вакансию:</b>",
            parse_mode="HTML",
            reply_markup=vacancies_keyboard(reg_idx),
        )
        return

    # Шаг 2 → выбрана вакансия, карточка + кнопка HR
    if data.startswith("vac_"):
        _, vac_key, reg_idx = data.split("_", 2)
        vac = VACANCIES[vac_key]
        region = REGIONS[int(reg_idx)]
        await query.edit_message_text(
            f"{vac['icon']} <b>{vac['title']}</b>\n"
            f"📍 {region}\n"
            f"💰 {vac['salary']}  |  🕐 {vac['schedule']}\n\n"
            f"<b>Обязанности:</b>\n{vac['duties']}\n\n"
            f"<b>Требования:</b>\n{vac['requirements']}\n\n"
            f"<b>Условия:</b>\n{vac['conditions']}\n\n"
            f"Напишите менеджеру {HR_NAME} — он свяжется с вами в течение 15 минут 👇",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton(f"✉️ Написать {HR_NAME}", url=hr_link(vac_key, region))],
                [InlineKeyboardButton("← Другая вакансия", callback_data=f"reg_{reg_idx}")],
            ]),
        )
        return


def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(handle))
    logger.info("Бот запущен")
    app.run_polling()


if __name__ == "__main__":
    main()
