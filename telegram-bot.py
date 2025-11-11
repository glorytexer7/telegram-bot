from flask import Flask, request
from telegram import Bot, Update
from telegram.ext import Dispatcher, CommandHandler, MessageHandler, Filters

TOKEN = "7778661471:AAFpJxmN7_tmu4UDZEZnvqnm2m3dX_4dkXg"
bot = Bot(token=TOKEN)
app = Flask(__name__)

@app.route("/")
def home():
    return "Bot is running ✅"

@app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    update = Update.de_json(request.get_json(), bot)
    dispatcher.process_update(update)
    return "ok"

# تنظیم هندلرها
def start(update, context):
    update.message.reply_text("سلام! من آنلاینم 😄")

dispatcher = Dispatcher(bot, None, workers=0)
dispatcher.add_handler(CommandHandler("start", start))

if __name__ == "__main__":
    app.run(port=8080)

import requests

url = f"https://api.telegram.org/bot{TOKEN}/setWebhook?url=https://my-telegram-bot.onrender.com/{TOKEN}"
print(requests.get(url).json())
