from flask import Flask, request
import pyotp, time
from database import get_db

app = Flask(__name__)

@app.route('/')
def health():
    return "Web Server is Running ✅"

@app.route('/miniapp')
def miniapp():
    user_id = request.args.get('uid')
    if not user_id: return "Invalid User ID", 400
    
    with get_db() as conn:
        # শুধুমাত্র সেই ইউজারের ডাটাবেস থেকে ডাটা নেওয়া হচ্ছে
        accounts = conn.execute("SELECT * FROM links WHERE user_id=?", (user_id,)).fetchall()

    # বর্তমান সময়ের ওপর ভিত্তি করে ৩০ সেকেন্ডের টাইমার ক্যালকুলেশন
    current_time = int(time.time())
    remaining_sec = 30 - (current_time % 30)
    # প্রোগ্রেস বারের প্রস্থ (Width) শতাংশে
    progress_width = (remaining_sec / 30) * 100

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
        <script src="https://telegram.org/js/telegram-web-app.js"></script>
        <style>
            body {{ background: #0f172a; color: white; font-family: 'Segoe UI', Roboto, sans-serif; margin: 0; padding: 15px; user-select: none; }}
            .container {{ max-width: 500px; margin: 0 auto; }}
            .header {{ text-align: center; font-size: 18px; font-weight: bold; margin-bottom: 20px; color: #38bdf8; }}
            
            /* ওটিপি কার্ড ডিজাইন */
            .card {{ 
                background: #1e293b; border-radius: 16px; padding: 18px; 
                margin-bottom: 12px; border: 1px solid #334155;
                box-shadow: 0 4px 10px rgba(0,0,0,0.2);
                position: relative; overflow: hidden; cursor: pointer;
                transition: transform 0.1s;
            }}
            .card:active {{ transform: scale(0.97); background: #262f3f; }}

            /* লোগো এবং নাম পাশাপাশি */
            .top-row {{ display: flex; align-items: center; gap: 12px; margin-bottom: 12px; }}
            .logo {{ 
                width: 42px; height: 42px; border-radius: 10px; background: #38bdf8; 
                display: flex; align-items: center; justify-content: center; 
                font-weight: bold; color: #0f172a; font-size: 20px;
            }}
            .name-sec {{ flex-grow: 1; }}
            .acc-name {{ font-size: 15px; font-weight: 600; color: #f8fafc; letter-spacing: 0.5px; }}
            .label {{ font-size: 11px; color: #38bdf8; opacity: 0.8; text-transform: uppercase; }}

            /* ওটিপি কোড ডিসপ্লে */
            .otp-display {{ 
                font-size: 34px; font-weight: 700; color: #38bdf8; 
                letter-spacing: 5px; text-align: center; margin: 8px 0;
            }}

            /* ৩০ সেকেন্ডের টাইমার লাইন (Progress Bar) */
            .progress-container {{ width: 100%; height: 4px; background: #334155; border-radius: 2px; margin-top: 15px; overflow: hidden; }}
            .progress-bar {{ height: 100%; background: #38bdf8; width: {progress_width}%; transition: width 1s linear; }}
            
            .timer-text {{ text-align: center; font-size: 12px; opacity: 0.6; margin-top: 8px; }}
            
            /* কপি টোস্ট নোটিফিকেশন */
            .toast {{ 
                position: fixed; bottom: 30px; left: 50%; transform: translateX(-50%); 
                background: #38bdf8; color: #0f172a; padding: 10px 25px; 
                border-radius: 25px; font-weight: bold; display: none; z-index: 100;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">🛡️ 2FA Authenticator</div>
            <div id="toast" class="toast">Copied!</div>
            <div id="list">
    """
    
    if accounts:
        for row in accounts:
            try:
                totp = pyotp.TOTP(row['secret'].replace(" ", ""))
                otp = totp.now()
                # নামের প্রথম অক্ষর লোগো হিসেবে
                initial = row['account'][0].upper()
                
                html += f"""
                <div class="card" onclick="copyCode('{otp}')">
                    <div class="top-row">
                        <div class="logo">{initial}</div>
                        <div class="name-sec">
                            <div class="label">Verification Code</div>
                            <div class="acc-name">{row['account']}</div>
                        </div>
                    </div>
                    <div class="otp-display">{otp[:3]} {otp[3:]}</div>
                    <div class="progress-container">
                        <div class="progress-bar"></div>
                    </div>
                    <div class="timer-text">Next OTP in: {remaining_sec}s</div>
                </div>"""
            except: continue
    else:
        html += "<p style='text-align:center; opacity:0.5; margin-top:50px;'>No accounts found!</p>"

    html += f"""
            </div>
        </div>
        <script>
            Telegram.WebApp.ready();
            Telegram.WebApp.expand();

            // ক্লিপবোর্ডে কপি এবং হ্যাপটিক ফিডব্যাক
            function copyCode(code) {{
                navigator.clipboard.writeText(code);
                const t = document.getElementById('toast');
                t.style.display = 'block';
                if(window.Telegram && Telegram.WebApp.HapticFeedback) {{
                    Telegram.WebApp.HapticFeedback.notificationOccurred('success');
                }}
                setTimeout(() => t.style.display='none', 1500);
            }}

            // ওটিপি রিফ্রেশ লজিক (৩০ সেকেন্ড চক্র অনুযায়ী)
            setInterval(() => {{
                location.reload();
            }}, {remaining_sec * 1000 if remaining_sec > 0 else 1000});
        </script>
    </body>
    </html>"""
    return html
