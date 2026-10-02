from django.urls import path

from . import views

app_name = "students"
urlpatterns = [
    path("students/", views.StudentListView.as_view(), name="list"),
    path("students/add/", views.StudentCreateView.as_view(), name="add"),
    path("students/<int:pk>/", views.StudentDetailView.as_view(), name="detail"),
    path("students/<int:pk>/edit/", views.StudentUpdateView.as_view(), name="edit"),
    path("students/<int:pk>/delete/", views.StudentDeleteView.as_view(), name="delete"),
    path("students/<int:pk>/enroll/", views.enrollment_add, name="enroll"),
    path("students/<int:pk>/enroll/<int:enrollment_pk>/remove/", views.enrollment_remove, name="enrollment_remove"),
    path("students/<int:pk>/enroll/<int:enrollment_pk>/edit/", views.enrollment_edit, name="enrollment_edit"),
    path("me/", views.my_record, name="me"),
    path("courses/", views.CourseListView.as_view(), name="courses"),
    path("courses/add/", views.CourseCreateView.as_view(), name="course_add"),
    path("courses/<int:pk>/edit/", views.CourseUpdateView.as_view(), name="course_edit"),
]
