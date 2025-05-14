import asyncio
import aiosqlite
from telegram import Update, Bot
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import logging

# === Configuration ===
BOT_TOKEN = '7938515275:AAETtPryHVehpEz6OgVpUDQwBherbXNNNQc'
ADMIN_ID = 5054998915  # Replace with your Telegram numeric ID
DB_PATH = 'users.db'

# === Logging (optional but helpful) ===
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# === Database Functions ===

async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute('CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY)')
        await db.commit()

async def add_user(user_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute('INSERT OR IGNORE INTO users (id) VALUES (?)', (user_id,))
        await db.commit()

async def get_all_users():
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute('SELECT id FROM users') as cursor:
            return [row[0] for row in await cursor.fetchall()]

# === Bot Functions ===

async def send_love(bot: Bot):
    users = await get_all_users()
    for user_id in users:
        try:
            await bot.send_message(chat_id=user_id, text="I love you ❤️")
        except Exception as e:
            logger.warning(f"Failed to send to {user_id}: {e}")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    await add_user(user_id)

    if user_id == ADMIN_ID:
        users = await get_all_users()
        for uid in users:
            if uid != ADMIN_ID:
                try:
                    await context.bot.forward_message(
                        chat_id=uid,
                        from_chat_id=update.effective_chat.id,
                        message_id=update.message.message_id
                    )
                except Exception as e:
                    logger.warning(f"Failed to forward to {uid}: {e}")

# === Main Bot Setup ===

async def main():
    await init_db()

    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(MessageHandler(filters.ALL, handle_message))

    # Schedule periodic love message
    scheduler = AsyncIOScheduler()
    scheduler.add_job(lambda: send_love(app.bot), 'interval', hours=1)
    scheduler.start()

    logger.info("Bot is running...")
    await app.run_polling()

if __name__ == '__main__':
    asyncio.run(main())
