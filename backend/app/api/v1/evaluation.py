from fastapi import APIRouter
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.evaluation import EvaluationTaskCreate, EvaluationTaskRead, FeedbackCreate
from app.services.evaluation_service import evaluation_service

router = APIRouter()


@router.post("/tasks", response_model=EvaluationTaskRead)
async def create_evaluation_task(
    payload: EvaluationTaskCreate,
    db: AsyncSession = Depends(get_db),
) -> EvaluationTaskRead:
    return await evaluation_service.create_task(payload, db)


@router.get("/tasks/{task_id}", response_model=EvaluationTaskRead)
async def get_evaluation_task(task_id: int) -> EvaluationTaskRead:
    return await evaluation_service.get_task(task_id)


@router.post("/responses/{response_id}/feedback")
async def create_feedback(response_id: int, payload: FeedbackCreate) -> dict[str, int | str]:
    return {"responseId": response_id, "feedbackType": payload.feedback_type, "status": "received"}
