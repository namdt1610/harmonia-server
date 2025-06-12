import logging
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth.models import User
from django.conf import settings

logger = logging.getLogger(__name__)


class EmailService:
    """
    Service class for handling all email-related functionality
    """
    
    @staticmethod
    def send_forgot_password_email(email: str) -> bool:
        """
        Send forgot password email to user
        
        Args:
            email (str): User's email address
            
        Returns:
            bool: True if email sent successfully, False otherwise
        """
        try:
            # Check if user exists
            try:
                user = User.objects.get(email=email)
            except User.DoesNotExist:
                # Don't reveal if email exists or not for security
                logger.warning(f"Password reset attempted for non-existent email: {email}")
                return True
            
            # Generate password reset token
            token = default_token_generator.make_token(user)
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            
            # Create reset URL (frontend URL)
            reset_url = f"{settings.FRONTEND_URL}/reset-password?uid={uid}&token={token}"
            
            # Email subject and message
            subject = "Reset password for Harmonia"
            
            # Try to render HTML template, fallback to plain text
            try:
                html_message = render_to_string('emails/forgot_password.html', {
                    'user': user,
                    'reset_url': reset_url,
                    'site_name': 'Harmonia',
                })
            except Exception as e:
                logger.warning(f"Could not render HTML template: {e}")
                html_message = None
            
            # Plain text message as fallback
            message = EmailService._get_plain_text_message(user.username, reset_url)
            
            # Send email
            send_mail(
                subject=subject,
                message=message,
                html_message=html_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[email],
                fail_silently=False,
            )
            
            logger.info(f"Password reset email sent to: {email}")
            return True
            
        except Exception as e:
            logger.error(f"Error sending password reset email to {email}: {str(e)}")
            return False
    
    @staticmethod
    def _get_plain_text_message(username: str, reset_url: str) -> str:
        """
        Generate plain text email message
        
        Args:
            username (str): User's username
            reset_url (str): Password reset URL
            
        Returns:
            str: Plain text email message
        """
        return f"""
Hello {username},

You have requested to reset your Harmonia account password.

Click the link below to reset your password:
{reset_url}

This link will expire in 24 hours.

If you did not request a password reset, please ignore this email.

Thank you,
Harmonia Team
        """
    
    @staticmethod
    def send_welcome_email(user: User) -> bool:
        """
        Send welcome email to new user
        
        Args:
            user (User): User instance
            
        Returns:
            bool: True if email sent successfully, False otherwise
        """
        try:
            subject = "Welcome to Harmonia!"
            
            # Try to render HTML template
            try:
                html_message = render_to_string('emails/welcome.html', {
                    'user': user,
                    'site_name': 'Harmonia',
                    'site_url': settings.FRONTEND_URL,
                })
            except Exception as e:
                logger.warning(f"Could not render welcome HTML template: {e}")
                html_message = None
            
            # Plain text message
            message = f"""
Hello {user.username},

Welcome to Harmonia!

Thank you for registering. You can start exploring music right now.

Access: {settings.FRONTEND_URL}

Thank you,
Harmonia Team
            """
            
            send_mail(
                subject=subject,
                message=message,
                html_message=html_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                fail_silently=False,
            )
            
            logger.info(f"Welcome email sent to: {user.email}")
            return True
            
        except Exception as e:
            logger.error(f"Error sending welcome email to {user.email}: {str(e)}")
            return False


class AuthService:
    """
    Service class for authentication-related business logic
    """
    
    @staticmethod
    def create_user_with_welcome_email(username: str, email: str, password: str) -> User:
        """
        Create user and send welcome email
        
        Args:
            username (str): Username
            email (str): Email address
            password (str): Password
            
        Returns:
            User: Created user instance
        """
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password
        )
        
        # Send welcome email asynchronously (can be improved with Celery)
        EmailService.send_welcome_email(user)
        
        return user
    
    @staticmethod
    def handle_password_reset_request(email: str) -> bool:
        """
        Handle password reset request
        
        Args:
            email (str): User's email address
            
        Returns:
            bool: True if handled successfully
        """
        return EmailService.send_forgot_password_email(email) 