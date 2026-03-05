import google.generativeai as genai
from config import GEMINI_API_KEY

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-1.5-flash")

def ai_summary(news_items: list[dict]) -> str:
    if not news_items:
        return "Новин за цей період не знайдено."
    
    texts = "\n\n".join([
        f"[{item['channel']}]: {item['text'][:300]}"
        for item in news_items[:15]
    ])
    
    try:
        response = model.generate_content(
            f"""Ти — редактор новин. На основі цих постів з українських ТГ-каналів напиши короткий дайджест дня (3-5 речень). 
Тільки найважливіше, без води. Мова: українська.

{texts}"""
        )
        return response.text
    except Exception as e:
        return f"AI-резюме недоступне: {e}"
