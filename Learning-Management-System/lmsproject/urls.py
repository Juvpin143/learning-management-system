from django.contrib import admin
from django.urls import path, include
from django.shortcuts import redirect
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('', lambda request: redirect('login')),

    path('admin/', admin.site.urls),
    path('accounts/', include('accounts.urls')),
    path('lms/', include('lms.urls')),

    path('', include('teacher.urls')),
    path('adminpanel/', include('adminpanel.urls')),
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
