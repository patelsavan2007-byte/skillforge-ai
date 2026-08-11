import secrets
import urllib.parse
import httpx
from sqlalchemy.orm import Session
from app.config import settings
from app.models.user import User

GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v2/userinfo"

def generate_oauth_state() -> str:
    return secrets.token_urlsafe(32)

def get_google_auth_url(state: str) -> str:
    params = {
        "client_id": settings.GOOGLE_CLIENT_ID,
        "redirect_uri": settings.GOOGLE_REDIRECT_URI,
        "response_type": "code",
        "scope": "openid email profile",
        "state": state,
        "prompt": "select_account",
    }
    return f"{GOOGLE_AUTH_URL}?{urllib.parse.urlencode(params)}"

async def exchange_code_for_token(code: str) -> str:
    data = {
        "client_id": settings.GOOGLE_CLIENT_ID,
        "client_secret": settings.GOOGLE_CLIENT_SECRET,
        "code": code,
        "grant_type": "authorization_code",
        "redirect_uri": settings.GOOGLE_REDIRECT_URI,
    }
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.post(GOOGLE_TOKEN_URL, data=data)
        if response.status_code != 200:
            raise Exception(f"Failed to exchange code with Google: {response.text}")
        token_data = response.json()
        access_token = token_data.get("access_token")
        if not access_token:
            raise Exception("No access_token returned by Google")
        return access_token

async def fetch_google_user_profile(access_token: str) -> dict:
    headers = {"Authorization": f"Bearer {access_token}"}
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(GOOGLE_USERINFO_URL, headers=headers)
        if response.status_code != 200:
            raise Exception(f"Failed to fetch Google profile: {response.text}")
        return response.json()

def get_or_create_user(db: Session, google_profile: dict) -> User:
    google_id = str(google_profile.get("id") or google_profile.get("sub"))
    email = google_profile.get("email")
    name = google_profile.get("name") or email.split("@")[0]
    picture = google_profile.get("picture") or ""

    if not google_id or not email:
        raise ValueError("Google user profile missing google_id or email")

    user = db.query(User).filter(User.google_id == google_id).first()
    if not user:
        # Check if user exists with same email
        user = db.query(User).filter(User.email == email).first()
        if user:
            user.google_id = google_id
            user.name = name or user.name
            user.profile_picture = picture or user.profile_picture
        else:
            user = User(
                google_id=google_id,
                email=email,
                name=name,
                profile_picture=picture,
            )
            db.add(user)
    else:
        # Update details if changed
        user.name = name or user.name
        user.profile_picture = picture or user.profile_picture

    db.commit()
    db.refresh(user)
    return user
