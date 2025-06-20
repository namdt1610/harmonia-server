from django.db import models
from django.contrib.auth.models import BaseUserManager, User

class UserManager(BaseUserManager):
      def create_user(self, email, password = None, **extra_fields):
        if not email:
            raise ValueError('This email is not valid')
        email = self.normalize_email(email)
        user = self.model(email = email, **extra_fields)
        user.set_password(password)
        user.save()
        return user
      
      def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self.create_user(email, password, **extra_fields)

class TokenBlacklist(models.Model):
    """Store blacklisted JWT tokens"""
    token = models.CharField(max_length=500, unique=True)
    blacklisted_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    
    class Meta:
        db_table = 'token_blacklist'
        
    def __str__(self):
        return f"Blacklisted token {self.pk}, expires: {self.expires_at}"
      