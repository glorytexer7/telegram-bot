import os
import requests
from flask import Flask, request
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

TOKEN = os.getenv("BOT_TOKEN")
if not TOKEN:
    raise ValueError("توکن ربات در Environment Variable با نام BOT_TOKEN قرار نگرفته!")

app = Flask(__name__)

COINS = {
    "btc": "bitcoin",
    "eth": "ethereum",
    "sol": "solana",
    "bnb": "binancecoin",
    "doge": "dogecoin"
}

def get_price(symbols):
    result = []
    for sym in symbols:
        sym = sym.lower()
        if sym in COINS:
            coin_id = COINS[sym]
            try:
                r = requests.get("https://api.coingecko.com/api/v3/simple/price", params={"ids": coin_id, "vs_currencies": "usd"})
                price = r.json().get(coin_id, {}).get("usd")
                if price:
                    result.append(f"💰 {sym.upper()}: ${price:,}")
                else:
                    result.append(f"❌ {sym.upper()}: داده موجود نیست")
            except:
                result.append(f"❌ {sym.upper()}: خطا در دریافت دیتا")
        else:
            result.append(f"❌ {sym.upper()}: ارز پشتیبانی نمیشه")
    return "\n".join(result)

# فرمان‌ها
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

# ساخت Application
application = ApplicationBuilder().token(TOKEN).build()
application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("price", price))

# Webhook endpoint
@app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    update = Update.de_json(request.get_json(force=True), application.bot)
    application.update_queue.put(update)  # پردازش مستقیم پیام‌ها
    return "ok"

@app.route("/")
def home():
    return "Bot is running ✅"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
