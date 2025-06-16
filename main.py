import os
import logging
import requests
from flask import Flask, request
from telegram import Bot, Update, InlineKeyboardButton, InlineKeyboardMarkup, InputSticker
from telegram.ext import Dispatcher, CommandHandler, MessageHandler, Filters, CallbackQueryHandler

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Init
TOKEN = os.getenv("BOT_TOKEN")
if not TOKEN:
    raise RuntimeError("BOT_TOKEN is missing!")

app = Flask(__name__)
bot = Bot(token=TOKEN)
dispatcher = Dispatcher(bot, None, use_context=True)
user_languages = {}
translation_log = []  # For stats tracking

# LibreTranslate API
API_URL = "https://libretranslate.de/translate"

def translate(text, target_lang="bn"):
    try:
        res = requests.post(API_URL, data={
            "q": text,
            "source": "auto",
            "target": target_lang,
            "format": "text"
        })
        return res.json().get("translatedText", "❌ Translation failed")
    except Exception as e:
        logger.error(f"Translation error: {e}")
        return "❌ Translation failed"

# Command: /start
def start(update, context):
    buttons = [
        ["af", "ar", "az", "bn"],
        ["bg", "zh", "cs", "da"],
        ["nl", "en", "et", "fi"],
        ["fr", "de", "el", "gu"],
        ["he", "hi", "hu", "id"],
        ["ga", "it", "ja", "kn"],
        ["ko", "fa", "pl", "pt"],
        ["pa", "ro", "ru", "sk"],
        ["es", "sv", "ta", "te"],
        ["th", "tr", "uk", "ur"],
        ["vi", "ms", "ml", "mr"]
    ]
    keyboard = [
        [InlineKeyboardButton(code.upper(), callback_data=code) for code in row]
        for row in buttons
    ]
    update.message.reply_sticker("CAACAgUAAxkBAAEFNB1lkiKZkoKKyOd8rITOl2QzFVHKegACewIAAvkN0VdDdEqCy05Cdy8E")
    update.message.reply_text("👋 Welcome to BD Translate Bot!\nChoose your target language:", reply_markup=InlineKeyboardMarkup(keyboard))

# Handle language selection
def handle_buttons(update, context):
    query = update.callback_query
    user_languages[query.from_user.id] = query.data
    query.edit_message_text(text=f"✅ Language set to: {query.data.upper()}")

# Translate messages
def handle_message(update, context):
    user_id = update.message.from_user.id
    text = update.message.text
    target_lang = user_languages.get(user_id, "bn")
    translated = translate(text, target_lang)
    update.message.reply_text(f"🔁 {translated}")

    # Track stats
    translation_log.append({
        "user": user_id,
        "from": text,
        "to": translated,
        "target_lang": target_lang
    })

# Command: /stats
def stats(update, context):
    user_id = update.message.from_user.id
    user_logs = [log for log in translation_log if log["user"] == user_id]
    count = len(user_logs)
    langs = list(set(log["target_lang"] for log in user_logs))
    update.message.reply_text(f"📊 You've translated {count} message(s).\n🌐 Languages used: {', '.join(langs).upper()}")

# Register handlers
dispatcher.add_handler(CommandHandler("start", start))
dispatcher.add_handler(CommandHandler("stats", stats))
dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))
dispatcher.add_handler(CallbackQueryHandler(handle_buttons))

# Webhook
@app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    update = Update.de_json(request.get_json(force=True), bot)
    dispatcher.process_update(update)
    return "OK", 200

@app.route("/", methods=["GET"])
def index():
    return "✅ BD Translate Bot is live!", 200

if __name__ == "__main__":
    PORT = int(os.environ.get("PORT", 5000))
    logger.info("Starting Flask server...")
    app.run(host="0.0.0.0", port=PORT)