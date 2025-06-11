from rest_framework.permissions import BasePermission
from .utils import has_permission
import logging

logger = logging.getLogger(__name__)

class HasCustomPermission(BasePermission):
    """
    Kiểm tra xem người dùng có quyền truy cập vào một permission_code cụ thể
    Usage:
    permission_classes = [HasCustomPermission]
    required_permission = 'your_permission_code'
    """

    def has_permission(self, request, view):
        if request.user.is_superuser:
            return True
        
        permission_code = getattr(view, 'required_permission', None)
        if not permission_code:
            return True  # Cho phép nếu không có permission code cụ thể
        if not has_permission(request.user, permission_code):
            logger.warning(f"User {request.user} lacks permission {permission_code}")
            return False
        return True
