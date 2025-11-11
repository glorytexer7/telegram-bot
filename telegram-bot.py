import time
import requests
import xml.etree.ElementTree as ET
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, CallbackContext

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

# ======= توابع =======
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
                _price_cache[key] = {"price": price, "time": now}
            except Exception as e:
                result.append(f"❌ {key.upper()}: Error fetching data ({e})")
                continue

        result.append(f"💰 {key.upper()}: ${price:,.2f}")
    return "\n".join(result)

def convert_crypto(amount, from_sym, to_sym):
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

def analyze_market(symbols):
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
            except:
                result.append(f"❌ {key.upper()}: Error fetching data")
                continue

        sentiment = "Bullish 📈" if _price_cache[key].get("change", 0) >= 0 else "Bearish 📉"
        result.append(f"💡 {key.upper()} Market Analysis:\nPrice: ${price:,.2f}\nSentiment: {sentiment}")
    return "\n\n".join(result)

# ======= فرمان‌ها =======
def start(update: Update, context: CallbackContext):
    keyboard = [
        [InlineKeyboardButton("💰 Live Prices", callback_data="live_prices")],
        [InlineKeyboardButton("🧮 Convert Crypto", callback_data="convert_crypto")],
        [InlineKeyboardButton("🧠 Market Analysis", callback_data="market_analysis")],
        [InlineKeyboardButton("📰 Crypto News", callback_data="crypto_news")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    text = "👋 Hello!\nWelcome to EagleNova.\nChoose an option from below:"
    update.message.reply_text(text, reply_markup=reply_markup)

def button_handler(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    data = query.data

    if data == "live_prices":
        query.message.reply_text(get_price(list(SYMBOLS.keys())))
    elif data == "convert_crypto":
        query.message.reply_text("Send command: /convert <amount> <from_symbol> <to_symbol>\nExample: /convert 1 btc eth")
    elif data == "market_analysis":
        query.message.reply_text(analyze_market(list(SYMBOLS.keys())))
    elif data == "crypto_news":
        rss_urls = [
            "https://cryptopanic.com/news.rss",
            "https://cointelegraph.com/rss",
            "https://decrypt.co/feed"
        ]
        query.message.reply_text(get_news_rss(rss_urls))

def convert(update: Update, context: CallbackContext):
    try:
        amount = float(context.args[0])
        from_sym = context.args[1]
        to_sym = context.args[2]
        update.message.reply_text(convert_crypto(amount, from_sym, to_sym))
    except:
        update.message.reply_text("❌ Usage: /convert <amount> <from_symbol> <to_symbol>\nExample: /convert 1 btc eth")

# ======= Updater =======
updater = Updater(TOKEN, use_context=True)
dp = updater.dispatcher
dp.add_handler(CommandHandler("start", start))
dp.add_handler(CommandHandler("convert", convert))
dp.add_handler(CallbackQueryHandler(button_handler))

# ======= Polling =======
updater.start_polling()
updater.idle()
