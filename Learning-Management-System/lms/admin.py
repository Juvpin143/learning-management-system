from django.contrib import admin
from .models import Course, Enrolment, Review

admin.site.register(Enrolment)
admin.site.register(Review)
@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('title', 'level', 'language', 'is_published')
    fields = (
        'title', 'subtitle', 'description',
        'category', 'level',
        'thumbnail',
        'promo_video_url',   # <-- IMPORTANT!
        'duration', 'language',
        'created_by', 'is_published', 'slug'
    )


