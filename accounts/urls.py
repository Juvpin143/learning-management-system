from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('login/', auth_views.LoginView.as_view(template_name='accounts/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),

    path('register/student/', views.register_student, name='register_student'),
    path('register/teacher/', views.register_teacher, name='register_teacher'),

    # Email verification
    path("activate/<uidb64>/<token>/", views.activate_account, name="activate"),
    path("send-verification-email/", views.send_verification_email, name="send-verification-email"),

    # Reset Password
    path('forgot-password/', views.forgot_password, name="forgot-password"),
    path('reset/<uidb64>/<token>/', views.reset_password, name="reset"),
    path('reset_password_email/', views.reset_password_email, name="reset-email"),

    path('dashboard/', views.dashboard, name='dashboard'),
]
