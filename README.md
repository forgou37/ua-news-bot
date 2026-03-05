# 🇺🇦 UA News Digest Bot

Telegram-бот що агрегує топ-10 українських новинних каналів, фільтрує по темах і робить AI-дайджест.

## Функції

- 🔥 `/top` — топ новин за 12 годин (з пріоритетом україномовних джерел)
- 📰 `/digest` — хронологічний дайджест
- 🤖 `/summary` — AI-резюме дня (Claude Haiku)
- 📡 `/topics` — фільтр по темах (Війна, Економіка, Політика, Світ...)
- 📊 `/stats` — статистика по каналах
- ℹ️ `/sources` — список джерел
- 🌅 Ранкова авторозсилка о 8:00

Під кожною топ-новиною — посилання на інші канали що писали про те саме.

## Джерела

Суспільне, Українська правда, TSN, Цензор.НЕТ, 24 Канал, УНІАН, Ліга.net, Главком, НВ, РБК-Україна

## Встановлення

```bash
git clone https://github.com/forgou37/ua-news-bot
cd ua-news-bot
python3 -m venv venv
./venv/bin/pip install -r requirements.txt
cp config.example.py config.py
# відредагуй config.py — вкажи BOT_TOKEN і ANTHROPIC_API_KEY
./venv/bin/python bot.py
```

## Стек

- Python 3.12
- python-telegram-bot v22
- BeautifulSoup4 (скрейпінг t.me/s/)
- Anthropic Claude Haiku (AI-резюме)
- SQLite
- APScheduler
