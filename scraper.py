import requests
from bs4 import BeautifulSoup
from datetime import datetime, timezone
import re
import logging

logger = logging.getLogger(__name__)

def scrape_channel(channel_username: str, limit: int = 15) -> list[dict]:
    """Scrape public posts from a Telegram channel via t.me/s/"""
    url = f"https://t.me/s/{channel_username}"
    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"
    }
    
    try:
        resp = requests.get(url, headers=headers, timeout=10)
        resp.raise_for_status()
    except Exception as e:
        logger.warning(f"Failed to scrape {channel_username}: {e}")
        return []

    soup = BeautifulSoup(resp.text, "html.parser")
    posts = []

    for msg in soup.select(".tgme_widget_message")[-limit:]:
        # text
        text_el = msg.select_one(".tgme_widget_message_text")
        text = text_el.get_text(" ", strip=True) if text_el else ""
        if not text or len(text) < 30:
            continue

        # time
        time_el = msg.select_one("time")
        dt = None
        if time_el and time_el.get("datetime"):
            try:
                dt = datetime.fromisoformat(time_el["datetime"].replace("Z", "+00:00"))
            except Exception:
                pass

        # link
        link_el = msg.select_one(".tgme_widget_message_date")
        link = link_el["href"] if link_el and link_el.get("href") else ""

        # views
        views_el = msg.select_one(".tgme_widget_message_views")
        views_text = views_el.get_text(strip=True) if views_el else "0"
        views = parse_views(views_text)

        posts.append({
            "text": text[:500],
            "datetime": dt,
            "link": link,
            "views": views,
            "channel": channel_username,
        })

    return posts


def parse_views(views_str: str) -> int:
    views_str = views_str.replace(" ", "").replace("\xa0", "").lower()
    try:
        if "k" in views_str:
            return int(float(views_str.replace("k", "")) * 1000)
        if "m" in views_str:
            return int(float(views_str.replace("m", "")) * 1_000_000)
        return int(re.sub(r"[^\d]", "", views_str) or 0)
    except Exception:
        return 0
