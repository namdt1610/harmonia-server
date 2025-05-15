from rest_framework import serializers
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from django.core.cache import cache
import secrets
import uuid
import logging

logger = logging.getLogger(__name__)

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "email"]

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ["username", "password", "email"]
    
    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Email đã tồn tại!")
        return value
    
    def validate_username(self, value):
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("Username đã tồn tại!")
        return value

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data["username"],
            email=validated_data["email"],
            password=validated_data["password"]
        )
        return user

class LoginSerializer(serializers.Serializer):
    username_or_email = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        username_or_email = data.get("username_or_email")
        password = data.get("password")
        
        # Check if username_or_email is an email address
        if '@' in username_or_email:
            try:
                user = User.objects.get(email=username_or_email)
                username = user.username
            except User.DoesNotExist:
                raise serializers.ValidationError("Email không tồn tại hoặc mật khẩu không đúng") 
        else:
            username = username_or_email
            
        user = authenticate(username=username, password=password)
        
        if not user:
            raise serializers.ValidationError("Username hoặc password không đúng")
        
        # Generate token và lưu vào Redis
        refresh_token = str(uuid.uuid4())
        access_token = secrets.token_hex(32)

        # Lưu token vào Redis
        cache.set(f"auth_token_{access_token}", user.id, timeout=86400)  # 24 hours
        cache.set(f"refresh_token_{refresh_token}", user.id, timeout=604800)  # 7 days
        
        logger.debug(f"Setting tokens in cache for user {user.id}:")
        logger.debug(f"Access token key: auth_token_{access_token}")
        logger.debug(f"Refresh token key: refresh_token_{refresh_token}")
        
        # Trả kết quả
        user_data = {
            "id": user.id,
            "username": user.username,
            "email": user.email
        }
    
        return {
            "user": user_data,
            "access": access_token,
            "refresh": refresh_token
        }
    
        
