from flask import Flask, request
import pyotp
from database import get_db

app = Flask(__name__)

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
            body {{ background: #0f172a; color: white; font-family: sans-serif; margin: 0; padding: 15px; user-select: none; }}
            .card {{ background: #1e293b; padding: 15px; border-radius: 12px; border: 1px solid #334155; display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; cursor: pointer; transition: 0.2s; }}
            .card:active {{ background: #334155; transform: scale(0.98); }}
            .otp {{ color: #38bdf8; font-size: 26px; font-weight: bold; letter-spacing: 2px; }}
            .name {{ font-size: 15px; font-weight: bold; color: #f8fafc; }}
            .copy-msg {{ position: fixed; bottom: 20px; left: 50%; transform: translateX(-50%); background: #38bdf8; color: black; padding: 8px 20px; border-radius: 20px; font-size: 14px; display: none; z-index: 100; }}
        </style>
    </head>
    <body>
        <h3 style="text-align:center;">🛡️ Hridoy 2FA Dashboard</h3>
        <div id="toast" class="copy-msg">Copied to clipboard!</div>
        <div id="list">
    """
    
    if accounts:
        for row in accounts:
            try:
                # ওটিপি জেনারেট করা
                otp = pyotp.TOTP(row['secret'].replace(" ", "")).now()
                # কার্ডে ক্লিক করলে copyOTP ফাংশন কল হবে
                html += f"""
                <div class="card" onclick="copyOTP('{otp}')">
                    <div class="info">
                        <div class="name">{row['account']}</div>
                        <div style="font-size:11px; opacity:0.5;">{row['gmail'] if 'gmail' in row.keys() else ''}</div>
                    </div>
                    <div class="otp">{otp[:3]} {otp[3:]}</div>
                </div>"""
            except: continue
    else:
        html += "<p style='text-align:center; opacity:0.5;'>No accounts found!</p>"

    html += """</div>
        <script>
            Telegram.WebApp.ready();
            Telegram.WebApp.expand();

            function copyOTP(code) {
                // ক্লিপবোর্ডে কপি করার লজিক
                navigator.clipboard.writeText(code).then(() => {
                    const toast = document.getElementById('toast');
                    toast.style.display = 'block';
                    // টেলিগ্রামের হ্যাপটিক ফিডব্যাক (ভাইব্রেশন)
                    if (Telegram.WebApp.HapticFeedback) {
                        Telegram.WebApp.HapticFeedback.notificationOccurred('success');
                    }
                    setTimeout(() => { toast.style.display = 'none'; }, 2000);
                });
            }

            // ১০ সেকেন্ড পর অটো রিফ্রেশ যাতে নতুন ওটিপি আসে
            setTimeout(() => location.reload(), 10000); 
        </script>
    </body>
    </html>"""
    return html
