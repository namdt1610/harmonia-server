from .models import RolePermission, UserRole, Permission

def has_permission(user, permission_code: str) -> bool:
    if not user or not user.is_authenticated:
        return False
    return RolePermission.objects.filter(
        role__userrole__user=user,
        permission__code=permission_code
    ).exists()
