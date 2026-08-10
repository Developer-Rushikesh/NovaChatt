# 🚆 Step-by-Step Railway Cloud Deployment Guide for NovaChat

This guide provides complete instructions for deploying NovaChat to **Railway Cloud** (`railway.app`) with PostgreSQL, WebSockets (Daphne/Channels), Google OAuth 2.0, and WhiteNoise static asset serving.

---

## 📋 Pre-Deployment Checklist

Before deploying, verify that your project contains the following generated files:
- [x] `Procfile` -> Contains `web: daphne -b 0.0.0.0 -p $PORT chatappp.asgi:application`
- [x] `requirements.txt` -> Includes `daphne`, `channels`, `dj-database-url`, `psycopg2-binary`, `whitenoise`, `gunicorn`
- [x] `runtime.txt` -> Contains `python-3.12.5`
- [x] `static/css/output.css` -> Compiled Tailwind CSS
- [x] `.env.example` -> Environment variables reference

---

## 🛠️ Step 1: Create a Railway Account
1. Go to [railway.app](https://railway.app/).
2. Sign up or log in using your **GitHub account**.

---

## 🐙 Step 2: Push Code to GitHub
Ensure all your project code is committed and pushed to your GitHub repository:
```bash
git add .
git commit -m "Prepare NovaChat for Railway Cloud Deployment"
git push origin main
```

---

## 🗄️ Step 3: Create Railway Project & Add PostgreSQL
1. On the Railway dashboard, click **+ New Project**.
2. Select **Deploy from GitHub repo** and choose your `novachat` repository.
3. Once the repository is selected, click **+ Add Service** -> **Database** -> **Add PostgreSQL**.
4. Railway will automatically provision a production PostgreSQL database and set the `DATABASE_URL` environment variable for your application!

---

## 🔑 Step 4: Configure Environment Variables
In your Railway Service -> **Variables** tab, add the following environment variables:

| Variable Name | Example Value | Description |
| :--- | :--- | :--- |
| `SECRET_KEY` | `your-production-secret-key-here` | Secret key for Django cryptographic signing |
| `DEBUG` | `False` | Disables development debug mode for production security |
| `ALLOWED_HOSTS` | `.railway.app` | Permits Railway domain traffic |
| `CSRF_TRUSTED_ORIGINS` | `https://*.railway.app` | Trust HTTPS requests from Railway domains |
| `GOOGLE_CLIENT_ID` | `965441393230-....apps.googleusercontent.com` | Google Cloud OAuth Client ID |
| `GOOGLE_CLIENT_SECRET` | `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` | Google Cloud OAuth Client Secret |

*(Note: `DATABASE_URL` is automatically configured by Railway when you connect the PostgreSQL database).*

---

## 🌐 Step 5: Configure Google Cloud OAuth Redirect URI
1. Go to [Google Cloud Console Credentials Page](https://console.cloud.google.com/apis/credentials).
2. Click on your OAuth 2.0 Client ID.
3. Under **Authorized JavaScript Origins**, add:
   `https://your-app.up.railway.app`
4. Under **Authorized Redirect URIs**, add:
   `https://your-app.up.railway.app/accounts/google/login/callback/`
5. Click **Save**.

---

## ⚡ Step 6: Generate Public Domain & Deploy
1. In your Railway Service -> **Settings** tab, scroll down to **Networking**.
2. Click **Generate Domain** (e.g., `novachat-production.up.railway.app`).
3. Railway will trigger a build using `Procfile` and deploy your app under HTTPS!

---

## 💻 Step 7: Run Migrations & Create Admin Superuser on Railway
To run database migrations and create an admin user on Railway:
1. Install Railway CLI:
   ```bash
   npm i -g @railway/cli
   ```
2. Log in and link your project:
   ```bash
   railway login
   railway link
   ```
3. Run migrations on the Railway PostgreSQL database:
   ```bash
   railway run python manage.py migrate
   ```
4. Create superuser:
   ```bash
   railway run python manage.py createsuperuser
   ```

---

## 🔍 Step 8: Verify Deployment Checklist
- [x] Application loads securely under `https://your-app.up.railway.app`.
- [x] Static files (CSS, JS, Fonts) load with HTTP 200 via WhiteNoise.
- [x] Google Login redirects smoothly and creates user accounts in PostgreSQL.
- [x] Light & Dark mode toggle switches themes seamlessly.
- [x] WebSockets connect for real-time messaging via Daphne ASGI.
