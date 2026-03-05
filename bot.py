import asyncio
import logging
import os
import sys
from datetime import datetime, timezone
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    ContextTypes, JobQueue
)
from config import BOT_TOKEN, CHANNELS, TOPICS, DIGEST_HOUR, DIGEST_MINUTE, TOP_NEWS_COUNT

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    stream=sys.stdout
)
logger = logging.getLogger(__name__)
from scraper import scrape_channel
from db import init_db, save_news, get_top_news, get_digest_news, get_news_by_topic, get_stats, upsert_user
from summarizer import ai_summary




# ─── helpers ────────────────────────────────────────────────────────────────

def classify_topics(text: str) -> list[str]:
    text_lower = text.lower()
    found = []
    for topic, keywords in TOPICS.items():
        if any(kw in text_lower for kw in keywords):
            found.append(topic)
    return found


def format_news_item(item: dict, idx: int, show_similar: bool = False) -> str:
    from db import find_similar_sources
    channel_map = {ch["username"]: ch["name"] for ch in CHANNELS}
    source = channel_map.get(item["channel"], item["channel"])
    text = item["text"][:200].replace("<", "&lt;").replace(">", "&gt;")
    views = f"{item['views']:,}".replace(",", " ") if item["views"] else "—"
    link = f' <a href="{item["link"]}">читати</a>' if item["link"] else ""
    result = f"{idx}. <b>{source}</b> | 👁 {views}\n{text}…{link}"
    if show_similar:
        similar = find_similar_sources(item["text"], item.get("link", ""))
        if similar:
            result += f"\n📡 <i>Також: {', '.join(similar)}</i>"
    return result


async def fetch_all_news():
    """Fetch news from all channels and save to DB."""
    total = 0
    for ch in CHANNELS:
        posts = scrape_channel(ch["username"])
        for post in posts:
            post["topics"] = classify_topics(post["text"])
        saved = save_news(posts)
        total += saved
        logger.info(f"  {ch['username']}: {len(posts)} fetched, {saved} new")
    logger.info(f"Total new posts saved: {total}")
    return total


# ─── commands ───────────────────────────────────────────────────────────────

async def cmd_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    upsert_user(update.effective_user.id)
    await update.message.reply_text(
        "🇺🇦 <b>UA News Digest</b>\n\n"
        "Агрегатор 10 найпопулярніших українських новинних каналів.\n\n"
        "<b>Команди:</b>\n"
        "🔥 /top — топ новин прямо зараз\n"
        "📰 /digest — дайджест за 12 годин\n"
        "🤖 /summary — AI-резюме дня\n"
        "📡 /topics — новини по темах\n"
        "📊 /stats — статистика\n"
        "ℹ️ /sources — список каналів",
        parse_mode="HTML"
    )


async def cmd_top(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("⏳ Оновлюю новини…")
    await fetch_all_news()
    
    news = get_top_news(hours=12, limit=TOP_NEWS_COUNT)
    if not news:
        await update.message.reply_text("Новин поки немає. Спробуй пізніше.")
        return
    
    lines = [f"🔥 <b>Топ-{len(news)} новин</b> за 12 годин:\n"]
    for i, item in enumerate(news, 1):
        lines.append(format_news_item(item, i, show_similar=True))
    
    await update.message.reply_text("\n\n".join(lines), parse_mode="HTML",
                                    disable_web_page_preview=True)


async def cmd_digest(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("⏳ Збираю дайджест…")
    await fetch_all_news()
    
    news = get_digest_news(hours=12)
    if not news:
        await update.message.reply_text("Новин поки немає.")
        return
    
    lines = [f"📰 <b>Дайджест за 12 годин</b> ({len(news)} новин):\n"]
    for i, item in enumerate(news[:10], 1):
        lines.append(format_news_item(item, i))
    
    await update.message.reply_text("\n\n".join(lines), parse_mode="HTML",
                                    disable_web_page_preview=True)


async def cmd_summary(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🤖 Готую AI-резюме…")
    await fetch_all_news()
    
    news = get_digest_news(hours=12)
    summary = ai_summary(news)
    
    await update.message.reply_text(
        f"🤖 <b>AI-резюме дня:</b>\n\n{summary}",
        parse_mode="HTML"
    )


async def cmd_topics(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    keyboard = [[InlineKeyboardButton(topic, callback_data=f"topic:{topic}")]
                for topic in TOPICS.keys()]
    await update.message.reply_text(
        "📡 Обери тему:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def cb_topic(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    topic = query.data.split(":", 1)[1]
    
    news = get_news_by_topic(topic, hours=12, limit=5)
    if not news:
        await query.edit_message_text(f"По темі <b>{topic}</b> новин не знайдено.", parse_mode="HTML")
        return
    
    lines = [f"<b>{topic}</b> — останні новини:\n"]
    for i, item in enumerate(news, 1):
        lines.append(format_news_item(item, i))
    
    await query.edit_message_text("\n\n".join(lines), parse_mode="HTML",
                                   disable_web_page_preview=True)


async def cmd_stats(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    stats = get_stats(hours=24)
    lines = [f"📊 <b>Статистика за 24 год:</b>\n", f"Всього новин: <b>{stats['total']}</b>\n"]
    for ch, cnt in stats["by_channel"]:
        channel_map = {c["username"]: c["name"] for c in CHANNELS}
        name = channel_map.get(ch, ch)
        lines.append(f"• {name}: {cnt}")
    await update.message.reply_text("\n".join(lines), parse_mode="HTML")


async def cmd_sources(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    lines = ["📡 <b>Канали що моніторяться:</b>\n"]
    for ch in CHANNELS:
        uname = ch["username"]
        name = ch["name"]
        lines.append(f"• <a href='https://t.me/{uname}'>{name}</a>")
    await update.message.reply_text("\n".join(lines), parse_mode="HTML",
                                    disable_web_page_preview=True)


# ─── scheduled digest ────────────────────────────────────────────────────────

async def send_morning_digest(ctx: ContextTypes.DEFAULT_TYPE):
    logger.info("Sending morning digest...")
    await fetch_all_news()
    news = get_top_news(hours=12, limit=7)
    summary = ai_summary(news)
    
    text = (
        f"🌅 <b>Ранковий дайджест</b> — {datetime.now().strftime('%d.%m.%Y')}\n\n"
        f"🤖 <b>AI-резюме:</b>\n{summary}\n\n"
        f"🔥 <b>Топ новини:</b>\n"
    )
    for i, item in enumerate(news[:5], 1):
        text += f"\n{format_news_item(item, i)}\n"
    
    # broadcast to all subscribed users
    from db import sqlite3, DB_PATH
    conn = sqlite3.connect(DB_PATH)
    users = conn.execute("SELECT user_id FROM users WHERE digest_enabled=1").fetchall()
    conn.close()
    
    for (uid,) in users:
        try:
            await ctx.bot.send_message(uid, text, parse_mode="HTML",
                                       disable_web_page_preview=True)
        except Exception as e:
            logger.warning(f"Failed to send digest to {uid}: {e}")


# ─── main ───────────────────────────────────────────────────────────────────

def main():
    if not BOT_TOKEN:
        logger.error("BOT_TOKEN is not set!")
        sys.exit(1)
    logger.info(f"Starting bot with token: {BOT_TOKEN[:10]}...")
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
    
    # morning digest job
    app.job_queue.run_daily(
        send_morning_digest,
        time=datetime.now().replace(hour=DIGEST_HOUR, minute=DIGEST_MINUTE,
                                    second=0, microsecond=0).timetz()
    )
    
    logger.info("Bot started!")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
