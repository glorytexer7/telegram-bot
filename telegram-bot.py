import os
import requests
from telegram import Update
from telegram.ext import Updater, CommandHandler, CallbackContext

# === دریافت توکن از Environment Variable ===
TOKEN = os.getenv("BOT_TOKEN")
if not TOKEN:
    raise ValueError("توکن ربات در Environment Variable با نام BOT_TOKEN قرار نگرفته!")

# === ارزهای پشتیبانی شده ===
COINS = {
    "btc": "bitcoin",
    "eth": "ethereum",
    "sol": "solana",
    "bnb": "binancecoin",
    "doge": "dogecoin"
}

# === تابع گرفتن قیمت از CoinGecko ===
def get_price(symbols):
    prices = []
    for sym in symbols:
        sym = sym.lower()
        if sym in COINS:
            coin_id = COINS[sym]
            url = f"https://api.coingecko.com/api/v3/simple/price"
            params = {"ids": coin_id, "vs_currencies": "usd"}
            response = requests.get(url, params=params).json()
            price = response.get(coin_id, {}).get("usd")
            if price is not None:
                prices.append(f"💰 {sym.upper()}: ${price:,}")
            else:
                prices.append(f"❌ {sym.upper()}: داده موجود نیست")
        else:
            prices.append(f"❌ {sym.upper()}: ارز پشتیبانی نمیشه")
    return "\n".join(prices)

# === فرمان /start ===
def start(update: Update, context: CallbackContext):
    update.message.reply_text(
        "سلام 👋\nمن ربات نمایش قیمت ارزهای دیجیتال هستم.\n\n"
        "برای دیدن قیمت‌ها بنویس:\n"
        "/price btc\nیا چند ارز همزمان:\n/price btc eth sol"
    )

# === فرمان /price ===
def price(update: Update, context: CallbackContext):
    if not context.args:
        update.message.reply_text(
            "لطفاً حداقل یک ارز وارد کن، مثال:\n/price btc"
        )
        return
    message = get_price(context.args)
    update.message.reply_text(message)

# === ساخت Updater و Dispatcher ===
updater = Updater(TOKEN, use_context=True)
dp = updater.dispatcher

dp.add_handler(CommandHandler("start", start))
dp.add_handler(CommandHandler("price", price))

# === اجرای ربات ===
print("ربات کریپتویی شما شروع شد 🚀")
updater.start_polling()
updater.idle()
