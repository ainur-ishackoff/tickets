from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
import sqlite3
import logging

# Замените эти значения на свои
TOKEN = '7087293809:AAGmxciLweDmwyqHU7LMPADpRKaZlLVtw0Q'
ADMIN_CHAT_ID = '912784928'

logging.basicConfig(filename='bot.log', level=logging.INFO)

def create_database():
    db_path = 'tickets.db'
    logging.info(f"Создание или проверка файла базы данных {db_path}.")

    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    try:
        c.execute('''CREATE TABLE IF NOT EXISTS tickets
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                      name TEXT,
                      organization TEXT,
                      subject TEXT,
                      description TEXT,
                      status TEXT DEFAULT 'Open',
                      solution TEXT,
                      review TEXT)''')
        conn.commit()
        logging.info("Создание/проверка базы данных и таблицы завершена.")
    except sqlite3.Error as e:
        logging.error(f"Ошибка при создании/проверке базы данных: {e}")
    finally:
        conn.close()

async def start(update: Update, _: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text('Привет! Я ваш бот для тикетинга. Используйте /newticket для создания нового тикета.')

async def new_ticket(update: Update, _: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text('Пожалуйста, введите ваше имя, организацию, тему проблемы и описание проблемы в формате:\nИмя, Организация, Тема, Описание')

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message = update.message.text
    parts = message.split(', ')
    if len(parts) == 4:
        name, organization, subject, description = parts
        conn = sqlite3.connect('tickets.db')
        c = conn.cursor()
        try:
            c.execute("INSERT INTO tickets (name, organization, subject, description) VALUES (?, ?, ?, ?)",
                      (name, organization, subject, description))
            ticket_id = c.lastrowid
            conn.commit()
            await update.message.reply_text(f'Тикет #{ticket_id} создан.')
            await context.bot.send_message(chat_id=ADMIN_CHAT_ID, text=f'Новый тикет #{ticket_id}:\n{message}')
        except sqlite3.Error as e:
            logging.error(f"SQLite error: {e}")
            await update.message.reply_text('Произошла ошибка при создании тикета. Пожалуйста, попробуйте снова.')
        finally:
            conn.close()
    else:
        await update.message.reply_text('Неверный формат. Пожалуйста, повторите ввод.')

async def check_status(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if len(context.args) == 0:
        await update.message.reply_text('Пожалуйста, укажите ID тикета. Пример: /checkstatus 1')
        return

    ticket_id = context.args[0]
    conn = sqlite3.connect('tickets.db')
    c = conn.cursor()
    try:
        c.execute("SELECT status FROM tickets WHERE id = ?", (ticket_id,))
        result = c.fetchone()
        if result:
            await update.message.reply_text(f'Статус тикета #{ticket_id}: {result[0]}')
        else:
            await update.message.reply_text('Тикет не найден.')
    except sqlite3.Error as e:
        logging.error(f"SQLite error: {e}")
        await update.message.reply_text('Произошла ошибка при проверке статуса тикета. Пожалуйста, попробуйте снова.')
    finally:
        conn.close()

async def write_review(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if len(context.args) < 2:
        await update.message.reply_text('Пожалуйста, укажите ID тикета и отзыв. Пример: /writereview 1 Отлично')
        return

    ticket_id = context.args[0]
    review = ' '.join(context.args[1:])
    conn = sqlite3.connect('tickets.db')
    c = conn.cursor()
    try:
        c.execute("UPDATE tickets SET review = ? WHERE id = ?", (review, ticket_id))
        conn.commit()
        await update.message.reply_text(f'Отзыв для тикета #{ticket_id} сохранен.')
    except sqlite3.Error as e:
        logging.error(f"SQLite error: {e}")
        await update.message.reply_text('Произошла ошибка при сохранении отзыва. Пожалуйста, попробуйте снова.')
    finally:
        conn.close()

def main() -> None:
    create_database()  # Создай базу данных в самом начале
    application = ApplicationBuilder().token(TOKEN).build()

    application.add_handler(CommandHandler('start', start))
    application.add_handler(CommandHandler('newticket', new_ticket))
    application.add_handler(CommandHandler('checkstatus', check_status))
    application.add_handler(CommandHandler('writereview', write_review))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    application.run_polling()

if __name__ == '__main__':
    main()