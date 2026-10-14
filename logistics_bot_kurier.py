import logging
import os
from html import escape
from urllib.parse import quote

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes

BOT_TOKEN = os.getenv("BOT_TOKEN", "ВСТАВИТЬ_ТОКЕН")
HR_USERNAME = os.getenv("HR_USERNAME", "ВСТАВИТЬ_USERNAME_ВАЛЕРИЯ").strip().lstrip("@")
HR_MESSAGE = "Здравствуйте, я по поводу вакансии курьера."
# tg://resolve открывает сразу чат (а не профиль) и вставляет текст в поле ввода
HR_LINK = f"tg://resolve?domain={HR_USERNAME}&text={quote(HR_MESSAGE, safe='')}"
logging.getLogger(__name__).warning("HR link: %s", HR_LINK)

TEXT = (
    "Здравствуйте, {name}! 👋\n\n"
    "<b>Курьер РФ</b> — курьерская служба, специализирующаяся на срочной доставке "
    "документов и небольших посылок по России.\n\n"
    "<b>📋 Условия работы:</b>\n"
    "💰 Оплата: от 200 до 500 ₽ за заказ\n"
    "📍 Работа в вашем городе\n"
    "🕒 Гибкий график\n"
    "✅ Опыт работы не требуется\n"
    "📦 Доставка малогабаритных отправлений\n\n"
    "<b>📲 Хотите узнать подробнее о вакансии?</b>\n"
    "Наш HR-специалист Валерий расскажет об условиях сотрудничества, ответит на ваши "
    "вопросы и поможет с оформлением заявки.\n\n"
    "👇 Нажмите кнопку «Написать Валерию», чтобы обсудить все детали.\n\n"
    "<i>Работодатель: ООО «КУРЬЕР», ИНН 9717147317, ОГРН 1237700764135</i>"
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    name = escape(update.effective_user.first_name or "")
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("✉️ Написать Валерию", url=HR_LINK)]
    ])
    await update.message.reply_text(
        TEXT.format(name=name),
        parse_mode="HTML",
        reply_markup=keyboard,
        disable_web_page_preview=True,
    )


def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    logger.info("Бот запущен")
    app.run_polling()


if __name__ == "__main__":
    main()
