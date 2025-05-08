from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from django_ratelimit.decorators import ratelimit
from django.core.cache import cache
from .serializers import RegisterSerializer, LoginSerializer
from django.utils.decorators import method_decorator
from datetime import datetime, timezone
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.views import TokenRefreshView
from django.http import JsonResponse
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
    
    def get_rate_limit_key(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return f"user_{request.user.id}"
        return request.META.get("REMOTE_ADDR")

    @method_decorator(ratelimit(
        key=get_rate_limit_key,
        rate='5/m',
        method='POST',
        block=True
    ))
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)
    
    def post(self, request):
        serializer = LoginSerializer(data=request.data, context={"request": request})
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data
        user = data["user"]
        refresh_token = data["refresh"]
        access_token = data["access"]

        # Tính expires của refresh token
        refresh_lifetime = RefreshToken(refresh_token).lifetime  # timedelta
        expires_at = datetime.now(timezone.utc) + refresh_lifetime

        response = Response({
            "access": access_token,
            "user": user,
        }, status=status.HTTP_200_OK)

        # Chỉ dùng cho local dev
        response.set_cookie(
            key="refresh_token",
            value=refresh_token,
            httponly=True,
            expires=expires_at,
            path="/",
            samesite="lax",
            secure=False,
        )
        return response

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

class MeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if not request.user.is_authenticated:
            return Response({"error": "User not authenticated"}, status=status.HTTP_401_UNAUTHORIZED)
        
        user = request.user
        data = {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
        }
        return Response(data, status=status.HTTP_200_OK)
    

class CustomTokenRefreshView(TokenRefreshView):
    def post(self, request, *args, **kwargs):
        try:
            # Lấy refresh token từ cookie
            refresh_token = request.COOKIES.get('refresh_token')
            if not refresh_token:
                return Response(
                    {"error": "No refresh token found"}, 
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Validate refresh token
            try:
                refresh = RefreshToken(refresh_token)
            except Exception as e:
                logger.error(f"Invalid refresh token: {str(e)}")
                return Response(
                    {"error": "Invalid refresh token"}, 
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Tạo access token mới
            access_token = str(refresh.access_token)
            
            return Response({
                "access": access_token
            })

        except Exception as e:
            logger.error(f"Error refreshing token: {str(e)}")
            return Response(
                {"error": "Failed to refresh token"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )