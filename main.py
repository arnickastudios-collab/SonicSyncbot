import logging
from telegram import Update
from telegram.ext import (
    Application, CommandHandler, MessageHandler, filters,
    ConversationHandler, ContextTypes
)
from config import TELEGRAM_TOKEN
import database as db
import utils
import threading
import webapp

# Enable logging
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                    level=logging.INFO)
logger = logging.getLogger(__name__)

# Global voice setting
voice_enabled = {}  # user_id: bool

# States for conversation
NAME, CITY = range(2)

async def voice_toggle(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Toggle voice responses on/off"""
    user_id = update.effective_user.id
    current = voice_enabled.get(user_id, False)
    voice_enabled[user_id] = not current
    status = "enabled" if not current else "disabled"
    await update.message.reply_text(f"Voice responses {status}!")
    return ConversationHandler.END

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.effective_user
    existing = db.get_user(user.id)
    if existing:
        name, city = existing
        greeting = utils.generate_greeting(name, city)
        await update.message.reply_text(f"Welcome back, {name}!\n{greeting}")
        return ConversationHandler.END
    else:
        await update.message.reply_text("Hi! I'm Sonic. What's your name?")
        return NAME

async def get_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['name'] = update.message.text
    await update.message.reply_text(f"Nice to meet you, {context.user_data['name']}! Which city are you from?")
    return CITY

async def get_city(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    name = context.user_data['name']
    city = update.message.text
    user_id = update.effective_user.id

    db.save_user(user_id, name, city)
    greeting = utils.generate_greeting(name, city)
    await update.message.reply_text(greeting)
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Okay, see you later!")
    return ConversationHandler.END

async def time_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Tell current time"""
    import datetime
    now = datetime.datetime.now()
    current_time = now.strftime("%I:%M %p")
    reply = f"The current time is {current_time}"
    await update.message.reply_text(reply)
    await send_voice_message(update, reply)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_msg = update.message.text

    # Check if user exists in DB
    user_data = db.get_user(user_id)
    if not user_data:
        await update.message.reply_text("Please start with /start to set up your profile.")
        return

    name, city = user_data

    # Check for "who are you" or "who developed you" questions
    who_are_you_keywords = ["who are you", "who developed you", "who created you", "your developer", "your creator", "about you"]
    if any(word in user_msg.lower() for word in who_are_you_keywords):
        reply = "I was designed and developed by Arnicka Studios. I'm here to help you with weather information, AI conversations, and more!"
        await update.message.reply_text(reply)
        # Send voice message
        await send_voice_message(update, reply)
        db.log_message(user_id, user_msg, reply)
        return

    # Time keyword detection
    time_keywords = ["time", "what time", "current time", "tell me the time", "what's the time", "time is", "clock"]
    if any(word in user_msg.lower() for word in time_keywords):
        import datetime
        now = datetime.datetime.now()
        current_time = now.strftime("%I:%M %p")
        reply = f"The current time is {current_time}"
        await update.message.reply_text(reply)
        await send_voice_message(update, reply)
        db.log_message(user_id, user_msg, reply)
        return

    # Weather keyword detection
    weather_keywords = ["weather", "temperature", "forecast", "temp", "rain", "sunny"]
    if any(word in user_msg.lower() for word in weather_keywords):
        weather = utils.get_weather(city)
        if weather:
            reply = f"Weather in {city}: {weather}"
        else:
            reply = f"Sorry, I couldn't fetch weather for {city}."
        await update.message.reply_text(reply)
        await send_voice_message(update, reply)
    # Check for real-time search queries
    elif utils.is_search_query(user_msg):
        await update.message.reply_text("🔍 Searching...")
        search_result = utils.search_web(user_msg)
        if search_result:
            reply = f"📊 Here's what I found:\n\n{search_result}"
        else:
            reply = "Sorry, I couldn't find any results for your query."
        await update.message.reply_text(reply)
        await send_voice_message(update, reply)
    else:
        # AI response
        reply = utils.ask_openrouter(user_msg)
        await update.message.reply_text(reply)
        await send_voice_message(update, reply)

    db.log_message(user_id, user_msg, reply)

async def send_voice_message(update: Update, text: str):
    """Convert text to speech and send as voice message"""
    try:
        user_id = update.effective_user.id
        # Check if user has voice enabled
        if not voice_enabled.get(user_id, False):
            return  # Skip voice if not enabled
            
        # Use gTTS to convert text to speech
        import io
        from gtts import gTTS
        
        tts = gTTS(text=text, lang='en')
        audio_buffer = io.BytesIO()
        tts.write_to_fp(audio_buffer)
        audio_buffer.seek(0)
        
        await update.message.reply_voice(audio_buffer)
    except Exception as e:
        logger.warning(f"Could not send voice message: {e}")

def main():
    db.init_db()
    app = Application.builder().token(TELEGRAM_TOKEN).build()

    # Conversation handler for new users
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_name)],
            CITY: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_city)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )
    app.add_handler(conv_handler)

    # Handler for regular messages
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # Voice toggle command
    app.add_handler(CommandHandler("voice", voice_toggle))
    
    # Time command
    app.add_handler(CommandHandler("time", time_command))

    # Start web dashboard in a separate thread
    web_thread = threading.Thread(target=webapp.run_web, daemon=True)
    web_thread.start()
    logger.info("Web dashboard started on http://localhost:5000")

    logger.info("Bot started polling...")
    app.run_polling()

def run_24_7():
    """Run bot 24/7 with auto-restart on crash"""
    while True:
        try:
            logger.info("=" * 50)
            logger.info("Sonic Bot starting - Arnicka Studios")
            logger.info("Server: Arnicka;s Server")
            logger.info("Running 24/7 mode enabled")
            logger.info("=" * 50)
            main()
        except Exception as e:
            logger.error(f"Bot crashed: {e}")
            logger.info("Restarting bot in 10 seconds...")
            import time
            time.sleep(10)

if __name__ == "__main__":
    run_24_7()
