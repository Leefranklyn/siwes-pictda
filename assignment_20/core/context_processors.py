from pathlib import Path

from django.conf import settings

from accounts.roles import user_role
from students.utils import current_session

SHOT_NAMES = ("dashboard", "students", "student-detail")


def shot_files():
    shots_dir = Path(settings.BASE_DIR) / "static" / "img" / "shots"
    return {
        name.replace("-", "_"): f"{settings.STATIC_URL}img/shots/{name}.webp"
        for name in SHOT_NAMES
        if (shots_dir / f"{name}.webp").exists()
    }


def app_context(request):
    return {
        "role": user_role(request.user),
        "demo_mode": settings.DEMO_MODE,
        "demo_accounts": settings.DEMO_ACCOUNTS if settings.DEMO_MODE else [],
        "photo_uploads": settings.PHOTO_UPLOADS,
        "shots": shot_files(),
        "email_configured": bool(settings.EMAIL_HOST),
        "institution": settings.INSTITUTION_NAME,
        "current_session": current_session(),
    }
