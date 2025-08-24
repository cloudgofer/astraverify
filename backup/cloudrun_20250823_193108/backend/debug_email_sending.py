#!/usr/bin/env python3
"""
Debug script to test email sending and identify delivery issues
"""

import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

def test_email_sending():
    """Test email sending with detailed logging"""
    
    # Email configuration
    EMAIL_SENDER = 'hi@astraverify.com'
    EMAIL_SMTP_SERVER = 'smtp.gmail.com'
    EMAIL_SMTP_PORT = 587
    EMAIL_USERNAME = 'hi@astraverify.com'
    
    # Get password from environment
    EMAIL_PASSWORD = os.environ.get('EMAIL_PASSWORD')
    
    if not EMAIL_PASSWORD:
        print("❌ EMAIL_PASSWORD not set in environment")
        return False
    
    # Test email details
    to_email = input("Enter test email address: ").strip()
    if not to_email:
        print("❌ No email address provided")
        return False
    
    print(f"\n🧪 Testing email sending to: {to_email}")
    print("=" * 50)
    
    try:
        # Create test message
        msg = MIMEMultipart('alternative')
        msg['From'] = f'AstraVerify <{EMAIL_SENDER}>'
        msg['To'] = to_email
        msg['Subject'] = f'Email Test - {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}'
        
        # Create HTML content
        html_content = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: #f5f5f5; }}
                .container {{ max-width: 600px; margin: 0 auto; background: white; border-radius: 8px; padding: 30px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
                .header {{ text-align: center; margin-bottom: 30px; }}
                .test-info {{ margin: 20px 0; padding: 15px; background: #e3f2fd; border-radius: 5px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🧪 Email Test</h1>
                    <p>This is a test email from AstraVerify</p>
                </div>
                
                <div class="test-info">
                    <h3>Test Details:</h3>
                    <p><strong>Sent to:</strong> {to_email}</p>
                    <p><strong>Sent from:</strong> {EMAIL_SENDER}</p>
                    <p><strong>SMTP Server:</strong> {EMAIL_SMTP_SERVER}:{EMAIL_SMTP_PORT}</p>
                    <p><strong>Timestamp:</strong> {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
                </div>
                
                <div class="test-info">
                    <h3>Domain Link Test:</h3>
                    <p>Test domain: <a href="https://astraverify.com?domain=example.com" style="color: #007bff; text-decoration: none; font-weight: bold; border-bottom: 1px dotted #007bff;">example.com</a></p>
                </div>
                
                <div class="footer">
                    <p>If you receive this email, the email configuration is working correctly!</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        # Attach HTML content
        html_part = MIMEText(html_content, 'html')
        msg.attach(html_part)
        
        print("📧 Connecting to SMTP server...")
        server = smtplib.SMTP(EMAIL_SMTP_SERVER, EMAIL_SMTP_PORT)
        print("✅ SMTP connection established")
        
        print("🔐 Starting TLS...")
        server.starttls()
        print("✅ TLS started")
        
        print("🔑 Authenticating...")
        server.login(EMAIL_USERNAME, EMAIL_PASSWORD)
        print("✅ Authentication successful")
        
        print("📤 Sending email...")
        text = msg.as_string()
        server.sendmail(EMAIL_SENDER, to_email, text)
        print("✅ Email sent successfully")
        
        server.quit()
        print("✅ SMTP connection closed")
        
        print("\n" + "=" * 50)
        print("✅ Email test completed successfully!")
        print(f"📧 Email sent to: {to_email}")
        print(f"📧 Email sent from: {EMAIL_SENDER}")
        print(f"🕐 Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        print("\n📝 Troubleshooting tips:")
        print("1. Check your spam/junk folder")
        print("2. Check if the email address is correct")
        print("3. Wait a few minutes for delivery")
        print("4. Check your email provider's settings")
        
        return True
        
    except smtplib.SMTPAuthenticationError as e:
        print(f"❌ Authentication failed: {e}")
        print("   Check your EMAIL_PASSWORD")
        return False
    except smtplib.SMTPRecipientsRefused as e:
        print(f"❌ Recipient refused: {e}")
        print("   Check the email address")
        return False
    except smtplib.SMTPSenderRefused as e:
        print(f"❌ Sender refused: {e}")
        print("   Check the sender email configuration")
        return False
    except smtplib.SMTPDataError as e:
        print(f"❌ Data error: {e}")
        print("   Check the email content")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def check_email_delivery():
    """Check common email delivery issues"""
    print("\n🔍 Email Delivery Checklist:")
    print("=" * 30)
    
    # Check environment
    email_password = os.environ.get('EMAIL_PASSWORD')
    print(f"✅ EMAIL_PASSWORD set: {bool(email_password)}")
    
    # Check SMTP server connectivity
    try:
        import socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = sock.connect_ex(('smtp.gmail.com', 587))
        sock.close()
        print(f"✅ SMTP server reachable: {result == 0}")
    except Exception as e:
        print(f"❌ SMTP server check failed: {e}")
    
    print("\n📧 Common delivery issues:")
    print("1. Email in spam/junk folder")
    print("2. Email provider blocking external emails")
    print("3. Incorrect email address")
    print("4. Email provider rate limiting")
    print("5. DNS issues")

if __name__ == "__main__":
    print("🧪 AstraVerify Email Debug Tool")
    print("=" * 40)
    
    check_email_delivery()
    
    print("\n" + "=" * 40)
    response = input("Run email test? (y/n): ").strip().lower()
    
    if response == 'y':
        test_email_sending()
    else:
        print("Test cancelled.")
