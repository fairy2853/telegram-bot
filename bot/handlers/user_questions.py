from telegram import Update
from telegram.ext import ContextTypes
from functools import partial


async def handle_user_question(
    update: Update, context: ContextTypes.DEFAULT_TYPE, genai, user_states
):
    user_id = update.message.from_user.id
    user_message = update.message.text
    # Ігноруємо команди типу /start
    if user_message.startswith("/"):
        return

    try:
        model = genai.GenerativeModel("gemini-2.0-flash")

        prompt = (
            "Ти телеграм-бот, який допомагає користувачам оформити страховку. "
            "Відповідай коротко, ввічливо та по суті.\n\n"
            f"Користувач питає: {user_message}"
        )
        response = model.generate_content(prompt)
        reply_text = response.text

    except Exception as e:
        reply_text = "Вибач, наразі я не можу відповісти на це питання"
        print(e)

    await update.message.reply_text(reply_text)

    state = user_states.get(user_id)

    if state == "waiting_passport":
        await update.message.reply_text(
            "📷 Якщо у вас більше немає питань, будь ласка, надішліть фото *паспорта*",
            parse_mode="Markdown",
        )

    elif state == "waiting_car_doc":
        await update.message.reply_text(
            "📷 Якщо немає додаткових питань, надішліть фото *техпаспорта*",
            parse_mode="Markdown",
        )
