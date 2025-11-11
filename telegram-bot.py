from flask import Flask, request
from telegram import Bot, Update
from telegram.ext import Dispatcher, CommandHandler, MessageHandler, Filters
import requests

# === تنظیمات اصلی ===
TOKEN = "8272494379:AAGs_PKW1gIN-mU4I72X4Vyx1Iv03f-PVqk"
bot = Bot(token=TOKEN)
app = Flask(__name__)

# === گرفتن قیمت از CoinGecko ===
def get_price(symbol):
    symbol = symbol.lower()
    url = "https://api.coingecko.com/api/v3/simple/price"
    params = {"ids": symbol, "vs_currencies": "usd"}
    response = requests.get(url, params=params).json()
    if symbol in response:
        price = response[symbol]["usd"]
        return f"💰 {symbol.capitalize()}: ${price:,}"
    else:
        return "❌ ارز مورد نظر پیدا نشد."

# === فرمان /start ===
def start(update, context):
    update.message.reply_text(
        "سلام 👋\nمن ربات نمایش قیمت ارزهای دیجیتال هستم.\n"
        "برای دیدن قیمت بنویس مثلاً:\n"
        "`/price bitcoin` یا `/price eth`",
        parse_mode="Markdown"
    )

# === فرمان /price ===
def price(update, context):
    if len(context.args) == 0:
        update.message.reply_text("🔹 لطفاً نماد ارز را وارد کن، مثل:\n/price bitcoin")
        return
    symbol = context.args[0]
    update.message.reply_text(get_price(symbol))

# === تنظیم Dispatcher ===
dispatcher = Dispatcher(bot, None, workers=0)
dispatcher.add_handler(CommandHandler("start", start))
dispatcher.add_handler(CommandHandler("price", price))

# === مسیر وب‌هوک ===
@app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    update = Update.de_json(request.get_json(), bot)
    dispatcher.process_update(update)
    return "ok"

@app.route("/", methods=["GET"])
def home():
    return "Bot is running ✅"

if __name__ == "__main__":
    app.run(port=8080)
