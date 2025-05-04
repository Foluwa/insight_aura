import requests
import smtplib
from email.message import EmailMessage
import os

def send_telegram_alert(message: str):
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    if not bot_token or not chat_id:
        return
    try:
        requests.post(
            f"https://api.telegram.org/bot{bot_token}/sendMessage",
            data={"chat_id": chat_id, "text": message}
        )
    except Exception as e:
        print(f"Telegram notification failed: {e}")

def send_slack_alert(message: str):
    slack_webhook = os.getenv("SLACK_WEBHOOK_URL")
    if not slack_webhook:
        return
    try:
        requests.post(
            slack_webhook,
            json={"text": message}
        )
    except Exception as e:
        print(f"Slack notification failed: {e}")

def send_email_alert(subject: str, body: str, to: str):
    smtp_host = os.getenv("SMTP_HOST")
    smtp_user = os.getenv("SMTP_USER")
    smtp_pass = os.getenv("SMTP_PASS")
    from_addr = os.getenv("EMAIL_FROM", smtp_user)

    if not smtp_host or not smtp_user or not smtp_pass:
        return

    try:
        msg = EmailMessage()
        msg.set_content(body)
        msg["Subject"] = subject
        msg["From"] = from_addr
        msg["To"] = to

        with smtplib.SMTP_SSL(smtp_host, 465) as server:
            server.login(smtp_user, smtp_pass)
            server.send_message(msg)
    except Exception as e:
        print(f"Email notification failed: {e}")