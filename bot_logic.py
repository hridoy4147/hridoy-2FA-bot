import os
import secrets
import time
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import ContextTypes
from database import get_db

RENDER_URL = os.getenv("RENDER_URL")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    # মিনি অ্যাপ ইউআরএল যেখানে ইউজার আইডি অটো পাস হবে
    web_app_url = f"{RENDER_URL}/miniapp?uid={user_id}"
    
    keyboard = [[InlineKeyboardButton("🚀 Open 2FA Mini App", web_app=WebAppInfo(url=web_app_url))]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "স্বাগতম! আপনার সব ওটিপি একসাথে দেখতে নিচের বাটনে ক্লিক করুন।",
        reply_markup=reply_markup
    )

async def sharelink(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    if len(args) < 2: return await update.message.reply_text("Format: /sharelink Name Secret Time")

    token = secrets.token_urlsafe(10)
    expiry = time.time() + (int(args[2]) if len(args) > 2 else 5) * 60
    user_id = update.effective_user.id
    
    with get_db() as conn:
        conn.execute("INSERT INTO links VALUES (?, ?, ?, ?, ?)", 
                     (token, user_id, args[0], args[1].upper(), expiry))
        conn.commit()

    await update.message.reply_text(f"🔗 Private Link: {RENDER_URL}/view?t={token}")
