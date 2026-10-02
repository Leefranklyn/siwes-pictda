ADMIN, STAFF, STUDENT = "admin", "staff", "student"
ADMIN_GROUP, STAFF_GROUP = "Admin", "Staff"


def user_role(user):
    if not user.is_authenticated:
        return None
    if user.is_superuser or user.groups.filter(name=ADMIN_GROUP).exists():
        return ADMIN
    if user.groups.filter(name=STAFF_GROUP).exists():
        return STAFF
    if hasattr(user, "student"):
        return STUDENT
    return None
