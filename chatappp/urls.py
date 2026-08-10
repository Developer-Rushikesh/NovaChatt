from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

# Master URL patterns array for NovaChat project
urlpatterns = [
    # Route for Django Administration interface
    path("admin/", admin.site.urls),
    
    # Route for django-allauth authentication system (Google OAuth callback, sign in, logout)
    path("accounts/", include("allauth.urls")),
    
    # Primary application routes from apps.accounts (home, login, register, profile, settings, search, etc.)
    path("", include("apps.accounts.urls")),
    
    # Chat application routes from apps.chat (messages, call logs, QR codes)
    path("chat/", include("apps.chat.urls")),
]

# Serve media files (avatars, QR codes)
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)