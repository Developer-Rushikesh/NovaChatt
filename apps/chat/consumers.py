import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import User
from django.utils.timezone import localtime
from django.db.models import Q
from .models import Message, CallLog

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope["user"]
        if not self.user.is_authenticated:
            await self.close()
            return

        self.room_name = self.scope["url_route"]["kwargs"]["room_name"]
        self.room_group_name = f"chat_{self.room_name}"

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
            msg_type = data.get("type", "chat_message")

            if msg_type == "typing":
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        "type": "typing_indicator",
                        "sender": self.user.username,
                        "is_typing": data.get("is_typing", True)
                    }
                )
                return

            if msg_type == "read_receipt":
                sender_id = data.get("sender_id")
                if sender_id:
                    await self.mark_messages_read(self.user.id, sender_id)
                    await self.channel_layer.group_send(
                        self.room_group_name,
                        {
                            "type": "messages_read_event",
                            "reader_id": self.user.id,
                            "reader": self.user.username
                        }
                    )
                return

            message_text = data.get("message", "").strip()
            receiver_id = data.get("receiver_id")

            if not message_text or not receiver_id:
                return

            # Strict security check: Friendship must be accepted!
            is_accepted = await self.check_accepted_friendship(self.user.id, receiver_id)
            if not is_accepted:
                return

            # Save message to database
            msg_obj = await self.save_message(self.user.id, receiver_id, message_text)
            ist_time = localtime(msg_obj.created_at).strftime("%I:%M %p")

            # 1. Broadcast to room group
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "chat_message",
                    "message_id": msg_obj.id,
                    "message": msg_obj.message,
                    "sender": self.user.username,
                    "sender_id": self.user.id,
                    "time": ist_time,
                    "date_str": localtime(msg_obj.created_at).strftime("%Y-%m-%d"),
                }
            )

            # 2. Broadcast global notification alert to receiver's user group
            await self.channel_layer.group_send(
                f"user_{receiver_id}",
                {
                    "type": "notification_alert",
                    "payload": {
                        "type": "new_message_alert",
                        "sender_id": self.user.id,
                        "sender_username": self.user.username,
                        "message": message_text,
                        "time": ist_time
                    }
                }
            )
        except Exception as e:
            print("ChatConsumer receive error:", e)

    async def chat_message(self, event):
        await self.send(text_data=json.dumps({
            "type": "chat_message",
            "message_id": event["message_id"],
            "message": event["message"],
            "sender": event["sender"],
            "sender_id": event["sender_id"],
            "time": event["time"],
            "date_str": event.get("date_str", ""),
        }))

    async def typing_indicator(self, event):
        if event["sender"] != self.user.username:
            await self.send(text_data=json.dumps({
                "type": "typing",
                "sender": event["sender"],
                "is_typing": event["is_typing"]
            }))

    async def messages_read_event(self, event):
        if event["reader_id"] != self.user.id:
            await self.send(text_data=json.dumps({
                "type": "messages_read",
                "reader_id": event["reader_id"],
                "reader": event["reader"]
            }))

    @database_sync_to_async
    def check_accepted_friendship(self, user_id_1, user_id_2):
        from apps.accounts.models import FriendRequest
        return FriendRequest.objects.filter(
            accepted=True
        ).filter(
            Q(sender_id=user_id_1, receiver_id=user_id_2) | Q(sender_id=user_id_2, receiver_id=user_id_1)
        ).exists()

    @database_sync_to_async
    def save_message(self, sender_id, receiver_id, text):
        receiver = User.objects.get(id=receiver_id)
        sender = User.objects.get(id=sender_id)
        return Message.objects.create(sender=sender, receiver=receiver, message=text)

    @database_sync_to_async
    def mark_messages_read(self, user_id, sender_id):
        Message.objects.filter(sender_id=sender_id, receiver_id=user_id, is_read=False).update(is_read=True)


class NotificationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope["user"]
        if not self.user.is_authenticated:
            await self.close()
            return

        self.user_group = f"user_{self.user.id}"

        await self.channel_layer.group_add(
            self.user_group,
            self.channel_name
        )
        await self.accept()

    async def disconnect(self, close_code):
        if hasattr(self, "user_group"):
            await self.channel_layer.group_discard(
                self.user_group,
                self.channel_name
            )

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
            msg_type = data.get("type")
            target_id = data.get("target_id")

            if not target_id:
                return

            target_group = f"user_{target_id}"

            if msg_type in ["call_offer", "call_answer", "ice_candidate", "call_declined", "call_ended"]:
                data["sender_id"] = self.user.id
                data["sender_username"] = self.user.username
                avatar_url = ""
                if hasattr(self.user, "profile") and self.user.profile.profile_picture:
                    try:
                        avatar_url = self.user.profile.profile_picture.url
                    except Exception:
                        avatar_url = ""
                data["sender_avatar"] = avatar_url

                # Process CallLog entry
                new_call_id = await self.process_call_log(data)
                if new_call_id:
                    data["call_log_id"] = new_call_id

                await self.channel_layer.group_send(
                    target_group,
                    {
                        "type": "webrtc_signal",
                        "payload": data
                    }
                )
        except Exception as e:
            print("NotificationConsumer receive error:", e)

    @database_sync_to_async
    def process_call_log(self, data):
        msg_type = data.get("type")
        target_id = data.get("target_id")
        call_log_id = data.get("call_log_id")

        if msg_type == "call_offer" and target_id and not call_log_id:
            log_obj = CallLog.objects.create(
                caller_id=self.user.id,
                receiver_id=target_id,
                call_type=data.get("call_type", "Voice"),
                status="Missed"
            )
            return log_obj.id

        elif msg_type == "call_answer" and call_log_id:
            CallLog.objects.filter(id=call_log_id).update(status="Completed")

        elif msg_type == "call_declined" and call_log_id:
            CallLog.objects.filter(id=call_log_id).update(status="Declined")

        return call_log_id

    async def webrtc_signal(self, event):
        await self.send(text_data=json.dumps(event["payload"]))

    async def notification_alert(self, event):
        await self.send(text_data=json.dumps(event["payload"]))