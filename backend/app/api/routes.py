from fastapi import APIRouter

from app.api.v1 import auth, evaluation, health, model_configs, models

api_router = APIRouter()
api_router.include_router(health.router, tags=["health"])
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(evaluation.router, prefix="/evaluation", tags=["evaluation"])
api_router.include_router(models.router, prefix="/models", tags=["models"])
api_router.include_router(
    model_configs.router,
    prefix="/admin/model-configs",
    tags=["admin-model-configs"],
)
