from django.shortcuts import render, redirect, get_object_or_404
from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.db.models import Q
from .models import FriendRequest, UserStatus, UserProfile
from apps.chat.models import Message

def home(request):
    if not request.user.is_authenticated:
        return redirect("login")

    user_profile, _ = UserProfile.objects.get_or_create(user=request.user)

    pending_requests = FriendRequest.objects.filter(
        receiver=request.user,
        accepted=False
    ).count()

    friends_count = FriendRequest.objects.filter(accepted=True).filter(
        Q(sender=request.user) | Q(receiver=request.user)
    ).count()

    unread_count = Message.objects.filter(
        receiver=request.user,
        is_read=False
    ).count()

    # Get top 5 recent chats
    requests = FriendRequest.objects.filter(accepted=True).filter(
        Q(sender=request.user) | Q(receiver=request.user)
    )
    recent_users = []
    added_ids = set()
    for req in requests:
        friend = req.receiver if req.sender == request.user else req.sender
        if friend.id in added_ids:
            continue
        added_ids.add(friend.id)
        last_msg = Message.objects.filter(
            Q(sender=request.user, receiver=friend) | Q(sender=friend, receiver=request.user)
        ).order_by("-created_at").first()
        status = UserStatus.objects.filter(user=friend).first()
        profile = UserProfile.objects.filter(user=friend).first()
        recent_users.append({
            "user": friend,
            "profile": profile,
            "status": status,
            "last_message": last_msg
        })

    return render(request, "accounts/home.html", {
        "profile": user_profile,
        "pending_requests": pending_requests,
        "friends_count": friends_count,
        "unread_count": unread_count,
        "recent_users": recent_users[:5]
    })

def user_register(request):
    if request.user.is_authenticated:
        return redirect("home")
    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        email = request.POST.get("email", "").strip()
        password = request.POST.get("password", "")

        if not username or not password:
            return render(request, "accounts/register.html", {"error": "Username and password are required"})

        if User.objects.filter(username=username).exists():
            return render(request, "accounts/register.html", {"error": "Username already taken"})

        if email and User.objects.filter(email=email).exists():
            return render(request, "accounts/register.html", {"error": "Email already registered"})

        user = User.objects.create_user(username=username, email=email, password=password)
        login(request, user)
        status, _ = UserStatus.objects.get_or_create(user=user)
        status.online = True
        status.save()
        return redirect("home")

    return render(request, "accounts/register.html")


def user_login(request):
    if request.user.is_authenticated:
        return redirect("home")

    if request.method == "POST":
        login_input = request.POST.get("username", "").strip()
        password = request.POST.get("password", "")

        target_username = login_input
        if "@" in login_input:
            user_by_email = User.objects.filter(email=login_input).first()
            if user_by_email:
                target_username = user_by_email.username

        user = authenticate(request, username=target_username, password=password)

        if user is not None:
            login(request, user)
            status, _ = UserStatus.objects.get_or_create(user=user)
            status.online = True
            status.save()
            return redirect("home")

        return render(request, "accounts/login.html", {"error": "Invalid credentials. Please try again."})

    return render(request, "accounts/login.html")
@login_required
def user_logout(request):
    try:
        status, _ = UserStatus.objects.get_or_create(user=request.user)
        status.online = False
        status.save()
    except Exception:
        pass
    logout(request)
    return redirect("login")


@login_required
def profile(request):
    user_profile, _ = UserProfile.objects.get_or_create(user=request.user)
    error = None
    success = None

    if request.method == "POST":
        new_username = request.POST.get("username", "").strip()
        new_email = request.POST.get("email", "").strip()
        bio = request.POST.get("bio", "").strip()
        phone = request.POST.get("phone", "").strip()
        face_unlock = request.POST.get("face_unlock_enabled") == "on"

        # Update username if changed
        if new_username and new_username != request.user.username:
            if User.objects.filter(username=new_username).exclude(id=request.user.id).exists():
                error = "Username is already taken by another user."
            else:
                request.user.username = new_username

        # Update email if changed
        if not error and new_email and new_email != request.user.email:
            if User.objects.filter(email=new_email).exclude(id=request.user.id).exists():
                error = "Email address is already registered to another user."
            else:
                request.user.email = new_email

        if not error:
            request.user.save()
            user_profile.bio = bio
            user_profile.phone = phone
            user_profile.face_unlock_enabled = face_unlock

            if "profile_picture" in request.FILES:
                user_profile.profile_picture = request.FILES["profile_picture"]

            user_profile.save()
            success = "Profile updated successfully!"

    return render(request, "accounts/profile.html", {
        "profile": user_profile,
        "error": error,
        "success": success
    })


@login_required
def settings_view(request):
    user_profile, _ = UserProfile.objects.get_or_create(user=request.user)
    return render(request, "accounts/settings.html", {"profile": user_profile})


@login_required
def search_users(request):
    query = request.GET.get("q", "").strip()
    users = User.objects.exclude(id=request.user.id)
    if query:
        users = users.filter(Q(username__icontains=query) | Q(email__icontains=query))

    sent_requests = set(FriendRequest.objects.filter(sender=request.user).values_list("receiver_id", flat=True))
    accepted_friends = set(
        FriendRequest.objects.filter(accepted=True)
        .filter(Q(sender=request.user) | Q(receiver=request.user))
        .values_list("sender_id", "receiver_id")
    )
    friend_ids = set()
    for s, r in accepted_friends:
        friend_ids.add(s if s != request.user.id else r)

    users_data = []
    for u in users:
        users_data.append({
            "user": u,
            "is_friend": u.id in friend_ids,
            "request_sent": u.id in sent_requests
        })

    return render(request, "accounts/search.html", {"users_data": users_data, "query": query})


@login_required
def send_friend_request(request, user_id):
    receiver = get_object_or_404(User, id=user_id)
    if receiver != request.user:
        FriendRequest.objects.get_or_create(sender=request.user, receiver=receiver)
    return redirect("search")


@login_required
def friend_requests(request):
    requests = FriendRequest.objects.filter(receiver=request.user, accepted=False)
    return render(request, "accounts/friend_requests.html", {"requests": requests})


@login_required
def accept_request(request, request_id):
    freq = get_object_or_404(FriendRequest, id=request_id, receiver=request.user)
    freq.accepted = True
    freq.save()
    return redirect("friend_requests")


@login_required
def reject_request(request, request_id):
    freq = get_object_or_404(FriendRequest, id=request_id, receiver=request.user)
    freq.delete()
    return redirect("friend_requests")


@login_required
def friends(request):
    sent = FriendRequest.objects.filter(sender=request.user, accepted=True).values_list("receiver", flat=True)
    received = FriendRequest.objects.filter(receiver=request.user, accepted=True).values_list("sender", flat=True)
    friend_ids = set(sent).union(set(received))
    friend_users = User.objects.filter(id__in=friend_ids)
    return render(request, "accounts/friends.html", {"friends": friend_users})


@login_required
def scan_qr(request):
    if request.method == "POST":
        payload = ""
        if request.content_type == "application/json":
            try:
                body = json.loads(request.body)
                payload = body.get("qr_payload", "").strip()
            except Exception:
                pass
        else:
            payload = request.POST.get("qr_payload", "").strip()

        if not payload:
            return JsonResponse({"success": False, "message": "No QR payload provided."})

        # Parse QR code format "chatapp:user:<user_id>" or raw user_id/username
        target_user = None
        if payload.startswith("chatapp:user:"):
            try:
                user_id = int(payload.split(":")[-1])
                target_user = User.objects.filter(id=user_id).first()
            except ValueError:
                pass
        elif payload.isdigit():
            target_user = User.objects.filter(id=int(payload)).first()
        else:
            target_user = User.objects.filter(username=payload).first()

        if not target_user:
            return JsonResponse({"success": False, "message": "User not found from QR scan."})

        if target_user == request.user:
            return JsonResponse({"success": False, "message": "This is your own QR code!"})

        # Check existing friendship or request
        existing_req = FriendRequest.objects.filter(
            Q(sender=request.user, receiver=target_user) | Q(sender=target_user, receiver=request.user)
        ).first()

        if existing_req:
            if existing_req.accepted:
                return JsonResponse({
                    "success": True,
                    "status": "already_friends",
                    "user_id": target_user.id,
                    "username": target_user.username,
                    "message": f"You are already friends with {target_user.username}!"
                })
            elif existing_req.sender == request.user:
                return JsonResponse({
                    "success": True,
                    "status": "request_pending",
                    "user_id": target_user.id,
                    "username": target_user.username,
                    "message": f"Friend request sent to {target_user.username} is pending approval."
                })
            else:
                existing_req.accepted = True
                existing_req.save()
                return JsonResponse({
                    "success": True,
                    "status": "accepted",
                    "user_id": target_user.id,
                    "username": target_user.username,
                    "message": f"Accepted friend request from {target_user.username}! You can now chat."
                })

        # Send new request (accepted=False) so target user receives invitation
        FriendRequest.objects.create(sender=request.user, receiver=target_user, accepted=False)
        return JsonResponse({
            "success": True,
            "status": "sent",
            "user_id": target_user.id,
            "username": target_user.username,
            "message": f"Sent friend request to {target_user.username}! Once accepted, you can start chatting."
        })

    return JsonResponse({"success": False, "message": "Invalid request method."})