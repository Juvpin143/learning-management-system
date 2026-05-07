from django.shortcuts import render, get_object_or_404, redirect
from .models import Course, Lesson, Enrolment, SavedCourse, LessonProgress, Certificate, Review
from .forms import ProfileUpdateForm, ReviewForm
from django.contrib import messages
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from .utils import check_and_issue_certificate
from weasyprint import HTML
from django.http import HttpResponse
from django.db.models import Avg
from django.template.loader import render_to_string
from .utils import add_notification

def course_list(request):
    courses = Course.objects.filter(is_published=True).order_by('-created_at')

    # Search
    query = request.GET.get('q')
    if query:
        courses = courses.filter(title__icontains=query) | courses.filter(subtitle__icontains=query)

    # Pagination
    paginator = Paginator(courses, 6)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'lms/course_list.html', {
        'page_obj': page_obj,
        'query_params': request.GET.urlencode(),
    })

def course_detail(request, pk):
    course = get_object_or_404(Course, pk=pk)

    lessons = Lesson.objects.filter(course=course)
    total_lessons = lessons.count()

    completed_lessons = LessonProgress.objects.filter(
        user=request.user,
        lesson__course=course,
        completed=True
    ).count() if request.user.is_authenticated else 0

    progress_percent = int((completed_lessons / total_lessons) * 100) if total_lessons > 0 else 0

    is_enrolled = False
    if request.user.is_authenticated:
        is_enrolled = Enrolment.objects.filter(
            user=request.user,
            course=course,
            status="enrolled"
        ).exists()

    # Reviews
    reviews = Review.objects.filter(course=course, is_approved=True)
    avr_rating = reviews.aggregate(avg=Avg('rating'))['avg']

    existing_review = None
    can_review = False
    can_reply = False

    if request.user.is_authenticated:
        existing_review = Review.objects.filter(
            course=course,
            user=request.user
        ).first()

        can_review = is_enrolled and not existing_review

        can_reply = (
                (request.user == course.created_by and request.user.profile.is_instructor)
                or request.user.is_superuser
        )

    if request.method == "POST" and can_review:
        form = ReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.course = course
            review.user = request.user
            review.save()
            messages.success(request, "Review submitted!")
            return redirect("course-detail", pk=course.pk)
    else:
        form = ReviewForm()

    return render(request, "lms/course_detail.html", {
        "course": course,
        "lessons": lessons,
        "progress_percent": progress_percent,
        "is_enrolled": is_enrolled,
        "avr_rating": avr_rating,
        "reviews": reviews,
        "form": form,
        "can_review": can_review,
        "can_reply": can_reply,
        "existing_review": existing_review,
    })

def about(request):
    return render(request, 'lms/about.html')

@login_required
def save_course(request, pk):
    course = get_object_or_404(Course, pk=pk)

    saved, created = SavedCourse.objects.get_or_create(
        user=request.user,
        course=course
    )

    if created:
        messages.success(request, f"✔ '{course.title}' added to your wishlist!")
    else:
        messages.info(request, f" '{course.title}' is already in your wishlist.")

    return redirect('course-detail', pk=pk)


@login_required
def unsave_course(request, pk):
    course = get_object_or_404(Course, pk=pk)
    SavedCourse.objects.filter(user=request.user, course=course).delete()

    messages.info(request, f"❌ '{course.title}' removed from your wishlist!")
    return redirect('saved')


@login_required
def saved_course_list(request):
    saved = SavedCourse.objects.filter(user=request.user).order_by("-saved_at")
    return render(request, "lms/saved_course.html", {"saved": saved})

@login_required
def complete_lesson(request, lesson_id):
    lesson = get_object_or_404(Lesson, id=lesson_id)

    progress, created = LessonProgress.objects.get_or_create(
        user=request.user,
        lesson=lesson
    )

    progress.completed = True
    progress.completed_at = timezone.now()
    progress.save()

    check_and_issue_certificate(request.user, lesson.course)

    return redirect('course-detail', lesson.course.id)


def lesson_detail(request, pk):
    lesson = get_object_or_404(Lesson, pk=pk)
    return render(request, 'lms/lesson_detail.html', {'lesson': lesson})

@login_required
def profile(request):
    if request.method == "POST":
        form = ProfileUpdateForm(request.POST, request.FILES, instance=request.user.profile)
        if form.is_valid():
            form.save()
            messages.success(request, "Profile updated!")
    else:
        form = ProfileUpdateForm(instance=request.user.profile)

    return render(request, "lms/profile.html", {
        "form": form,
    })

@login_required
def enroll_course(request, course_id):
    course = get_object_or_404(Course, id=course_id)

    # Auto-create enrollment, no form, no extra steps
    enrollment, created = Enrolment.objects.get_or_create(
        user=request.user,
        course=course,
        defaults={"status": "pending", "enrolled_at": timezone.now()},
    )

    if created:
        add_notification(
            recipient=course.created_by,
            message=f"{request.user.username} applied to your course: {course.title}",
            link=f"/teacher/course/{course.id}/applications/"
        )

    if created:
        messages.success(request, f"You're now enrolled in {course.title}!")
    else:
        messages.info(request, f"You're already enrolled in {course.title}.")

    return redirect("my-courses")

@login_required
def my_course(request):
    enrolments = Enrolment.objects.filter(user=request.user)
    return render(request, "lms/my_courses.html", {'enrollments': enrolments    })

def get_recommended_course(user, limit=5):
    enrolled_ids = Enrolment.objects.filter(user=user)\
        .values_list("course_id", flat=True)
    # Only recommended published courses
    return Course.objects.filter(is_published=True)\
        .exclude(id__in=enrolled_ids)[:limit]

class StudentDashboardView(LoginRequiredMixin, TemplateView):
    template_name = "accounts/student_dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        user = self.request.user

        # ============================
        # 1) APPLICATIONS
        # ============================
        applications = Enrolment.objects.filter(
            user=user
        ).order_by("-enrolled_at")

        # ============================
        # 2) SAVED COURSES
        # ============================
        saved = SavedCourse.objects.filter(
            user=user
        ).order_by("-saved_at")

        # ============================
        # 3) ACTIVITY FEED (BAGO)
        # ============================
        feed = []

        # Enrollment activities
        for app in applications:
            feed.append({
                "type": "application",
                "course": app.course,
                "status": app.status,
                "date": app.enrolled_at,
            })

        # Saved course activities
        for s in saved:
            feed.append({
                "type": "saved",
                "course": s.course,
                "date": s.saved_at,
            })

        # POSITIVE SORT
        feed = sorted(feed, key=lambda x: x["date"], reverse=True)
        context["activity_feed"] = feed[:10]  # limit 10

        # ============================
        # 4) SMART RECOMMENDATIONS
        # ============================
        enrolled_ids = applications.values_list("course_id", flat=True)

        recommended = Course.objects.filter(
            is_published=True
        ).exclude(id__in=enrolled_ids)

        # limit 5
        context["recommended_course"] = recommended[:5]
        context["saved_courses"] = saved.count()

        return context

@login_required
def course_lessons(request, course_id):
    course = get_object_or_404(Course, id=course_id)

    # check if student is enrolled
    is_enrolled = Enrolment.objects.filter(
        user=request.user,
        course=course,
        status='enrolled'
    ).exists()

    lessons = course.lessons.all().order_by('order')

    # ✅ CALCULATE PROGRESS HERE
    total_lessons = lessons.count()
    completed_lessons = LessonProgress.objects.filter(
        user=request.user,
        lesson__course=course,
        completed=True
    ).count()

    progress_percent = 0
    if total_lessons > 0:
        progress_percent = int((completed_lessons / total_lessons) * 100)

    return render(request, "lms/course_lessons.html", {
        "course": course,
        "lessons": lessons,
        "is_enrolled": is_enrolled,
        "progress_percent": progress_percent,
    })

@login_required
def view_certificate(request, course_id):
    certificate = get_object_or_404(
        Certificate,
        user=request.user,
        course_id=course_id
    )

    return render(request, "lms/certificate.html", {
        "certificate": certificate
    })

@login_required
def download_certificate_pdf(request, course_id):
    certificate = get_object_or_404(
        Certificate,
        user=request.user,
        course_id=course_id
    )

    html_string = render_to_string(
        "lms/certificate_pdf.html",
        {"certificate": certificate, "user": request.user}
    )

    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = (
        f'attachment; filename="certificate-{certificate.certificate_id}.pdf"'
    )

    HTML(string=html_string, base_url=request.build_absolute_uri()).write_pdf(response)
    return response

