import os
import secrets
import time
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import ContextTypes
from database import get_db

# এনভায়রনমেন্ট ভেরিয়েবল থেকে ইউআরএল নেওয়া
RENDER_URL = os.getenv("RENDER_URL", "").strip()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    # ইউআরএল চেক করা (যদি রেন্ডারে সেট না থাকে তবে মেসেজ দিবে)
    if not RENDER_URL:
        await update.message.reply_text("⚠️ Please set RENDER_URL in Environment Variables!")
        return

    # নিশ্চিত করা যে লিঙ্কটি https দিয়ে শুরু হয়েছে
    base_url = RENDER_URL if RENDER_URL.startswith("https") else f"https://{RENDER_URL}"
    web_app_url = f"{base_url.rstrip('/')}/miniapp?uid={user_id}"
    
    # Mini App বাটন
    keyboard = [[InlineKeyboardButton("🚀 Open 2FA Mini App", web_app=WebAppInfo(url=web_app_url))]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "স্বাগতম 𝙷𝚛𝚒𝚍𝚘𝚢! আপনার সব ওটিপি একসাথে দেখতে নিচের বাটনে ক্লিক করুন।",
        reply_markup=reply_markup
    )
