import os
import mimetypes
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputFile
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from pytz import timezone

# Настройка логирования
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# Словарь с файлами
FILES = {
    "open_close_shift": "files/Astral_open_close.pdf",
    "open_shift_detailed": "files/Astral_open_detailed.pdf",
    "close_shift_detailed": "files/Astral_close_detailed.pdf",
    "service_rules": "files/Service_rules.pdf",
    "cleaning_schedule": "files/Cleaning_schedule.pdf",
    "special_offer": "files/Special_offer.pdf",
}

# Список сотрудников (Telegram ID)
EMPLOYEES = [1517933513]  # Замените на реальные ID сотрудников

# Расписания уборок
NOTIFICATIONS = {
    "monday": "Понедельник: выбросить мусорные пакеты и помыть кальяны с полной разборкой.",
    "friday": "Пятница: помыть кальяны с полной разборкой.",
    "sunday": "Воскресенье: помыть туалет и раковину, убрать мусор и помыть под диванами.",
}

# Проверка доступности файлов при старте
for file_key, file_path in FILES.items():
    if not os.path.exists(file_path):
        logger.error(f"Файл не найден: {file_path}")
    else:
        mime_type, _ = mimetypes.guess_type(file_path)
        logger.info(f"Файл найден: {file_path}, MIME: {mime_type}")

# Хэндлер команды /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Приветствие и отображение меню."""
    keyboard = [
        [InlineKeyboardButton("Открытие-закрытие смены", callback_data="open_close_shift")],
        [InlineKeyboardButton("Открытие смены (детально)", callback_data="open_shift_detailed")],
        [InlineKeyboardButton("Закрытие смены (детально)", callback_data="close_shift_detailed")],
        [InlineKeyboardButton("Правила сервиса", callback_data="service_rules")],
        [InlineKeyboardButton("Дни уборки", callback_data="cleaning_schedule")],
        [InlineKeyboardButton("Акции", callback_data="special_offer")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "Добро пожаловать! Выберите необходимую информацию:", reply_markup=reply_markup
    )

# Хэндлер кнопок
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработка кнопок и отправка файлов."""
    query = update.callback_query
    await query.answer()

    file_key = query.data
    if file_key in FILES:
        file_path = FILES[file_key]
        try:
            await query.message.reply_document(document=open(file_path, "rb"))
        except Exception as e:
            await query.message.reply_text(f"Ошибка при отправке файла: {e}")
    else:
        await query.message.reply_text("Ошибка: неизвестная команда.")

# Функция для отправки уведомлений
async def send_notification(context: ContextTypes.DEFAULT_TYPE, message: str) -> None:
    """Отправка уведомлений сотрудникам."""
    for employee_id in EMPLOYEES:
        try:
            await context.bot.send_message(chat_id=employee_id, text=message)
        except Exception as e:
            logger.error(f"Не удалось отправить сообщение сотруднику {employee_id}: {e}")

# Настройка планировщика
def setup_scheduler(application: Application) -> None:
    """Настройка расписания уведомлений."""
    scheduler = BackgroundScheduler(timezone=timezone("Europe/Moscow"))

    # Добавление задач на расписание
    scheduler.add_job(
        lambda: application.create_task(send_notification(application.bot, NOTIFICATIONS["monday"])),
        trigger=CronTrigger(day_of_week="mon", hour=14, minute=0)
    )
    scheduler.add_job(
        lambda: application.create_task(send_notification(application.bot, NOTIFICATIONS["friday"])),
        trigger=CronTrigger(day_of_week="fri", hour=14, minute=0)
    )
    scheduler.add_job(
        lambda: application.create_task(send_notification(application.bot, NOTIFICATIONS["sunday"])),
        trigger=CronTrigger(day_of_week="sun", hour=14, minute=0)
    )

    scheduler.start()

# Основная функция
def main() -> None:
    """Запуск бота."""
    BOT_TOKEN = "7831219812:AAFVHdeN57pXQGMmHFc5BnNWpM_8LZCfjIE"
    application = Application.builder().token(BOT_TOKEN).build()

    # Регистрация хэндлеров
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button_handler))

    # Настройка уведомлений
    setup_scheduler(application)

    logger.info("Бот запущен...")
    application.run_polling()

if __name__ == "__main__":
    main()



