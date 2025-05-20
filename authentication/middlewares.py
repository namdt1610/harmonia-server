from django.core.cache import cache
from rest_framework.authentication import get_authorization_header, BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from django.contrib.auth.models import User
import logging
import jwt
from django.conf import settings
import re
from rest_framework_simplejwt.tokens import RefreshToken, AccessToken, TokenError
from datetime import datetime, timezone, timedelta
from .models import TokenBlacklist

logger = logging.getLogger(__name__)

class JWTAuthentication(BaseAuthentication):
    def __init__(self):
        # Define paths that don't require authentication
        self.exempt_urls = [
            r'^/api/auth/login/$',
            r'^/api/auth/register/$',
            r'^/api/auth/logout/$',
            r'^/api/auth/token/$',
            r'^/api/auth/token/refresh/$',
            r'^/api/auth/google/$',
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
        access_token_str = request.COOKIES.get('access_token')
        refresh_token_str = request.COOKIES.get('refresh_token')
        
        # If not in cookies, try to get from Authorization header
        if not access_token_str:
            try:
                auth_header = get_authorization_header(request).decode("utf-8")
                if not auth_header:
                    logger.debug("No Authorization header found")
                    return None
                
                access_token_str = auth_header.split("Bearer ")[-1]
            except Exception as e:
                logger.debug(f"Error processing auth header: {str(e)}")
                return None
        
        if not access_token_str:
            logger.debug("No token found in either cookies or header")
            return None

        # Check if token is blacklisted
        if TokenBlacklist.objects.filter(token=access_token_str).exists():
            logger.debug(f"Token is blacklisted")
            raise AuthenticationFailed("Token has been revoked")

        # Verify access token
        try:
            # Validate JWT token
            access_token = AccessToken(access_token_str)
            user_id = access_token.payload.get('user_id')
            if not user_id:
                raise AuthenticationFailed("Invalid token - no user ID")
            
            user = User.objects.get(id=user_id)
            return (user, None)
        except TokenError as e:
            logger.debug(f"Access token error: {str(e)}")
            # Token has expired, try to refresh if refresh token available
            if refresh_token_str:
                try:
                    # Check if refresh token is blacklisted
                    if TokenBlacklist.objects.filter(token=refresh_token_str).exists():
                        logger.debug(f"Refresh token is blacklisted")
                        raise AuthenticationFailed("Refresh token has been revoked")
                    
                    # Create a new access token
                    refresh_token = RefreshToken(refresh_token_str)
                    new_access_token = str(refresh_token.access_token)
                    
                    # If response is available, set the new cookie
                    if hasattr(request, '_request') and hasattr(request._request, 'response'):
                        response = request._request.response
                        if response:
                            response.set_cookie(
                                key="access_token",
                                value=new_access_token,
                                httponly=True,
                                expires=datetime.now(timezone.utc) + timedelta(days=1),
                                path="/",
                                samesite="lax",
                                secure=False,
                            )
                    
                    # Get user from the token payload
                    access_token = AccessToken(new_access_token)
                    user_id = access_token.payload.get('user_id')
                    if not user_id:
                        raise AuthenticationFailed("Invalid token - no user ID")
                    
                    user = User.objects.get(id=user_id)
                    return (user, None)
                except Exception as e:
                    logger.error(f"Error refreshing token: {str(e)}")
                    raise AuthenticationFailed("Token refresh failed")
            else:
                logger.debug("No refresh token available")
                raise AuthenticationFailed("Token expired and no refresh token available")
        except User.DoesNotExist:
            logger.debug(f"User with ID {user_id} not found")
            raise AuthenticationFailed("User không tồn tại")
        except Exception as e:
            logger.error(f"Authentication error: {str(e)}")
            raise AuthenticationFailed("Authentication failed")

# Keep old class for backwards compatibility
RedisTokenAuthentication = JWTAuthentication
