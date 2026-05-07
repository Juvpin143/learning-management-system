from django.db import models
from django.conf import settings
from django.utils.text import slugify
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator

User = get_user_model()

class Course(models.Model):

    LEVEL_CHOICES = [
        ('beginner', 'Beginner'),
        ('intermediate', 'Intermediate'),
        ('advanced', 'Advanced'),
    ]

    title = models.CharField(max_length=200)
    subtitle = models.CharField(max_length=250, blank=True, null=True)
    description = models.TextField()

    category = models.CharField(max_length=100, blank=True, null=True)
    level = models.CharField(max_length=20, choices=LEVEL_CHOICES, default='beginner')

    thumbnail = models.ImageField(upload_to="course_thumbnails/", blank=True, null=True)
    promo_video_url = models.URLField(blank=True, null=True)

    duration = models.CharField(max_length=50, blank=True, null=True)
    language = models.CharField(max_length=50, default="English")

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_courses"
    )
    is_published = models.BooleanField(default=False)

    slug = models.SlugField(unique=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        # Auto-create slug only if empty
        if not self.slug:
            base_slug = slugify(self.title)
            slug = base_slug
            counter = 1

            # Ensure slug is unique
            while Course.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1

            self.slug = slug

        super().save(*args, **kwargs)

    def __str__(self):
        return self.title

class Lesson(models.Model):
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name="lessons"
    )

    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)

    video_url = models.URLField(blank=True, null=True)
    document = models.FileField(upload_to="lesson_docs/", blank=True, null=True)

    order = models.PositiveIntegerField(default=1)
    is_published = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["order"]

    def __str__(self):
        return f"{self.course.title} - {self.title}"

class Enrolment(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    course = models.ForeignKey('Course', on_delete=models.CASCADE)

    applicant = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="manage_application",
        null=True,
        blank=True
    )

    full_name = models.CharField(max_length=150, blank=True)
    email = models.EmailField(blank=True)

    enrolled_at = models.DateTimeField(auto_now_add=True)

    progress = models.IntegerField(default=0)
    completed = models.BooleanField(default=False)
    certificate_url = models.CharField(max_length=255, blank=True, null=True)

    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("approved", "Approved"),
        ("rejected", "Rejected"),
        ("enrolled", "Enrolled"),
        ("completed", "Completed"),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    rejection_reason = models.TextField(blank=True, null=True)

    class Meta:
        unique_together = ('user', 'course')

    def save(self, *args, **kwargs):
        is_new = self.pk is None

        old_status = None
        if not is_new:
            old_status = Enrolment.objects.get(pk=self.pk).status

        if not self.full_name:
            self.full_name = self.user.get_full_name() or self.user.username
        if not self.email:
            self.email = self.user.email

        super().save(*args, **kwargs)

        # 🔔 STATUS CHANGE NOTIFICATION
        if old_status and old_status != self.status:
            from .models import Notification  # safe local import

            status_messages = {
                "approved": f"✅ Your application for {self.course.title} was approved.",
                "rejected": f"❌ Your application for {self.course.title} was rejected.",
                "enrolled": f"🎉 You are now enrolled in {self.course.title}.",
                "completed": f"🏆 You completed the course {self.course.title}.",
            }

            message = status_messages.get(self.status)

            if message:
                Notification.objects.create(
                    recipient=self.user,
                    message=message,
                    link=f"/courses/{self.course.slug}/"
                )


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)

    # 🖼 Profile Image
    profile_image = models.ImageField(
        upload_to='profile_pics/',
        default='default-user.png'
    )

    # 👤 Basic Info
    full_name = models.CharField(max_length=100, blank=True, null=True)
    address = models.CharField(max_length=255, blank=True, null=True)
    phone_number = models.CharField(max_length=20, blank=True, null=True)

    # 🎯 Skills / Interests
    skills = models.TextField(blank=True, null=True)

    # 📚 LMS-specific
    bio = models.TextField(blank=True, null=True)
    is_instructor = models.BooleanField(default=False)
    enrolled_courses_count = models.IntegerField(default=0)
    completed_courses_count = models.IntegerField(default=0)

    # 👨‍🏫 Teacher-specific fields
    expertise = models.CharField(max_length=255, blank=True, null=True)
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)

    def __str__(self):
        return f"{self.user.username} Profile"


class SavedCourse(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="saved_course")
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    saved_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "course")

    def __str__(self):
        return f"{self.user.username} saved {self.course.title}"

class LessonProgress(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE)
    completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ('user', 'lesson')

    def __str__(self):
        return f"{self.user} - {self.lesson.title}"

class Certificate(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    issued_at = models.DateTimeField(auto_now_add=True)
    certificate_id = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return f"{self.user} - {self.course}"

class Review(models.Model):
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name="reviews"
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="course_reviews"
    )

    rating = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )

    comment = models.TextField()

    reply = models.TextField(blank=True, null=True)
    replied_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="review_replies"
    )

    is_approved = models.BooleanField(
        default=True,
        help_text="Only approved reviews are visible to public"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Review"
        verbose_name_plural = "Reviews"
        unique_together = ("course", "user")

    def __str__(self):
        return f"{self.user.username} → {self.course.title} ({self.rating}⭐)"

class Notification(models.Model):
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name="notifications")
    message = models.CharField(max_length=255)
    link = models.URLField(blank=True, null=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.message
    
class Message(models.Model):
    sender = models.ForeignKey(User, related_name="sent_messages", on_delete=models.CASCADE)
    receiver = models.ForeignKey(User, related_name="received_messages", on_delete=models.CASCADE)
    subject = models.CharField(max_length=255, blank=True)
    body = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.subject if self.subject else f"Message #{self.id}"

