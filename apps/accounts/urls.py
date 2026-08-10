# Import path function from django.urls for URL routing
from django.urls import path
# Import views module from current package (apps.accounts)
from . import views

# URL patterns for accounts application
urlpatterns = [
    # Dashboard / Home page (protected view)
    path("", views.home, name="home"),
    
    # Standard username/password registration view
    path("register/", views.user_register, name="register"),
    
    # Standard username/password & Google login landing page view
    path("login/", views.user_login, name="login"),
    
    # Logout view
    path("logout/", views.user_logout, name="logout"),
    
    # User Profile view
    path("profile/", views.profile, name="profile"),
    
    # Settings view
    path("settings/", views.settings_view, name="settings"),
    
    # Search users view
    path("search/", views.search_users, name="search"),
    
    # Friend Request Action routes
    path("send-request/<int:user_id>/", views.send_friend_request, name="send_request"),
    path("friend-requests/", views.friend_requests, name="friend_requests"),
    path("accept-request/<int:request_id>/", views.accept_request, name="accept_request"),
    path("reject-request/<int:request_id>/", views.reject_request, name="reject_request"),
    
    # Friends list view
    path("friends/", views.friends, name="friends"),
    
    # Scan QR Code view
    path("scan-qr/", views.scan_qr, name="scan_qr"),
    
    # Chats alias route pointing to home
    path("chats/", views.home),
]