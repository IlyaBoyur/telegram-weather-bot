import logging
import os

from dotenv import load_dotenv
from telegram import ForceReply, Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

load_dotenv()


TOKEN = os.getenv("BOT_TOKEN")
CRYING_FACE = "\U0001F622"
REPLY_DEFAULT = (
    f"Извините, я Вас не понимаю {CRYING_FACE}\n"
    "Используйте /help для просмотра доступных команд."
)
REPLY_HELP = """
/my_weather - погода рядом
/get_weather - погода в любой точке мира
/best_weather - топ городов с лучшей погодой сегодня:
 • макс. средняя температура, температура днём +18..+27 °C
 • макс. часов приятных погодных условий: только безоблачная и малооблачная погода
"""
REPLY_PROMO = "📌Приглашай людей по реферальной ссылке и улучшай карму"
REPLY_START = (
    "Привет, {username}! Что я умею:\n" + REPLY_HELP + "\n" + REPLY_PROMO
)


logger = logging.getLogger(__name__)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /start is issued."""
    user = update.effective_user
    await update.message.reply_html(
        REPLY_START.format(username=user.mention_html())
    )


async def help_command(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Send a message when the command /help is issued."""
    await update.message.reply_text(REPLY_HELP)


async def my_weather_command(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Send a message when the command /my_weather is issued."""
    raise NotImplementedError


async def best_weather_command(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Send a message when the command /best_weather is issued."""
    from forecasting import forecast_weather

    await update.message.reply_text(REPLY_WAIT)
    dataset = forecast_weather()
    with open("forecasts.xls", "wb") as f:
        f.write(dataset.export("xls"))
    await update.message.reply_document(
        document=open("./forecasts.xls", "rb"),
        filename="forecasts.xls",
        caption="Подробный прогноз здесь",
    )


async def default(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Reply with default message."""
    await update.message.reply_text(REPLY_DEFAULT)


def main() -> None:
    """Start the bot."""
    logging.basicConfig(
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        level=logging.INFO,
    )
    # Disable telegram library`s httpx message logging
    logging.getLogger("httpx").setLevel(logging.WARNING)
    app = Application.builder().token(TOKEN).build()
    # Register commands - answers in Telegram
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("my_weather", my_weather_command))
    app.add_handler(CommandHandler("best_weather", best_weather_command))
    # Register user`s non-command request reply
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, default))
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
