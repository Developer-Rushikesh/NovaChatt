"""
Django settings for chatappp project.
Optimized for Production Deployment on Railway Cloud.
Integrated with django-allauth for Google OAuth 2.0 Authentication.
"""

from pathlib import Path
import os
import dotenv
import dj_database_url

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Load environment variables from .env file located at BASE_DIR / '.env'
dotenv.load_dotenv(BASE_DIR / ".env")

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv('SECRET_KEY', 'django-insecure-31mpygl!yig0ap0!9m3me5m(8h1xo9*l0!@ei)2i%u5&-j3u2d')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.getenv('DEBUG', 'False').lower() in ('true', '1', 't')

# ALLOWED_HOSTS defines which host/domain names this Django site can serve
ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', '*').split(',')

# CSRF Trusted Origins for Railway HTTPS domain & local development
CSRF_TRUSTED_ORIGINS = [
    origin.strip() for origin in os.getenv(
        'CSRF_TRUSTED_ORIGINS',
        'http://127.0.0.1:8000,http://localhost:8000,https://*.railway.app'
    ).split(',') if origin.strip()
]


# Application definition - List of installed Django apps and third-party packages
INSTALLED_APPS = [
    # ASGI server for WebSockets and async handling
    'daphne',
    
    # Built-in Django core applications
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # Required by django-allauth to identify the domain/site instance (SITE_ID = 1)
    'django.contrib.sites',
    
    # Project custom local applications inside apps/ directory
    "apps.accounts",
    "apps.chat",
    
    # Django Channels for real-time WebSocket communication
    "channels",
    
    # django-allauth apps for authentication & social account support
    'allauth',                             # Core django-allauth framework
    'allauth.account',                     # Handles standard local accounts (email/password)
    'allauth.socialaccount',               # Handles OAuth social login framework
    'allauth.socialaccount.providers.google', # Specific provider for Google OAuth 2.0
]

# SITE_ID represents the ID of the current site record in the django_site database table.
SITE_ID = 1

# List of HTTP request/response middleware executed on every request
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware', # Production Static Files Serving via WhiteNoise
    'django.contrib.sessions.middleware.SessionMiddleware',  # Manages user session state across requests
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',             # Protects against Cross-Site Request Forgery attacks
    'django.contrib.auth.middleware.AuthenticationMiddleware', # Associates user object with HTTP request
    'django.contrib.messages.middleware.MessageMiddleware',    # Handles flash messages
    'allauth.account.middleware.AccountMiddleware',           # AllAuth middleware for OAuth sessions
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# Root URL configuration module for the project
ROOT_URLCONF = 'chatappp.urls'

# Authentication Backends
AUTHENTICATION_BACKENDS = (
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
)

# Template Engine Configuration
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'], # Custom global templates directory
        'APP_DIRS': True,                 # Search for templates inside app directories
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

# WSGI & ASGI application entry points
WSGI_APPLICATION = 'chatappp.wsgi.application'
ASGI_APPLICATION = 'chatappp.asgi.application'


# Database Configuration - Uses Railway PostgreSQL when DATABASE_URL is present, falls back to SQLite for local dev
DATABASE_URL = os.environ.get("DATABASE_URL")
if DATABASE_URL:
    DATABASES = {
        "default": dj_database_url.config(
            default=DATABASE_URL,
            conn_max_age=600,
            ssl_require=False,
        )
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }


# Django Channels Redis Channel Layer for Production Real-Time Messaging
REDIS_URL = os.getenv('REDIS_URL', '')
if REDIS_URL:
    CHANNEL_LAYERS = {
        "default": {
            "BACKEND": "channels_redis.core.RedisChannelLayer",
            "CONFIG": {
                "hosts": [REDIS_URL],
            },
        },
    }
else:
    CHANNEL_LAYERS = {
        "default": {
            "BACKEND": "channels.layers.InMemoryChannelLayer",
        },
    }


# Password validation rules
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]


# Internationalization & Localization Settings
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Asia/Kolkata'
USE_I18N = True
USE_TZ = True


# Static files (CSS, JavaScript, Images) configuration
STATIC_URL = "/static/"
STATICFILES_DIRS = [
    BASE_DIR / "static",
]
STATIC_ROOT = BASE_DIR / "staticfiles"

# Storage Configuration using WhiteNoise for production static file compression
STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage" if not DEBUG else "django.contrib.staticfiles.storage.StaticFilesStorage",
    },
}


# Media files (User uploaded profile pictures, QR codes, etc.)
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"


# Production Security Headers & SSL Redirects
if not DEBUG:
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    SECURE_SSL_REDIRECT = os.getenv('SECURE_SSL_REDIRECT', 'True').lower() in ('true', '1', 't')
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    SECURE_HSTS_SECONDS = 31536000 # 1 year HSTS
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True


# Email configuration (console backend in dev mode)
EMAIL_BACKEND = os.getenv('EMAIL_BACKEND', 'django.core.mail.backends.console.EmailBackend')


# Login and Logout Redirect URLs
LOGIN_URL = "/login/"
LOGIN_REDIRECT_URL = "/"
LOGOUT_REDIRECT_URL = "/login/"


# Google OAuth credentials loaded securely from environment variables
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "")

# django-allauth Social Account Provider Configuration for Google OAuth 2.0
SOCIALACCOUNT_PROVIDERS = {
    'google': {
        'SCOPE': [
            'profile',
            'email',
            'openid',
        ],
        'AUTH_PARAMS': {
            'access_type': 'online',
            'prompt': 'select_account',
        },
        'METHOD': 'oauth2',
        'VERIFIED_EMAIL': True,
        'APP': {
            'client_id': GOOGLE_CLIENT_ID,
            'secret': GOOGLE_CLIENT_SECRET,
            'key': ''
        }
    }
}

# AllAuth Custom Social Account Adapter
SOCIALACCOUNT_ADAPTER = 'apps.accounts.adapters.CustomSocialAccountAdapter'
SOCIALACCOUNT_AUTO_SIGNUP = True
ACCOUNT_LOGIN_METHODS = {'username', 'email'}
ACCOUNT_SIGNUP_FIELDS = ['email*']
SOCIALACCOUNT_QUERY_EMAIL = True
ACCOUNT_LOGOUT_ON_GET = True