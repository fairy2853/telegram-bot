from google import generativeai as genai
from functools import partial
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
)
from mindee import Client
from core import settings
from handlers import (
    handle_user_question,
    handle_file_generation,
    handle_confirmation,
    handle_photo,
    start,
)
import logging


logger = logging.getLogger(__name__)

user_photos = {}  # saving photos that user sends
user_states = {}  # saving user_info

mindee_client = Client(api_key=settings.MINDEE_API_KEY)

genai.configure(api_key=settings.GENAI_API_KEY)


# start bot
app = Application.builder().token(settings.TELEGRAM_BOT_TOKEN).build()
app.add_handler(
    CommandHandler(
        "start", partial(start, user_states=user_states, user_photos=user_photos)
    )
)
app.add_handler(
    MessageHandler(
        filters.PHOTO,
        partial(
            handle_photo,
            mindee_client=mindee_client,
            user_states=user_states,
            user_photos=user_photos,
            genai=genai
        ),
    )
)
app.add_handler(
    CallbackQueryHandler(
        partial(handle_confirmation, user_states=user_states, user_photos=user_photos),
        pattern="^confirm_",
    )
)
app.add_handler(CallbackQueryHandler(handle_file_generation, pattern="^price_"))
app.add_handler(
    MessageHandler(
        filters.TEXT & ~filters.COMMAND, partial(handle_user_question, genai=genai , user_states=user_states)
    )
)


app.run_polling()
