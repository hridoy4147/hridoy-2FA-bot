import os, threading
from telegram.ext import Application, CommandHandler
from web_server import app
from bot_logic import *
from database import init_db

def run_web():
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 10000)))

if __name__ == "__main__":
    init_db()
    threading.Thread(target=run_web, daemon=True).start()
    bot = Application.builder().token(os.getenv("BOT_TOKEN")).build()
    handlers = [("start",start),("add",add_account),("otp",get_otp),("delete",delete_account),("list",list_backup)]
    for cmd, func in handlers: bot.add_handler(CommandHandler(cmd, func))
    bot.run_polling()
