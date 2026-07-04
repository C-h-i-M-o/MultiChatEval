from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.api.dependencies import get_current_user
from app.core.security import AUTH_COOKIE_NAME, create_access_token
from app.db.session import get_db
from app.models.user import User
from app.schemas.auth import AuthCredentials, RegisterCredentials, UserRead
from app.services.auth_service import (
    DuplicateUsernameError,
    InvalidCredentialsError,
    UserDisabledError,
    auth_service,
)

router = APIRouter()


def set_auth_cookie(response: Response, user_id: int) -> None:
    response.set_cookie(
        key=AUTH_COOKIE_NAME,
        value=create_access_token(user_id),
        max_age=settings.access_token_expire_minutes * 60,
        httponly=True,
        secure=settings.auth_cookie_secure,
        samesite="lax",
        path="/",
    )


@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def register(
    payload: RegisterCredentials,
    response: Response,
    db: AsyncSession = Depends(get_db),
) -> UserRead:
    try:
        user = await auth_service.register(db, payload.username, payload.password)
    except DuplicateUsernameError as error:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(error)) from error
    set_auth_cookie(response, user.id)
    return user


@router.post("/login", response_model=UserRead)
async def login(
    payload: AuthCredentials,
    response: Response,
    db: AsyncSession = Depends(get_db),
) -> UserRead:
    try:
        user = await auth_service.authenticate(db, payload.username, payload.password)
    except InvalidCredentialsError as error:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(error)) from error
    except UserDisabledError as error:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(error)) from error
    set_auth_cookie(response, user.id)
    return user


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(response: Response) -> Response:
    response.delete_cookie(
        key=AUTH_COOKIE_NAME,
        path="/",
        secure=settings.auth_cookie_secure,
        httponly=True,
        samesite="lax",
    )
    response.status_code = status.HTTP_204_NO_CONTENT
    return response


@router.get("/me", response_model=UserRead)
async def get_me(current_user: User = Depends(get_current_user)) -> UserRead:
    return auth_service.serialize_user(current_user)
