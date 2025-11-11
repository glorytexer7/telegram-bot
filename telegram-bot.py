import time
import requests
import xml.etree.ElementTree as ET
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes

# ======= تنظیمات ربات =======
TOKEN = "8272494379:AAGs_PKW1gIN-mU4I72X4Vyx1Iv03f-PVqk"
WEBHOOK_URL = f"https://telegram-bot-2-ve4l.onrender.com/8272494379:AAGs_PKW1gIN-mU4I72X4Vyx1Iv03f-PVqk"

# ======= API CryptoCompare =======
API_KEY = "e4c4036f48ea8bca9ff5d844dfb7f8fc0a7610d58c8312be1ddca692afaee82a"
HEADERS = {"authorization": f"Apikey {API_KEY}"}

# ======= نگاشت نمادها =======
SYMBOLS = {
    "btc": "BTC", "eth": "ETH", "sol": "SOL", "bnb": "BNB",
    "doge": "DOGE", "ada": "ADA", "xrp": "XRP", "matic": "MATIC",
    "ltc": "LTC", "trx": "TRX", "ton": "TON"
}

# ======= کش داخلی =======
_price_cache = {}
_news_cache = {}
CACHE_TTL_PRICE = 30
CACHE_TTL_NEWS = 600

# ======= توابع کمکی =======
def get_price(symbols):
    now = time.time()
    result = []
    for sym in symbols:
        key = sym.lower()
        if key not in SYMBOLS:
            result.append(f"❌ {key.upper()}: Not supported")
            continue

        if key in _price_cache and now - _price_cache[key]["time"] < CACHE_TTL_PRICE:
            price = _price_cache[key]["price"]
        else:
            url = "https://min-api.cryptocompare.com/data/pricemultifull"
            params = {"fsyms": SYMBOLS[key], "tsyms": "USD"}
            try:
                r = requests.get(url, headers=HEADERS, params=params, timeout=5)
                r.raise_for_status()
                data = r.json()["RAW"][SYMBOLS[key]]["USD"]
                price = data["PRICE"]
                change = data.get("CHANGEPCT24HOUR", 0)
                _price_cache[key] = {"price": price, "change": change, "time": now}
            except Exception as e:
                result.append(f"❌ {key.upper()}: Error fetching data ({e})")
                continue

        result.append(f"💰 {key.upper()}: ${price:,.2f}")
    return "\n".join(result)

def convert_crypto(amount, from_sym, to_sym="USDT"):
    prices = get_price([from_sym, to_sym]).split("\n")
    try:
        from_price = float(prices[0].split("$")[1].replace(",", ""))
        to_price = float(prices[1].split("$")[1].replace(",", ""))
        converted = (amount * from_price) / to_price
        return f"🔄 {amount} {from_sym.upper()} ≈ {converted:.6f} {to_sym.upper()}"
    except:
        return "❌ Error converting currencies."

def get_news_rss(urls):
    now = time.time()
    if "time" in _news_cache and now - _news_cache["time"] < CACHE_TTL_NEWS:
        return _news_cache["data"]

    news_items = []
    for url in urls:
        try:
            r = requests.get(url, timeout=5)
            r.raise_for_status()
            root = ET.fromstring(r.content)
            for item in root.findall('.//item')[:3]:
                title = item.find('title').text
                link = item.find('link').text
                news_items.append(f"📰 {title}\n🔗 {link}")
        except:
            continue

    _news_cache["time"] = now
    _news_cache["data"] = "\n\n".join(news_items)
    return _news_cache["data"] if news_items else "❌ No news available."

def analyze_market(symbol):
    now = time.time()
    key = symbol.lower()
    if key not in SYMBOLS:
        return f"❌ {key.upper()}: Not supported"

    if key in _price_cache and now - _price_cache[key]["time"] < CACHE_TTL_PRICE:
        price = _price_cache[key]["price"]
        change = _price_cache[key].get("change", 0)
    else:
        url = "https://min-api.cryptocompare.com/data/pricemultifull"
        params = {"fsyms": SYMBOLS[key], "tsyms": "USD"}
        try:
            r = requests.get(url, headers=HEADERS, params=params, timeout=5)
            r.raise_for_status()
            data = r.json()["RAW"][SYMBOLS[key]]["USD"]
            price = data["PRICE"]
            change = data.get("CHANGEPCT24HOUR", 0)
            _price_cache[key] = {"price": price, "change": change, "time": now}
        except:
            return f"❌ {key.upper()}: Error fetching data"

    sentiment = "Bullish 📈" if change >= 0 else "Bearish 📉"
    # حمایت/مقاومت ساده (میانگین ±1%)
    support = price * 0.99
    resistance = price * 1.01
    return (
        f"💡 {key.upper()} Market Analysis:\n"
        f"Price: ${price:,.2f}\n"
        f"24h Change: {change:.2f}% ({sentiment})\n"
        f"Support: ${support:,.2f}\n"
        f"Resistance: ${resistance:,.2f}\n"
        f"Recommendation: {'Buy zone' if price <= support else 'Sell zone' if price >= resistance else 'Hold'}"
    )

# ======= فرمان‌ها =======
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("💰 Live Prices", callback_data="live_prices")],
        [InlineKeyboardButton("🔁 Convert Crypto", callback_data="convert_crypto")],
        [InlineKeyboardButton("📰 Crypto News", callback_data="crypto_news")],
        [InlineKeyboardButton("🤖 AI Market Analysis", callback_data="market_analysis")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    text = "👋 Hello!\nWelcome to EagleNova.\nChoose an option from below:"
    await update.message.reply_text(text, reply_markup=reply_markup)

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "live_prices":
        await query.message.reply_text(get_price(list(SYMBOLS.keys())))
    elif data == "convert_crypto":
        await query.message.reply_text("Send command: /convert <amount> <from_symbol> <to_symbol>\nExample: /convert 1 btc usdt")
    elif data == "market_analysis":
        # مرحله انتخاب ارز
        keyboard = [[InlineKeyboardButton(sym.upper(), callback_data=f"analyze_{sym}")] for sym in SYMBOLS]
        await query.message.reply_text("Select a crypto to analyze:", reply_markup=InlineKeyboardMarkup(keyboard))
    elif data == "crypto_news":
        rss_urls = [
            "https://cryptopanic.com/news.rss",
            "https://cointelegraph.com/rss",
            "https://decrypt.co/feed"
        ]
        await query.message.reply_text(get_news_rss(rss_urls))
    elif data.startswith("analyze_"):
        sym = data.replace("analyze_", "")
        await query.message.reply_text(analyze_market(sym))

async def convert(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        amount = float(context.args[0])
        from_sym = context.args[1]
        to_sym = context.args[2] if len(context.args) > 2 else "USDT"
        await update.message.reply_text(convert_crypto(amount, from_sym, to_sym))
    except:
        await update.message.reply_text("❌ Usage: /convert <amount> <from_symbol> <to_symbol>\nExample: /convert 1 btc usdt")

# ======= ساخت Application =======
application = ApplicationBuilder().token(TOKEN).build()
application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("convert", convert))
application.add_handler(CallbackQueryHandler(button_handler))

# ======= اجرای Webhook =======
if __name__ == "__main__":
    application.run_webhook(
        listen="0.0.0.0",
        port=5000,
        url_path=TOKEN,
        webhook_url=WEBHOOK_URL
    )
