import os
import threading
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from web_server import app
from bot_logic import *
from database import init_db

# ওয়েব সার্ভার চালানোর ফাংশন
def run_web():
    port = int(os.getenv("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

if __name__ == "__main__":
    # ১. ডাটাবেস চেক ও তৈরি
    init_db()
    
    # ২. ওয়েব সার্ভার আলাদা থ্রেডে চালু করা
    threading.Thread(target=run_web, daemon=True).start()
    
    # ৩. টেলিগ্রাম বট সেটআপ
    TOKEN = os.getenv("BOT_TOKEN")
    if not TOKEN:
        print("❌ BOT_TOKEN missing!")
        exit(1)

    bot_app = Application.builder().token(TOKEN).build()
    
    # ৪. সব কমান্ড হ্যান্ডলার যুক্ত করা
    bot_app.add_handler(CommandHandler("start", start))
    bot_app.add_handler(CommandHandler("add", add_account))
    bot_app.add_handler(CommandHandler("otp", get_otp))
    bot_app.add_handler(CommandHandler("delete", delete_account))
    bot_app.add_handler(CommandHandler("sharelink", sharelink))
    bot_app.add_handler(CommandHandler("list", list_backup))
    
    # ৫. ফাইল রিস্টোর হ্যান্ডলার
    bot_app.add_handler(MessageHandler(filters.Document.ALL, handle_restore))
    
    print("🚀 Hridoy 2FA Bot is LIVE...")
    
    # ৬. পোলিং শুরু
    bot_app.run_polling()
