# alerts.py
import logging
import smtplib
from email.mime.text import MIMEText

# === Configuration: fill in your Gmail credentials ===
GMAIL_USER = "diyaaparbhoo09@gmail.com"
GMAIL_PASS = "waau pvcy eycw fkwv"
CC_RECIP   = "sssimjee@gmail.com" 
# ======================================================

logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s - %(levelname)s - %(message)s")

def send_email_alert(message):
    """Send a real email via Gmail SMTP."""
    subject = "🚨 Honeypot Alert"
    body = f"Intrusion detected:\n\n{message}"
    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = GMAIL_USER
    msg["To"] = GMAIL_USER  # send to yourself
    msg["Cc"] = CC_RECIP

    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.ehlo()
        server.starttls()
        server.login(GMAIL_USER, GMAIL_PASS)
        server.send_message(msg)
        server.quit()
        logging.info("📩 Email alert sent successfully")
    except Exception as e:
        logging.error(f"❌ Failed to send email alert: {e}")

def send_mqtt_alert(message):
    # Placeholder: simulate sending an MQTT notification
    print(f"[MQTT ALERT] {message}")

def trigger_led(message):
    # Placeholder: simulate turning on an LED/buzzer
    print(f"[LED BUZZER ALERT] {message}")
