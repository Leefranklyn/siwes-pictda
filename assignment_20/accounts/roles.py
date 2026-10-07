ADMIN, STAFF, LECTURER, STUDENT = "admin", "staff", "lecturer", "student"
ADMIN_GROUP, STAFF_GROUP, LECTURER_GROUP = "Admin", "Staff", "Lecturer"


def user_role(user):
    if not user.is_authenticated:
        return None
    if user.is_superuser or user.groups.filter(name=ADMIN_GROUP).exists():
        return ADMIN
    if user.groups.filter(name=STAFF_GROUP).exists():
        return STAFF
    if user.groups.filter(name=LECTURER_GROUP).exists() and hasattr(user, "lecturer"):
        return LECTURER
    if hasattr(user, "student"):
        return STUDENT
    return None


def can_grade(user, course):
    """True when the user may enter grades for this course."""
    role = user_role(user)
    if role in (ADMIN, STAFF):
        return True
    return role == LECTURER and course.lecturers.filter(user=user).exists()
