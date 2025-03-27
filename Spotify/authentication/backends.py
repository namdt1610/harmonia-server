from django.contrib.auth.backends import ModelBackend
from django.contrib.auth.models import User

class EmailOrUsernameBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        try:
            # Tìm user bằng email hoặc username
            user = User.objects.filter(email=username).first() or User.objects.filter(username=username).first()
            if user and user.check_password(password):
                return user
        except User.DoesNotExist:
            return None
        return None