from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from django_ratelimit.decorators import ratelimit
from django.core.cache import cache
from .serializers import RegisterSerializer, LoginSerializer
import logging
logger = logging.getLogger(__name__)

class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class LoginView(APIView):
    permission_classes = [AllowAny]
    
    def get_rate_limit_key(request):
        """Lấy user ID nếu đã login, nếu chưa thì dùng IP"""
        if request.user.is_authenticated:
            return f"user_{request.user.id}"
        return request.META.get("REMOTE_ADDR")
    
    @ratelimit(key=get_rate_limit_key, rate='5/m', method='POST', block=True)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)
    
    def post(self, request):
        serializer = LoginSerializer(data=request.data, context={"request": request})
        if serializer.is_valid():
            data = serializer.validated_data
            user = data["user"]
            
            # Đẩy refresh token lên cookie
            refresh_token = data["refresh"]
            access_token = data["access"]
            
            # Lưu access token vào cache với thời gian sống bằng thời gian sống của refresh token
            access_lifetime = int(RefreshToken(refresh_token).access_token.lifetime.total_seconds())
            refresh_lifetime = int(RefreshToken(refresh_token).lifetime.total_seconds())

            cache.set(f"auth_token_{user.id}", access_token, timeout=access_lifetime)
            cache.set(f"refresh_token_{user.id}", refresh_token, timeout=refresh_lifetime)
            
            secure = request.is_secure()  # False nếu không dùng HTTPS
            response = Response(data, status=status.HTTP_200_OK)
            response.set_cookie(
                key="refresh",
                value=refresh_token,
                httponly=True,
                secure=secure,
                samesite="None",
                expires=RefreshToken(refresh_token).access_token.lifetime,
            )
            logger.debug("Cookie set successfully")
            return response
        
        logger.warning(f"Login failed for IP: {request.META.get('REMOTE_ADDR')}, Data: {request.data}")
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class LogoutView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        if not request.user.is_authenticated:
            return Response({"error": "User not authenticated"}, status=status.HTTP_401_UNAUTHORIZED)
        
        # Xóa token trong cache
        user = request.user
        cache.delete(f"auth_token_{user.id}")
        cache.delete(f"refresh_token_{user.id}")

        # Xóa cookie
        response = Response({"message": "Logout successfully!"}, status=status.HTTP_200_OK)
        response.delete_cookie("refresh")
        return response
