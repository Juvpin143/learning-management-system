from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

# Create your models here.
class TeacherCourse(models.Model):
    teacher = models.ForeignKey(User, on_delete=models.CASCADE, related_name="assigned_courses")
    title = models.CharField(max_length=200)
    description = models.TextField()
    category = models.CharField(max_length=100)
    level = models.CharField(max_length=50)
    duration = models.CharField(max_length=50)
    thumbnail = models.ImageField(upload_to="course_thumbnails/", blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

