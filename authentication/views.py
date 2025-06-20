from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken, AccessToken
from django_ratelimit.decorators import ratelimit
from .serializers import RegisterSerializer, AuthUserSerializer, ForgotPasswordSerializer, ResetPasswordSerializer, CustomTokenObtainPairSerializer
from django.utils.decorators import method_decorator
from datetime import datetime, timezone, timedelta
from rest_framework_simplejwt.views import TokenRefreshView, TokenObtainPairView
import logging
from .models import TokenBlacklist
from user.models import Profile
from django.contrib.auth.models import User
from django.conf import settings
from rest_framework.decorators import api_view, permission_classes
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from .services import AuthService, EmailService
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from google.oauth2 import id_token
from google.auth.transport import requests
from django.conf import settings
GOOGLE_CLIENT_ID = settings.GOOGLE_CLIENT_ID

logging.basicConfig(level=logging.DEBUG)
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
    serializer_class = CustomTokenObtainPairSerializer

    def get_rate_limit_key(self, request, *args, **kwargs):
        try:
            # Try to get username from POST data first
            username = request.POST.get('username_or_email', '')
            if not username and request.content_type == 'application/json':
                # If not in POST and content type is JSON, try to parse body
                import json
                try:
                    body = json.loads(request.body)
                    username = body.get('username_or_email', '')
                except:
                    pass
            return username or request.META.get('REMOTE_ADDR')
        except:
            return request.META.get('REMOTE_ADDR')

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
        request_body=CustomTokenObtainPairSerializer(),
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
            # Get tokens from response
            tokens = response.data
            access_token = tokens.get('access')
            refresh_token = tokens.get('refresh')
            
            # Set cookie options
            access_expires = datetime.now(timezone.utc) + timedelta(hours=24)
            refresh_expires = datetime.now(timezone.utc) + timedelta(days=7)
            opts = get_cookie_options()
            
            # Create new response with user info
            new_response = Response(response.data, status=status.HTTP_200_OK)
            
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
            logger.info("=== LOGOUT REQUEST STARTED ===")
            logger.info(f"Request cookies: {dict(request.COOKIES)}")

            access_token = request.COOKIES.get('access_token')
            refresh_token = request.COOKIES.get('refresh_token')

            # Blacklist tokens if found
            for token_str, token_class in [
                (access_token, AccessToken),
                (refresh_token, RefreshToken)
            ]:
                if token_str:
                    try:
                        token = token_class(token_str)
                        exp_timestamp = token.payload.get('exp')
                        expires_at = datetime.fromtimestamp(exp_timestamp, tz=timezone.utc)

                        TokenBlacklist.objects.create(
                            token=token_str,
                            expires_at=expires_at
                        )
                        logger.info(f"{token_class.__name__} blacklisted successfully.")
                    except Exception as e:
                        logger.warning(f"Error blacklisting token: {e}")

            # Prepare response
            response = Response({"message": "Logout successfully!"}, status=status.HTTP_200_OK)

            # Get cookie options
            opts = get_cookie_options()

            # Set cookie deletion with all possible combinations
            cookie_names = ['access_token', 'refresh_token']
            
            # First try with delete_cookie
            for name in cookie_names:
                response.delete_cookie(name, path='/')
                response.delete_cookie(name, path='/', domain='localhost')
                response.delete_cookie(name, path='/', domain='')

            # Then try setting expired cookies with all combinations
            for cookie_name in cookie_names:
                # Try with secure true and false
                for secure in [True, False]:
                    # Try with different samesite values
                    for same_site in ['Lax', 'Strict', 'None']:
                        # Try with different domains
                        for domain in [None, 'localhost', '']:
                            # Try with different paths
                            for path in ['/', '']:
                                response.set_cookie(
                                    cookie_name,
                                    value='',
                                    expires='Thu, 01 Jan 1970 00:00:00 GMT',
                                    path=path,
                                    domain=domain,
                                    samesite=same_site,
                                    secure=secure,
                                    httponly=True
                                )

            # Add Set-Cookie headers directly
            for cookie_name in cookie_names:
                response["Set-Cookie"] = [
                    f"{cookie_name}=; Path=/; Expires=Thu, 01 Jan 1970 00:00:00 GMT; Max-Age=0",
                    f"{cookie_name}=; Path=/; Domain=localhost; Expires=Thu, 01 Jan 1970 00:00:00 GMT; Max-Age=0",
                    f"{cookie_name}=; Path=/; Domain=; Expires=Thu, 01 Jan 1970 00:00:00 GMT; Max-Age=0",
                    f"{cookie_name}=; Path=/; Expires=Thu, 01 Jan 1970 00:00:00 GMT; Max-Age=0; Secure",
                    f"{cookie_name}=; Path=/; Expires=Thu, 01 Jan 1970 00:00:00 GMT; Max-Age=0; SameSite=None; Secure",
                    f"{cookie_name}=; Path=/; Expires=Thu, 01 Jan 1970 00:00:00 GMT; Max-Age=0; SameSite=Lax",
                    f"{cookie_name}=; Path=/; Expires=Thu, 01 Jan 1970 00:00:00 GMT; Max-Age=0; SameSite=Strict"
                ]

            # Set additional headers to prevent caching
            response["Cache-Control"] = "no-cache, no-store, must-revalidate"
            response["Pragma"] = "no-cache"
            response["Expires"] = "0"

            logger.info("=== LOGOUT COMPLETED SUCCESSFULLY ===")
            return response

        except Exception as e:
            logger.error(f"Logout error: {str(e)}")
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
    Can get refresh token from either request body or cookie.
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
        # If refresh token not in request body, try to get from cookie
        if 'refresh' not in request.data:
            refresh_token = request.COOKIES.get('refresh_token')
            if refresh_token:
                request.data['refresh'] = refresh_token
            else:
                return Response(
                    {"detail": "No refresh token provided"},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        response = super().post(request, *args, **kwargs)
        
        # If refresh successful, set new access token in cookie
        if response.status_code == 200:
            access_token = response.data.get('access')
            if access_token:
                opts = get_cookie_options()
                response.set_cookie(
                    key='access_token',
                    value=access_token,
                    httponly=True,
                    expires=datetime.now(timezone.utc) + timedelta(days=1),
                    path='/',
                    **opts,
                )
        
        return response

@csrf_exempt
def google_auth(request):
    logger.info("=== google_auth called ===")
    if request.method == 'POST':
        import json
        from user.models import Profile
        try:
            data = json.loads(request.body)
        except Exception as e:
            logger.error(f"Lỗi parse JSON: {e}")
            return JsonResponse({'error': 'Invalid JSON'}, status=400)
        id_token_str = data.get('id_token')
        try:
            idinfo = id_token.verify_oauth2_token(id_token_str, requests.Request(), GOOGLE_CLIENT_ID)
            email = idinfo['email']
            google_sub = idinfo['sub']

            users = User.objects.filter(email=email)
            if users.exists():
                user = users.first()
                profile, _ = Profile.objects.get_or_create(user=user)
                if profile.google_sub == google_sub:
                    # Đã từng liên kết Google, cho đăng nhập
                    pass
                else:
                    return JsonResponse({'error': 'Email đã tồn tại. Hãy liên kết Google trong tài khoản hoặc đăng ký tài khoản mới.'}, status=400)
            else:
                # Tạo user mới và profile mới, lưu google_sub
                user = User.objects.create(
                    email=email,
                    username=email.split('@')[0],
                )
                profile = Profile.objects.get(user=user)
                profile.google_sub = google_sub
                profile.save()

            # Tạo JWT
            refresh = RefreshToken.for_user(user)
            access_token = str(refresh.access_token)
            response = JsonResponse({'access_token': access_token})
            response.set_cookie(
                key='access_token',
                value=access_token,
                httponly=True,
                samesite='Lax',
                secure=False,  # Để True nếu dùng HTTPS
                path='/',
            )
            return response
        except Exception as e:
            import traceback
            logger.error(f"Lỗi verify Google token: {traceback.format_exc()}")
            logger.error(f"Request body: {data}")
            return JsonResponse({'error': str(e)}, status=400)
    return JsonResponse({'error': 'Invalid method'}, status=405)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def link_google(request):
    id_token_str = request.data.get('id_token')
    try:
        idinfo = id_token.verify_oauth2_token(id_token_str, requests.Request(), GOOGLE_CLIENT_ID)
        google_sub = idinfo['sub']
        user = request.user
        profile = user.profile
        if profile.google_sub:
            return JsonResponse({'error': 'Tài khoản đã liên kết Google.'}, status=400)
        profile.google_sub = google_sub
        profile.save()
        return JsonResponse({'message': 'Liên kết Google thành công!'})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)