from telegram import Update
from telegram.ext import ContextTypes


# /start – start
async def start(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    user_photos,
    user_states
):
    user_id = update.message.from_user.id
    user_photos[user_id] = {}
    user_states[user_id] = "waiting_passport"
    await update.message.reply_text(
        "👋 Привіт! Я бот, який допоможе тобі швидко оформити страховий поліс.\n\n"
        "📄 Будь ласка, надішли фото *паспорта* для початку.",
        parse_mode="Markdown",
    )
