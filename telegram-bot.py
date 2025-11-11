import time
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# ======= تنظیمات ربات =======
TOKEN = "8272494379:AAGs_PKW1gIN-mU4I72X4Vyx1Iv03f-PVqk"
WEBHOOK_URL = f"https://telegram-bot-2-ve4l.onrender.com/8272494379:AAGs_PKW1gIN-mU4I72X4Vyx1Iv03f-PVqk"  # URL سرویس Render + توکن

# ======= دیتای ارزها =======
COINS = {
    "btc": "bitcoin",
    "eth": "ethereum",
    "sol": "solana",
    "bnb": "binancecoin",
    "doge": "dogecoin"
}

# ======= کش داخلی برای جلوگیری از Rate Limit =======
_price_cache = {"data": {}, "time": 0}
CACHE_TTL = 30  # ثانیه، زمان نگهداری قیمت‌ها در کش

# ======= تابع دریافت قیمت با کش =======
def get_price(symbols):
    now = time.time()
    # استفاده از کش اگر هنوز معتبره
    if now - _price_cache["time"] < CACHE_TTL and _price_cache["data"]:
        data = _price_cache["data"]
    else:
        # درخواست یکباره برای تمام ارزها
        all_ids = ",".join(set(COINS.values()))
        try:
            r = requests.get(
                "https://api.coingecko.com/api/v3/simple/price",
                params={"ids": all_ids, "vs_currencies": "usd"},
                timeout=10
            )
        except requests.exceptions.RequestException as e:
            if _price_cache["data"]:
                data = _price_cache["data"]
            else:
                return "\n".join([f"❌ {sym.upper()}: خطای شبکه: {e}" for sym in symbols])
        else:
            if r.status_code == 200:
                data = r.json()
                _price_cache["data"] = data
                _price_cache["time"] = now
            elif r.status_code == 429:
                if _price_cache["data"]:
                    data = _price_cache["data"]
                else:
                    return "\n".join([f"❌ {sym.upper()}: CoinGecko Rate Limit (HTTP 429). لطفاً بعدا تلاش کن." for sym in symbols])
            else:
                if _price_cache["data"]:
                    data = _price_cache["data"]
                else:
                    return "\n".join([f"❌ {sym.upper()}: خطا در دریافت دیتا (HTTP {r.status_code})" for sym in symbols])

    # ساخت پیام برای ارزهای درخواست‌شده
    result = []
    for sym in symbols:
        key = sym.lower()
        if key not in COINS:
            result.append(f"❌ {sym.upper()}: ارز پشتیبانی نمیشه")
            continue
        coin_id = COINS[key]
        price = data.get(coin_id, {}).get("usd")
        if price is not None:
            result.append(f"💰 {key.upper()}: ${price:,}")
        else:
            result.append(f"❌ {key.upper()}: داده موجود نیست")
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
        port=5000,  # Render خودش PORT درست می‌کنه؛ می‌تونی os.environ.get("PORT") هم بذاری
        url_path=TOKEN,
        webhook_url=WEBHOOK_URL
    )
