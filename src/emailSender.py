# src/emailSender.py
import os
import pickle
import base64
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build


class GmailSender:
    def __init__(self):
        self.SCOPES = ['https://www.googleapis.com/auth/gmail.send']
        self.service = self.get_gmail_service()
        self.resume_path = "resume/resume.pdf"  # Update this path

        # Email subject
        self.subject = "Could I be your next Recruit?"

        # Email template with exact spacing preserved
        # HTML template with proper styling
        self.template = """
        <div style="font-family: Arial, sans-serif; font-size: 14px; line-height: 1.6; color: #000;">
            <p>Dear {Recruiter_Name},</p>

            <p>I am Krishnna from Boston. I recently graduated from Northeastern University with a master's degree in computer software engineering.</p>

            <p>I am reaching out to express my strong interest in joining {Company_Name} as a Software Engineer. I would love to learn more about and be considered for any open positions that you might currently be recruiting for. If not, I would greatly appreciate it if you could forward my profile to someone who might be.</p>

            <p>I have attached my resume to this email for your review. Beyond my resume, I have been learning more about Gen AI and its integration with software through personal projects. I am always excited to tackle problems and hungry for experience and learning in the process.</p>

            <p>I am excited by the work {Company_Name} is doing, and I truly believe my hard work and grit can make a difference there.</p>

            <p>Thank you for taking the time and looking forward to speaking with you,<br>
            Krishnna Sarrdah</p>

            <p style="font-style: italic;">P.S I understand if you do not appreciate being contacted this way, and apologize for the same</p>
        </div>
        """

    def get_gmail_service(self):
        """Set up Gmail API service with OAuth 2.0"""
        creds = None

        if os.path.exists('token.pickle'):
            with open('token.pickle', 'rb') as token:
                creds = pickle.load(token)

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    'credentials.json', self.SCOPES)
                creds = flow.run_local_server(port=0)

            with open('token.pickle', 'wb') as token:
                pickle.dump(creds, token)

        return build('gmail', 'v1', credentials=creds)

    def create_message_with_attachment(self, to_email, subject, body):
        """Create email message with PDF attachment"""
        message = MIMEMultipart()
        message['to'] = to_email
        message['subject'] = subject

        # Add body
        message.attach(MIMEText(body, 'html'))

        # Add resume attachment
        try:
            with open(self.resume_path, 'rb') as f:
                pdf = MIMEApplication(f.read(), _subtype='pdf')
                pdf.add_header('Content-Disposition', 'attachment',
                               filename=os.path.basename(self.resume_path))
                message.attach(pdf)
        except Exception as e:
            print(f"Warning: Could not attach resume: {str(e)}")
            print("Email will be sent without attachment.")

        # Encode the message
        raw = base64.urlsafe_b64encode(message.as_bytes())
        return {'raw': raw.decode()}

    def send_email(self, to_email="kcsarrdahspamacc@gmail.com",
                   recruiter_name="Test", company_name="TestCompany"):
        """Send email with resume attachment"""
        try:
            # Verify resume exists
            if not os.path.exists(self.resume_path):
                print(f"Warning: Resume not found at {self.resume_path}")
                return False

            # Create message body with replaced placeholders
            body = self.template.format(
                Recruiter_Name=recruiter_name,
                Company_Name=company_name
            )

            # Create the message with attachment
            message = self.create_message_with_attachment(
                to_email,
                self.subject,
                body
            )

            # Send the email
            sent = self.service.users().messages().send(
                userId='me',
                body=message
            ).execute()

            print(f"Email sent successfully to {to_email}!")
            print(f"Recruiter: {recruiter_name}")
            print(f"Company: {company_name}")
            return True

        except Exception as e:
            print(f"Error sending email: {str(e)}")
            return False


def send_test_email():
    """Function to be called from main script"""
    try:
        sender = GmailSender()
        # You can update these test values as needed
        return sender.send_email(
            to_email="kcsarrdahspamacc@gmail.com",
            recruiter_name="John",
            company_name="Google"
        )
    except Exception as e:
        print(f"Error: {str(e)}")
        return False


if __name__ == "__main__":
    # Test the sender
    send_test_email()