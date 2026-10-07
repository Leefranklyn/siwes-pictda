from django.urls import path

from . import courses, views

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
    path("students/<int:pk>/transcript/", views.transcript, name="transcript"),
    path("me/", views.my_record, name="me"),
    path("me/transcript/", views.my_transcript, name="me_transcript"),

    path("students/import/", views.students_import, name="import"),
    path("students/import/template.csv", views.students_import_template, name="import_template"),
    path("students/import/history/", views.students_import_history, name="import_history"),
    path("students/import/<int:pk>/", views.students_import_preview, name="import_preview"),
    path("students/import/<int:pk>/credentials.csv", views.students_import_credentials, name="import_credentials"),
    path("students/import/<int:pk>/errors.csv", views.students_import_errors_csv, name="import_errors_csv"),
    path("students/export.csv", views.students_export, name="export"),
    path("students/bulk/promote/", views.bulk_promote, name="bulk_promote"),
    path("students/bulk/status/", views.bulk_status, name="bulk_status"),

    path("students/<int:pk>/register-all/", views.register_all, name="register_all"),
    path("departments/", views.DepartmentListView.as_view(), name="departments"),
    path("departments/add/", views.DepartmentCreateView.as_view(), name="department_add"),
    path("departments/<int:pk>/edit/", views.DepartmentUpdateView.as_view(), name="department_edit"),
    path("departments/<int:pk>/delete/", views.DepartmentDeleteView.as_view(), name="department_delete"),

    path("teaching/", courses.teaching, name="teaching"),
    path("courses/", courses.CourseListView.as_view(), name="courses"),
    path("courses/add/", courses.CourseCreateView.as_view(), name="course_add"),
    path("courses/import/", courses.course_import, name="course_import"),
    path("courses/import/<int:pk>/", courses.course_import_preview, name="course_import_preview"),
    path("courses/<int:pk>/", courses.course_detail, name="course_detail"),
    path("courses/<int:pk>/edit/", courses.CourseUpdateView.as_view(), name="course_edit"),
    path("courses/<int:pk>/enroll-matching/", courses.enroll_matching, name="enroll_matching"),
    path("courses/<int:pk>/grades/", courses.grade_sheet, name="grade_sheet"),
    path("courses/<int:pk>/grades/import/", courses.grades_import, name="grades_import"),
    path("courses/<int:pk>/grades/import/<int:batch_pk>/", courses.grades_import_preview, name="grades_import_preview"),
    path("courses/<int:pk>/roster.csv", courses.roster_csv, name="roster_csv"),
]
