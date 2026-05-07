from django.urls import path
from .views import StudentDashboardView
from . import views

urlpatterns = [
    path('course-list/', views.course_list, name='course-list'),
    path('course/<int:pk>/', views.course_detail, name='course-detail'),

    path('my-courses/', views.my_course, name='my-courses'),
    path('about/', views.about, name='about'),

    path('lesson/<int:pk>/', views.lesson_detail, name='lesson-detail'),

    path("profile/", views.profile, name="profile"),

    path("saved/", views.saved_course_list, name="saved"),

    path("save/<int:pk>/", views.save_course, name="save-course"),
    path("unsave/<int:pk>/", views.unsave_course, name="unsave-course"),
    path("course/<int:course_id>/enroll/", views.enroll_course, name="enroll"),
    path("student_dashboard/", StudentDashboardView.as_view(), name="student-dashboard"),

    path("course/<int:course_id>/lessons/", views.course_lessons, name="course-lessons"),
    path('certificate/<int:course_id>/', views.view_certificate, name='view-certificate'),
    path(
        'lesson/<int:lesson_id>/complete/',
        views.complete_lesson,
        name='complete-lesson'

    ),
    path(
        "certificate/<int:course_id>/download/",
        views.download_certificate_pdf,
        name="download_certificate_pdf"
    ),
]
