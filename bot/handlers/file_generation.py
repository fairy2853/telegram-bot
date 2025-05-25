from telegram import Update, InputFile
from telegram.ext import ContextTypes
from io import BytesIO
from fpdf import FPDF


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
