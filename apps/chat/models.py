from django.db import models
from django.contrib.auth.models import User

class Message(models.Model):
    sender = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="sent_messages"
    )
    receiver = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="received_messages"
    )
    message = models.TextField()
    created_at = models.DateTimeField(
        auto_now_add=True
    )
    seen = models.BooleanField(
        default=False
    )
    is_read = models.BooleanField(
        default=False
    )
    is_edited = models.BooleanField(
        default=False
    )

    def __str__(self):
        return f"{self.sender} -> {self.receiver}"


class CallLog(models.Model):
    CALL_TYPES = (
        ("Voice", "Voice Call"),
        ("Video", "Video Call"),
    )
    STATUS_CHOICES = (
        ("Completed", "Completed"),
        ("Missed", "Missed"),
        ("Declined", "Declined"),
    )

    caller = models.ForeignKey(User, on_delete=models.CASCADE, related_name="outgoing_calls")
    receiver = models.ForeignKey(User, on_delete=models.CASCADE, related_name="incoming_calls")
    call_type = models.CharField(max_length=10, choices=CALL_TYPES, default="Voice")
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default="Missed")
    duration = models.IntegerField(default=0) # duration in seconds
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.call_type} Call ({self.status}): {self.caller} -> {self.receiver}"