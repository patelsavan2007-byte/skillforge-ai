from typing import Dict, Any, List
from fastapi import APIRouter, Depends, HTTPException, Body
from app.routes.auth import get_current_user_id
from app.schemas.portfolio import PortfolioCreate
from app.services.portfolio_service import (
    analyze_portfolio_url,
    create_portfolio_record,
    get_user_portfolios,
    get_portfolio_by_id,
    delete_portfolio_by_id,
)

router = APIRouter(prefix="/api/portfolios", tags=["portfolios"])

@router.post("", response_model=Dict[str, Any])
async def create_portfolio(
    payload: PortfolioCreate = Body(...),
    user_id: str = Depends(get_current_user_id)
):
    """Analyze portfolio URL and persist analysis output to MongoDB portfolios collection."""
    profile_dict = payload.profile.model_dump() if payload.profile else None
    if not profile_dict:
        profile_dict = await analyze_portfolio_url(payload.url)

    doc = create_portfolio_record(
        user_id=user_id,
        url=payload.url,
        profile=profile_dict
    )
    return {"success": True, "data": doc}

@router.get("", response_model=Dict[str, Any])
async def list_portfolios(user_id: str = Depends(get_current_user_id)):
    """Retrieve all portfolio records for authenticated user."""
    portfolios = get_user_portfolios(user_id)
    return {"success": True, "count": len(portfolios), "data": portfolios}

@router.get("/{portfolio_id}", response_model=Dict[str, Any])
async def get_portfolio(portfolio_id: str, user_id: str = Depends(get_current_user_id)):
    """Retrieve portfolio by ID with strict user isolation."""
    portfolio = get_portfolio_by_id(portfolio_id, user_id)
    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    return {"success": True, "data": portfolio}

@router.delete("/{portfolio_id}", response_model=Dict[str, Any])
async def delete_portfolio(portfolio_id: str, user_id: str = Depends(get_current_user_id)):
    """Delete portfolio by ID with strict user isolation."""
    deleted = delete_portfolio_by_id(portfolio_id, user_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Portfolio not found or unauthorized")
    return {"success": True, "message": "Portfolio deleted successfully"}
