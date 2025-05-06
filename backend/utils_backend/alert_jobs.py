# FILE: backend/alerts/alert_jobs.py

import os
import smtplib
import psycopg2
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

# Load env vars
load_dotenv(dotenv_path=os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".env")))

EMAIL_HOST = "smtp.gmail.com"
EMAIL_PORT = 587
EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASS = os.getenv("EMAIL_PASS")

# PostgreSQL Connection
def get_pg_connection():
    return psycopg2.connect(
        host=os.getenv("POSTGRES_HOST"),
        port=os.getenv("POSTGRES_PORT"),
        dbname=os.getenv("POSTGRES_DB"),
        user=os.getenv("POSTGRES_USER"),
        password=os.getenv("POSTGRES_PASSWORD")
    )

# 🔔 Email utility
def send_email(to_email: str, subject: str, body: str):
    msg = MIMEMultipart()
    msg["From"] = EMAIL_USER
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "html", _charset="utf-8"))

    try:
        with smtplib.SMTP(EMAIL_HOST, EMAIL_PORT) as server:
            server.starttls()
            server.login(EMAIL_USER, EMAIL_PASS)
            server.send_message(msg)
            print(f"✅ Email sent to {to_email}")
    except Exception as e:
        print(f"❌ Email sending failed: {e}")

# 🔧 Email body wrapper
def wrap_email_body(content: str, footer_note: str = "Track your health with CareMate 🩺"):
    header_image_url = "https://raw.githubusercontent.com/Vemana-Northeastern/Big_Data_Final_Project/main/backend/utils_backend/Nutrition_Agent2.png"

    return f"""
    <html>
    <head>
        <style>
            body {{
                font-family: 'Segoe UI', Roboto, sans-serif;
                background-color: #f4f6f8;
                margin: 0;
                padding: 0;
            }}
            .container {{
                max-width: 600px;
                margin: 40px auto;
                background-color: #ffffff;
                border-radius: 12px;
                overflow: hidden;
                box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
            }}
            .header {{
                background-color: #2f855a;
                padding: 20px;
                text-align: center;
                color: white;
                font-size: 24px;
                font-weight: bold;
            }}
            .banner img {{
                width: 100%;
                height: auto;
                display: block;
            }}
            .content {{
                padding: 30px;
                color: #333;
                line-height: 1.7;
                font-size: 16px;
            }}
            .footer {{
                padding: 20px;
                background-color: #f1f5f9;
                text-align: center;
                font-size: 13px;
                color: #888;
            }}
            a.button {{
                display: inline-block;
                margin-top: 20px;
                background-color: #2f855a;
                color: white !important;
                padding: 10px 18px;
                border-radius: 8px;
                text-decoration: none;
                font-weight: 600;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="banner">
                <img src="{header_image_url}" alt="Health Tracker Banner" style="width: 200px; height: auto;" />
            </div>
            <div class="content">
                {content}
                <div style="margin-top: 20px;">
                    <a href="#" class="button">Go to Nutrition Planner</a>
                </div>
            </div>
            <div class="footer">
                {footer_note}<br/>
                © 2025 CareMate. All rights reserved.
            </div>
        </div>
    </body>
    </html>
    """

# 🔔 1. Daily Nutrition Summary
def send_daily_summary():
    today = datetime.now().date()
    conn = get_pg_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT u.username, u.email, u.tdee,
               SUM(n.calories_per_serving_kcal) AS total_kcal,
               COUNT(n.recipe_name) AS meal_count
        FROM users u
        LEFT JOIN user_nutrition_logs n
        ON u.username = n.username AND n.date = %s
        GROUP BY u.username, u.email, u.tdee;
    """, (today,))
    users = cursor.fetchall()

    for username, email, tdee, total_kcal, meal_count in users:
        total_kcal = total_kcal or 0
        content = f"""👋 Hello <b>{username}</b>,<br><br>
        Here's your daily nutrition summary for <b>{today}</b>:<br><br>
        📌 <b>Meals Logged:</b> {meal_count}<br>
        🔥 <b>Calories Consumed:</b> {total_kcal} kcal<br>
        🎯 <b>Your TDEE Goal:</b> {tdee} kcal<br><br>
        {('✅ You met your goal!' if abs(total_kcal - tdee) < 200 else '⚠️ You were off your goal today. Try balancing tomorrow.')}<br><br>
        Open the app → <b>Nutrition Planner ✅</b>
        """
        send_email(email, f"📊 Daily Nutrition Summary - {today}", wrap_email_body(content))

    cursor.close()
    conn.close()

# 🔔 2. Low Logging Alert
def send_low_logging_alert():
    today = datetime.now().date()
    check_date = today - timedelta(days=2)

    conn = get_pg_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT u.username, u.email
        FROM users u
        LEFT JOIN user_nutrition_logs n
        ON u.username = n.username AND n.date >= %s
        GROUP BY u.username, u.email
        HAVING COUNT(n.recipe_name) = 0;
    """, (check_date,))
    users = cursor.fetchall()

    for username, email in users:
        content = f"""👋 Hey <b>{username}</b>,<br><br>
        We noticed you haven’t logged any meals in the last few days (since <b>{check_date}</b>).<br><br>
        📅 Log your meals to stay on track.<br>
        🧠 Stay consistent and beat your goals!<br><br>
        Open the app → <b>Nutrition Planner 💪</b>
        """
        send_email(email, "⏰ Time to Log Your Meals!", wrap_email_body(content))

    cursor.close()
    conn.close()

# 🔔 3. Weekly Nutrition Digest
def send_weekly_digest():
    today = datetime.now().date()
    week_start = today - timedelta(days=6)

    conn = get_pg_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT u.username, u.email,
               ROUND(AVG(n.calories_per_serving_kcal)::numeric, 2) AS avg_kcal,
               COUNT(DISTINCT n.date) AS active_days,
               MAX(n.recipe_name) AS last_recipe
        FROM users u
        LEFT JOIN user_nutrition_logs n
        ON u.username = n.username AND n.date >= %s
        GROUP BY u.username, u.email;
    """, (week_start,))
    users = cursor.fetchall()

    for username, email, avg_kcal, active_days, last_recipe in users:
        content = f"""📅 <b>Weekly Digest</b> for <b>{username}</b> ({week_start} to {today})<br><br>
        🔥 <b>Avg. Calorie Intake:</b> {avg_kcal or 0} kcal/day<br>
        📆 <b>Active Days:</b> {active_days}<br>
        🍽️ <b>Last Logged Meal:</b> {last_recipe or 'None'}<br><br>
        🏆 Keep pushing toward your goals. We believe in you!<br>
        ✅ Open the app and plan your week ahead.
        """
        send_email(email, "📊 Your Weekly Nutrition Digest", wrap_email_body(content))

    cursor.close()
    conn.close()

# 🔔 4. Critical Calorie Warning
def send_critical_calorie_warning():
    today = datetime.now().date()
    week_start = today - timedelta(days=6)

    conn = get_pg_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT u.username, u.email, u.tdee,
               ROUND(AVG(n.calories_per_serving_kcal)::numeric, 2) AS avg_kcal
        FROM users u
        LEFT JOIN user_nutrition_logs n
        ON u.username = n.username AND n.date >= %s
        GROUP BY u.username, u.email, u.tdee
        HAVING AVG(n.calories_per_serving_kcal) < 0.7 * u.tdee;
    """, (week_start,))
    users = cursor.fetchall()

    for username, email, tdee, avg_kcal in users:
        content = f"""🚨 <b>URGENT:</b> Your average calorie intake is critically low<br><br>
        Hello <b>{username}</b>,<br><br>
        Your weekly average calorie intake is <b>{avg_kcal} kcal</b>, while your goal (TDEE) is <b>{tdee} kcal</b>.<br><br>
        ⚠️ Please ensure you're eating enough to meet your body's needs.<br><br>
        Let’s get back on track → <b>Log your meals now!</b><br>
        Your health matters 💪
        """
        send_email(email, "🚨 Low Calorie Intake Alert!", wrap_email_body(content))

    cursor.close()
    conn.close()