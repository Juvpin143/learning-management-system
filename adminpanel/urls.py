from django.urls import path
from . import views

app_name = "adminpanel"

urlpatterns = [
    path("admin_dashboard/", views.admin_dashboard, name="admin-dashboard"),
    path(
        "applications-trend/",
        views.application_trend,
        name="applications_trend_data"
    ),
    path("applications/", views.applications_overview, name="applications"),
    path("teacher_detail/<int:teacher_id>/", views.teacher_details, name="teacher-detail"),
    path("teacher_overview/", views.teachers_overview, name="teacher-overview"),
    path("user-list/", views.user_list, name="user_list"),
    path("teachers/activate/<int:user_id>/", views.activate, name="activate"),
    path("teachers/deactivate/<int:user_id>/" , views.deactivate, name="deactivate"),
    path("teachers/delete/<int:user_id>/", views.delete_user, name="delete"),

    # MESSAGE
    path("admin/inbox/", views.inbox, name="inbox"),
    path("admin/<int:pk>/message-detail/", views.message_detail, name="message-detail"),
    path("admin/sent/", views.sent_messages, name="sent-messages"),
    path("admin/messages-compose/", views.compose_message, name="compose-message"),
    path("admin/<int:user_id>/send-message", views.send_message, name="send-message"),
]
