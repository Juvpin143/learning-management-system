from django.shortcuts import render, redirect
from django.core.mail import EmailMultiAlternatives
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.sites.shortcuts import get_current_site
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.contrib.auth.tokens import default_token_generator
from django.utils.encoding import force_bytes, force_str
from django.contrib.auth import get_user_model
from .forms import StudentRegisterForm, TeacherRegisterForm
from django.template.loader import render_to_string
from email.mime.image import MIMEImage
from django.conf import settings
import os

User = get_user_model()

def register_student(request):
    if request.method == "POST":
        form = StudentRegisterForm(request.POST)
        if form.is_valid():
            student = form.save(commit=False)
            student.role = "student"
            student.is_active = False
            student.save()

            send_verification_email(request, student)

            messages.success(request, "Your account has been created! Please check your email to verify your account.")
            return redirect("login")

    else:
        form = StudentRegisterForm()
    return render(request, 'accounts/register_students.html', {'form': form})

def register_teacher(request):
    if request.method == "POST":
        form = TeacherRegisterForm(request.POST)
        if form.is_valid():
            teacher = form.save(commit=False)
            teacher.role = "teacher"
            teacher.is_active = False
            teacher.save()

            # ✅ SET PROFILE FLAG
            teacher.profile.is_instructor = True
            teacher.profile.save()

            send_verification_email(request, teacher)

            messages.success(request, "Your account has been created! Please check your email to verify your account.")
            return redirect("login")
    else:
        form = TeacherRegisterForm()
    return render(request, 'accounts/register_teachers.html', {'form': form})


def send_verification_email(request, user):
    domain = get_current_site(request).domain
    protocol = "https" if request.is_secure() else "http"

    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = default_token_generator.make_token(user)

    activation_link = f"{protocol}://{domain}/accounts/activate/{uid}/{token}/"

    subject = "Welcome to Learning Management System (LMS) – Verify Your Email"
    from_email = settings.DEFAULT_FROM_EMAIL
    to = [user.email]

    html_content = render_to_string("accounts/verify_email.html", {
        "user": user,
        "activation_link": activation_link,
    })

    email = EmailMultiAlternatives(subject, '', from_email, to)
    email.attach_alternative(html_content, "text/html")

    # ✅ AUTO EMBED LMS LOGO
    logo_path = os.path.join(settings.BASE_DIR, "static", "img", "lms_logo.png")

    if os.path.exists(logo_path):
        with open(logo_path, "rb") as f:
            logo = MIMEImage(f.read())
            logo.add_header('Content-ID', '<lms_logo>')
            logo.add_header('Content-Disposition', 'inline', filename="lms_logo.png")
            email.attach(logo)

    email.send()

def activate_account(request, uidb64, token):
    try:
        uuid = urlsafe_base64_decode(uidb64).decode()
        user = User.objects.get(pk=uuid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user is not None and default_token_generator.check_token(user, token):
        user.is_active = True
        user.save()
        return render(request, "accounts/activation_success.html")
    else:
        messages.error(request, "❌ The activation link is invalid or has expired.")
        return redirect("login")

def forgot_password(request):
    if request.method == "POST":
        email = request.POST.get("email")

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            messages.error(request, "No account found with this email.")
            return redirect("forgot-password")

        reset_password_email(request, user)

        messages.success(request, "Password reset email has been sent. Please check your email.")
        return redirect("login")

    return render(request, "accounts/forgot_password.html")

def reset_password(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user is not None and default_token_generator.check_token(user, token):
        if request.method == "POST":
            password1 = request.POST.get("password1")
            password2 = request.POST.get("password2")

            if password1 != password2:
                messages.error(request, "Passwords do not match.")
                return redirect(request.path)

            user.set_password(password1)
            user.save()

            messages.success(request, "Your password has been reset successfully. You can now login.")
            return redirect("login")

        return render(request, "accounts/reset_password.html")

    else:
        messages.error(request, "Invalid or expired password reset link.")
        return redirect("forgot-password")

def reset_password_email(request, user):
    domain = get_current_site(request).domain
    protocol = "https" if request.is_secure() else "http"

    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = default_token_generator.make_token(user)

    reset_link = f"{protocol}://{domain}/accounts/reset/{uid}/{token}/"

    subject = "Reset Your Password - Learning Management System (LMS)"
    from_email = settings.DEFAULT_FROM_EMAIL
    to = [user.email]

    html_content = render_to_string("accounts/reset_password_email.html", {
        "user": user,
        "reset_link": reset_link,
    })

    email = EmailMultiAlternatives(subject, "", from_email, to)
    email.attach_alternative(html_content, "text/html")

    # ✅ AUTO EMBED LMS LOGO
    logo_path = os.path.join(settings.BASE_DIR, "static", "img", "lms_logo.png")

    if os.path.exists(logo_path):
        with open(logo_path, "rb") as f:
            logo = MIMEImage(f.read())
            logo.add_header('Content-ID', '<lms_logo>')
            logo.add_header('Content-Disposition', 'inline', filename="lms_logo.png")
            email.attach(logo)
    email.send()

@login_required
def dashboard(request):
    user = request.user

    if user.is_superuser:
        messages.success(request, f"Welcome back Admin {user.username}!")
        return redirect("adminpanel:admin-dashboard")

    elif user.role == "teacher":
        messages.success(request, f"Welcome back {user.username}!")
        return redirect("teacher-dashboard")

    elif user.role == "student":
        messages.success(request, f"Welcome {user.username}, Thanks for visiting!")
        return redirect("student-dashboard")
