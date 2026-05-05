import os
import threading
from telegram.ext import Application, CommandHandler
from web_server import app
from bot_logic import start, add_account, get_otp, delete_account, sharelink, list_backup
from database import init_db

# Render-এর Environment Variable থেকে BOT_TOKEN নেওয়া হচ্ছে
TOKEN = os.getenv("BOT_TOKEN")

def run_web():
    # Render-এর জন্য ডাইনামিক পোর্ট সেট করা হয়েছে
    port = int(os.getenv("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

if __name__ == "__main__":
    # টোকেন চেক করা
    if not TOKEN:
        print("❌ Error: BOT_TOKEN environment variable not found!")
        exit(1)

    # ডাটাবেস ইনিশিয়ালাইজ করা
    init_db()
    
    # ওয়েব সার্ভার (Flask) আলাদা থ্রেডে চালানো যাতে বট ও ওয়েবসাইট একসাথে চলে
    threading.Thread(target=run_web, daemon=True).start()
    
    # টেলিগ্রাম বট সেটআপ
    bot_app = Application.builder().token(TOKEN).build()
    
    # নতুন কমান্ডগুলো রেজিস্টার করা
    bot_app.add_handler(CommandHandler("start", start))
    bot_app.add_handler(CommandHandler("add", add_account))
    bot_app.add_handler(CommandHandler("otp", get_otp))
    bot_app.add_handler(CommandHandler("delete", delete_account))
    bot_app.add_handler(CommandHandler("sharelink", sharelink))
    bot_app.add_handler(CommandHandler("list", list_backup))
    
    print("🚀 Hridoy 2FA Bot & Mini App is running...")
    
    # বট পোলিং শুরু করা
    bot_app.run_polling()
