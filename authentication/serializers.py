from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from rest_framework import serializers
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_decode
from django.utils.encoding import force_str
import logging


logger = logging.getLogger(__name__)

class AuthUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'first_name', 'last_name', 'date_joined')
        read_only_fields = ('id', 'date_joined')

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
        
        # Generate JWT tokens using Simple JWT
        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)
        refresh_token = str(refresh)
        
        logger.debug(f"Generated JWT tokens for user {user.username}")
        
        # Trả kết quả
        user_data = {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "is_superuser": user.is_superuser,
        }
    
        return {
            "user": user_data,
            "access": access_token,
            "refresh": refresh_token
        }
    
class ForgotPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate_email(self, value):
        if not User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Email does not exist")
        return value

class ResetPasswordSerializer(serializers.Serializer):
    uid = serializers.CharField()
    token = serializers.CharField()
    new_password = serializers.CharField(min_length=6, write_only=True)
    confirm_password = serializers.CharField(min_length=6, write_only=True)

    def validate(self, data):
        uid = data.get('uid')
        token = data.get('token')
        new_password = data.get('new_password')
        confirm_password = data.get('confirm_password')

        # Check if passwords match
        if new_password != confirm_password:
            raise serializers.ValidationError("Passwords do not match")

        # Verify token and get user
        try:
            user_id = force_str(urlsafe_base64_decode(uid))
            user = User.objects.get(pk=user_id)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            raise serializers.ValidationError("Invalid reset link")

        # Check if token is valid
        if not default_token_generator.check_token(user, token):
            raise serializers.ValidationError("Invalid or expired reset link")

        data['user'] = user
        return data

    def save(self):
        user = self.validated_data['user']
        new_password = self.validated_data['new_password']
        user.set_password(new_password)
        user.save()
        return user
