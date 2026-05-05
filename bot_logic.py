import os
import secrets
import time
import json
import pyotp
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import ContextTypes
from database import get_db

# Render-এর Environment Variable থেকে URL নেওয়া
RENDER_URL = os.getenv("RENDER_URL", "").strip()

# --- ১. স্টার্ট ও ড্যাশবোর্ড বাটন ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    base_url = RENDER_URL if RENDER_URL.startswith("https") else f"https://{RENDER_URL}"
    url = f"{base_url.rstrip('/')}/miniapp?uid={user_id}"
    
    kbd = [[InlineKeyboardButton("🚀 Open 2FA Dashboard", web_app=WebAppInfo(url=url))]]
    
    await update.message.reply_text(
        f"স্বাগতম **{update.effective_user.first_name}**!\n\n"
        "🔐 এটি আপনার ব্যক্তিগত ২এফএ অথেনটিকেটর বট।\n"
        "ড্যাশবোর্ড ওপেন করতে নিচের বাটনে ক্লিক করুন অথবা কমান্ড ব্যবহার করুন।",
        reply_markup=InlineKeyboardMarkup(kbd),
        parse_mode="Markdown"
    )

# --- ২. অ্যাকাউন্ট সেভ করা (/add) ---
async def add_account(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 3:
        return await update.message.reply_text("❌ ব্যবহার: `/add Name Gmail Secret`", parse_mode="Markdown")
    
    name, gmail, secret = context.args[0], context.args[1], context.args[2].upper()
    full_name = f"{name} ({gmail})"
    user_id = update.effective_user.id
    token = secrets.token_urlsafe(8)

    with get_db() as conn:
        conn.execute("INSERT INTO links (token, user_id, account, secret, expiry) VALUES (?, ?, ?, ?, ?)", 
                     (token, user_id, full_name, secret, time.time() + 315360000))
        conn.commit()
    
    await update.message.reply_text(f"✅ **{name}** সফলভাবে সেভ হয়েছে!")

# --- ৩. সরাসরি ওটিপি দেখা (/otp) ---
async def get_otp(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        return await update.message.reply_text("❌ ব্যবহার: `/otp [Name বা Gmail]`")
    
    search = context.args[0]
    user_id = update.effective_user.id
    
    with get_db() as conn:
        row = conn.execute("SELECT account, secret FROM links WHERE user_id=? AND account LIKE ?", 
                           (user_id, f"%{search}%")).fetchone()
    
    if row:
        totp = pyotp.TOTP(row['secret'].replace(" ", ""))
        await update.message.reply_text(f"🔑 **{row['account']}**\nOTP: `{totp.now()}`", parse_mode="Markdown")
    else:
        await update.message.reply_text("❌ কোনো অ্যাকাউন্ট পাওয়া যায়নি।")

# --- ৪. অ্যাকাউন্ট ডিলিট করা (/delete) ---
async def delete_account(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        return await update.message.reply_text("❌ ব্যবহার: `/delete Name`")
    
    search = context.args[0]
    user_id = update.effective_user.id
    
    with get_db() as conn:
        check = conn.execute("SELECT account FROM links WHERE user_id=? AND account LIKE ?", 
                             (user_id, f"%{search}%")).fetchone()
        if check:
            conn.execute("DELETE FROM links WHERE user_id=? AND account LIKE ?", (user_id, f"%{search}%"))
            conn.commit()
            await update.message.reply_text(f"🗑️ **{check['account']}** মুছে ফেলা হয়েছে।")
        else:
            await update.message.reply_text("❌ ডিলিট করার জন্য কোনো অ্যাকাউন্ট পাওয়া যায়নি।")

# --- ৫. শেয়ার লিঙ্ক তৈরি (/sharelink) ---
async def sharelink(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 2:
        return await update.message.reply_text("❌ ব্যবহার: `/sharelink Name Secret Time`")
    
    name, secret = context.args[0], context.args[1].upper()
    mins = int(context.args[2]) if len(context.args) > 2 else 5
    token = secrets.token_urlsafe(10)
    expiry = time.time() + (mins * 60)

    with get_db() as conn:
        conn.execute("INSERT INTO links VALUES (?, ?, ?, ?, ?)", (token, update.effective_user.id, name, secret, expiry))
        conn.commit()

    await update.message.reply_text(f"🔗 **অস্থায়ী ওটিপি লিঙ্ক:**\n{RENDER_URL}/miniapp?uid={update.effective_user.id}\n⏳ মেয়াদ: {mins} মিনিট")

# --- ৬. ব্যাকআপ ফাইল ডাউনলোড (/list) ---
async def list_backup(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    with get_db() as conn:
        rows = conn.execute("SELECT account, secret FROM links WHERE user_id=?", (user_id,)).fetchall()
    
    if not rows:
        return await update.message.reply_text("❌ আপনার কোনো ডাটা সেভ করা নেই।")

    file_path = f"backup_{user_id}.txt"
    with open(file_path, "w") as f:
        for r in rows:
            f.write(f"{r['account']}|{r['secret']}\n")
    
    await update.message.reply_document(document=open(file_path, "rb"), caption="📂 আপনার ব্যাকআপ ফাইল। এটি নিরাপদ রাখুন।")
    os.remove(file_path)

# --- ৭. অটো রিস্টোর (ফাইল পাঠালে) ---
async def handle_restore(update: Update, context: ContextTypes.DEFAULT_TYPE):
    doc = update.message.document
    if not doc.file_name.endswith('.txt'):
        return
    
    file = await context.bot.get_file(doc.file_id)
    content = await file.download_as_bytearray()
    lines = content.decode('utf-8').split('\n')
    
    count = 0
    with get_db() as conn:
        for line in lines:
            if '|' in line:
                name, secret = line.split('|')
                conn.execute("INSERT OR REPLACE INTO links VALUES (?, ?, ?, ?, ?)", 
                             (secrets.token_urlsafe(8), update.effective_user.id, name.strip(), secret.strip(), time.time() + 315360000))
                count += 1
        conn.commit()
    await update.message.reply_text(f"✅ সফলভাবে {count}টি অ্যাকাউন্ট রিস্টোর হয়েছে!")
