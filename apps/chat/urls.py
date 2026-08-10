from django.urls import path
from . import views

urlpatterns = [
    path("", views.chats, name="chats"),
    path("<int:user_id>/", views.chat, name="chat"),
    path("messages/<int:user_id>/", views.get_messages, name="get_messages"),
    path("delete-message/<int:message_id>/", views.delete_message, name="delete_message"),
    path("edit-message/<int:message_id>/", views.edit_message, name="edit_message"),
    path("calls/", views.calls, name="calls"),
    path("api/send_call_signal/", views.send_call_signal, name="send_call_signal"),
]