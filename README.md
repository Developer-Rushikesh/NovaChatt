# 💬 NovaChat – Modern Real-Time Chat & Collaboration Web Application

NovaChat is a full-featured, production-ready real-time chat application built with **Django 5**, **Django Channels (WebSockets)**, **django-allauth (Google OAuth 2.0)**, and **Tailwind CSS**. It features a complete Light/Dark theme system, voice & video call capabilities, QR code profile sharing, contact search, and instant message read receipts.

---

## ✨ Features

- 🔐 **Dual Authentication System**: Standard username/email login + Seamless **Google OAuth 2.0** Sign-In.
- 🌓 **Application-Wide Light & Dark Mode**: Custom animated Sun 🌞 / Moon 🌙 toggle switcher with `localStorage` persistence and multi-tab state sync.
- ⚡ **Real-Time WebSockets Messaging**: Powered by Django Channels & Daphne with typing indicators and live read receipts (`✓✓`).
- 📞 **Voice & Video Calling Logs**: Initiate and log voice and video calls between contacts.
- 📷 **QR Code Scanner & Profile Cards**: Generate personal QR codes and scan friends' QR codes to add contacts instantly.
- 🎨 **Modern Design Tokens & Responsive UI**: Built with Tailwind CSS, custom design tokens, micro-animations, and full mobile drawer navigation.
- 🚀 **Production Ready for Railway Cloud**: Configured with WhiteNoise static asset compression, PostgreSQL support via `dj-database-url`, and Redis Channel Layer support.

---

## 🛠️ Tech Stack

- **Backend**: Python 3.12, Django 5.x, Django Channels (ASGI), Daphne
- **Database**: PostgreSQL (Production on Railway), SQLite (Local Development)
- **Caching & WebSockets Broker**: Redis (`channels-redis`)
- **Frontend**: HTML5, Vanilla JavaScript, Tailwind CSS (CLI Production Build), FontAwesome 6, Google Fonts (`Inter` & `Outfit`)
- **Authentication**: `django-allauth` (Google OAuth 2.0 & Local Auth)
- **Static Assets Serving**: WhiteNoise (`CompressedManifestStaticFilesStorage`)

---

## 📂 Project Structure

```text
chatappp/
├── apps/
│   ├── accounts/          # User Profiles, Friend Requests, Google OAuth Adapters
│   └── chat/              # Real-Time WebSocket Consumers, Chat Rooms, Call Logs
├── chatappp/
│   ├── asgi.py            # ASGI Configuration for WebSockets & Daphne
│   ├── wsgi.py            # WSGI Configuration for Gunicorn
│   ├── settings.py        # Django Settings (Configured for Railway & Local)
│   └── urls.py            # Root URL Dispatcher
├── static/
│   ├── css/
│   │   ├── input.css      # Tailwind CSS Directives
│   │   ├── output.css     # Production Compiled Tailwind CSS
│   │   └── style.css      # NovaChat Light/Dark Theme CSS Design Tokens
│   ├── js/
│   │   └── theme.js       # Light/Dark Theme Controller Engine
│   └── images/
│       └── logo.png       # NovaChat Brand Logo
├── templates/
│   ├── base.html          # Global Layout Template with Header & Theme Drawer
│   ├── accounts/          # Login, Register, Home, Profile, Settings, Search
│   └── chat/              # Chat Room, Chats List, Calls Log
├── .env.example           # Complete Environment Variables Reference
├── Procfile               # Railway Cloud Daphne Start Command
├── runtime.txt            # Python 3.12.5 Runtime Specification
├── tailwind.config.js     # Tailwind CSS Configuration
└── requirements.txt       # Production Dependencies
```

---

## 🚀 Local Development Setup

### 1. Clone Repository & Create Virtual Environment
```bash
git clone https://github.com/your-username/novachat.git
cd novachat

# Create virtual environment
python -m venv env

# Activate virtual environment (Windows PowerShell)
.\env\Scripts\Activate.ps1

# Activate virtual environment (Linux/macOS)
source env/bin/activate
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
npm install
```

### 3. Build Tailwind CSS
```bash
npm run build:css
```

### 4. Configure Environment Variables
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```
Fill in your `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET` from Google Cloud Console.

### 5. Run Database Migrations & Create Superuser
```bash
python manage.py migrate
python manage.py createsuperuser
```

### 6. Start Development Server
```bash
python manage.py runserver
```
Visit `http://127.0.0.1:8000/` in your browser.

---

## ☁️ Production Deployment on Railway Cloud

1. Push your repository to **GitHub**.
2. Connect your GitHub repository to **Railway Cloud** (`railway.app`).
3. Add a **PostgreSQL Database** plugin in Railway.
4. Add environment variables in Railway Dashboard:
   - `SECRET_KEY`: High-entropy random key.
   - `DEBUG`: `False`
   - `ALLOWED_HOSTS`: `.railway.app`
   - `CSRF_TRUSTED_ORIGINS`: `https://*.railway.app`
   - `GOOGLE_CLIENT_ID`: Your Google OAuth Client ID.
   - `GOOGLE_CLIENT_SECRET`: Your Google OAuth Client Secret.
5. Railway will automatically detect the `Procfile` (`web: daphne -b 0.0.0.0 -p $PORT chatappp.asgi:application`) and deploy your application.

For detailed step-by-step instructions, see [RAILWAY_DEPLOYMENT.md](RAILWAY_DEPLOYMENT.md).

---

## ❓ Troubleshooting & Common Questions

- **Google OAuth Redirect URI Error**: Ensure your Google Cloud Console Authorized Redirect URIs include `https://your-app.up.railway.app/accounts/google/login/callback/`.
- **WebSocket Connection Failures**: Make sure Railway is running the ASGI command via `daphne` specified in `Procfile`.

---

## 📄 License
This project is licensed under the MIT License.
