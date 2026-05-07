import uuid
from .models import LessonProgress, Certificate
from .models import Notification

def add_notification(recipient, message, link=None):
    if recipient:
        Notification.objects.create(
            recipient=recipient,
            message=message,
            link=link
        )

def check_and_issue_certificate(user, course):
    total_lessons = course.lessons.count()
    completed = LessonProgress.objects.filter(
        user=user,
        lesson__course=course,
        completed=True
    ).count()

    if total_lessons == 0:
        return

    progress = (completed / total_lessons) * 100

    if progress == 100:
        Certificate.objects.get_or_create(
            user=user,
            course=course,
            defaults={
                'certificate_id': str(uuid.uuid4()).upper()
            }
        )
