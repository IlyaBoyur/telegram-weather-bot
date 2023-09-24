import logging
import os
from enum import Enum

from dotenv import load_dotenv
from telegram import (
    KeyboardButton,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
    Update,
)
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
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
REPLY_LOCATION_REQUEST = "Мне нужна Ваша геолокация"
REPLY_HOW_TO_CANCEL = "Отправьте /cancel для возврата в основное меню."
REPLY_CANCEL = "Запрос отменен. Меню:\n" + REPLY_HELP
REPLY_WAIT = "Запрос отправлен, пожалуйста подождите..."
REPLY_WEATHER = (
    "По данным Яндекс.Погоды,"
    " сегодня в городе {location} в среднем {temperature:.1f} °C"
)
REPLY_NEED_PLACE = "Напишите место, где вы хотите узнать погоду"
BTN_REQUEST_GEO = "Отправить свою геолокацию"


logger = logging.getLogger(__name__)


class ConversationState(int, Enum):
    LOCATION = 0
    PLACE = 1


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
) -> int:
    """Send a message when the command /my_weather is issued."""
    keyboard = [[KeyboardButton(BTN_REQUEST_GEO, request_location=True)]]
    await update.message.reply_text(
        REPLY_LOCATION_REQUEST + "\n" + REPLY_HOW_TO_CANCEL,
        reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True),
    )
    return ConversationState.LOCATION


async def location(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Uses the location to request weather and reply it to the user."""
    from forecasting import get_weather_by_position

    user = update.message.from_user
    latitude = update.message.location.latitude
    longitude = update.message.location.longitude
    logger.info("User %s: %f / %f", user.first_name, latitude, longitude)
    await update.message.reply_text(REPLY_WAIT)
    weather = get_weather_by_position(latitude, longitude)
    logger.info(f"Weather: %s", weather)
    await update.message.reply_text(
        REPLY_WEATHER.format(
            location=weather.get("city"),
            temperature=weather.get("temperature_total_avg"),
        ),
        reply_markup=ReplyKeyboardRemove(),
    )
    return ConversationHandler.END


async def cancel_command(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    """Cancels and ends the conversation."""
    user = update.message.from_user
    logger.info("User %s canceled the conversation.", user.first_name)
    await update.message.reply_text(
        REPLY_CANCEL, reply_markup=ReplyKeyboardRemove()
    )
    return ConversationHandler.END





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


def create_my_weather_handler():
    conversation_handler = ConversationHandler(
        entry_points=[CommandHandler("my_weather", my_weather_command)],
        states={
            ConversationState.LOCATION: [
                MessageHandler(filters.LOCATION, location),
                CommandHandler("cancel", cancel_command),
            ]
        },
        fallbacks=[CommandHandler("cancel", cancel_command)],
        conversation_timeout=30,
    )
    return conversation_handler





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
    app.add_handler(create_my_weather_handler())
    app.add_handler(CommandHandler("best_weather", best_weather_command))
    # Register user`s non-command request reply
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, default))
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
