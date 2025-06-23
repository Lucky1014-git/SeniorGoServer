import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Email account credentials
sender_email = "vkalpsm@gmail.com"
receiver_email = "vkalps@gmail.com"
app_password = "wkmu kctm vpje coib"  # Use App Password, NOT your Gmail login password

# Email content
subject = "Test Email from Python"
body = "Hi there,\n\nThis is a test email sent from a Python script!"

# Set up MIME
msg = MIMEMultipart()
msg['From'] = sender_email
msg['To'] = receiver_email
msg['Subject'] = subject
msg.attach(MIMEText(body, 'plain'))

# Send via Gmail SMTP
try:
    with smtplib.SMTP("smtp.gmail.com", 587) as server:
        server.starttls()  # Secure the connection
        server.login(sender_email, app_password)
        server.send_message(msg)
        print("✅ Email sent successfully!")
except Exception as e:
    print(f"❌ Failed to send email: {e}")
