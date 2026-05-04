from telegram import Update
from telegram.ext import CommandHandler, ContextTypes
import secrets, time
from database import get_db

RENDER_URL = "https://twofabot-py.onrender.com"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 Welcome! Use /sharelink to create a secure link.")

async def sharelink(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    if len(args) < 2: return await update.message.reply_text("Format: /sharelink Name Secret Time")

    token = secrets.token_urlsafe(10)
    expiry = time.time() + (int(args[2]) if len(args) > 2 else 5) * 60
    
    with get_db() as conn:
        conn.execute("INSERT INTO links VALUES (?, ?, ?, ?)", (token, args[0], args[1].upper(), expiry))
        conn.commit()

    await update.message.reply_text(f"🔗 Link: {RENDER_URL}/view?t={token}")
