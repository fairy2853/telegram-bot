import os
from functools import partial
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from mindee import AsyncPredictResponse, product
from telegram.ext import ContextTypes
from PIL import Image
import json


async def handle_photo(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    mindee_client,
    user_states: dict,
    user_photos: dict,
    genai,
):
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
        try:
            result: AsyncPredictResponse = mindee_client.enqueue_and_parse(
                product.InternationalIdV2, input_doc
            )
        except Exception as e:
            error_message = str(e).lower()
            if (
                "quota" in error_message
                or "limit" in error_message
                or "too many requests" in error_message
            ):
                await update.message.reply_text(
                    "⛔ Сервіс розпізнавання тимчасово недоступний (перевищено ліміт). Спробуйте пізніше."
                )
            else:
                await update.message.reply_text(
                    f"⚠️ Сталася помилка при обробці документа:\n{e}"
                )
                return

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

        img = Image.open(path)

        model = genai.GenerativeModel("gemini-2.0-flash")

        # Запит
        response = model.generate_content(
            [
                img,
                "Витягни дані з цього тех паспорту та поверни як Python словник. Поля: registration_date, date_of_first_registration, registration_number",
            ]
        )
        clean_response = response.text.replace("```python", "").replace("```", "")

        try:
            car_data_dict = json.loads(clean_response)

        except Exception as e:
            user_states[user_id] = "waiting_car_doc"

            await update.message.reply_text(
                "⚠️ Не вдалося розпізнати всі необхідні дані з техпаспорту. "
                "Будь ласка, надішліть фото ще раз, переконавшись що документ чіткий та всі дані видно."
            )
            return

        required_fields = [
            "registration_date",
            "date_of_first_registration",
            "registration_number",
        ]
        print(car_data_dict)
        if not all(field in car_data_dict for field in required_fields):
            user_states[user_id] = "waiting_car_doc"

            await update.message.reply_text(
                "⚠️ Не вдалося розпізнати всі необхідні дані з техпаспорту. "
                "Будь ласка, надішліть фото ще раз, переконавшись що документ чіткий та всі дані видно."
            )
            return

        img.close()
        # result that sends to user
        result_text = (
            f"*Паспорт:*\n"
            f"- ПІБ: {full_name}\n"
            f"- Дата народження: {birth_date}\n"
            f"- Номер паспорта: {passport_number}\n\n"
            f"*Техпаспорт:*\n"
            f"Дата реєстрації: {car_data_dict['registration_date']}\n"
            f"Рік випуску: {car_data_dict['date_of_first_registration']}\n"
            f"Реєстраційний номер: {car_data_dict['registration_number']}\n"
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
