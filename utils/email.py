import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

def send(subject, body, recipient_email, html_attachment=None):
    """
    Sends an email with optional HTML attachment using Gmail SMTP.
    
    Args:
        subject (str): Email subject
        body (str): Email body (HTML format)
        recipient_email (str): Recipient's email address
        html_attachment (str, optional): HTML content to attach
    
    Returns:
        bool: True if email sent successfully, False otherwise
    """
    try:
        # Load environment variables
        load_dotenv()
        
        # Get email credentials
        smtp_server = "smtp.gmail.com"
        smtp_port = 587
        email_address = os.getenv("email_address")
        email_password = os.getenv("email_password")
        
        # Validate environment variables
        if not email_address or not email_password:
            raise ValueError("Email address or password not found in environment variables")
            
        # Create message
        msg = MIMEMultipart()
        msg['From'] = email_address
        msg['To'] = recipient_email
        msg['Subject'] = subject
        
        # Attach the body
        msg.attach(MIMEText(body, 'html'))
        
        # Attach HTML content if provided
        if html_attachment:
            part = MIMEText(html_attachment, 'html')
            part.add_header('Content-Disposition', 'attachment', filename="report.html")
            msg.attach(part)
        
        # Send the email
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(email_address, email_password)
            server.sendmail(email_address, recipient_email, msg.as_string())
            print(f"Email sent to {recipient_email} with subject: {subject}")
            return True
            
    except ValueError as e:
        print(f"Configuration error: {e}")
    except smtplib.SMTPAuthenticationError:
        print("Authentication failed. Check your email and password/app password.")
    except smtplib.SMTPException as e:
        print(f"SMTP error occurred: {e}")
    except Exception as e:
        print(f"Error: {e}")
    
    return False

# Example usage:
# subject = "Political Risk Analysis Report"
# body = "<h1>Your Political Risk Analysis Report</h1><p>Please find the attached report.</p>"
# recipient_email = "example@example.com"
# html_attachment = result['report']['html']  # Your HTML content
# send_email_with_attachment(subject, body, recipient_email, html_attachment)