from flask import Flask, request, jsonify
import pyotp, time
from database import get_db

app = Flask(__name__)

@app.route('/api/otps')
def get_otps():
    uid = request.args.get('uid')
    if not uid: return jsonify({"error": "No UID"}), 400
    with get_db() as conn:
        rows = conn.execute("SELECT account, secret FROM links WHERE user_id=?", (uid,)).fetchall()
    
    current_time = int(time.time())
    remaining = 30 - (current_time % 30)
    data = [{"name": r["account"], "otp": pyotp.TOTP(r["secret"].replace(" ","")).now()} for r in rows]
    return jsonify({"accounts": data, "remaining": remaining})

@app.route('/miniapp')
def miniapp():
    uid = request.args.get('uid')
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
        <script src="https://telegram.org/js/telegram-web-app.js"></script>
        <style>
            body {{ background: #0f172a; color: white; font-family: sans-serif; margin: 0; padding: 15px; user-select: none; }}
            .card {{ background: #1e293b; border-radius: 12px; padding: 15px; margin-bottom: 12px; border: 1px solid #334155; }}
            .row {{ display: flex; align-items: center; gap: 12px; }}
            .logo {{ width: 40px; height: 40px; background: #38bdf8; border-radius: 8px; display: flex; align-items: center; justify-content: center; color: #0f172a; font-weight: bold; font-size: 20px; }}
            .otp {{ font-size: 30px; font-weight: bold; color: #38bdf8; text-align: center; margin: 10px 0; letter-spacing: 3px; cursor: pointer; }}
            .p-bar {{ height: 4px; background: #334155; border-radius: 2px; overflow: hidden; }}
            .p-fill {{ height: 100%; background: #38bdf8; width: 100%; transition: width 1s linear; }}
            .time-text {{ text-align: center; font-size: 12px; opacity: 0.6; margin-top: 5px; }}
        </style>
    </head>
    <body>
        <div id="list">Loading...</div>
        <script>
            let remain = 30;
            async def update() {{
                const res = await fetch(`/api/otps?uid={uid}`);
                const data = await res.json();
                remain = data.remaining;
                document.getElementById('list').innerHTML = data.accounts.map(a => `
                    <div class="card" onclick="copy('${{a.otp}}')">
                        <div class="row"><div class="logo">${{a.name[0].toUpperCase()}}</div><b>${{a.name}}</b></div>
                        <div class="otp">${{a.otp.slice(0,3)}} ${{a.otp.slice(3)}}</div>
                        <div class="p-bar"><div class="p-fill" style="width:${{(remain/30)*100}}%"></div></div>
                        <div class="time-text">Next OTP in: ${{remain}}s</div>
                    </div>`).join('');
            }}
            function copy(c) {{
                navigator.clipboard.writeText(c);
                if(window.Telegram) Telegram.WebApp.HapticFeedback.notificationOccurred('success');
            }}
            setInterval(() => {{ 
                if(remain > 0) {{ 
                    remain--; 
                    document.querySelectorAll('.p-fill').forEach(b => b.style.width = (remain/30)*100 + '%');
                    document.querySelectorAll('.time-text').forEach(t => t.innerText = "Next OTP in: " + remain + "s");
                }} else {{ update(); }}
            }}, 1000);
            update(); Telegram.WebApp.ready(); Telegram.WebApp.expand();
        </script>
    </body></html>"""
