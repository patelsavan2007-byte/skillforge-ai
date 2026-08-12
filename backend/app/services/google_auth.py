import secrets
import urllib.parse
from datetime import datetime
import httpx
from app.config import settings
from app.database.mongodb import get_users_collection
from app.utils.object_id import serialize_doc

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

def get_or_create_user(google_profile: dict) -> dict:
    """Find or create user in MongoDB users collection."""
    users_col = get_users_collection()
    google_id = str(google_profile.get("id") or google_profile.get("sub") or "")
    email = google_profile.get("email")
    name = google_profile.get("name") or (email.split("@")[0] if email else "User")
    picture = google_profile.get("picture") or ""

    if not email:
        raise ValueError("Google user profile missing email")

    query = {"$or": [{"email": email}]}
    if google_id:
        query["$or"].append({"google_id": google_id})

    user = users_col.find_one(query)
    now = datetime.utcnow()

    if user:
        user_id = str(user["_id"])
        users_col.update_one(
            {"_id": user["_id"]},
            {
                "$set": {
                    "name": name,
                    "google_id": google_id or user.get("google_id", ""),
                    "profile_picture": picture or user.get("profile_picture", ""),
                    "updatedAt": now,
                }
            },
        )
        user["id"] = user_id
        user["name"] = name
        user["profile_picture"] = picture or user.get("profile_picture", "")
        return serialize_doc(user)
    else:
        new_doc = {
            "name": name,
            "email": email,
            "google_id": google_id,
            "profile_picture": picture,
            "createdAt": now,
            "updatedAt": now,
        }
        res = users_col.insert_one(new_doc)
        new_doc["id"] = str(res.inserted_id)
        new_doc["_id"] = str(res.inserted_id)
        return serialize_doc(new_doc)
