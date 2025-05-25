from telegram import Update
from telegram.ext import ContextTypes
from functools import partial


async def handle_user_question(
    update: Update, context: ContextTypes.DEFAULT_TYPE, genai
):
    user_message = update.message.text

    # Ігноруємо команди типу /start
    if user_message.startswith("/"):
        return

    try:
        model = genai.GenerativeModel("gemini-2.0-flash")
        response = model.generate_content(user_message)
        reply_text = response.text
    except Exception as e:
        reply_text = "Вибач, наразі я не можу відповісти на це питання"
        print(e)

    await update.message.reply_text(reply_text)
