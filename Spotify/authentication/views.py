from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth.models import User
from .serializers import RegisterSerializer, LoginSerializer
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
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

    def post(self, request):
        serializer = LoginSerializer(data=request.data, context={"request": request})
        if serializer.is_valid():
            data = serializer.validated_data

            # Đẩy refresh token lên cookie
            refresh_token = data["refresh"]
            secure = not request.is_secure()  # False nếu không dùng HTTPS
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
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class LogoutView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        # Xóa cookie refresh token
        request.COOKIES.pop("refresh", None)
        return Response({"message": "Đăng xuất thành công!"}, status=status.HTTP_200_OK)