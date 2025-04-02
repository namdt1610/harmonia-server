from django.core.cache import cache
from rest_framework.authentication import get_authorization_header
from rest_framework.exceptions import AuthenticationFailed
from django.contrib.auth.models import User

class RedisTokenAuthentication:
    def authenticate(self, request):
        auth_header = get_authorization_header(request).decode("utf-8")
        if not auth_header:
            return None

        token_key = auth_header.split("Bearer ")[-1]
        user_id = cache.get(f"auth_token_{token_key}")
        
        if not user_id:
            raise AuthenticationFailed("Token không hợp lệ hoặc đã hết hạn")
        
        return (User.objects.get(id=user_id), None)
