from flask import Flask, request
import pyotp, time
from database import get_db

app = Flask(__name__)

@app.route('/')
def health():
    return "Bot is Active ✅"

@app.route('/miniapp')
def miniapp():
    user_id = request.args.get('uid')
    if not user_id: return "Invalid User ID", 400

    with get_db() as conn:
        accounts = conn.execute("SELECT * FROM links WHERE user_id=?", (user_id,)).fetchall()

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
        <script src="https://telegram.org/js/telegram-web-app.js"></script>
        <style>
            body {{ background: #0f172a; color: white; font-family: sans-serif; margin: 0; padding: 15px; }}
            .card {{ background: #1e293b; padding: 15px; border-radius: 12px; border: 1px solid #334155; display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; }}
            .otp {{ color: #38bdf8; font-size: 24px; font-weight: bold; letter-spacing: 2px; }}
            .name {{ font-size: 15px; font-weight: bold; }}
        </style>
    </head>
    <body>
        <h3 style="text-align:center;">🛡️ My 2FA Dashboard</h3>
        <div id="list">
    """
    if accounts:
        for row in accounts:
            try:
                otp = pyotp.TOTP(row['secret'].replace(" ", "")).now()
                html += f"""
                <div class="card">
                    <div class="name">{row['account']}</div>
                    <div class="otp">{otp[:3]} {otp[3:]}</div>
                </div>"""
            except: continue
    else:
        html += "<p style='text-align:center; opacity:0.5;'>No accounts found!</p>"

    html += """</div>
        <script>
            Telegram.WebApp.ready();
            Telegram.WebApp.expand();
            setTimeout(() => location.reload(), 10000); 
        </script>
    </body>
    </html>"""
    return html
