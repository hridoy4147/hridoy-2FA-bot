from flask import Flask, request
import time, pyotp
from database import get_db

app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is Active ✅"

@app.route('/view')
def view_otp():
    token = request.args.get('t')
    if not token: return "Invalid Token", 400

    with get_db() as conn:
        row = conn.execute("SELECT * FROM links WHERE token=?", (token,)).fetchone()
    
    if row and time.time() < row['expiry']:
        otp_code = pyotp.TOTP(row['secret'].replace(" ", "")).now()
        remaining = 30 - (int(time.time()) % 30)
        return f"<h2>{row['account']}</h2><h1>{otp_code}</h1><p>Refreshes in {remaining}s</p><script>setTimeout(()=>location.reload(), 5000);</script>"
    
    return "Expired!", 404
