import sqlite3
from datetime import datetime, timezone, timedelta
from config import MAX_NEWS_AGE_HOURS

DB_PATH = "news.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS news (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            channel TEXT,
            text TEXT,
            link TEXT UNIQUE,
            views INTEGER DEFAULT 0,
            published_at TEXT,
            fetched_at TEXT,
            topics TEXT
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            digest_enabled INTEGER DEFAULT 1,
            digest_hour INTEGER DEFAULT 8,
            topics_filter TEXT DEFAULT '',
            created_at TEXT
        )
    """)
    conn.commit()
    conn.close()


def save_news(items: list[dict]):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    saved = 0
    for item in items:
        try:
            c.execute("""
                INSERT OR IGNORE INTO news (channel, text, link, views, published_at, fetched_at, topics)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                item["channel"],
                item["text"],
                item["link"],
                item["views"],
                item["datetime"].isoformat() if item["datetime"] else None,
                datetime.now(timezone.utc).isoformat(),
                ",".join(item.get("topics", [])),
            ))
            if c.rowcount:
                saved += 1
        except Exception:
            pass
    conn.commit()
    conn.close()
    return saved


def get_top_news(hours: int = 12, limit: int = 7) -> list[dict]:
    from config import CHANNELS, MAX_PER_CHANNEL
    priority_map = {ch["username"]: ch["priority"] for ch in CHANNELS}

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    since = (datetime.now(timezone.utc) - timedelta(hours=hours)).isoformat()
    # Беремо більше щоб потім відфільтрувати по diversity
    c.execute("""
        SELECT channel, text, link, views, published_at, topics
        FROM news
        WHERE fetched_at > ?
        ORDER BY views DESC
        LIMIT 100
    """, (since,))
    rows = c.fetchall()
    conn.close()

    all_news = [{"channel": r[0], "text": r[1], "link": r[2],
                 "views": r[3], "published_at": r[4], "topics": r[5]} for r in rows]

    # Score = views * priority_weight
    for item in all_news:
        p = priority_map.get(item["channel"], 5)
        item["score"] = (item["views"] or 0) * p

    all_news.sort(key=lambda x: x["score"], reverse=True)

    # Diversity: max MAX_PER_CHANNEL на джерело
    result = []
    per_channel = {}
    for item in all_news:
        ch = item["channel"]
        if per_channel.get(ch, 0) < MAX_PER_CHANNEL:
            result.append(item)
            per_channel[ch] = per_channel.get(ch, 0) + 1
        if len(result) >= limit:
            break

    return result


def find_similar_sources(text: str, link: str, hours: int = 12) -> list[str]:
    """Знайти інші канали що писали про ту саму тему (спрощена схожість)."""
    from config import CHANNELS
    channel_map = {ch["username"]: ch["name"] for ch in CHANNELS}

    # Беремо ключові слова з тексту (слова 4+ символів)
    words = set(w.lower() for w in text.split() if len(w) >= 4)
    if len(words) < 3:
        return []

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    since = (datetime.now(timezone.utc) - timedelta(hours=hours)).isoformat()
    c.execute("""
        SELECT channel, text, link FROM news
        WHERE fetched_at > ? AND link != ?
    """, (since, link or ""))
    rows = c.fetchall()
    conn.close()

    similar = []
    seen_channels = set()
    for (ch, other_text, other_link) in rows:
        if ch in seen_channels:
            continue
        other_words = set(w.lower() for w in other_text.split() if len(w) >= 4)
        intersection = words & other_words
        union = words | other_words
        jaccard = len(intersection) / len(union) if union else 0
        if jaccard > 0.2:  # 20%+ схожість
            name = channel_map.get(ch, ch)
            link_part = f'<a href="{other_link}">{name}</a>' if other_link else name
            similar.append(link_part)
            seen_channels.add(ch)

    return similar[:4]  # максимум 4 додаткових джерела


def get_digest_news(hours: int = 12) -> list[dict]:
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    since = (datetime.now(timezone.utc) - timedelta(hours=hours)).isoformat()
    c.execute("""
        SELECT channel, text, link, views, published_at, topics
        FROM news
        WHERE fetched_at > ?
        ORDER BY published_at DESC
        LIMIT 30
    """, (since,))
    rows = c.fetchall()
    conn.close()
    return [{"channel": r[0], "text": r[1], "link": r[2],
             "views": r[3], "published_at": r[4], "topics": r[5]} for r in rows]


def get_news_by_topic(topic_key: str, hours: int = 12, limit: int = 5) -> list[dict]:
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    since = (datetime.now(timezone.utc) - timedelta(hours=hours)).isoformat()
    c.execute("""
        SELECT channel, text, link, views, published_at, topics
        FROM news
        WHERE fetched_at > ? AND topics LIKE ?
        ORDER BY views DESC
        LIMIT ?
    """, (since, f"%{topic_key}%", limit))
    rows = c.fetchall()
    conn.close()
    return [{"channel": r[0], "text": r[1], "link": r[2],
             "views": r[3], "published_at": r[4], "topics": r[5]} for r in rows]


def get_stats(hours: int = 24) -> dict:
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    since = (datetime.now(timezone.utc) - timedelta(hours=hours)).isoformat()
    c.execute("SELECT COUNT(*) FROM news WHERE fetched_at > ?", (since,))
    total = c.fetchone()[0]
    c.execute("""
        SELECT channel, COUNT(*) as cnt FROM news
        WHERE fetched_at > ?
        GROUP BY channel ORDER BY cnt DESC
    """, (since,))
    by_channel = c.fetchall()
    conn.close()
    return {"total": total, "by_channel": by_channel}


def upsert_user(user_id: int):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        INSERT OR IGNORE INTO users (user_id, created_at)
        VALUES (?, ?)
    """, (user_id, datetime.now(timezone.utc).isoformat()))
    conn.commit()
    conn.close()
