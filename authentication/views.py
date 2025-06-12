from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken, AccessToken
from django_ratelimit.decorators import ratelimit
from .serializers import RegisterSerializer, LoginSerializer, AuthUserSerializer, ForgotPasswordSerializer, ResetPasswordSerializer
from django.utils.decorators import method_decorator
from datetime import datetime, timezone, timedelta
from rest_framework_simplejwt.views import TokenRefreshView, TokenObtainPairView
import logging
from .models import TokenBlacklist
from django.contrib.auth.models import User
from django.conf import settings
from rest_framework.decorators import api_view, permission_classes
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from .services import AuthService, EmailService

logger = logging.getLogger(__name__)

def get_cookie_options():
    if settings.DEBUG:
        return {
            "samesite": "Lax",
            "secure": False,
        }
    else:
        return {
            "samesite": "None",
            "secure": True,
        }

class RegisterView(APIView):
    """
    API endpoint for user registration.
    Allows new users to create an account.
    """
    swagger_tags = ['Authentication']
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        tags=['Authentication'],
        operation_description="Register a new user",
        request_body=RegisterSerializer(),
        responses={
            201: AuthUserSerializer(),
            400: "Bad Request"
        }
    )
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            # Use service to create user with welcome email
            user = AuthService.create_user_with_welcome_email(
                username=serializer.validated_data['username'],
                email=serializer.validated_data['email'],
                password=serializer.validated_data['password']
            )
            
            # Return user data
            user_serializer = AuthUserSerializer(user)
            return Response(user_serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class LoginView(TokenObtainPairView):
    """
    API endpoint for user login.
    Provides JWT token-based authentication with rate limiting.
    Uses SimpleJWT's TokenObtainPairView for token generation.
    """
    swagger_tags = ['Authentication']
    permission_classes = [AllowAny]
    serializer_class = TokenObtainPairSerializer

    def get_rate_limit_key(self, request, *args, **kwargs):
        return request.data.get('username', '') or request.META.get('REMOTE_ADDR')

    @method_decorator(ratelimit(
        key=get_rate_limit_key,
        rate='5/m',
        method='POST',
        block=True
    ))
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)
    
    @swagger_auto_schema(
        tags=['Authentication'],
        operation_description="Login and get access token",
        request_body=LoginSerializer(),
        responses={
            200: openapi.Response(
                description="Successful login",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'user': openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            properties={
                                'id': openapi.Schema(type=openapi.TYPE_INTEGER),
                                'username': openapi.Schema(type=openapi.TYPE_STRING),
                                'email': openapi.Schema(type=openapi.TYPE_STRING),
                                'is_superuser': openapi.Schema(type=openapi.TYPE_BOOLEAN)
                            }
                        ),
                        'access': openapi.Schema(type=openapi.TYPE_STRING)
                    }
                )
            ),
            400: "Bad Request",
            401: "Invalid credentials",
            429: "Too many requests"
        }
    )
    def post(self, request, *args, **kwargs):
        # Get tokens using SimpleJWT's logic
        response = super().post(request, *args, **kwargs)
        
        if response.status_code == 200:
            # Get user info
            user = request.user
            user_data = {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'is_superuser': user.is_superuser
            }
            
            # Get tokens from response
            tokens = response.data
            access_token = tokens.get('access')
            refresh_token = tokens.get('refresh')
            
            # Set cookie options
            access_expires = datetime.now(timezone.utc) + timedelta(hours=24)
            refresh_expires = datetime.now(timezone.utc) + timedelta(days=7)
            opts = get_cookie_options()
            
            # Create new response with user info
            new_response = Response({
                'user': user_data,
                'access': access_token,
            }, status=status.HTTP_200_OK)
            
            # Set cookies
            new_response.set_cookie(
                key='refresh_token',
                value=refresh_token,
                httponly=True,
                expires=refresh_expires,
                path='/',
                **opts,
            )
            new_response.set_cookie(
                key='access_token',
                value=access_token,
                httponly=True,
                expires=access_expires,
                path='/',
                **opts,
            )
            return new_response
            
        return response

class LogoutView(APIView):
    """
    API endpoint for user logout.
    Invalidates JWT tokens and clears authentication cookies.
    """
    swagger_tags = ['Authentication']       
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        tags=['Authentication'],
        operation_description="Logout and invalidate tokens",
        responses={
            200: openapi.Response(
                description="Successful logout",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'message': openapi.Schema(type=openapi.TYPE_STRING)
                    }
                )
            ),
            400: "Bad Request"
        }
    )
    def post(self, request):
        try:
            access_token = request.COOKIES.get('access_token')
            refresh_token = request.COOKIES.get('refresh_token')
            
            if access_token:
                try:
                    token = AccessToken(access_token)
                    exp_timestamp = token.payload.get('exp')
                    expires_at = datetime.fromtimestamp(exp_timestamp, tz=timezone.utc)
                    
                    TokenBlacklist.objects.create(
                        token=access_token,
                        expires_at=expires_at
                    )
                except Exception as e:
                    logger.error(f"Error blacklisting access token: {str(e)}")
            
            if refresh_token:
                try:
                    token = RefreshToken(refresh_token)
                    exp_timestamp = token.payload.get('exp')
                    expires_at = datetime.fromtimestamp(exp_timestamp, tz=timezone.utc)
                    
                    TokenBlacklist.objects.create(
                        token=refresh_token,
                        expires_at=expires_at
                    )
                except Exception as e:
                    logger.error(f"Error blacklisting refresh token: {str(e)}")
            
            response = Response({"message": "Logout successfully!"}, status=status.HTTP_200_OK)
            
            opts = get_cookie_options()
            response.delete_cookie(
                "access_token",
                path="/",
                domain=None,
                **opts,
            )
            response.delete_cookie(
                "refresh_token",
                path="/",
                domain=None,
                **opts,
            )
            return response
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

class ForgotPasswordView(APIView):
    """
    API endpoint for user forgot password.
    """
    swagger_tags = ['Authentication']
    permission_classes = [AllowAny]
    
    @swagger_auto_schema(
        tags=['Authentication'],
        operation_description="Forgot password",
        request_body=ForgotPasswordSerializer(),
        responses={
            200: openapi.Response(
                description="Email sent successfully",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'message': openapi.Schema(type=openapi.TYPE_STRING)
                    }
                )
            ),
            400: "Bad Request"
        }
    )
    def post(self, request):
        serializer = ForgotPasswordSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            # Use service to handle password reset
            AuthService.handle_password_reset_request(email)
            return Response({"message": "Email sent successfully!"}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ResetPasswordView(APIView):
    """
    API endpoint for password reset.
    """
    swagger_tags = ['Authentication']
    permission_classes = [AllowAny]
    
    @swagger_auto_schema(
        tags=['Authentication'],
        operation_description="Reset password with token",
        request_body=ResetPasswordSerializer(),
        responses={
            200: openapi.Response(
                description="Password reset successful",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'message': openapi.Schema(type=openapi.TYPE_STRING)
                    }
                )
            ),
            400: "Bad Request - Invalid token or passwords don't match"
        }
    )
    def post(self, request):
        serializer = ResetPasswordSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Password reset successfully!"}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class MeView(APIView):
    """
    API endpoint to get current user information.
    Returns the authenticated user's details.
    """
    swagger_tags = ['Authentication']
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        tags=['Authentication'],
        operation_description="Get current user information",
        responses={
            200: AuthUserSerializer(),
            401: "Unauthorized"
        }
    )
    def get(self, request):
        serializer = AuthUserSerializer(request.user)
        return Response(serializer.data)

class CustomTokenRefreshView(TokenRefreshView):
    """
    API endpoint for refreshing JWT tokens.
    Provides a new access token using a valid refresh token.
    """
    swagger_tags = ['Authentication']
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        tags=['Authentication'],
        operation_description="Refresh access token",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['refresh'],
            properties={
                'refresh': openapi.Schema(type=openapi.TYPE_STRING, description='Valid refresh token')
            }
        ),
        responses={
            200: openapi.Response(
                description="Token refresh successful",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'access': openapi.Schema(type=openapi.TYPE_STRING)
                    }
                )
            ),
            400: "Bad Request",
            401: "Invalid refresh token"
        }
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)