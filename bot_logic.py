import os, secrets, time, json, pyotp
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import ContextTypes
from database import get_db

RENDER_URL = os.getenv("RENDER_URL", "").strip()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    url = f"{RENDER_URL}/miniapp?uid={user_id}"
    kbd = [[InlineKeyboardButton("🚀 Open Dashboard", web_app=WebAppInfo(url=url))]]
    await update.message.reply_text("👋 স্বাগতম! আপনার ড্যাশবোর্ড দেখতে নিচের বাটনে ক্লিক করুন।", reply_markup=InlineKeyboardMarkup(kbd))

async def add_account(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 3: return await update.message.reply_text("❌ /add Name Email Secret")
    with get_db() as conn:
        conn.execute("INSERT INTO links VALUES (?,?,?,?,?)", (secrets.token_urlsafe(8), update.effective_user.id, context.args[0], context.args[2].upper(), time.time()+315360000))
        conn.commit()
    await update.message.reply_text(f"✅ {context.args[0]} সেভ হয়েছে!")

async def get_otp(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args: return
    with get_db() as conn:
        row = conn.execute("SELECT secret FROM links WHERE user_id=? AND account=?", (update.effective_user.id, context.args[0])).fetchone()
    if row: await update.message.reply_text(f"🔑 {context.args[0]} OTP: `{pyotp.TOTP(row['secret']).now()}`", parse_mode="Markdown")

async def delete_account(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args: return
    with get_db() as conn:
        conn.execute("DELETE FROM links WHERE user_id=? AND account=?", (update.effective_user.id, context.args[0]))
        conn.commit()
    await update.message.reply_text(f"🗑️ {context.args[0]} ডিলিট হয়েছে।")

async def list_backup(update: Update, context: ContextTypes.DEFAULT_TYPE):
    with get_db() as conn:
        rows = conn.execute("SELECT account, secret FROM links WHERE user_id=?", (update.effective_user.id,)).fetchall()
    if rows:
        with open("backup.json", "w") as f: json.dump([dict(r) for r in rows], f)
        await update.message.reply_document(document=open("backup.json", "rb"), caption="📂 ব্যাকআপ ফাইল।")
