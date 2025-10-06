import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formataddr
from email.header import Header

# Check if variables from the previous cell are available
if 'email_server' in locals() and email_server and 'emails' in locals() and emails:
    smtp_server = email_server
    smtp_port = 25
    sender_domain = derived_domain if 'derived_domain' in locals() and derived_domain else "example.org"
    sender_email = f"helpdesk@{sender_domain}"
    sender_display = "Help Desk"

    # Use the first email found as the receiver
    receiver_email = sorted(emails)[0] if emails else "tvandenburg@example.org"

    print(f"Attempting to send test email to: {receiver_email} via server: {smtp_server}")

    msg = MIMEMultipart()
    msg["From"] = formataddr((str(Header(sender_display, "utf-8")), sender_email))
    msg["To"] = receiver_email
    msg["Subject"] = "Direct Send Test"

    # Request delivery notifications (DSN)
    # Headers for standard Read Receipt (Disposition-Notification-To) and Return Receipt (Return-Receipt-To)
    msg["Disposition-Notification-To"] = sender_email
    msg["Return-Receipt-To"] = sender_email

    msg.attach(MIMEText("This is a test email sent using the direct send method.", "plain"))

    try:
        with smtplib.SMTP(smtp_server, smtp_port, timeout=30) as server:
            server.ehlo()
            server.mail(sender_email)
            dsn_options = ['NOTIFY=SUCCESS,FAILURE,DELAY']
            server.rcpt(receiver_email, options=dsn_options)
            server.data(msg.as_string())

        print("Email sent successfully (DSN requested)!")

    except Exception as e:
        print(f"Failed to send email: {e}")

else:
    print("Email server or email list not available from the previous cell.")
    print("Please run the web scraping cell first.")