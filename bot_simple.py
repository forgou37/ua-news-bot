import logging
import sys
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from config import BOT_TOKEN

logging.basicConfig(level=logging.INFO, stream=sys.stdout,
                    format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

async def cmd_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🇺🇦 UA News Bot — живий!")

async def cmd_top(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    from scraper import scrape_channel
    await update.message.reply_text("⏳ Збираю новини...")
    posts = scrape_channel("suspilne_news")
    if posts:
        text = "\n\n".join(p["text"][:200] for p in posts[:3])
        await update.message.reply_text(text)
    else:
        await update.message.reply_text("Новин не знайдено")

def main():
    if not BOT_TOKEN:
        logger.error("BOT_TOKEN not set!")
        sys.exit(1)
    logger.info(f"Starting bot...")
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("top", cmd_top))
    logger.info("Bot running!")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
