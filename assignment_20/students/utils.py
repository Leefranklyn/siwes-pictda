from django.conf import settings
from django.utils import timezone


def current_session(today=None):
    """The academic session for today, e.g. "2025/2026" (September starts the year).
    Set CURRENT_SESSION in the environment to pin it."""
    if getattr(settings, "CURRENT_SESSION", ""):
        return settings.CURRENT_SESSION
    today = today or timezone.localdate()
    start = today.year if today.month >= 9 else today.year - 1
    return f"{start}/{start + 1}"


def previous_session(today=None):
    current = current_session(today)
    start = int(current[:4]) - 1
    return f"{start}/{start + 1}"


def session_gpa(enrollments):
    """Credit-weighted GPA on the 5.0 scale for a list of graded enrollments.
    Returns None when nothing is graded."""
    graded = [e for e in enrollments if e.grade]
    units = sum(e.course.credit_units for e in graded)
    if not units:
        return None
    points = sum(e.grade_points * e.course.credit_units for e in graded)
    return round(points / units, 2)


def units_summary(enrollments):
    """(units attempted, units earned) for a list of enrollments.
    Units earned count grades above F."""
    attempted = sum(e.course.credit_units for e in enrollments if e.grade)
    earned = sum(e.course.credit_units for e in enrollments if e.grade and e.grade != "F")
    return attempted, earned
