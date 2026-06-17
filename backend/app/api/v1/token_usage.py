from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.token_usage import TokenUsageRead
from app.services.token_quota_service import token_quota_service

router = APIRouter()


@router.get("/me/today", response_model=TokenUsageRead)
async def get_my_today_usage(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> TokenUsageRead:
    return await token_quota_service.get_today_usage(db, current_user)
