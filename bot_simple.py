import logging
import sys
from datetime import timezone
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from config import BOT_TOKEN, CHANNELS, TOPICS, TOP_NEWS_COUNT
from db import init_db, save_news, get_top_news, get_digest_news, get_news_by_topic, get_stats, upsert_user
from scraper import scrape_channel
from summarizer import ai_summary

logging.basicConfig(level=logging.INFO, stream=sys.stdout,
                    format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

CHANNEL_MAP = {ch["username"]: ch["name"] for ch in CHANNELS}

def classify_topics(text: str) -> list:
    t = text.lower()
    return [topic for topic, kws in TOPICS.items() if any(k in t for k in kws)]

def fmt(item, idx):
    src = CHANNEL_MAP.get(item["channel"], item["channel"])
    text = item["text"][:200].replace("<","&lt;").replace(">","&gt;")
    views = f"{item['views']:,}".replace(",", " ") if item["views"] else "—"
    link = f' <a href="{item["link"]}">читати</a>' if item["link"] else ""
    return f"{idx}. <b>{src}</b> | 👁 {views}\n{text}…{link}"

async def fetch_all():
    total = 0
    for ch in CHANNELS:
        posts = scrape_channel(ch["username"])
        for p in posts:
            p["topics"] = classify_topics(p["text"])
        total += save_news(posts)
    return total

async def cmd_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    upsert_user(update.effective_user.id)
    await update.message.reply_text(
        "🇺🇦 <b>UA News Digest</b>\n\n"
        "🔥 /top — топ новин\n"
        "📰 /digest — дайджест 12 год\n"
        "🤖 /summary — AI-резюме\n"
        "📡 /topics — по темах\n"
        "📊 /stats — статистика\n"
        "📋 /sources — канали",
        parse_mode="HTML"
    )

async def cmd_top(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("⏳ Оновлюю…")
    await fetch_all()
    news = get_top_news(hours=12, limit=TOP_NEWS_COUNT)
    if not news:
        return await update.message.reply_text("Новин поки немає.")
    lines = [f"🔥 <b>Топ-{len(news)}</b> за 12 год:\n"] + [fmt(n,i) for i,n in enumerate(news,1)]
    await update.message.reply_text("\n\n".join(lines), parse_mode="HTML", disable_web_page_preview=True)

async def cmd_digest(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("⏳ Збираю…")
    await fetch_all()
    news = get_digest_news(hours=12)
    if not news:
        return await update.message.reply_text("Новин поки немає.")
    lines = [f"📰 <b>Дайджест</b> ({len(news)} новин):\n"] + [fmt(n,i) for i,n in enumerate(news[:10],1)]
    await update.message.reply_text("\n\n".join(lines), parse_mode="HTML", disable_web_page_preview=True)

async def cmd_summary(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🤖 Готую AI-резюме…")
    await fetch_all()
    news = get_digest_news(hours=12)
    summary = ai_summary(news)
    await update.message.reply_text(f"🤖 <b>AI-резюме дня:</b>\n\n{summary}", parse_mode="HTML")

async def cmd_topics(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    keyboard = [[InlineKeyboardButton(t, callback_data=f"topic:{t}")] for t in TOPICS]
    await update.message.reply_text("📡 Обери тему:", reply_markup=InlineKeyboardMarkup(keyboard))

async def cb_topic(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    topic = q.data.split(":",1)[1]
    news = get_news_by_topic(topic, hours=12, limit=5)
    if not news:
        return await q.edit_message_text(f"По темі <b>{topic}</b> новин немає.", parse_mode="HTML")
    lines = [f"<b>{topic}</b>:\n"] + [fmt(n,i) for i,n in enumerate(news,1)]
    await q.edit_message_text("\n\n".join(lines), parse_mode="HTML", disable_web_page_preview=True)

async def cmd_stats(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    stats = get_stats(hours=24)
    lines = [f"📊 <b>За 24 год:</b> {stats['total']} новин\n"]
    for ch, cnt in stats["by_channel"]:
        lines.append(f"• {CHANNEL_MAP.get(ch,ch)}: {cnt}")
    await update.message.reply_text("\n".join(lines), parse_mode="HTML")

async def cmd_sources(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    lines = ["📋 <b>Канали:</b>\n"] + [f"• <a href='https://t.me/{c[\"username\"]}'>{c[\"name\"]}</a>" for c in CHANNELS]
    await update.message.reply_text("\n".join(lines), parse_mode="HTML", disable_web_page_preview=True)

def main():
    if not BOT_TOKEN:
        logger.error("BOT_TOKEN not set!")
        sys.exit(1)
    init_db()
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("top", cmd_top))
    app.add_handler(CommandHandler("digest", cmd_digest))
    app.add_handler(CommandHandler("summary", cmd_summary))
    app.add_handler(CommandHandler("topics", cmd_topics))
    app.add_handler(CommandHandler("stats", cmd_stats))
    app.add_handler(CommandHandler("sources", cmd_sources))
    app.add_handler(CallbackQueryHandler(cb_topic, pattern="^topic:"))
    logger.info("Bot started!")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
