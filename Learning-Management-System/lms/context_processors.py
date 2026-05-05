from .models import Notification

def notification_context(request):
    if request.user.is_authenticated:
        qs = Notification.objects.filter(
            recipient=request.user
        ).order_by("-created_at")

        unread_notification_count = qs.filter(
            is_read=False
        ).count()

        notifications = qs[:5]  # slice LAST

    else:
        notifications = []
        unread_notification_count = 0

    return {
        "notifications": notifications,
        "unread_notifications_count": unread_notification_count,
    }
