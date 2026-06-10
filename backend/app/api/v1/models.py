from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user
from app.db.session import get_db
from app.schemas.model_config import AvailableModelRead
from app.services.model_config_service import model_config_service

router = APIRouter(dependencies=[Depends(get_current_user)])


@router.get("/available", response_model=list[AvailableModelRead])
async def list_available_models(db: AsyncSession = Depends(get_db)) -> list[AvailableModelRead]:
    return await model_config_service.list_available_configs(db)
