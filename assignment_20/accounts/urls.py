from django.contrib.auth import views as auth_views
from django.urls import path

from . import manage_views, views

app_name = "accounts"
urlpatterns = [
    path("login/", views.RoleLoginView.as_view(), name="login"),
    path("logout/", views.RoleLogoutView.as_view(), name="logout"),
    path("manage/", manage_views.account_list, name="manage"),
    path("manage/add/", manage_views.account_add, name="account_add"),
    path("manage/link-students/", manage_views.link_students, name="link_students"),
    path("manage/<int:pk>/edit/", manage_views.account_edit, name="account_edit"),
    path("manage/<int:pk>/toggle/", manage_views.account_toggle, name="account_toggle"),
    path("manage/<int:pk>/reset-password/", manage_views.account_reset_password, name="account_reset"),
    path("password/change/", views.PasswordChangeView.as_view(), name="password_change"),
]

# Self-service reset by email is only offered when email is configured;
# the login template checks settings.EMAIL_HOST before showing the link.
urlpatterns += [
    path("password/reset/", views.PasswordResetView.as_view(), name="password_reset"),
    path("password/reset/done/", views.PasswordResetDoneView.as_view(), name="password_reset_done"),
    path("password/reset/<uidb64>/<token>/", views.PasswordResetConfirmView.as_view(), name="password_reset_confirm"),
    path("password/reset/complete/", views.PasswordResetCompleteView.as_view(), name="password_reset_complete"),
]
