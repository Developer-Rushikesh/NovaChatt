import json
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models import Q
from django.http import JsonResponse
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from .models import Message, CallLog
from apps.accounts.models import FriendRequest, UserStatus, UserProfile

@login_required
def chats(request):
    # Find accepted friends ONLY
    requests = FriendRequest.objects.filter(accepted=True).filter(
        Q(sender=request.user) | Q(receiver=request.user)
    )

    users_list = []
    added_ids = set()

    for req in requests:
        friend = req.receiver if req.sender == request.user else req.sender
        if friend.id in added_ids:
            continue
        added_ids.add(friend.id)

        # Get latest message
        last_msg = Message.objects.filter(
            Q(sender=request.user, receiver=friend) | Q(sender=friend, receiver=request.user)
        ).order_by("-created_at").first()

        unread = Message.objects.filter(
            sender=friend,
            receiver=request.user,
            is_read=False
        ).count()

        status = UserStatus.objects.filter(user=friend).first()
        profile = UserProfile.objects.filter(user=friend).first()

        users_list.append({
            "user": friend,
            "profile": profile,
            "status": status,
            "last_message": last_msg,
            "unread": unread
        })

    # Sort chats by latest message time
    users_list.sort(
        key=lambda x: x["last_message"].created_at if x["last_message"] else x["user"].date_joined,
        reverse=True
    )

    return render(request, "chat/chats.html", {"users_list": users_list})


@login_required
def chat(request, user_id):
    friend = get_object_or_404(User, id=user_id)
    if friend == request.user:
        return redirect("chats")

    # Strict check: Friendship must be accepted!
    pending_req = FriendRequest.objects.filter(
        Q(sender=request.user, receiver=friend) | Q(sender=friend, receiver=request.user)
    ).first()

    if not pending_req or not pending_req.accepted:
        status_msg = f"You can only chat with {friend.username} after your friend request is accepted!"
        if pending_req:
            if pending_req.sender == request.user:
                status_msg = f"Friend request sent to {friend.username} is pending approval."
            else:
                status_msg = f"{friend.username} sent you a friend request. Accept it below to start chatting!"

        return render(request, "chat/no_access.html", {
            "friend": friend,
            "status_msg": status_msg,
            "pending_req": pending_req
        })

    friend_status, _ = UserStatus.objects.get_or_create(user=friend)
    friend_profile, _ = UserProfile.objects.get_or_create(user=friend)

    # Mark all incoming messages from this friend as read
    Message.objects.filter(
        sender=friend,
        receiver=request.user,
        is_read=False
    ).update(is_read=True)

    if request.method == "POST":
        text = request.POST.get("message", "").strip()
        if text:
            Message.objects.create(
                sender=request.user,
                receiver=friend,
                message=text
            )
        return redirect("chat", user_id=friend.id)

    messages = Message.objects.filter(
        Q(sender=request.user, receiver=friend) | Q(sender=friend, receiver=request.user)
    ).select_related("sender", "receiver").order_by("created_at")

    # Room name for WebSocket (sorted IDs so both users join same room)
    room_name = f"{min(request.user.id, friend.id)}_{max(request.user.id, friend.id)}"

    return render(request, "chat/chat.html", {
        "friend": friend,
        "friend_status": friend_status,
        "friend_profile": friend_profile,
        "messages": messages,
        "room_name": room_name,
    })


@login_required
def delete_message(request, message_id):
    msg = get_object_or_404(Message, id=message_id, sender=request.user)
    friend_id = msg.receiver.id
    msg.delete()
    return redirect("chat", user_id=friend_id)


@login_required
def edit_message(request, message_id):
    msg = get_object_or_404(Message, id=message_id, sender=request.user)
    if request.method == "POST":
        new_text = request.POST.get("message", "").strip()
        if new_text:
            msg.message = new_text
            msg.is_edited = True
            msg.save()
            return JsonResponse({"success": True, "message": new_text})
    return JsonResponse({"success": False, "error": "Invalid request"})


@login_required
def get_messages(request, user_id):
    friend = get_object_or_404(User, id=user_id)
    
    # Verify friendship
    is_friend = FriendRequest.objects.filter(
        accepted=True
    ).filter(
        Q(sender=request.user, receiver=friend) | Q(sender=friend, receiver=request.user)
    ).exists()

    if not is_friend:
        return JsonResponse({"error": "Chat access denied. Friendship not accepted."}, status=403)

    # Mark messages as read
    Message.objects.filter(sender=friend, receiver=request.user, is_read=False).update(is_read=True)

    messages = Message.objects.filter(
        Q(sender=request.user, receiver=friend) | Q(sender=friend, receiver=request.user)
    ).order_by("created_at")

    data = []
    for msg in messages:
        data.append({
            "id": msg.id,
            "sender_id": msg.sender.id,
            "sender_username": msg.sender.username,
            "message": msg.message,
            "mine": msg.sender == request.user,
            "time": msg.created_at.strftime("%I:%M %p"),
            "is_read": msg.is_read,
            "is_edited": msg.is_edited,
        })

    return JsonResponse(data, safe=False)


@login_required
def calls(request):
    logs = CallLog.objects.filter(
        Q(caller=request.user) | Q(receiver=request.user)
    ).select_related("caller", "receiver").order_by("-created_at")

    logs_data = []
    for log in logs:
        is_outgoing = (log.caller == request.user)
        other_user = log.receiver if is_outgoing else log.caller
        profile = UserProfile.objects.filter(user=other_user).first()
        status = UserStatus.objects.filter(user=other_user).first()

        logs_data.append({
            "log": log,
            "is_outgoing": is_outgoing,
            "other_user": other_user,
            "profile": profile,
            "status": status,
        })

    return render(request, "chat/calls.html", {"logs_data": logs_data})


@login_required
def send_call_signal(request):
    if request.method == "POST":
        try:
            body = json.loads(request.body)
            target_id = body.get("target_id")
            sig_type = body.get("type")
            if not target_id or not sig_type:
                return JsonResponse({"success": False, "error": "Missing parameters"}, status=400)

            avatar_url = ""
            profile = UserProfile.objects.filter(user=request.user).first()
            if profile and profile.profile_picture:
                try:
                    avatar_url = profile.profile_picture.url
                except Exception:
                    avatar_url = ""

            body["sender_id"] = request.user.id
            body["sender_username"] = request.user.username
            body["sender_avatar"] = avatar_url

            # Record call history in CallLog
            call_log_id = body.get("call_log_id")
            if sig_type == "call_offer":
                log_obj = CallLog.objects.create(
                    caller=request.user,
                    receiver_id=target_id,
                    call_type=body.get("call_type", "Voice"),
                    status="Missed"
                )
                body["call_log_id"] = log_obj.id

            elif sig_type == "call_answer" and call_log_id:
                CallLog.objects.filter(id=call_log_id).update(status="Completed")

            elif sig_type == "call_declined" and call_log_id:
                CallLog.objects.filter(id=call_log_id).update(status="Declined")

            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)(
                f"user_{target_id}",
                {
                    "type": "webrtc_signal",
                    "payload": body
                }
            )
            return JsonResponse({"success": True, "call_log_id": body.get("call_log_id")})
        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)}, status=500)
    return JsonResponse({"success": False, "error": "POST required"}, status=405)