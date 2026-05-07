from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponseForbidden, JsonResponse
from django.views.generic import ListView, TemplateView
from django.shortcuts import render, redirect, get_object_or_404
from lms.models import Enrolment, Course, Review, Notification
from django.utils.dateparse import parse_date
from django.contrib import messages
from django.views.decorators.http import require_POST
from lms.utils import add_notification
from django.db.models import Q
from lms.models import Lesson
import json

# Teacher Dashboard
class TeacherDashboardView(LoginRequiredMixin, TemplateView):
    template_name = "accounts/teacher_dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # All courses created by this teacher
        teacher_courses = Course.objects.filter(created_by=self.request.user)

        # Stats
        enrolments = Enrolment.objects.filter(course__created_by=self.request.user)

        context["total_courses"] = teacher_courses.count()
        context["total_applications"] = enrolments.count()

        context["pending_count"] = enrolments.filter(status="pending").count()
        context["approved_count"] = enrolments.filter(status="approved").count()
        context["enrolled_count"] = enrolments.filter(status="enrolled").count()
        context["completed_count"] = enrolments.filter(status="completed").count()
        context["rejected_count"] = enrolments.filter(status="rejected").count()
        context["teacher_courses"] = teacher_courses

        # Recent Applications (last 10 based on date)
        context["recent_applications"] = enrolments.order_by("-enrolled_at")[:10]

        # Activity Feed
        feed = []

        # Courses created (last 10)
        for c in teacher_courses.order_by("-created_at")[:10]:
            feed.append({
                "type": "course",
                "title": c.title,
                "date": c.created_at,
            })

        # Applications
        for app in context["recent_applications"]:
            feed.append({
                "type": "application",
                "applicant": app.user.username,
                "title": app.course.title,
                "date": app.enrolled_at,
            })

        context["activity_feed"] = sorted(feed, key=lambda x: x["date"], reverse=True)

        return context


@login_required
def create_course(request):
    if not request.user.is_teacher:
        return redirect("student_dashboard")

    if request.method == "POST":
        Course.objects.create(
            title=request.POST.get("title"),
            subtitle=request.POST.get("subtitle"),
            description=request.POST.get("description"),
            category=request.POST.get("category"),
            level=request.POST.get("level"),
            duration=request.POST.get("duration"),
            language=request.POST.get("language"),
            promo_video_url=request.POST.get("promo_video_url"),
            thumbnail=request.FILES.get("thumbnail"),
            created_by=request.user,
            is_published=True
        )

        messages.success(request, "Course created successfully!")
        return redirect("teacher-dashboard")

    return render(request, "teacher/create_course.html")

@login_required
def view_course_application(request, course_id):
    course = get_object_or_404(Course, id=course_id, created_by=request.user)
    applications = Enrolment.objects.filter(course=course)
    return render(request, "teacher/view_course_application.html", {
        "course": course,
        "applications": applications
    })

class ManageApplicationView(LoginRequiredMixin, ListView):
    model = Course
    template_name = "teacher/manage_application.html"
    context_object_name = "courses"

    def get_queryset(self):
        return Course.objects.filter(created_by=self.request.user)

class CourseApplicationView(LoginRequiredMixin, ListView):
    template_name = "teacher/course_application_view.html"
    context_object_name = "enrolments"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        course_id = self.kwargs["course_id"]

        context["course"] = get_object_or_404(
            Course,
            id=course_id,
            created_by=self.request.user
        )

        return context

    def get_queryset(self):
        course_id = self.kwargs["course_id"]
        user = self.request.user

        enrolments = Enrolment.objects.select_related(
            "course", "user"
        ).filter(
            course__id=course_id,
            course__created_by=user
        )

        enrolments = self.apply_search(enrolments)
        enrolments = self.apply_status_filter(enrolments)
        enrolments = self.apply_date_filter(enrolments)

        return enrolments.order_by("-enrolled_at")

    def apply_search(self, queryset):
        query = self.request.GET.get("search")
        if query:
            return queryset.filter(
                Q(course__title__icontains=query) |
                Q(user__username__icontains=query)
            )
        return queryset

    def apply_status_filter(self, queryset):
        status = self.request.GET.get("status")
        if status:
            return queryset.filter(status=status)
        return queryset

    def apply_date_filter(self, queryset):
        date = self.request.GET.get("date")
        if date:
            parsed = parse_date(date)
            if parsed:
                return queryset.filter(enrolled_at__date=parsed)
        return queryset

@login_required
@require_POST
def update_application_status(request, app_id):
    enrolment = get_object_or_404(
        Enrolment,
        id=app_id,
        course__created_by=request.user
    )

    new_status = request.POST.get("status")

    valid_statuses = dict(Enrolment.STATUS_CHOICES).keys()

    if new_status not in valid_statuses:
        return JsonResponse({
            "success": False,
            "error": "Invalid status"
        })

    enrolment.status = new_status
    enrolment.save()

    add_notification(
        recipient=enrolment.user,
        message=f"Your enrollment for '{enrolment.course.title}' was {new_status}.",
        link=f"/my-courses/"
    )

    return JsonResponse({
        "success": True,
        "status": enrolment.status
    })

@login_required
def lesson_list(request, course_id):
    course = get_object_or_404(
        Course,
        id=course_id,
        created_by=request.user
    )

    lessons = course.lessons.all()

    return render(request, "teacher/lesson_list.html", {
        "course": course,
        "lessons": lessons
    })

@login_required
def lesson_create(request, course_id):
    course = get_object_or_404(
        Course,
        id=course_id,
        created_by=request.user
    )

    if request.method == "POST":
        Lesson.objects.create(
            course=course,
            title=request.POST.get("title"),
            description=request.POST.get("description"),
            video_url=request.POST.get("video_url"),
            document=request.FILES.get("document"),
            order=request.POST.get("order") or 1
        )

        messages.success(request, "Lesson created successfully!")
        return redirect("lesson_list", course_id=course.id)

    return render(request, "teacher/lesson_create.html", {
        "course": course
    })

@login_required
def lesson_delete(request, lesson_id):
    lesson = get_object_or_404(
        Lesson,
        id=lesson_id,
        course__created_by=request.user
    )

    course_id = lesson.course.id
    lesson.delete()

    messages.success(request, "Lesson deleted.")
    return redirect("lesson_list", course_id=course_id)

@login_required
def edit_lesson(request, lesson_id):
    lesson = get_object_or_404(
        Lesson,
        id=lesson_id,
        course__created_by=request.user
    )

    if request.method == "POST":
        lesson.title = request.POST.get("title")
        lesson.description = request.POST.get("description")
        lesson.video_url = request.POST.get("video_url")
        lesson.order = request.POST.get("order")

        if request.FILES.get("document"):
            lesson.document = request.FILES.get("document")

        lesson.save()

        messages.success(request, "Lesson updated successfully!")
        return redirect("lesson_list", course_id=lesson.course.id)

    return render(request, "teacher/lesson_edit.html", {
        "lesson": lesson
    })

@login_required
def manage_review(request):
    user = request.user

    if user.is_superuser:
        reviews = Review.objects.select_related(
            "course", "user"
        ).order_by("-created_at")

    elif hasattr(user, "profile") and user.profile.is_instructor:
        reviews = Review.objects.select_related(
            "course", "user"
        ).filter(
            course__created_by=user
        ).order_by("-created_at")

    else:
        return HttpResponseForbidden("Not allowed")

    return render(request, "teacher/manage_review.html", {
        "reviews": reviews
    })

@login_required
def reply_review(request, review_id):
    if request.method != "POST":
        return HttpResponseForbidden()

    review = get_object_or_404(Review, id=review_id)

    # 🔐 SECURITY: teacher/admin lang pwede
    if not (
        request.user.is_superuser or
        (hasattr(request.user, "profile")
         and request.user.profile.is_instructor
         and review.course.created_by == request.user)
    ):
        return HttpResponseForbidden()

    reply = request.POST.get("reply")

    if reply:
        review.reply = reply
        review.replied_by = request.user
        review.save()
        messages.success(request, "Reply sent successfully.")

    return redirect("manage-review")

@login_required
def delete_review(request, review_id):
    if request.method != "POST":
        return HttpResponseForbidden()

    review = get_object_or_404(Review, id=review_id)

    if not (
        request.user.is_superuser or
        (hasattr(request.user, "profile")
         and request.user.profile.is_instructor
         and review.course.created_by == request.user)
    ):
        return HttpResponseForbidden()

    review.delete()
    messages.success(request, "Review deleted.")

    return redirect("manage-review")


@login_required
def notification_view(request):
    notifications = Notification.objects.filter(
        recipient=request.user
    ).order_by("-created_at")

    unread_notification_count = notifications.filter(is_read=False).count()

    return render(request, "notifications/list.html", {
        "notifications": notifications,
        "unread_notification_count": unread_notification_count
    })

@login_required
def mark_as_read(request, notif_id):
    if request.method == "POST":
        notif = get_object_or_404(
            Notification,
            id=notif_id,
            recipient=request.user
        )
        notif.is_read = True
        notif.save()
    return redirect("view-notification")

def unread_notifications(request):
    if request.user.is_authenticated:
        notifications = Notification.objects.filter(
            recipient=request.user
        ).order_by("-created_at")[:5]

        return {
            "unread_notifications_count": notifications.filter(is_read=False).count(),
            "notifications": notifications
        }

    return {
        "unread_notifications_count": 0,
        "notifications": []
    }

