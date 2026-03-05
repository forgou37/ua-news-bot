import requests
from config import GEMINI_API_KEY

GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent"

def ai_summary(news_items: list[dict]) -> str:
    if not news_items:
        return "Новин за цей період не знайдено."
    
    texts = "\n\n".join([
        f"[{item['channel']}]: {item['text'][:300]}"
        for item in news_items[:15]
    ])
    
    prompt = f"""Ти — редактор новин. На основі цих постів з українських ТГ-каналів напиши короткий дайджест дня (3-5 речень). 
Тільки найважливіше, без води. Мова: українська.

{texts}"""

    try:
        resp = requests.post(
            f"{GEMINI_URL}?key={GEMINI_API_KEY}",
            json={"contents": [{"parts": [{"text": prompt}]}]},
            timeout=30
        )
        resp.raise_for_status()
        return resp.json()["candidates"][0]["content"]["parts"][0]["text"]
    except Exception as e:
        return f"AI-резюме недоступне: {e}"
