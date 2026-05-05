from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from lms.models import Profile

User = get_user_model()

@receiver(post_save, sender=User)
def create_or_update_profile(sender, instance, created, **kwargs):
    profile, _ = Profile.objects.get_or_create(user=instance)

    # Admin / superuser safety
    if instance.is_superuser or instance.is_staff:
        profile.is_instructor = False
    else:
        profile.is_instructor = getattr(instance, "role", None) == "teacher"

    profile.save()
