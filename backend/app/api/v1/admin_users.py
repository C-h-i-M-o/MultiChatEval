from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import require_admin
from app.db.session import get_db
from app.models.user import User
from app.schemas.token_usage import AdminUserListRead, AdminUserUsageRead, UserQuotaUpdate, UserStatusUpdate
from app.services.token_quota_service import TokenQuotaUserError, token_quota_service

router = APIRouter(dependencies=[Depends(require_admin)])


@router.get("", response_model=AdminUserListRead)
async def list_users(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, alias="pageSize", ge=1, le=100),
    keyword: str | None = Query(default=None, max_length=64),
    role: Literal["user", "admin"] | None = None,
    status_filter: Literal["active", "disabled"] | None = Query(default=None, alias="status"),
    db: AsyncSession = Depends(get_db),
) -> AdminUserListRead:
    return await token_quota_service.list_users(
        db,
        page=page,
        page_size=page_size,
        keyword=keyword,
        role=role,
        user_status=status_filter,
    )


@router.patch("/{user_id}/status", response_model=AdminUserUsageRead)
async def update_user_status(
    user_id: int,
    payload: UserStatusUpdate,
    db: AsyncSession = Depends(get_db),
    current_admin: User = Depends(require_admin),
) -> AdminUserUsageRead:
    try:
        return await token_quota_service.set_user_status(
            db,
            user_id=user_id,
            user_status=payload.status,
            operator_user_id=current_admin.id,
        )
    except TokenQuotaUserError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error


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
