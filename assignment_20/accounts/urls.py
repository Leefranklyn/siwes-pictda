from django.urls import path

from .views import RoleLoginView, RoleLogoutView

app_name = "accounts"
urlpatterns = [path("login/", RoleLoginView.as_view(), name="login"), path("logout/", RoleLogoutView.as_view(), name="logout")]
