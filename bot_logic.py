import os
import secrets
import time
import json
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import ContextTypes
from database import get_db

# এনভায়রনমেন্ট ভেরিয়েবল থেকে ইউআরএল নেওয়া
RENDER_URL = os.getenv("RENDER_URL", "").strip()

# --- ১. স্টার্ট কমান্ড (মিনি অ্যাপসহ) ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not RENDER_URL:
        await update.message.reply_text("⚠️ RENDER_URL set করা নেই!")
        return

    base_url = RENDER_URL if RENDER_URL.startswith("https") else f"https://{RENDER_URL}"
    web_app_url = f"{base_url.rstrip('/')}/miniapp?uid={user_id}"
    
    keyboard = [[InlineKeyboardButton("🚀 Open 2FA Mini App", web_app=WebAppInfo(url=web_app_url))]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "👋 স্বাগতম! আপনার ২এফএ অ্যাকাউন্টগুলো ম্যানেজ করতে নিচের কমান্ডগুলো ব্যবহার করুন অথবা সরাসরি Mini App ওপেন করুন।",
        reply_markup=reply_markup
    )

# --- ২. নতুন ২এফএ সেভ করা (/add) ---
async def add_account(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    if len(args) < 3:
        await update.message.reply_text("❌ ব্যবহার: `/add Name Email Secret`", parse_mode="Markdown")
        return

    name, gmail, secret = args[0], args[1], args[2].upper()
    user_id = update.effective_user.id
    token = secrets.token_urlsafe(8)

    with get_db() as conn:
        conn.execute("INSERT INTO links (token, user_id, account, secret, expiry) VALUES (?, ?, ?, ?, ?)", 
                     (token, user_id, name, secret, time.time() + 315360000)) # ১০ বছরের জন্য সেভ
        conn.commit()
    
    await update.message.reply_text(f"✅ **{name}** সফলভাবে সেভ করা হয়েছে!")

# --- ৩. ওটিপি দেখা (/otp) ---
async def get_otp(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("❌ ব্যবহার: `/otp Name`")
        return
    
    name = context.args[0]
    user_id = update.effective_user.id
    
    with get_db() as conn:
        row = conn.execute("SELECT secret FROM links WHERE user_id=? AND account=?", (user_id, name)).fetchone()
    
    if row:
        import pyotp
        totp = pyotp.TOTP(row['secret'].replace(" ", ""))
        await update.message.reply_text(f"🔑 **{name} OTP:** `{totp.now()}`", parse_mode="Markdown")
    else:
        await update.message.reply_text("❌ অ্যাকাউন্ট পাওয়া যায়নি!")

# --- ৪. অ্যাকাউন্ট মুছে ফেলা (/delete) ---
async def delete_account(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("❌ ব্যবহার: `/delete Name`")
        return
    
    name = context.args[0]
    user_id = update.effective_user.id
    
    with get_db() as conn:
        conn.execute("DELETE FROM links WHERE user_id=? AND account=?", (user_id, name))
        conn.commit()
    
    await update.message.reply_text(f"🗑️ **{name}** মুছে ফেলা হয়েছে।")

# --- ৫. অস্থায়ী লিঙ্ক তৈরি (/sharelink) ---
async def sharelink(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    if len(args) < 2:
        await update.message.reply_text("❌ ব্যবহার: `/sharelink Name Secret Time`")
        return

    name, secret = args[0], args[1].upper()
    mins = int(args[2]) if len(args) > 2 else 5
    token = secrets.token_urlsafe(10)
    expiry = time.time() + (mins * 60)
    user_id = update.effective_user.id

    with get_db() as conn:
        conn.execute("INSERT INTO links VALUES (?, ?, ?, ?, ?)", (token, user_id, name, secret, expiry))
        conn.commit()

    await update.message.reply_text(f"🔗 **অস্থায়ী লিঙ্ক:** {RENDER_URL}/view?t={token}\n⏳ মেয়াদ: {mins} মিনিট")

# --- ৬. ব্যাকআপ ফাইল ডাউনলোড (/list) ---
async def list_backup(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    with get_db() as conn:
        rows = conn.execute("SELECT account, secret FROM links WHERE user_id=?", (user_id,)).fetchall()
    
    if not rows:
        await update.message.reply_text("❌ আপনার কোনো ডাটা সেভ করা নেই।")
        return

    data = [dict(row) for row in rows]
    file_path = f"backup_{user_id}.json"
    with open(file_path, "w") as f:
        json.dump(data, f, indent=4)
    
    await update.message.reply_document(document=open(file_path, "rb"), caption="📂 আপনার ২এফএ ব্যাকআপ ফাইল। এটি নিরাপদ রাখুন।")
    os.remove(file_path)
