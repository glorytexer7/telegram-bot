import requests
import time
import math
import xml.etree.ElementTree as ET
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes

# ============================
# 🔧 تنظیمات اصلی
# ============================
TOKEN = "8272494379:AAGs_PKW1gIN-mU4I72X4Vyx1Iv03f-PVqk"
WEBHOOK_URL = f"https://telegram-bot-2-ve4l.onrender.com/8272494379:AAGs_PKW1gIN-mU4I72X4Vyx1Iv03f-PVqk"

SYMBOLS = {
    "btc": "BTC","eth": "ETH","bnb": "BNB","sol": "SOL","xrp": "XRP",
    "doge": "DOGE","ada": "ADA","trx": "TRX","avax": "AVAX","dot": "DOT",
    "matic": "MATIC","link": "LINK","ton": "TON","ltc": "LTC","uni": "UNI","etc": "ETC"
}

HEADERS = {"User-Agent": "EagleNovaBot/1.0"}
CACHE_TTL_PRICE = 60  # 1 min
_price_cache = {}

# ============================
# 💰 دریافت قیمت زنده از CryptoCompare
# ============================
def get_price(symbol):
    now = time.time()
    sym = symbol.lower()
    if sym in _price_cache and now - _price_cache[sym]["time"] < CACHE_TTL_PRICE:
        return _price_cache[sym]

    url = "https://min-api.cryptocompare.com/data/pricemultifull"
    params = {"fsyms": SYMBOLS[sym], "tsyms": "USD"}
    try:
        r = requests.get(url, headers=HEADERS, params=params, timeout=8)
        r.raise_for_status()
        data = r.json()["RAW"][SYMBOLS[sym]]["USD"]
        price = data["PRICE"]
        change = data["CHANGEPCT24HOUR"]
        _price_cache[sym] = {"price": price, "change": change, "time": now}
        return _price_cache[sym]
    except:
        return None

# ============================
# 📈 سطوح حمایت و مقاومت با دقت مناسب
# ============================
def nice_round_level(price, direction="down"):
    if price >= 1000: step = 100
    elif price >= 100: step = 10
    elif price >= 10: step = 1
    elif price >= 1: step = 0.1
    elif price >= 0.01: step = 0.001
    else: step = 0.000001

    if direction == "down":
        lvl = (price // step) * step
    else:
        lvl = ((price // step) + 1) * step

    decimals = max(0, -int(round(math.log10(step)))) if step < 1 else 0
    return round(lvl, decimals)

# ============================
# 🧠 تحلیل بازار هوشمند (AI-like)
# ============================
POS_WORDS = ["approve","bull","rally","surge","gain","up","record","adoption"]
NEG_WORDS = ["sell","bear","drop","decline","dump","down","crash","halt"]

def score_headlines_sentiment(headlines):
    score = 0
    for h in headlines:
        text = h.lower()
        for w in POS_WORDS: 
            if w in text: score += 1
        for w in NEG_WORDS: 
            if w in text: score -= 1
    return score

def analyze_market_ai(symbol):
    sym = symbol.lower()
    if sym not in SYMBOLS:
        return f"❌ {sym.upper()} not supported."

    data = get_price(sym)
    if not data:
        return f"❌ {sym.upper()}: Error fetching live data."

    price = data["price"]
    change = data["change"]
    abs_change = abs(change)

    # Momentum
    if abs_change >= 5: momentum = "Strong"
    elif abs_change >= 1.5: momentum = "Moderate"
    else: momentum = "Mild"

    # Trend
    trend = "uptrend" if change > 0 else ("downtrend" if change < 0 else "sideways")

    # Support / Resistance
    sup1 = nice_round_level(price * 0.99, "down")
    sup2 = nice_round_level(price * 0.985, "down")
    res1 = nice_round_level(price * 1.01, "up")
    res2 = nice_round_level(price * 1.02, "up")

    # News
    rss_urls = [
        "https://cryptopanic.com/news.rss",
        "https://cointelegraph.com/rss",
        "https://decrypt.co/feed",
    ]
    headlines = []
    for url in rss_urls:
        try:
            r = requests.get(url, timeout=5)
            r.raise_for_status()
            root = ET.fromstring(r.content)
            for item in root.findall(".//item"):
                title = item.find("title").text or ""
                link = item.find("link").text or ""
                if SYMBOLS[sym] in title.upper():
                    headlines.append(f"{title} ({link})")
        except:
            continue
    if not headlines:
        headlines = ["No direct news found, using general market data."]

    sentiment_score = score_headlines_sentiment(headlines)
    total_signal = (1 if change > 0 else -1 if change < 0 else 0) * 0.7 + \
                   (1 if sentiment_score > 0 else -1 if sentiment_score < 0 else 0) * 0.3

    if total_signal > 0.4: overall = "Bullish"
    elif total_signal < -0.4: overall = "Bearish"
    else: overall = "Neutral / Mixed"

    message = (
        f"🔍 *{SYMBOLS[sym]} Market Analysis*\n\n"
        f"💰 Price: `${price:,.6f}` ({change:+.2f}% 24h)\n"
        f"📊 Trend: {trend} ({momentum} momentum)\n"
        f"📈 Overall: *{overall}*\n\n"
        f"⚙️ Key Levels:\n"
        f"- Support: {sup2:,}, {sup1:,}\n"
        f"- Resistance: {res1:,}, {res2:,}\n\n"
        f"📰 Top News:\n"
        + "\n".join([f"- {h}" for h in headlines[:3]]) +
        f"\n\n💡 Analysis Explanation:\n"
        f"- Price is showing {trend} with {momentum} momentum.\n"
        f"- Supports and resistances are calculated for key levels.\n"
        f"- Market sentiment from news considered.\n"
        f"_Note: Not financial advice._*"
    )
    return message

# ============================
# 🔁 تبدیل ارز به ارز دیگر
# ============================
def convert_currency(amount, from_sym, to_sym):
    from_data = get_price(from_sym)
    to_data = get_price(to_sym)
    if not from_data or not to_data: return None
    return amount * from_data["price"] / to_data["price"]

# ============================
# 🤖 دستورات و دکمه‌ها
# ============================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("💰 Live Prices", callback_data="prices")],
        [InlineKeyboardButton("🔁 Convert Crypto", callback_data="convert")],
        [InlineKeyboardButton("📰 Crypto News", callback_data="news")],
        [InlineKeyboardButton("🤖 AI Market Analysis", callback_data="analysis")]
    ]
    text = (
        "👋 *Welcome to EagleNova Crypto Bot!*\n\n"
        "I can help you with:\n"
        "💰 Live cryptocurrency prices\n"
        "🔁 Converting crypto to other coins\n"
        "📰 Latest crypto news\n"
        "🤖 Smart market analysis with AI insights\n\n"
        "Choose an option below:"
    )
    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "prices":
        lines = []
        for k in SYMBOLS.keys():
            d = get_price(k)
            if d:
                lines.append(f"{SYMBOLS[k]}: ${d['price']:,.6f} ({d['change']:+.2f}%)")
        msg = "💰 *Live Prices:*\n" + "\n".join(lines)
        await query.message.reply_text(msg, parse_mode="Markdown")

    elif data == "convert":
        await query.message.reply_text("Use: `/convert 1 btc eth`", parse_mode="Markdown")

    elif data == "news":
        urls = ["https://cointelegraph.com/rss", "https://decrypt.co/feed"]
        news_items = []
        for url in urls:
            try:
                r = requests.get(url, timeout=5)
                r.raise_for_status()
                root = ET.fromstring(r.content)
                for item in root.findall(".//item")[:2]:
                    title = item.find("title").text
                    link = item.find("link").text
                    news_items.append(f"- {title} ({link})")
            except:
                continue
        msg = "📰 *Top Crypto News:*/n" + "\n".join(news_items[:6])
        await query.message.reply_text(msg, parse_mode="Markdown")

    elif data == "analysis":
        keys = list(SYMBOLS.keys())
        keyboard = []
        for i in range(0, len(keys), 2):
            row = [InlineKeyboardButton(keys[i].upper(), callback_data=f"analyze_{keys[i]}")]
            if i+1 < len(keys):
                row.append(InlineKeyboardButton(keys[i+1].upper(), callback_data=f"analyze_{keys[i+1]}"))
            keyboard.append(row)
        await query.message.reply_text("Select a symbol to analyze:", reply_markup=InlineKeyboardMarkup(keyboard))

    elif data.startswith("analyze_"):
        sym = data.replace("analyze_", "")
        msg = analyze_market_ai(sym)
        await query.message.reply_text(msg, parse_mode="Markdown")

# ============================
# تبدیل ارز بین هر دو ارز
# ============================
async def convert_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        amount = float(context.args[0])
        from_sym = context.args[1].lower()
        to_sym = context.args[2].lower()
        result = convert_currency(amount, from_sym, to_sym)
        if result:
            await update.message.reply_text(f"{amount} {from_sym.upper()} ≈ {result:,.6f} {to_sym.upper()}")
        else:
            await update.message.reply_text("❌ Error converting.")
    except:
        await update.message.reply_text("Use: `/convert 1 btc eth`", parse_mode="Markdown")

# ============================
# 🚀 اجرای ربات
# ============================
if __name__ == "__main__":
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("convert", convert_command))
    app.add_handler(CallbackQueryHandler(button))
    app.run_webhook(
        listen="0.0.0.0",
        port=5000,
        url_path=TOKEN,
        webhook_url=WEBHOOK_URL
    )
