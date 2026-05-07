from django.db.models.signals import pre_delete
from django.db.models.signals import post_save
from django.contrib.auth import get_user_model
from django.dispatch import receiver
from django.conf import settings
from .models import Profile
from .models import Course

User = get_user_model()

@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.get_or_create(user=instance)

@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def save_profile(sender, instance, **kwargs):
    if hasattr(instance, "profile"):
        instance.profile.save()

@receiver(pre_delete, sender=User)
def reassign_courses_before_user_delete(sender, instance, **kwargs):
    try:
        profile = instance.profile
    except Profile.DoesNotExist:
        return

    if profile.is_instructor:
        admin = User.objects.filter(is_superuser=True, is_active=True).first()
        if admin:
            Course.objects.filter(created_by=instance).update(created_by=admin)
