from fastapi import APIRouter

from app.api.v1 import evaluation, health, model_configs

api_router = APIRouter()
api_router.include_router(health.router, tags=["health"])
api_router.include_router(evaluation.router, prefix="/evaluation", tags=["evaluation"])
api_router.include_router(model_configs.router, prefix="/model-configs", tags=["model-configs"])
