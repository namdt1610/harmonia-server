from django.test import TestCase, override_settings
from django.contrib.auth.models import User
from django.core import mail
from unittest.mock import patch
from .services import EmailService, AuthService


class EmailServiceTest(TestCase):
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
    
    @override_settings(
        EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend',
        FRONTEND_URL='http://localhost:3000'
    )
    def test_send_forgot_password_email_success(self):
        """Test sending forgot password email successfully"""
        result = EmailService.send_forgot_password_email('test@example.com')
        
        self.assertTrue(result)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ['test@example.com'])
        self.assertIn('Đặt lại mật khẩu', mail.outbox[0].subject)
    
    @override_settings(
        EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend'
    )
    def test_send_forgot_password_email_nonexistent_user(self):
        """Test sending forgot password email for non-existent user"""
        result = EmailService.send_forgot_password_email('nonexistent@example.com')
        
        # Should return True for security (don't reveal if email exists)
        self.assertTrue(result)
        # But no email should be sent
        self.assertEqual(len(mail.outbox), 0)
    
    @override_settings(
        EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend',
        FRONTEND_URL='http://localhost:3000'
    )
    def test_send_welcome_email_success(self):
        """Test sending welcome email successfully"""
        result = EmailService.send_welcome_email(self.user)
        
        self.assertTrue(result)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ['test@example.com'])
        self.assertIn('Chào mừng', mail.outbox[0].subject)


class AuthServiceTest(TestCase):
    
    @override_settings(
        EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend'
    )
    def test_create_user_with_welcome_email(self):
        """Test creating user and sending welcome email"""
        user = AuthService.create_user_with_welcome_email(
            username='newuser',
            email='newuser@example.com',
            password='newpass123'
        )
        
        # Check user was created
        self.assertIsInstance(user, User)
        self.assertEqual(user.username, 'newuser')
        self.assertEqual(user.email, 'newuser@example.com')
        
        # Check welcome email was sent
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ['newuser@example.com'])
    
    @override_settings(
        EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend'
    )
    def test_handle_password_reset_request(self):
        """Test handling password reset request"""
        User.objects.create_user(
            username='resetuser',
            email='reset@example.com',
            password='oldpass123'
        )
        
        result = AuthService.handle_password_reset_request('reset@example.com')
        
        self.assertTrue(result)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ['reset@example.com'])
