import os
import requests
from flask import Flask, request
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

TOKEN = os.getenv("BOT_TOKEN")
if not TOKEN:
    raise ValueError("توکن BOT_TOKEN در Environment Variable قرار نگرفته!")

app = Flask(__name__)

COINS = {
    "btc": "bitcoin",
    "eth": "ethereum",
    "sol": "solana",
    "bnb": "binancecoin",
    "doge": "dogecoin"
}

def get_price(symbols):
    prices = []
    for sym in symbols:
        sym = sym.lower()
        if sym in COINS:
            coin_id = COINS[sym]
            url = "https://api.coingecko.com/api/v3/simple/price"
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

# فرمان‌ها
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "سلام 👋\nمن ربات نمایش قیمت کریپتو هستم.\n"
        "برای دیدن قیمت‌ها بنویس:\n/price btc\nیا چند ارز همزمان: /price btc eth sol"
    )

async def price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("لطفاً حداقل یک ارز وارد کن، مثال: /price btc")
        return
    await update.message.reply_text(get_price(context.args))

# ساخت Application
app_bot = ApplicationBuilder().token(TOKEN).build()
app_bot.add_handler(CommandHandler("start", start))
app_bot.add_handler(CommandHandler("price", price))

# Webhook endpoint
@app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    update = Update.de_json(request.get_json(force=True), app_bot.bot)
    app_bot.update_queue.put(update)
    return "ok"

@app.route("/")
def home():
    return "Bot is running ✅"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
