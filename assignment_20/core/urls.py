from django.urls import path

from . import views

app_name = "core"
urlpatterns = [
    path("", views.home, name="home"),
    path("dashboard/", views.dashboard, name="dashboard"),
    path("dashboard/charts.json", views.charts_json, name="charts"),
    path("audit/", views.AuditLogListView.as_view(), name="audit"),
]
