from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import require_admin
from app.db.session import get_db
from app.schemas.token_usage import AdminUserUsageRead, UserQuotaUpdate
from app.services.token_quota_service import TokenQuotaUserError, token_quota_service

router = APIRouter(dependencies=[Depends(require_admin)])


@router.get("", response_model=list[AdminUserUsageRead])
async def list_users(db: AsyncSession = Depends(get_db)) -> list[AdminUserUsageRead]:
    return await token_quota_service.list_users(db)


@router.put("/{user_id}/quota", response_model=AdminUserUsageRead)
async def update_user_quota(
    user_id: int,
    payload: UserQuotaUpdate,
    db: AsyncSession = Depends(get_db),
) -> AdminUserUsageRead:
    try:
        return await token_quota_service.set_user_quota(db, user_id, payload.daily_limit)
    except TokenQuotaUserError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error
