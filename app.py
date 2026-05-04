import os
import threading
from telegram.ext import Application
from web_server import app
from bot_logic import start, sharelink
from database import init_db

# Environment Variable থেকে TOKEN নেওয়া হচ্ছে
TOKEN = os.getenv("BOT_TOKEN")

def run_web():
    # Render-এর জন্য পোর্ট ডাইনামিক করা হয়েছে
    port = int(os.getenv("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

if __name__ == "__main__":
    if not TOKEN:
        print("❌ Error: BOT_TOKEN environment variable not found!")
        exit(1)
        
    init_db()
    threading.Thread(target=run_web, daemon=True).start()
    
    bot_app = Application.builder().token(TOKEN).build()
    bot_app.add_handler(CommandHandler("start", start))
    bot_app.add_handler(CommandHandler("sharelink", sharelink))
    
    print("🚀 Bot is running with environment variables...")
    bot_app.run_polling()
