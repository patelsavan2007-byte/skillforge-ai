from typing import Optional
from fastapi import APIRouter, Depends, Request, Query
from fastapi.responses import RedirectResponse, JSONResponse
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models.user import User
from app.services.google_auth import (
    generate_oauth_state,
    get_google_auth_url,
    exchange_code_for_token,
    fetch_google_user_profile,
    get_or_create_user,
)

router = APIRouter(prefix="/api/auth", tags=["authentication"])

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
    db: Session = Depends(get_db),
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
        user = get_or_create_user(db, google_profile)

        # Set session
        request.session["user_id"] = user.id
        request.session.pop("oauth_state", None)

        return RedirectResponse(url=settings.FRONTEND_URL, status_code=307)
    except Exception as e:
        frontend_error_url = f"{settings.FRONTEND_URL}/login?error=auth_failed"
        return RedirectResponse(url=frontend_error_url, status_code=307)

@router.get("/me")
async def get_current_user(request: Request, db: Session = Depends(get_db)):
    user_id = request.session.get("user_id")
    if not user_id:
        return JSONResponse(
            status_code=401,
            content={"authenticated": False, "detail": "Not authenticated"},
        )

    user = db.query(User).filter(User.id == user_id).first()
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
                "id": user.id,
                "email": user.email,
                "name": user.name,
                "profile_picture": user.profile_picture or "",
            },
        }
    )

@router.post("/logout")
async def logout(request: Request):
    request.session.clear()
    return JSONResponse(content={"success": True, "message": "Logged out successfully"})
