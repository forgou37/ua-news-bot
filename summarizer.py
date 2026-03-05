import anthropic
from config import ANTHROPIC_API_KEY

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

def ai_summary(news_items: list[dict]) -> str:
    if not news_items:
        return "Новин за цей період не знайдено."
    
    texts = "\n\n".join([
        f"[{item['channel']}]: {item['text'][:300]}"
        for item in news_items[:15]
    ])
    
    try:
        msg = client.messages.create(
            model="claude-haiku-4-5",
            max_tokens=600,
            messages=[{
                "role": "user",
                "content": f"""Ти — редактор новин. На основі цих постів з українських ТГ-каналів напиши короткий дайджест дня (3-5 речень). 
Тільки найважливіше, без води. Мова: українська.

{texts}"""
            }]
        )
        return msg.content[0].text
    except Exception as e:
        return f"AI-резюме недоступне: {e}"
