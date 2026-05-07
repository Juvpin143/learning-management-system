from datetime import timedelta
from django.core.paginator import Paginator
from django.db.models.functions import TruncDate
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.http import JsonResponse
from django.contrib import messages

from adminpanel.forms import MessageForm, SendMessageForm
from lms.models import Course, Enrolment
from django.contrib.auth import get_user_model
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Count
from django.utils import timezone
from django.db.models import Q
from lms.models import Message

User = get_user_model()


@staff_member_required
def admin_dashboard(request):
    courses = Course.objects.all()
    applications = Enrolment.objects.all()
    timeframe = request.GET.get("timeframe")
    today = timezone.now().date()

    if timeframe == "30":
        start_date = today - timedelta(days=29)
    elif timeframe == "all":
        start_date = None
    else:
        start_date = today - timedelta(days=6)

    total_users = User.objects.count()
    total_courses = Course.objects.count()
    total_applications = Enrolment.objects.count()
    total_applicants = Enrolment.objects.count()
    total_teachers = User.objects.filter(
        profile__is_instructor=True,
        is_staff=False,
        is_superuser=False
    ).count()
    total_students = User.objects.filter(
        profile__is_instructor=False,
        is_staff=False,
        is_superuser=False
    ).count()

    # === Employers Search + Filter ===
    teachers = User.objects.filter(
        profile__is_instructor=True,
        is_staff=False,
        is_superuser=False
    )

    q = request.GET.get("q")
    if q:
        teachers = teachers.filter(
            Q(username__icontains=q) | Q(email__icontains=q)
        )

    # Filter by active/inactive
    status = request.GET.get("status")
    if status == "active":
        teachers = teachers.filter(is_active=True)
    elif status == "inactive":
        teachers = teachers.filter(is_active=False)

    filtered_teachers = (
        teachers
        .annotate(course_count=Count("created_courses"))
        .order_by("-date_joined")[:10]
    )

    course_per_teachers = (
        Course.objects
        .filter(created_by__isnull=False)
        .values("created_by__username")
        .annotate(count=Count("id"))
        .order_by("-count")[:5]
    )

    teacher_names = [item["created_by__username"] for item in course_per_teachers]
    course_counts = [item["count"] for item in course_per_teachers]

    # === JOBS PER MONTH (for extra bar chart) ===
    course_per_month = (
        Course.objects.annotate(month=TruncDate("created_at")).values("month").annotate(count=Count("id")).order_by("month")
    )
    chart_labels = [item["month"].strftime("%%Y-%m-%d") for item in course_per_month]
    chart_data = [item["count"] for item in course_per_month]

    # === LINE CHART (Applications trend) ===
    start_date = request.GET.get('start_date')

    applications_query = Enrolment.objects.all()
    if start_date:
        applications_query = applications_query.filter(enrolled_at__date__gte=start_date)

    applications_per_day = (
        applications_query.annotate(date=TruncDate("enrolled_at")).values("date").annotate(total=Count("id")).order_by("-date")
    )
    dates = [item["date"].strftime("%Y-%m-%d") for item in applications_per_day]
    application_count = [item["total"] for item in applications_per_day]

    # === RECENT ===
    recent_course = Course.objects.order_by("-created_at")[:5]
    recent_applications = Enrolment.objects.order_by("-enrolled_at")[:5]
    recent_applicants = User.objects.filter(profile__is_instructor=False).order_by("-date_joined")[:5]
    recent_teachers = User.objects.filter(profile__is_instructor=True, is_staff=False, is_superuser=False).order_by("-date_joined")[:5]


    context = {
        'courses': courses,
        'applications': applications,
        'total_users': total_users,
        'total_courses': total_courses,
        'total_applications': total_applications,
        'total_teachers': total_teachers,
        'total_students': total_students,
        'filtered_teachers': filtered_teachers,
        'total_applicants': total_applicants,
        'teacher_names': teacher_names,
        'course_counts': course_counts,
        'chart_labels': chart_labels,
        'chart_data': chart_data,
        'dates': dates,
        'application_count': application_count,
        'recent_course': recent_course,
        'recent_applications': recent_applications,
        'recent_applicants': recent_applicants,
        'recent_teachers': recent_teachers,
        'timeframe': timeframe,
    }
    return render(request, 'accounts/admin_dashboard.html', context)

@staff_member_required
def application_trend(request):
    timeframe = request.GET.get("timeframe", "7")
    today = timezone.now().date()

    if timeframe == "30":
        start_date = today - timedelta(days=29)
    elif timeframe == "all":
        first = Enrolment.objects.order_by("enrolled_at").first()
        if not first:
            return JsonResponse({"dates": [], "applications_count": []})
        start_date = first.enrolled_at.date()
    else:
        start_date = today - timedelta(days=6)

    applications = (
        Enrolment.objects
        .filter(enrolled_at__date__gte=start_date)
        .annotate(date=TruncDate("enrolled_at"))
        .values("date")
        .annotate(total=Count("id"))
    )

    application_dict = {
        item["date"]: item["total"]
        for item in applications
    }

    dates = []
    applications_count = []

    current_date = start_date
    while current_date <= today:
        dates.append(current_date.strftime("%Y-%m-%d"))
        applications_count.append(application_dict.get(current_date, 0))
        current_date += timedelta(days=1)

    return JsonResponse({
        "dates": dates,
        "applications_count": applications_count
    })

@staff_member_required
def activate(request, user_id):
    user = get_object_or_404(User, id=user_id)

    # ❌ bawal i-deactivate ang superuser
    if user.is_superuser:
        messages.error(request, "Admin users cannot be deactivated.")
        return redirect(request.GET.get("next", "adminpanel:user_list"))

    user.is_active = True
    user.save()

    messages.success(request, f"{user.username} has been activated.")
    return redirect(request.GET.get("next", "adminpanel:user_list"))


@staff_member_required
def deactivate(request, user_id):
    user = get_object_or_404(User, id=user_id)

    # ❌ bawal i-deactivate ang superuser
    if user.is_superuser:
        messages.error(request, "Admin users cannot be deactivated.")
        return redirect(request.GET.get("next", "adminpanel:user_list"))

    user.is_active = False
    user.save()

    messages.warning(request, f"{user.username} has been deactivated.")
    return redirect(request.GET.get("next", "adminpanel:user_list"))

@staff_member_required
def delete_user(request, user_id):
    print("✅ DELETE triggered with user_id:", user_id)
    teacher = get_object_or_404(
        User,
        id=user_id,
        profile__is_instructor=True
    )

    # 👉 get admin (superuser)
    admin_user = User.objects.filter(
        is_superuser=True,
        is_active=True
    ).first()

    if not admin_user:
        messages.error(request, "No admin user found to reassign courses.")
        return redirect("adminpanel:teacher-overview")

    # 👉 reassign courses to admin
    Course.objects.filter(created_by=teacher).update(created_by=admin_user)

    username = teacher.username
    teacher.delete()

    messages.success(
        request,
        f"Teacher {username} deleted. Courses reassigned to Admin."
    )

    return redirect("adminpanel:teacher-overview")


@staff_member_required
def teachers_overview(request):
    search_query = request.GET.get("search", "")
    status_filter = request.GET.get("status", "")

    teachers = User.objects.filter(
        profile__is_instructor=True,
        is_staff=False,
        is_superuser=False
    )

    if search_query:
        teachers = teachers.filter(username__icontains=search_query)

    if status_filter == "active":
        teachers = teachers.filter(is_active=True)
    elif status_filter == "inactive":
        teachers = teachers.filter(is_active=False)

    paginator = Paginator(
        teachers.order_by("-date_joined"),
        5
    )
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    context = {
        "page_obj": page_obj,
        "search_query": search_query,
        "status_filter": status_filter,
    }
    return render(
        request,
        "adminpanel/teachers_overview.html",
        context
    )

@staff_member_required
def teacher_details(request, teacher_id):
    teacher = get_object_or_404(
        User,
        id=teacher_id,
        profile__is_instructor=True,
        is_staff=False,
        is_superuser=False
    )

    courses = Course.objects.filter(created_by=teacher)

    applications = Enrolment.objects.filter(course__created_by=teacher)

    return render(request, "adminpanel/teacher_detail.html", {"teacher": teacher, "applications": applications, "courses": courses})

@staff_member_required
def user_list(request):
    query = request.GET.get("q", "").strip()
    role = request.GET.get("role", "")

    users = User.objects.select_related("profile")

    #  Search (username OR email)
    if query:
        users = users.filter(
            Q(username__icontains=query) |
            Q(email__icontains=query)
        )

    #  Role filter
    if role == "admin":
        users = users.filter(is_superuser=True)

    elif role == "teacher":
        users = users.filter(
            is_superuser=False,
            profile__is_instructor=True
        )

    elif role == "student":
        users = users.filter(
            is_superuser=False,
            profile__is_instructor=False
        )

    return render(request, "adminpanel/user_list.html", {
        "users": users
    })

@staff_member_required
def applications_overview(request):
    applications = Enrolment.objects.select_related("course", "applicant").all().order_by("-enrolled_at")
    return render(request, "adminpanel/applications_overview.html", {
        "applications": applications
    })

@login_required
def inbox(request):
    messages_qs = Message.objects.filter(
        receiver=request.user
    ).order_by("-created_at")

    return render(
        request,
        "adminpanel/inbox.html",
        {"messages": messages_qs}
    )

@login_required
def sent_messages(request):
    messages_qs = Message.objects.filter(
        sender=request.user
    ).order_by("-created_at")

    return render(
        request,
        "adminpanel/sent_messages.html",
        {"messages": messages_qs}
    )

@login_required
def message_detail(request, pk):
    msg = get_object_or_404(
        Message,
        id=pk
    )

    # 🔒 Security: sender OR receiver lang pwede
    if request.user != msg.sender and request.user != msg.receiver:
        return HttpResponseForbidden("You are not allowed to view this message.")

    # 📬 Mark as read kung receiver
    if request.user == msg.receiver and not msg.is_read:
        msg.is_read = True
        msg.save()

    return render(
        request,
        "adminpanel/message_detail.html",
        {"message": msg}
    )

@login_required
def compose_message(request):
    if request.method == "POST":
        form = MessageForm(request.POST)
        if form.is_valid():
            msg = form.save(commit=False)
            msg.sender = request.user
            msg.save()

            messages.success(request, "Message sent successfully!")
            return redirect("adminpanel:sent-messages")
    else:
        form = MessageForm()

    return render(
        request,
        "adminpanel/compose_message.html",
        {
            "form": form
        }
    )

@login_required
def send_message(request, user_id):
    receiver = get_object_or_404(User, id=user_id)

    if request.method == "POST":
        form = SendMessageForm(request.POST)
        if form.is_valid():
            msg = form.save(commit=False)
            msg.sender = request.user
            msg.receiver = receiver
            msg.save()
            messages.success(request, "Message sent successfully!")
            return redirect("adminpanel:sent-messages")
    else:
        # kapag GET, dito na gagawa ng form
        form = SendMessageForm()

    return render(
        request,
        "adminpanel/send_message.html",
        {"form": form, "receiver": receiver},
    )

