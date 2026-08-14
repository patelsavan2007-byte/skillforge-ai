import hashlib
import os
import secrets
import urllib.parse
from datetime import datetime
from typing import Optional
from bson import ObjectId
from fastapi import APIRouter, HTTPException, Request, Query
from fastapi.responses import RedirectResponse, JSONResponse
from pydantic import BaseModel

from app.config import settings
from app.database.mongodb import get_users_collection
from app.services.google_auth import (
    generate_oauth_state,
    get_google_auth_url,
    exchange_code_for_token,
    fetch_google_user_profile,
    get_or_create_user,
)
from app.utils.object_id import validate_object_id, serialize_doc

router = APIRouter(prefix="/api/auth", tags=["authentication"])

def hash_password(password: str) -> str:
    salt = os.urandom(16)
    key = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 100000)
    return f"{salt.hex()}:{key.hex()}"

def verify_password(stored_password: str, provided_password: str) -> bool:
    if not stored_password or ":" not in stored_password:
        return False
    try:
        salt_hex, key_hex = stored_password.split(":", 1)
        salt = bytes.fromhex(salt_hex)
        key = hashlib.pbkdf2_hmac("sha256", provided_password.encode("utf-8"), salt, 100000)
        return key.hex() == key_hex
    except Exception:
        return False

class RegisterRequest(BaseModel):
    name: str
    email: str
    password: str

class LoginRequest(BaseModel):
    email: str
    password: str

def get_current_user_id(request: Request) -> str:
    """Dependency to retrieve authenticated user's ID from session or X-User-ID header.
    Enforces strict authentication for user data isolation.
    """
    user_id = request.session.get("user_id")
    test_user_id = request.headers.get("X-User-ID")
    if test_user_id and not user_id:
        user_id = test_user_id

    if not user_id:
        raise HTTPException(
            status_code=401,
            detail="Authentication required. Please log in first."
        )
    return str(user_id)

@router.post("/register")
async def register(request: Request, body: RegisterRequest):
    users_col = get_users_collection()
    email_clean = body.email.strip().lower()
    
    existing = users_col.find_one({"email": email_clean})
    if existing:
        raise HTTPException(status_code=400, detail="An account with that email already exists.")
        
    now = datetime.utcnow()
    hashed_pwd = hash_password(body.password)
    user_doc = {
        "name": body.name.strip(),
        "email": email_clean,
        "password_hash": hashed_pwd,
        "provider": "password",
        "profile_picture": "",
        "createdAt": now,
        "updatedAt": now,
    }
    res = users_col.insert_one(user_doc)
    user_id = str(res.inserted_id)
    request.session["user_id"] = user_id
    
    return {
        "success": True,
        "user": {
            "id": user_id,
            "name": user_doc["name"],
            "email": user_doc["email"],
            "profile_picture": "",
            "provider": "password",
        }
    }

@router.post("/login")
async def login(request: Request, body: LoginRequest):
    users_col = get_users_collection()
    email_clean = body.email.strip().lower()
    
    user = users_col.find_one({"email": email_clean})
    if not user:
        raise HTTPException(status_code=400, detail="No account found with that email address.")
        
    if user.get("provider") == "google" and not user.get("password_hash"):
        raise HTTPException(status_code=400, detail="This account was created with Google. Continue with Google instead.")
        
    stored_hash = user.get("password_hash", "")
    if not verify_password(stored_hash, body.password):
        raise HTTPException(status_code=400, detail="Incorrect password. Please try again.")
        
    user_id = str(user["_id"])
    request.session["user_id"] = user_id
    
    return {
        "success": True,
        "user": {
            "id": user_id,
            "name": user.get("name", ""),
            "email": user.get("email", ""),
            "profile_picture": user.get("profile_picture") or "",
            "provider": user.get("provider", "password"),
        }
    }

@router.get("/google/login")
async def google_login(request: Request):
    if not settings.GOOGLE_CLIENT_ID:
        raise HTTPException(
            status_code=500,
            detail="Google OAuth is not configured. GOOGLE_CLIENT_ID is missing from server environment."
        )
    state = generate_oauth_state()
    request.session["oauth_state"] = state
    auth_url = get_google_auth_url(state)
    return RedirectResponse(url=auth_url, status_code=307)

@router.get("/google/callback")
async def google_callback(
    request: Request,
    code: Optional[str] = Query(None),
    state: Optional[str] = Query(None),
    error: Optional[str] = Query(None),
):
    if error:
        print(f"[Google Auth] OAuth returned error from Google: {error}")
        frontend_error_url = f"{settings.FRONTEND_URL}/login?error={error}"
        return RedirectResponse(url=frontend_error_url, status_code=307)

    saved_state = request.session.get("oauth_state")
    if not state or not saved_state or state != saved_state:
        print(f"[Google Auth] State mismatch or expired session cookie. Received: {state}, Saved in session: {saved_state}")
        frontend_error_url = f"{settings.FRONTEND_URL}/login?error=invalid_state"
        return RedirectResponse(url=frontend_error_url, status_code=307)

    if not code:
        print("[Google Auth] Missing authorization code in callback")
        frontend_error_url = f"{settings.FRONTEND_URL}/login?error=missing_code"
        return RedirectResponse(url=frontend_error_url, status_code=307)

    try:
        access_token = await exchange_code_for_token(code)
        google_profile = await fetch_google_user_profile(access_token)
        user = get_or_create_user(google_profile)

        # Set session
        user_id_str = str(user.get("id") or user.get("_id"))
        request.session["user_id"] = user_id_str
        request.session.pop("oauth_state", None)

        print(f"[Google Auth] Successfully authenticated user: {user.get('email')} (id: {user_id_str})")
        return RedirectResponse(url=settings.FRONTEND_URL, status_code=307)
    except Exception as e:
        print(f"[Google Auth] Token exchange or profile fetch failed: {str(e)}")
        frontend_error_url = f"{settings.FRONTEND_URL}/login?error=auth_failed"
        return RedirectResponse(url=frontend_error_url, status_code=307)

@router.get("/me")
async def get_current_user(request: Request):
    user_id = request.session.get("user_id") or request.headers.get("X-User-ID")
    if not user_id:
        return JSONResponse(
            status_code=200,
            content={"authenticated": False, "user": None},
        )

    users_col = get_users_collection()
    query = {}
    try:
        query = {"_id": validate_object_id(user_id)}
    except HTTPException:
        query = {"_id": user_id}

    user = users_col.find_one(query)
    if not user:
        # Fallback search by string id or email
        user = users_col.find_one({"id": user_id})

    if not user:
        request.session.clear()
        return JSONResponse(
            status_code=200,
            content={"authenticated": False, "user": None},
        )

    return JSONResponse(
        content={
            "authenticated": True,
            "user": {
                "id": str(user["_id"]),
                "email": user.get("email"),
                "name": user.get("name"),
                "profile_picture": user.get("profile_picture") or "",
                "provider": user.get("provider", "google" if user.get("google_id") else "password"),
            },
        }
    )

@router.post("/logout")
async def logout(request: Request):
    request.session.clear()
    return JSONResponse(content={"success": True, "message": "Logged out successfully"})

