from io import BytesIO
import os
from fpdf import FPDF
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton, InputFile
from google import generativeai as genai
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)
from mindee import Client, AsyncPredictResponse, product

from dotenv import load_dotenv

load_dotenv(override=True)
user_photos = {}  # saving photos that user sends
user_states = {}  # saving user_info

mindee_client = Client(api_key=os.getenv("MINDY_API_KEY"))

genai.configure(api_key=os.getenv("GENAI_API_KEY"))


# /start – start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    user_photos[user_id] = {}
    user_states[user_id] = "waiting_passport"
    await update.message.reply_text(
        "👋 Привіт! Я бот, який допоможе тобі швидко оформити страховий поліс.\n\n"
        "📄 Будь ласка, надішли фото *паспорта* для початку.",
        parse_mode="Markdown",
    )


async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    state = user_states.get(user_id)

    if not state:
        await update.message.reply_text("Натисни /start щоб розпочати.")
        return

    # load photo
    photo_file = await update.message.photo[-1].get_file()
    path = f"temp_{user_id}_{state}.jpg"
    await photo_file.download_to_drive(path)

    if state == "waiting_passport":
        user_photos[user_id]["passport"] = path
        user_states[user_id] = "waiting_car_doc"
        await update.message.reply_text(
            "✅ Дякую! Тепер надішли фото *паспорта машини*", parse_mode="Markdown"
        )

    elif state == "waiting_car_doc":
        user_photos[user_id]["car_doc"] = path
        user_states[user_id] = "ready"

        await update.message.reply_text("Отримано обидва фото. Обробляю...")

        # 1. take text from passport
        passport_path = user_photos[user_id]["passport"]
        input_doc = mindee_client.source_from_path(passport_path)
        result: AsyncPredictResponse = mindee_client.enqueue_and_parse(
            product.InternationalIdV2, input_doc
        )

        passport_data = result.document.inference.prediction
        full_name = (
            passport_data.given_names[0].value + " " + passport_data.surnames[0].value
            if passport_data.given_names and passport_data.surnames
            else "N/A"
        )
        birth_date = (
            passport_data.birth_date.value if passport_data.birth_date else "N/A"
        )
        passport_number = (
            passport_data.document_number.value
            if passport_data.document_number
            else "N/A"
        )

        # 2. mock car passport data
        car_doc_mock = {
            "Номер авто": "AA1234BB",
            "VIN": "WVWZZZ1JZXW000001",
            "Марка": "Volkswagen",
            "Модель": "Golf",
            "Рік випуску": "2019",
        }

        # result that sends to user
        result_text = (
            f"*Паспорт:*\n"
            f"- ПІБ: {full_name}\n"
            f"- Дата народження: {birth_date}\n"
            f"- Номер паспорта: {passport_number}\n\n"
            f"*Техпаспорт (мок):*\n"
            + "\n".join([f"- {k}: {v}" for k, v in car_doc_mock.items()])
        )

        context.user_data["last_result"] = result_text

        # delete parsed data
        for file in user_photos[user_id].values():
            os.remove(file)
        del user_photos[user_id]
        del user_states[user_id]

        # verify
        keyboard = [
            [
                InlineKeyboardButton("✅ Так", callback_data="confirm_yes"),
                InlineKeyboardButton("❌ Ні", callback_data="confirm_no"),
            ]
        ]
        await update.message.reply_text(
            f"{result_text}\n\nЦе вірна інформація?",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )


# verify price
async def handle_confirmation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "confirm_yes":
        price_text = (
            "Фіксована ціна страхування становить *100 USD*.\n\nВас влаштовує ця ціна?"
        )
        keyboard = [
            [
                InlineKeyboardButton("✅ Так", callback_data="price_yes"),
                InlineKeyboardButton("❌ Ні", callback_data="price_no"),
            ]
        ]
        await query.edit_message_text(
            f"✅ Дякую за підтвердження!\n\n{price_text}",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )
    elif query.data == "confirm_no":
        await query.edit_message_text(
            "Вибач але це мінімальнв ціна за генерацію страхування"
        )


# generate pdf file
async def handle_file_generation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "price_yes":
        await query.edit_message_text("Чудово! Готую страховий поліс...")

        result_text = context.user_data.get("last_result", "Дані не знайдено.")

        # Створення PDF у памʼяті
        pdf = FPDF()
        pdf.add_page()

        pdf.add_font("DejaVu", "", "fonts/DejaVuSans.ttf", uni=True)
        pdf.set_font("DejaVu", size=12)

        pdf.cell(200, 10, txt="Страховий поліс", ln=1, align="C")
        pdf.ln(10)

        for line in result_text.split("\n"):
            pdf.multi_cell(0, 10, line)

        # Зберігаємо в BytesIO
        pdf_bytes = pdf.output(dest="S").encode("latin1")
        pdf_buffer = BytesIO(pdf_bytes)
        pdf_buffer.name = "insurance_policy.pdf"

        await query.message.reply_document(
            document=InputFile(pdf_buffer, filename="insurance_policy.pdf"),
            caption="Ось ваш страховий поліс 🧾",
        )
    elif query.data == "price_no":
        await query.edit_message_text(
            "Вибач, але 100 USD — це єдина доступна ціна на страхування.\n"
            "Якщо передумаєш — просто натисни /start або звернись повторно."
        )


# replying on user questions
async def handle_user_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
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


# start bot
app = Application.builder().token(os.getenv("TELEGRAM_BOT_TOKEN")).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
app.add_handler(CallbackQueryHandler(handle_confirmation, pattern="^confirm_"))
app.add_handler(CallbackQueryHandler(handle_file_generation, pattern="^price_"))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_user_question))


app.run_polling()
