from django.core.cache import cache
from rest_framework.authentication import get_authorization_header
from rest_framework.exceptions import AuthenticationFailed
from django.contrib.auth.models import User
import logging
import jwt
from django.conf import settings
import re

logger = logging.getLogger(__name__)

class RedisTokenAuthentication:
    def __init__(self):
        # Define paths that don't require authentication
        self.exempt_urls = [
            r'^/api/auth/login/',
            r'^/api/auth/register/',
            r'^/api/auth/logout/',
            r'^/api/auth/token/',
            r'^/api/auth/token/refresh/',
            r'^/api/auth/google/',
            r'^/admin/',
        ]

    def authenticate(self, request):
        # Check if the path is exempt from authentication
        path = request.path_info
        for exempt_url in self.exempt_urls:
            if re.match(exempt_url, path):
                logger.debug(f"Path {path} is exempt from authentication")
                return None
                
        # First check if token is in cookies
        access_token = request.COOKIES.get('access_token')
        
        # Debug the cookie value
        logger.debug(f"Cookie access_token: {access_token}")
        
        # If not in cookies, try to get from Authorization header
        if not access_token:
            try:
                auth_header = get_authorization_header(request).decode("utf-8")
                if not auth_header:
                    logger.debug("No Authorization header found")
                    return None
                
                access_token = auth_header.split("Bearer ")[-1]
                logger.debug(f"Authorization header token: {access_token}")
            except Exception as e:
                logger.debug(f"Error processing auth header: {str(e)}")
                return None
        
        if not access_token:
            logger.debug("No token found in either cookies or header")
            return None

        # First try to find the token in Redis cache (custom token approach)
        user_id = cache.get(f"auth_token_{access_token}")
        logger.debug(f"User ID from Redis cache: {user_id}")
        
        # If not found in Redis, try to decode as JWT
        if not user_id:
            try:
                # Try to decode JWT token
                logger.debug("Attempting to decode JWT token")
                decoded_token = jwt.decode(
                    access_token, 
                    settings.SECRET_KEY, 
                    algorithms=["HS256"],
                    options={"verify_signature": True}
                )
                user_id = decoded_token.get('user_id')
                logger.debug(f"Decoded JWT token user_id: {user_id}")
            except jwt.PyJWTError as e:
                logger.debug(f"JWT decode error: {str(e)}")
                user_id = None
        
        if not user_id:
            logger.debug("Token not found in cache or invalid JWT")
            raise AuthenticationFailed("Token không hợp lệ hoặc đã hết hạn")
        
        try:
            user = User.objects.get(id=user_id)
            logger.debug(f"Authenticated user: {user.username}")
            return (user, None)
        except User.DoesNotExist:
            logger.debug(f"User with ID {user_id} not found")
            raise AuthenticationFailed("User không tồn tại")
