"""
Custom django-allauth adapters for apps.accounts.

This module provides customized behavior for social account authentication:
1. Automatic Account Linking: Prevents duplicate user accounts by linking Google logins
   to existing local user accounts with matching email addresses.
2. Avatar & Profile Sync: Downloads the user's Google profile picture (avatar) and populates
   the local UserProfile model upon successful social signup/login.
"""

# Import default SocialAccountAdapter from django-allauth
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
# Import User model from Django core authentication system
from django.contrib.auth.models import User
# Import UserProfile and UserStatus models from apps.accounts
from .models import UserProfile, UserStatus
# Import urllib for downloading avatar images over HTTPS
import urllib.request
# Import ContentFile for saving binary image data into Django FileField
from django.core.files.base import ContentFile


class CustomSocialAccountAdapter(DefaultSocialAccountAdapter):
    """
    Custom Social Account Adapter extending DefaultSocialAccountAdapter.
    """

    def pre_social_login(self, request, sociallogin):
        """
        Invoked after a user successfully authenticates with Google,
        but BEFORE the user is logged into Django or saved to the database.
        
        This method checks if a Django user already exists with the same email address as the Google account.
        If found, it links the Google social account to the existing local User account,
        preventing duplicate account creation and avoiding "email already registered" conflicts.
        """
        # If the social account is already connected to an existing user object, proceed normally
        if sociallogin.is_existing:
            return

        # Extract email address provided in Google extra_data payload
        email = sociallogin.account.extra_data.get('email')
        if not email:
            return

        # Search database for existing user with matching email address
        try:
            existing_user = User.objects.get(email__iexact=email)
            # Connect the incoming Google social account to the existing local user account
            sociallogin.connect(request, existing_user)
        except User.DoesNotExist:
            # If no existing user has this email, allauth will automatically proceed to create a new User account
            pass

    def save_user(self, request, sociallogin, form=None):
        """
        Invoked when a NEW user account is created via Google social login.
        
        This method saves the new User, creates associated UserProfile and UserStatus records,
        and downloads the user's Google profile avatar.
        """
        # Call superclass method to create and save the User instance in database
        user = super().save_user(request, sociallogin, form=form)

        # Ensure user profile and user status objects exist
        profile_obj, _ = UserProfile.objects.get_or_create(user=user)
        status_obj, _ = UserStatus.objects.get_or_create(user=user)

        # Extract Google profile details from extra_data payload
        extra_data = sociallogin.account.extra_data
        
        # Populate first_name and last_name on user model if provided by Google
        name = extra_data.get('name', '')
        if name and not user.first_name:
            user.first_name = name
            user.save()

        # Extract profile picture URL from Google extra_data
        picture_url = extra_data.get('picture', '')
        
        # If user does not yet have a profile picture, download avatar from Google
        if picture_url and not profile_obj.profile_picture:
            try:
                # Create HTTP request with standard User-Agent header to prevent 403 Forbidden errors
                req = urllib.request.Request(picture_url, headers={'User-Agent': 'Mozilla/5.0'})
                # Fetch image bytes from Google CDN
                with urllib.request.urlopen(req) as response:
                    img_bytes = response.read()
                    # Define filename for avatar image
                    filename = f"google_avatar_{user.id}.jpg"
                    # Save image binary content into UserProfile.profile_picture field
                    profile_obj.profile_picture.save(filename, ContentFile(img_bytes), save=True)
            except Exception as exc:
                # Log any avatar fetch exception gracefully without interrupting sign-in flow
                print(f"Warning: Failed to fetch Google profile picture for user {user.id}: {exc}")

        return user
