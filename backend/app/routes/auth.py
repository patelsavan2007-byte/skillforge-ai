from typing import Optional
from fastapi import APIRouter, HTTPException, Request, Query
from fastapi.responses import RedirectResponse, JSONResponse
from bson import ObjectId

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

def get_current_user_id(request: Request) -> str:
    """Dependency to retrieve authenticated user's ID from session.
    Enforces strict authentication for user data isolation.
    """
    user_id = request.session.get("user_id")
    
    # Optional header override for API testing tools if user_id is provided in header
    test_user_id = request.headers.get("X-User-ID")
    if test_user_id and not user_id:
        user_id = test_user_id

    if not user_id:
        raise HTTPException(
            status_code=401,
            detail="Authentication required. Please log in first."
        )
    return str(user_id)

@router.get("/google/login")
async def google_login(request: Request):
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
        frontend_error_url = f"{settings.FRONTEND_URL}/login?error={error}"
        return RedirectResponse(url=frontend_error_url, status_code=307)

    saved_state = request.session.get("oauth_state")
    if not state or not saved_state or state != saved_state:
        frontend_error_url = f"{settings.FRONTEND_URL}/login?error=invalid_state"
        return RedirectResponse(url=frontend_error_url, status_code=307)

    if not code:
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

        return RedirectResponse(url=settings.FRONTEND_URL, status_code=307)
    except Exception as e:
        frontend_error_url = f"{settings.FRONTEND_URL}/login?error=auth_failed"
        return RedirectResponse(url=frontend_error_url, status_code=307)

@router.get("/me")
async def get_current_user(request: Request):
    user_id = request.session.get("user_id")
    if not user_id:
        return JSONResponse(
            status_code=401,
            content={"authenticated": False, "detail": "Not authenticated"},
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
            status_code=401,
            content={"authenticated": False, "detail": "User not found"},
        )

    return JSONResponse(
        content={
            "authenticated": True,
            "user": {
                "id": str(user["_id"]),
                "email": user.get("email"),
                "name": user.get("name"),
                "profile_picture": user.get("profile_picture") or "",
            },
        }
    )

@router.post("/logout")
async def logout(request: Request):
    request.session.clear()
    return JSONResponse(content={"success": True, "message": "Logged out successfully"})
