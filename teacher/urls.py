from django.urls import path
from . import views

urlpatterns = [
    path(
        "teacher/dashboard/",
        views.TeacherDashboardView.as_view(),
        name="teacher-dashboard"
    ),

    path(
        "teacher/course/add/",
        views.create_course,
        name="create-course"
    ),

    # LIST OF COURSES (Manage page)
    path(
        "teacher/manage-application/",
        views.ManageApplicationView.as_view(),
        name="manage-application"
    ),

    # MANAGE-REVIEW
    path("teacher/manage-review/", views.manage_review, name="manage-review"),
    path("teacher/<int:review_id>/reply-review/", views.reply_review, name="reply-review"),
    path("teacher/<int:review_id>/delete-review/", views.delete_review, name="delete-review"),

    # APPLICATIONS PER COURSE
    path(
        "teacher/<int:course_id>/applications/",
        views.CourseApplicationView.as_view(),
        name="view-application"
    ),

    path(
        "teacher/application/<int:app_id>/update-status/",
        views.update_application_status,
        name="update-application-status"
    ),

    path("courses/<int:course_id>/lessons/", views.lesson_list, name="lesson_list"),
    path("courses/<int:course_id>/lessons/add/", views.lesson_create, name="lesson_create"),
    path("lessons/<int:lesson_id>/delete/", views.lesson_delete, name="lesson_delete"),
    path("lessons/<int:lesson_id>/edit/", views.edit_lesson, name="edit-lesson"),

    # Notification
    path("teacher/notification-view/", views.notification_view, name="view-notification"),
    path("teacher/<int:notif_id>/mark-as-read-notification", views.mark_as_read, name="mark-as-read"),
]
