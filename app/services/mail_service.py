import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app.config import get_settings

settings = get_settings()


class MailService:
    async def send_magic_link(self, email: str, token: str):
        magic_link_url = f"{settings.frontend_url}/auth/verify?token={token}"
        
        message = MIMEMultipart("alternative")
        message["Subject"] = "Your Login Link"
        message["From"] = settings.mail_from or settings.mail_username
        message["To"] = email
        
        html_content = f"""
        <html>
            <body>
                <h2>Login to Your Account</h2>
                <p>Click the button below to log in:</p>
                <a href="{magic_link_url}" style="
                    display: inline-block;
                    padding: 12px 24px;
                    background-color: #0052CC;
                    color: white;
                    text-decoration: none;
                    border-radius: 4px;
                ">Log In</a>
                <p>Or copy and paste this link: {magic_link_url}</p>
                <p>This link expires in 15 minutes.</p>
            </body>
        </html>
        """
        
        message.attach(MIMEText(html_content, "html"))
        
        if settings.debug:
            print(f"Magic link for {email}: {magic_link_url}")
            return
        
        await aiosmtplib.send(
            message,
            hostname=settings.mail_server,
            port=settings.mail_port,
            username=settings.mail_username,
            password=settings.mail_password,
            use_tls=settings.mail_use_tls
        )
    
    async def send_notification(self, email: str, subject: str, body: str):
        message = MIMEMultipart("alternative")
        message["Subject"] = subject
        message["From"] = settings.mail_from or settings.mail_username
        message["To"] = email
        
        message.attach(MIMEText(body, "html"))
        
        if settings.debug:
            print(f"Notification to {email}: {subject}")
            return
        
        await aiosmtplib.send(
            message,
            hostname=settings.mail_server,
            port=settings.mail_port,
            username=settings.mail_username,
            password=settings.mail_password,
            use_tls=settings.mail_use_tls
        )