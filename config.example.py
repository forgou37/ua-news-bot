BOT_TOKEN = "your_telegram_bot_token"
ANTHROPIC_API_KEY = "your_anthropic_api_key"

CHANNELS = [
    {"name": "Суспільне Новини",    "username": "suspilne_news",       "priority": 10},
    {"name": "Українська правда",   "username": "ukrainskaya_pravda",  "priority": 10},
    {"name": "TSN",                 "username": "tsnnews",             "priority": 9},
    {"name": "Цензор.НЕТ",         "username": "censor_ua",           "priority": 9},
    {"name": "24 Канал",            "username": "channel24ua",         "priority": 8},
    {"name": "УНІАН",               "username": "unian_ua",            "priority": 7},
    {"name": "Ліга.net",            "username": "liga_net_news",       "priority": 7},
    {"name": "Главком",             "username": "glavcom_ua",          "priority": 6},
    {"name": "НВ",                  "username": "nv_ua",               "priority": 5},
    {"name": "РБК-Україна",         "username": "rbc_ukraine",         "priority": 3},
]

MAX_PER_CHANNEL = 2

TOPICS = {
    "⚔️ Війна":       ["обстріл", "атака", "армія", "фронт", "зсу", "ворог", "ракет", "дрон", "загибл", "бойов"],
    "💰 Економіка":   ["гривн", "долар", "бюджет", "ввп", "інфляц", "банк", "кредит", "економ", "мвф"],
    "🏛️ Політика":    ["верховна рада", "зеленськ", "президент", "уряд", "кабмін", "закон", "депутат"],
    "🌍 Світ":        ["сша", "європ", "нато", "оон", "байден", "трамп", "путін", "санкц"],
    "⚡ Енергетика":  ["світло", "відключ", "укренерго", "генератор", "газ", "нафт", "енергетик"],
    "🏥 Суспільство": ["медицин", "охорон", "освіт", "пенсі", "соціальн", "гуманітарн"],
}

DIGEST_HOUR = 8
DIGEST_MINUTE = 0
MAX_NEWS_AGE_HOURS = 12
TOP_NEWS_COUNT = 7
