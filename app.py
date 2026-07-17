from flask import Flask, request, redirect, render_template_string, send_from_directory
import sqlite3
import smtplib
import os
import threading
from email.mime.text import MIMEText

app = Flask(__name__)

# Function to send email notification (runs in background thread)
def send_email_notification():
    smtp_server = os.environ.get('SMTP_SERVER', 'smtp.gmail.com')
    smtp_port = int(os.environ.get('SMTP_PORT', '587'))
    smtp_user = os.environ.get('SMTP_USER')
    smtp_password = os.environ.get('SMTP_PASSWORD')
    recipient = 'gaurasdairyfarm.annapurna@gmail.com'
    
    msg_text = "A new order booking has been received on the website. No details are included in this email to protect customer privacy. Please open your live admin panel dashboard to check the details."
    msg = MIMEText(msg_text)
    msg['Subject'] = '🚨 New Gauras Dairy Request Logged!'
    msg['From'] = smtp_user if smtp_user else 'gauras-alerts@localhost'
    msg['To'] = recipient
    
    if not smtp_user or not smtp_password:
        print("\n" + "📧" * 25)
        print(f" [EMAIL ALERT SIMULATION] Dispatch to {recipient}")
        print(" Msg: A new booking has been made! Check the dashboard.")
        print(" Note: To send actual emails, configure SMTP_USER/SMTP_PASSWORD in your environment.")
        print("📧" * 25 + "\n")
        return
        
    try:
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(smtp_user, smtp_password)
        server.sendmail(smtp_user, recipient, msg.as_string())
        server.close()
        print(f"📧 Notification email successfully sent to {recipient}")
    except Exception as e:
        print(f"❌ Failed to send notification email: {e}")

# Initialize a lightweight local SQL database
def init_db():
    conn = sqlite3.connect('orders.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT, phone TEXT, address TEXT, 
            breed TEXT, time_pref TEXT, volume TEXT, duration TEXT
        )
    ''')
    conn.commit()
    conn.close()

# Route 1: Handle form submissions from order.html
@app.route('/submit-order', methods=['POST'])
def submit_order():
    name = request.form.get('Customer Name')
    phone = request.form.get('Customer Phone')
    address = request.form.get('Delivery Destination')
    breed = request.form.get('Milk Breed Variety')
    time_pref = request.form.get('Delivery Schedule Preference')
    volume = request.form.get('Volume Per Day')
    duration = request.form.get('Subscription Length')

    # Save to our local database
    conn = sqlite3.connect('orders.db')
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO orders (name, phone, address, breed, time_pref, volume, duration)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (name, phone, address, breed, time_pref, volume, duration))
    conn.commit()
    conn.close()

    # Print a high-visibility terminal/console notification
    print("\n" + "🚨" * 25)
    print(f" NEW ORDER RECEIVED FROM: {name}")
    print(f" Phone: {phone}")
    print(f" Address: {address}")
    print(f" Milk Breed: {breed}")
    print(f" Delivery: {time_pref} | Volume: {volume} L/day | Duration: {duration} days")
    print("🚨" * 25 + "\n")

    # Asynchronously dispatch email notification in a background thread
    threading.Thread(target=send_email_notification, daemon=True).start()

    # Smoothly redirect directly to your billing placeholder page
    return redirect('/billing.html')

# Route 1b: Polling API for dashboard to discover new orders
@app.route('/dashboard/api/new-orders')
def new_orders_api():
    since_id = request.args.get('since_id', default=0, type=int)
    conn = sqlite3.connect('orders.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM orders WHERE id > ? ORDER BY id ASC', (since_id,))
    rows = cursor.fetchall()
    conn.close()

    orders = []
    for row in rows:
        orders.append({
            'id': row[0],
            'name': row[1],
            'phone': row[2],
            'address': row[3],
            'breed': row[4],
            'time_pref': row[5],
            'volume': row[6],
            'duration': row[7]
        })
    return {'orders': orders}

# Route 2: Your Live Admin Dashboard Panel
@app.route('/dashboard')
def dashboard():
    conn = sqlite3.connect('orders.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM orders ORDER BY id DESC')
    rows = cursor.fetchall()
    conn.close()

    max_id = rows[0][0] if rows else 0

    # A modern blue-themed admin panel with notification polling and sound
    html_template = '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Gauras Hub — Admin Panel</title>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            :root {
                --bg: #0b111e;
                --panel-bg: #121b2d;
                --text-main: #f3f4f6;
                --text-muted: #9ca3af;
                --accent-blue: #00d2ff;
                --border-color: #1f293d;
                --card-bg: #162238;
            }
            body { 
                background-color: var(--bg); 
                color: var(--text-main); 
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; 
                padding: 20px; 
                margin: 0;
            }
            .panel { 
                max-width: 800px; 
                margin: 0 auto; 
                background: var(--panel-bg); 
                border: 1px solid var(--border-color); 
                padding: 24px; 
                border-radius: 16px; 
                box-shadow: 0 10px 30px rgba(0,0,0,0.3); 
                position: relative;
            }
            h2 { 
                border-bottom: 2px solid var(--border-color); 
                padding-bottom: 12px; 
                margin-top: 0;
                color: var(--accent-blue);
            }
            .stats {
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 20px;
            }
            .btn-notif {
                background: var(--accent-blue);
                color: #0b111e;
                border: none;
                padding: 8px 16px;
                border-radius: 8px;
                font-size: 13px;
                font-weight: bold;
                cursor: pointer;
                transition: opacity 0.2s;
            }
            .btn-notif:hover {
                opacity: 0.9;
            }
            .order-container {
                display: flex;
                flex-direction: column;
                gap: 12px;
            }
            .order-card { 
                background: var(--card-bg); 
                border: 1px solid var(--border-color); 
                padding: 16px; 
                border-radius: 12px; 
                transition: transform 0.3s, box-shadow 0.3s;
                position: relative;
                overflow: hidden;
            }
            .order-card.new-order-flash {
                animation: flashBlue 2s ease-out;
            }
            @keyframes flashBlue {
                0% { border-color: var(--accent-blue); box-shadow: 0 0 15px rgba(0,210,255,0.6); background: #1e355c; }
                100% { border-color: var(--border-color); box-shadow: none; background: var(--card-bg); }
            }
            .meta { color: var(--text-muted); font-size: 13px; margin-bottom: 6px; }
            .meta strong { color: var(--accent-blue); }
            .phone-link { color: var(--accent-blue); font-weight: bold; text-decoration: none; }
            .phone-link:hover { text-decoration: underline; }
            
            /* Toast container */
            #toast-container {
                position: fixed;
                top: 20px;
                right: 20px;
                z-index: 9999;
                display: flex;
                flex-direction: column;
                gap: 10px;
            }
            .toast {
                background: var(--accent-blue);
                color: #0b111e;
                padding: 16px 24px;
                border-radius: 12px;
                box-shadow: 0 10px 25px rgba(0,0,0,0.5);
                font-weight: 500;
                transform: translateX(120%);
                transition: transform 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275);
            }
            .toast.show {
                transform: translateX(0);
            }
        </style>
    </head>
    <body>
        <div id="toast-container"></div>
        <div class="panel">
            <h2>Gauras Dairy Request Hub Dashboard</h2>
            <div class="stats">
                <p style="color: var(--text-muted); margin: 0;">Total Logged Allocations: <span id="total-count">{{ rows|length }}</span></p>
                <button class="btn-notif" id="notif-btn" onclick="requestNotificationPermission()">Enable Desktop Alerts</button>
            </div>
            
            <div class="order-container" id="order-list">
                {% if not rows %}
                    <p id="no-requests" style="margin-top:20px; color:var(--text-muted);">No requests incoming yet.</p>
                {% endif %}
                {% for row in rows %}
                    <div class="order-card" data-order-id="{{ row[0] }}">
                        <div class="meta">ID: #{{ row[0] }} | Breed: <strong>{{ row[4] }}</strong> | Preference: <strong>{{ row[5] }}</strong></div>
                        <div style="font-size: 18px; font-weight: bold; margin-bottom: 4px;">{{ row[1] }}</div>
                        <p style="margin: 4px 0;">📍 {{ row[3] }}</p>
                        <p style="margin: 4px 0;">🥛 {{ row[6] }} Ltrs / Day for {{ row[7] }} Days</p>
                        <p style="margin-top: 8px;">📞 Call to Verify: <a class="phone-link" href="tel:{{ row[2] }}">{{ row[2] }}</a></p>
                    </div>
                {% endfor %}
            </div>
        </div>

        <script>
            let latestId = {{ max_id }};
            let totalCount = {{ rows|length }};

            // Request permission for Desktop Notifications
            function requestNotificationPermission() {
                if ("Notification" in window) {
                    Notification.requestPermission().then(permission => {
                        if (permission === "granted") {
                            document.getElementById('notif-btn').style.display = 'none';
                        }
                    });
                }
            }

            // Hide button if already permitted
            if ("Notification" in window && Notification.permission === "granted") {
                document.getElementById('notif-btn').style.display = 'none';
            }

            // Synthesize notification chime using Web Audio API
            function playChime() {
                try {
                    const audioCtx = new (window.AudioContext || window.webkitAudioContext)();
                    
                    // Note 1: C5
                    const osc1 = audioCtx.createOscillator();
                    const gain1 = audioCtx.createGain();
                    osc1.type = 'sine';
                    osc1.frequency.setValueAtTime(523.25, audioCtx.currentTime);
                    gain1.gain.setValueAtTime(0.1, audioCtx.currentTime);
                    gain1.gain.exponentialRampToValueAtTime(0.01, audioCtx.currentTime + 0.3);
                    osc1.connect(gain1);
                    gain1.connect(audioCtx.destination);
                    osc1.start();
                    osc1.stop(audioCtx.currentTime + 0.3);
                    
                    // Note 2: E5
                    setTimeout(() => {
                        const osc2 = audioCtx.createOscillator();
                        const gain2 = audioCtx.createGain();
                        osc2.type = 'sine';
                        osc2.frequency.setValueAtTime(659.25, audioCtx.currentTime);
                        gain2.gain.setValueAtTime(0.1, audioCtx.currentTime);
                        gain2.gain.exponentialRampToValueAtTime(0.01, audioCtx.currentTime + 0.4);
                        osc2.connect(gain2);
                        gain2.connect(audioCtx.destination);
                        osc2.start();
                        osc2.stop(audioCtx.currentTime + 0.4);
                    }, 120);
                } catch (e) {
                    console.log("Audio chime failed to play", e);
                }
            }

            // Display floating Toast Notification
            function showToast(order) {
                const container = document.getElementById('toast-container');
                const toast = document.createElement('div');
                toast.className = 'toast';
                toast.innerHTML = `
                    <div style="font-weight:bold; margin-bottom: 2px;">🚨 New Order!</div>
                    <div style="font-size:13px;">${order.name} has ordered ${order.volume}L of ${order.breed}</div>
                `;
                container.appendChild(toast);
                setTimeout(() => toast.classList.add('show'), 50);
                setTimeout(() => {
                    toast.classList.remove('show');
                    setTimeout(() => toast.remove(), 400);
                }, 4000);
            }

            // Trigger OS / Browser level push notification
            function showDesktopNotification(order) {
                if ("Notification" in window && Notification.permission === "granted") {
                    new Notification("🚨 New Order Received!", {
                        body: `${order.name} - ${order.volume}L / Day of ${order.breed}.`,
                        icon: "https://images.unsplash.com/photo-1570042225831-d98fa7577f1e?auto=format&fit=crop&w=128&q=80"
                    });
                }
            }

            // Polling function
            function pollOrders() {
                fetch(`/dashboard/api/new-orders?since_id=${latestId}`)
                    .then(res => res.json())
                    .then(data => {
                        if (data.orders && data.orders.length > 0) {
                            // Sound Chime
                            playChime();
                            
                            // Remove empty placeholder if it exists
                            const noReq = document.getElementById('no-requests');
                            if (noReq) noReq.remove();

                            const orderList = document.getElementById('order-list');
                            
                            data.orders.forEach(order => {
                                // Create order card
                                const card = document.createElement('div');
                                card.className = 'order-card new-order-flash';
                                card.setAttribute('data-order-id', order.id);
                                card.innerHTML = `
                                    <div class="meta">ID: #${order.id} | Breed: <strong>${order.breed}</strong> | Preference: <strong>${order.time_pref}</strong></div>
                                    <div style="font-size: 18px; font-weight: bold; margin-bottom: 4px;">${order.name}</div>
                                    <p style="margin: 4px 0;">📍 ${order.address}</p>
                                    <p style="margin: 4px 0;">🥛 ${order.volume} Ltrs / Day for ${order.duration} Days</p>
                                    <p style="margin-top: 8px;">📞 Call to Verify: <a class="phone-link" href="tel:${order.phone}">${order.phone}</a></p>
                                `;
                                // Prepend card
                                orderList.insertBefore(card, orderList.firstChild);

                                // Trigger Alerts
                                showToast(order);
                                showDesktopNotification(order);

                                // Update counters
                                if (order.id > latestId) {
                                    latestId = order.id;
                                }
                                totalCount++;
                            });

                            document.getElementById('total-count').innerText = totalCount;
                        }
                    })
                    .catch(err => console.error("Error polling orders:", err));
            }

            // Poll every 4 seconds
            setInterval(pollOrders, 4000);
        </script>
    </body>
    </html>
    '''
    return render_template_string(html_template, rows=rows, max_id=max_id)

# Static file routers to serve your HTML pages on the same port
@app.route('/')
def home(): return open('index.html').read()
@app.route('/order.html')
def order_page(): return open('order.html').read()
@app.route('/billing.html')
def bill_page(): return open('billing.html').read()
@app.route('/qna.html')
@app.route('/qna')
def qna_page(): return open('qna.html').read()
@app.route('/app-intro.html')
@app.route('/app-intro')
def app_intro(): return open('app_intro.html').read()

@app.route('/images/<path:filename>')
def serve_images(filename):
    return send_from_directory('images', filename)

init_db()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)