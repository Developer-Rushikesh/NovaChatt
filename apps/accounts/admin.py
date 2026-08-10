from django.contrib import admin
from .models import FriendRequest, UserStatus

admin.site.register(FriendRequest)
admin.site.register(UserStatus)