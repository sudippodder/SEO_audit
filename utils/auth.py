import bcrypt
import smtplib
from email.mime.text import MIMEText
import os
import random
import string

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(password: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
    except ValueError:
        return False

def generate_temp_password(length=10) -> str:
    chars = string.ascii_letters + string.digits + "!@#$%^&*"
    return ''.join(random.choice(chars) for _ in range(length))

def send_forgot_password_email(to_email: str, new_password: str):
    smtp_server = os.getenv("SMTP_SERVER")
    smtp_port = os.getenv("SMTP_PORT", "587")
    smtp_user = os.getenv("SMTP_USER")
    smtp_pass = os.getenv("SMTP_PASS")

    if not all([smtp_server, smtp_user, smtp_pass]):
        print(f"\n[TEST MODE] Forgot Password Email")
        print(f"To: {to_email}")
        print(f"Your new temporary password is: {new_password}\n")
        return True

    try:
        msg = MIMEText(f"Your new temporary password is: {new_password}\nPlease login and change it immediately.")
        msg['Subject'] = 'Password Reset - SEO Audit Tool'
        msg['From'] = smtp_user
        msg['To'] = to_email

        server = smtplib.SMTP(smtp_server, int(smtp_port))
        server.starttls()
        server.login(smtp_user, smtp_pass)
        server.send_message(msg)
        server.quit()
        return True
    except Exception as e:
        print(f"Failed to send email: {e}")
        return False
