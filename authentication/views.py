from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken, AccessToken
from django_ratelimit.decorators import ratelimit
from .serializers import RegisterSerializer, LoginSerializer
from django.utils.decorators import method_decorator
from datetime import datetime, timezone, timedelta
from rest_framework_simplejwt.views import TokenRefreshView
import logging
from .models import TokenBlacklist
from django.contrib.auth.models import User
from django.conf import settings
logger = logging.getLogger(__name__)

def get_cookie_options():
    if settings.DEBUG:
        return {
            "samesite": "Lax",
            "secure": False,
            "path": "/",
        }
    else:
        return {
            "samesite": "None",
            "secure": True,
            "path": "/",
            # "domain": ".vercel.app"  # Allow cookies to be shared across subdomains
        }

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

        # Set expiration times for cookies - consistent with cache timeouts in serializer
        access_expires = datetime.now(timezone.utc) + timedelta(hours=24)
        refresh_expires = datetime.now(timezone.utc) + timedelta(days=7)

        response = Response({
            "user": user,
            "access": access_token,  # Return the token in the response too
        }, status=status.HTTP_200_OK)
        
        opts = get_cookie_options()
        # Set refresh token cookie
        response.set_cookie(
            key="refresh_token",
            value=refresh_token,
            httponly=True,
            expires=refresh_expires,
            path="/",
            **opts,
        )
        # Set access token cookie - EXACT name match with middleware
        response.set_cookie(
            key="access_token",  # This name MUST match what's in middleware
            value=access_token,
            httponly=True,
            expires=access_expires,
            path="/",
            **opts,
        )
        return response

class LogoutView(APIView):
    permission_classes = [AllowAny]  # Allow unauthenticated access for logout

    def post(self, request):
        try:
            # Lấy token từ cookie
            access_token = request.COOKIES.get('access_token')
            refresh_token = request.COOKIES.get('refresh_token')
            
            # Thêm token vào blacklist nếu tồn tại
            if access_token:
                try:
                    # Parse token để lấy thời gian hết hạn
                    token = AccessToken(access_token)
                    exp_timestamp = token.payload.get('exp')
                    expires_at = datetime.fromtimestamp(exp_timestamp, tz=timezone.utc)
                    
                    # Thêm vào blacklist
                    TokenBlacklist.objects.create(
                        token=access_token,
                        expires_at=expires_at
                    )
                except Exception as e:
                    logger.error(f"Error blacklisting access token: {str(e)}")
            
            if refresh_token:
                try:
                    # Parse token để lấy thời gian hết hạn
                    token = RefreshToken(refresh_token)
                    exp_timestamp = token.payload.get('exp')
                    expires_at = datetime.fromtimestamp(exp_timestamp, tz=timezone.utc)
                    
                    # Thêm vào blacklist
                    TokenBlacklist.objects.create(
                        token=refresh_token,
                        expires_at=expires_at
                    )
                except Exception as e:
                    logger.error(f"Error blacklisting refresh token: {str(e)}")
            
            # Xóa cookies với các options bảo mật
            response = Response({"message": "Logout successfully!"}, status=status.HTTP_200_OK)
            
            opts = get_cookie_options()
            # Xóa access token cookie
            response.delete_cookie(
                "access_token",
                path="/",
                domain=None,
                **opts,
            )
            
            # Xóa refresh token cookie
            response.delete_cookie(
                "refresh_token",
                path="/",
                domain=None,
                **opts,
            )
            
            # Log logout action
            if access_token:
                try:
                    user_id = AccessToken(access_token).payload.get('user_id')
                    if user_id:
                        user = User.objects.get(id=user_id)
                        logger.info(f"User {user.username} logged out successfully")
                except Exception as e:
                    logger.error(f"Error getting user info for logout: {str(e)}")
            
            return response
            
        except Exception as e:
            logger.error(f"Error during logout: {str(e)}")
            return Response(
                {"error": "An error occurred during logout"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

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
            "is_superuser": user.is_superuser,
        }
        return Response(data, status=status.HTTP_200_OK)
    

class CustomTokenRefreshView(TokenRefreshView):
    permission_classes = [AllowAny]
    
    def post(self, request, *args, **kwargs):
        try:
            # Lấy refresh token từ cookie
            refresh_token = request.COOKIES.get('refresh_token')
            if not refresh_token:
                logger.error("No refresh token found in cookies")
                return Response(
                    {"error": "No refresh token found"}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Sử dụng refresh token để lấy access token mới từ Simple JWT
            refresh = RefreshToken(refresh_token)
            new_access_token = str(refresh.access_token)
            
            # Set expiration time for cookie
            access_expires = datetime.now(timezone.utc) + timedelta(days=1)
            
            # Create response with token in body
            response = Response({
                "access": new_access_token
            })
            
            opts = get_cookie_options()
            # Set the access token cookie
            response.set_cookie(
                key="access_token",
                value=new_access_token,
                httponly=True,
                expires=access_expires,
                path="/",
                **opts,
            )
            
            logger.debug(f"Token refresh successful")
            return response
        except Exception as e:
            logger.error(f"Error refreshing token: {str(e)}")
            return Response(
                {"error": "Failed to refresh token"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )