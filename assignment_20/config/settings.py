import secrets
import sys
from pathlib import Path

import environ


# Django's test runner turns DEBUG off, but the test suite should not use
# production storage or forced HTTPS. "manage.py test" is the usual way to run it.
TESTING = "test" in sys.argv

BASE_DIR = Path(__file__).resolve().parent.parent
env = environ.Env()
environ.Env.read_env(BASE_DIR / ".env")
DEBUG = env.bool("DEBUG", default=True)
SECRET_KEY = env("SECRET_KEY", default="local-development-only-not-for-production")
if not DEBUG and SECRET_KEY == "local-development-only-not-for-production":
    # Sessions and cookies reset on restart until a private key is provided.
    SECRET_KEY = environ.Env()("SECRET_KEY", default="") or secrets.token_urlsafe(64)
ALLOWED_HOSTS = env.list("ALLOWED_HOSTS", default=["localhost", "127.0.0.1", "[::1]"])
CSRF_TRUSTED_ORIGINS = env.list("CSRF_TRUSTED_ORIGINS", default=[])

INSTALLED_APPS = [
    "accounts.apps.AccountsConfig",
    "accounts.apps.RecordsAdminConfig",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.humanize",
    "tailwind",
    "theme",
    "students.apps.StudentsConfig",
    "core.apps.CoreConfig",
]
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "accounts.middleware.MustChangePasswordMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "core.middleware.AuditUserMiddleware",
]
ROOT_URLCONF = "config.urls"
TEMPLATES = [{
    "BACKEND": "django.template.backends.django.DjangoTemplates",
    "DIRS": [BASE_DIR / "templates"],
    "APP_DIRS": True,
    "OPTIONS": {"context_processors": [
        "django.template.context_processors.request",
        "django.contrib.auth.context_processors.auth",
        "django.contrib.messages.context_processors.messages",
        "core.context_processors.app_context",
    ]},
}]
WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"
DATABASES = {"default": env.db("DATABASE_URL", default=f"sqlite:///{BASE_DIR / 'db.sqlite3'}")}
DATABASES["default"]["CONN_MAX_AGE"] = 600
DATABASES["default"]["CONN_HEALTH_CHECKS"] = True
if "pooler" in DATABASES["default"].get("HOST", ""):
    # Server-side prepared statements break behind PgBouncer's transaction
    # pooling (Neon's pooler endpoint), so fall back to client-side binding.
    DATABASES["default"].setdefault("OPTIONS", {})["server_side_binding"] = False
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]
AUTHENTICATION_BACKENDS = ["accounts.backends.RoleModelBackend"]
LANGUAGE_CODE = "en-us"
TIME_ZONE = "Africa/Lagos"
USE_I18N = True
USE_TZ = True
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
LOGIN_URL = "/accounts/login/"
LOGOUT_REDIRECT_URL = "/"
SESSION_ENGINE = "django.contrib.sessions.backends.db"
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"]
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"
TAILWIND_APP_NAME = "theme"
INTERNAL_IPS = ["127.0.0.1"]
PHOTO_UPLOADS = env.bool("PHOTO_UPLOADS", default=DEBUG)
USE_S3 = env.bool("USE_S3", default=False)
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"
                    if DEBUG or TESTING else "whitenoise.storage.CompressedManifestStaticFilesStorage"},
}
if USE_S3:
    STORAGES["default"] = {"BACKEND": "storages.backends.s3.S3Storage"}
    AWS_STORAGE_BUCKET_NAME = env("AWS_STORAGE_BUCKET_NAME")
    AWS_S3_ENDPOINT_URL = env("AWS_S3_ENDPOINT_URL", default=None)
    # Public bucket domain (e.g. a Cloudflare R2 "pub-...r2.dev" subdomain) so
    # uploaded media URLs are stable plain HTTPS links without query signatures.
    AWS_S3_CUSTOM_DOMAIN = env("AWS_S3_CUSTOM_DOMAIN", default=None)
    AWS_ACCESS_KEY_ID = env("AWS_ACCESS_KEY_ID")
    AWS_SECRET_ACCESS_KEY = env("AWS_SECRET_ACCESS_KEY")
    # R2-style S3-compatible endpoints need path-style addressing; the env
    # default stays "auto" for plain AWS S3.
    AWS_S3_ADDRESSING_STYLE = env("AWS_S3_ADDRESSING_STYLE", default="auto")
    AWS_S3_REGION_NAME = env("AWS_S3_REGION_NAME", default="us-east-1")
    AWS_QUERYSTRING_AUTH = False
    AWS_DEFAULT_ACL = None
DEMO_MODE = env.bool("DEMO_MODE", default=False)
DEMO_ACCOUNTS = [
    {"role": "Admin", "username": "demo_admin", "password": env("DEMO_ADMIN_PASSWORD", default="LocalAdmin20!")},
    {"role": "Staff", "username": "demo_staff", "password": env("DEMO_STAFF_PASSWORD", default="LocalStaff20!")},
    {"role": "Lecturer", "username": "demo_lecturer", "password": env("DEMO_LECTURER_PASSWORD", default="LocalLecturer20!")},
    {"role": "Student", "username": "demo_student", "password": env("DEMO_STUDENT_PASSWORD", default="LocalStudent20!")},
]
# Pin the academic session (e.g. "2025/2026"), or leave empty to derive it
# from today's date, where September starts a new session.
CURRENT_SESSION = env("CURRENT_SESSION", default="")
# Shown on transcripts and document headers.
INSTITUTION_NAME = env("INSTITUTION_NAME", default="Student Management System")
# Self-service password reset only appears when email is configured.
EMAIL_BACKEND = env("EMAIL_BACKEND", default="django.core.mail.backends.console.EmailBackend")
EMAIL_HOST = env("EMAIL_HOST", default="")
EMAIL_PORT = env.int("EMAIL_PORT", default=587)
EMAIL_HOST_USER = env("EMAIL_HOST_USER", default="")
EMAIL_HOST_PASSWORD = env("EMAIL_HOST_PASSWORD", default="")
EMAIL_USE_TLS = env.bool("EMAIL_USE_TLS", default=True)
DEFAULT_FROM_EMAIL = env("DEFAULT_FROM_EMAIL", default="noreply@studentrecords.local")
if not DEBUG and not TESTING:
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_SSL_REDIRECT = env.bool("SECURE_SSL_REDIRECT", default=True)
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    if env.bool("TRUST_PROXY_HEADERS", default=False):
        SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
