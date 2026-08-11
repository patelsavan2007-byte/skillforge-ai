# SkillForge AI — Google Authentication Backend

FastAPI backend service dedicated to Google OAuth 2.0 authentication, user session management, and user data persistence for SkillForge AI.

## Features

- **Google OAuth Login**: `GET /api/auth/google/login`
- **Google OAuth Callback**: `GET /api/auth/google/callback`
- **Current User Profile**: `GET /api/auth/me`
- **Logout Session**: `POST /api/auth/logout`
- **Health Check**: `GET /api/health`

## Setup & Run Instructions

### 1. Set Up Virtual Environment

```bash
cd backend
python -m venv venv
```

**Activate Environment:**
- **Windows (PowerShell)**: `venv\Scripts\activate`
- **Linux / macOS**: `source venv/bin/activate`

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Environment Variables

Ensure `.env` contains valid Google OAuth credentials:

```env
GOOGLE_CLIENT_ID=your_client_id
GOOGLE_CLIENT_SECRET=your_client_secret
GOOGLE_REDIRECT_URI=http://localhost:8000/api/auth/google/callback
FRONTEND_URL=http://localhost:5173
SESSION_SECRET=your_long_random_secret
ENVIRONMENT=development
```

### 4. Start Backend Server

Run:

```bash
python run.py
```

The server will start at `http://localhost:8000`. Automatic OpenAPI documentation is available at `http://localhost:8000/docs`.
