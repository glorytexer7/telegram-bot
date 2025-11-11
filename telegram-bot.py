
import time
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# ======= تنظیمات ربات =======
TOKEN = "8272494379:AAGs_PKW1gIN-mU4I72X4Vyx1Iv03f-PVqk"
WEBHOOK_URL = f"https://telegram-bot-2-ve4l.onrender.com/8272494379:AAGs_PKW1gIN-mU4I72X4Vyx1Iv03f-PVqk"

# ======= API CryptoCompare =======
API_KEY = "e4c4036f48ea8bca9ff5d844dfb7f8fc0a7610d58c8312be1ddca692afaee82a"
HEADERS = {"authorization": f"Apikey {API_KEY}"}

# ======= نگاشت نمادها =======
SYMBOLS = {
    "btc": "BTC",
    "eth": "ETH",
    "sol": "SOL",
    "bnb": "BNB",
    "doge": "DOGE",
    "ada": "ADA",
    "xrp": "XRP",
    "matic": "MATIC",
    "ltc": "LTC",
    "trx": "TRX",
    "ton": "TON",
    "shib": "SHIB",
    "pepe": "PEPE"
}

# ======= کش داخلی =======
_price_cache = {}
CACHE_TTL = 30  # ثانیه

# ======= تابع دریافت قیمت و درصد تغییر 24 ساعت =======
def get_price(symbols):
    now = time.time()
    result = []

    for sym in symbols:
        key = sym.lower()
        if key not in SYMBOLS:
            result.append(f"❌ {key.upper()}: ارز پشتیبانی نمیشه")
            continue

        # استفاده از کش
        if key in _price_cache and now - _price_cache[key]["time"] < CACHE_TTL:
            price = _price_cache[key]["price"]
            change = _price_cache[key]["change"]
        else:
            url = f"https://min-api.cryptocompare.com/data/pricemultifull"
            params = {"fsyms": SYMBOLS[key], "tsyms": "USD"}
            try:
                r = requests.get(url, headers=HEADERS, params=params, timeout=5)
                r.raise_for_status()
                data = r.json()["RAW"][SYMBOLS[key]]["USD"]
                price = data["PRICE"]
                change = data["CHANGEPCT24HOUR"]
                _price_cache[key] = {"price": price, "change": change, "time": now}
            except Exception as e:
                result.append(f"❌ {key.upper()}: خطا در دریافت دیتا ({e})")
                continue

        arrow = "🔺" if change >= 0 else "🔻"
        result.append(f"💰 {key.upper()}: ${price:,.2f} {arrow} {change:.2f}%")

    return "\n".join(result)

# ======= فرمان‌ها =======
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
     "Hello 👋"
     "Welcome To EagleNova."
     "To see prices, send /price btc."
     "If you just send /price, all currencies will be displayed."
    )

async def price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # اگر کاربر هیچ ارزی نفرستاد، همه ارزها رو نمایش بده
    symbols_to_show = context.args if context.args else list(SYMBOLS.keys())
    await update.message.reply_text(get_price(symbols_to_show))

# ======= ساخت Application =======
application = ApplicationBuilder().token(TOKEN).build()
application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("price", price))

# ======= اجرای Webhook =======
if __name__ == "__main__":
    application.run_webhook(
        listen="0.0.0.0",
        port=5000,
        url_path=TOKEN,
        webhook_url=WEBHOOK_URL
    )


