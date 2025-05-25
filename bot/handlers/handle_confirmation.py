from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes


async def handle_confirmation(update: Update, context: ContextTypes.DEFAULT_TYPE , user_states, user_photos):
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id

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
        # Скидаємо стан користувача
        user_states[user_id] = "waiting_passport"
        user_photos[user_id] = {}

        await query.edit_message_text(
            "🚫 Добре, давай спробуємо ще раз.\n\nБудь ласка, надішли фото *паспорта*", parse_mode="Markdown"
        )
