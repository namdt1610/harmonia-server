import logging
from channels.db import database_sync_to_async
from channels.middleware import BaseMiddleware
from django.contrib.auth.models import AnonymousUser, User
from rest_framework_simplejwt.tokens import AccessToken
from rest_framework_simplejwt.exceptions import TokenError
from urllib.parse import parse_qs
from django.conf import settings

logger = logging.getLogger(__name__)

@database_sync_to_async
def get_user_by_id(user_id):
    """Get user by ID from database"""
    try:
        return User.objects.get(id=user_id)
    except User.DoesNotExist:
        return AnonymousUser()

class JWTAuthMiddleware(BaseMiddleware):
    """Custom JWT authentication middleware for WebSockets"""
    
    async def __call__(self, scope, receive, send):
        # Only handle WebSocket connections
        if scope["type"] != "websocket":
            return await super().__call__(scope, receive, send)
        
        try:
            # First try to get user from session (if available)
            user = scope.get("user", AnonymousUser())
            
            # If user is not authenticated, try JWT authentication
            if user is None or isinstance(user, AnonymousUser) or not hasattr(user, 'is_authenticated') or not user.is_authenticated:
                # Try to get token from query parameters
                query_string = scope.get('query_string', b'').decode()
                query_params = parse_qs(query_string)
                token = query_params.get('token', [None])[0]
                
                # Try to get token from cookies if not in query params
                if not token:
                    cookies = {}
                    if 'headers' in scope:
                        for header_name, header_value in scope['headers']:
                            if header_name == b'cookie':
                                cookie_header = header_value.decode()
                                for cookie in cookie_header.split(';'):
                                    if '=' in cookie:
                                        key, value = cookie.strip().split('=', 1)
                                        cookies[key] = value
                    token = cookies.get('access_token')
                
                if token:
                    try:
                        # Validate JWT token
                        access_token = AccessToken(token)
                        user_id = access_token.payload.get('user_id')
                        
                        if user_id:
                            user = await get_user_by_id(user_id)
                            logger.info(f"WebSocket JWT authentication successful for user {user_id}")
                        else:
                            logger.warning("JWT token missing user_id")
                            user = AnonymousUser()
                    except TokenError as e:
                        logger.warning(f"Invalid JWT token in WebSocket: {e}")
                        user = AnonymousUser()
                else:
                    logger.debug("No JWT token found in WebSocket connection")
                    user = AnonymousUser()
            
            # Set the authenticated user in scope
            scope["user"] = user
            
        except Exception as e:
            logger.error(f"Error in JWT WebSocket authentication: {e}")
            scope["user"] = AnonymousUser()
        
        return await super().__call__(scope, receive, send)

def JWTAuthMiddlewareStack(inner):
    """Convenience function to apply JWT authentication middleware"""
    return JWTAuthMiddleware(inner) 