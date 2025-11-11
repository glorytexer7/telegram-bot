import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# ======= تنظیمات ربات =======
TOKEN = "8272494379:AAGs_PKW1gIN-mU4I72X4Vyx1Iv03f-PVqk"
WEBHOOK_URL = f"https://telegram-bot-2-ve4l.onrender.com/8272494379:AAGs_PKW1gIN-mU4I72X4Vyx1Iv03f-PVqk"

# ======= نگاشت نمادهای ساده به Binance =======
BINANCE_SYMBOLS = {
    "btc": "BTCUSDT",
    "eth": "ETHUSDT",
    "sol": "SOLUSDT",
    "bnb": "BNBUSDT",
    "doge": "DOGEUSDT"
}

# ======= کش ساده برای کاهش درخواست‌ها =======
_price_cache = {}
CACHE_TTL = 10  # ثانیه، می‌تونی بیشتر هم بذاری

def get_price(symbols):
    import time
    now = time.time()
    result = []
    for sym in symbols:
        key = sym.lower()
        if key not in BINANCE_SYMBOLS:
            result.append(f"❌ {key.upper()}: ارز پشتیبانی نمیشه")
            continue

        # بررسی کش
        if key in _price_cache and now - _price_cache[key]["time"] < CACHE_TTL:
            price = _price_cache[key]["price"]
        else:
            url = f"https://api.binance.com/api/v3/ticker/price?symbol={BINANCE_SYMBOLS[key]}"
            try:
                r = requests.get(url, timeout=5)
                r.raise_for_status()
                data = r.json()
                price = float(data["price"])
                _price_cache[key] = {"price": price, "time": now}
            except:
                result.append(f"❌ {key.upper()}: خطا در دریافت دیتا")
                continue

        result.append(f"💰 {key.upper()}: ${price:,.2f}")
    return "\n".join(result)

# ======= فرمان‌ها =======
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "سلام 👋\nمن ربات قیمت کریپتو هستم.\n"
        "برای دیدن قیمت‌ها بنویس:\n/price btc\nیا چند ارز همزمان:\n/price btc eth sol"
    )

async def price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("لطفاً حداقل یک ارز وارد کن، مثال: /price btc")
        return
    await update.message.reply_text(get_price(context.args))

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
