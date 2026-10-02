from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

from core.views import styleguide

urlpatterns = [
    path("accounts/", include("accounts.urls")),
    path("admin/", admin.site.urls),
    path("", include("core.urls")),
    path("", include("students.urls")),
]
if settings.DEBUG:
    urlpatterns += [path("dev/styleguide/", styleguide, name="styleguide")]
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

handler403 = "core.views.permission_denied"
handler404 = "core.views.page_not_found"
