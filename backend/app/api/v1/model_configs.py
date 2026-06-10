from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import require_admin
from app.db.session import get_db
from app.schemas.model_config import (
    ModelConfigCreate,
    ModelConfigRead,
    ModelConfigTestRequest,
    ModelConfigTestResult,
    ModelConfigUpdate,
)
from app.services.model_config_service import (
    ModelConfigNotFoundError,
    ModelConfigServiceError,
    model_config_service,
)

router = APIRouter(dependencies=[Depends(require_admin)])


@router.get("", response_model=list[ModelConfigRead])
async def list_model_configs(db: AsyncSession = Depends(get_db)) -> list[ModelConfigRead]:
    return await model_config_service.list_configs(db)


@router.post("", response_model=ModelConfigRead, status_code=status.HTTP_201_CREATED)
async def create_model_config(
    payload: ModelConfigCreate,
    db: AsyncSession = Depends(get_db),
) -> ModelConfigRead:
    try:
        return await model_config_service.create_config(db, payload)
    except ModelConfigServiceError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error


@router.put("/{model_config_id}", response_model=ModelConfigRead)
async def update_model_config(
    model_config_id: int,
    payload: ModelConfigUpdate,
    db: AsyncSession = Depends(get_db),
) -> ModelConfigRead:
    try:
        return await model_config_service.update_config(db, model_config_id, payload)
    except ModelConfigNotFoundError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error)) from error
    except ModelConfigServiceError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error


@router.delete("/{model_config_id}")
async def delete_model_config(
    model_config_id: int,
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    try:
        await model_config_service.delete_config(db, model_config_id)
    except ModelConfigNotFoundError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error)) from error
    except ModelConfigServiceError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error
    return {"status": "deleted"}


@router.post("/test", response_model=ModelConfigTestResult)
async def test_model_config(
    payload: ModelConfigTestRequest,
    db: AsyncSession = Depends(get_db),
) -> ModelConfigTestResult:
    return await model_config_service.test_config(db, payload)
