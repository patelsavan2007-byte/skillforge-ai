from fastapi import APIRouter, Depends, HTTPException, Request
from app.routes.auth import get_current_user_id
from app.database.mongodb import get_users_collection
from app.utils.object_id import validate_object_id, serialize_doc

router = APIRouter(prefix="/api/users", tags=["users"])

@router.get("/me")
async def get_user_profile(user_id: str = Depends(get_current_user_id)):
    """Retrieve authenticated user details from MongoDB users collection."""
    users_col = get_users_collection()
    query = {}
    try:
        query = {"_id": validate_object_id(user_id)}
    except Exception:
        query = {"_id": user_id}

    user = users_col.find_one(query)
    if not user:
        user = users_col.find_one({"id": user_id})

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return {
        "success": True,
        "data": serialize_doc(user)
    }
