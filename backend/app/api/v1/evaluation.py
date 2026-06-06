import json
from collections.abc import AsyncIterator

from fastapi import APIRouter, HTTPException, Query
from fastapi import Depends
from fastapi.encoders import jsonable_encoder
from fastapi.responses import Response, StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.evaluation import (
    CommentCreate,
    CommentListRead,
    CommentRead,
    EvaluationTaskCreate,
    EvaluationTaskListRead,
    EvaluationTaskRead,
    FeedbackCreate,
    FeedbackToggleRead,
)
from app.services.evaluation_service import (
    EvaluationCommentNotFoundError,
    EvaluationResponseNotFoundError,
    EvaluationTaskNotFoundError,
    evaluation_service,
)

router = APIRouter()


@router.post("/tasks", response_model=EvaluationTaskRead)
async def create_evaluation_task(
    payload: EvaluationTaskCreate,
    db: AsyncSession = Depends(get_db),
) -> EvaluationTaskRead:
    return await evaluation_service.create_task(payload, db)


@router.post("/tasks/stream")
async def stream_evaluation_task(
    payload: EvaluationTaskCreate,
    db: AsyncSession = Depends(get_db),
) -> StreamingResponse:
    async def render_events() -> AsyncIterator[str]:
        async for event in evaluation_service.stream_task_events(payload, db):
            yield json.dumps(jsonable_encoder(event), ensure_ascii=False) + "\n"

    return StreamingResponse(render_events(), media_type="application/x-ndjson")


@router.get("/tasks", response_model=EvaluationTaskListRead)
async def list_evaluation_tasks(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=100, alias="pageSize"),
    db: AsyncSession = Depends(get_db),
) -> EvaluationTaskListRead:
    return await evaluation_service.list_tasks(db, page, page_size)


@router.get("/tasks/{task_id}", response_model=EvaluationTaskRead)
async def get_evaluation_task(
    task_id: int,
    db: AsyncSession = Depends(get_db),
) -> EvaluationTaskRead:
    try:
        return await evaluation_service.get_task(task_id, db)
    except EvaluationTaskNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


@router.post("/responses/{response_id}/feedback", response_model=FeedbackToggleRead)
async def create_feedback(
    response_id: int,
    payload: FeedbackCreate,
    db: AsyncSession = Depends(get_db),
) -> FeedbackToggleRead:
    try:
        return await evaluation_service.toggle_response_feedback(response_id, payload, db)
    except EvaluationResponseNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


@router.get("/responses/{response_id}/comments", response_model=CommentListRead)
async def list_response_comments(
    response_id: int,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100, alias="pageSize"),
    db: AsyncSession = Depends(get_db),
) -> CommentListRead:
    try:
        return await evaluation_service.list_response_comments(response_id, db, page, page_size)
    except EvaluationResponseNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


@router.post("/responses/{response_id}/comments", response_model=CommentRead, status_code=201)
async def create_response_comment(
    response_id: int,
    payload: CommentCreate,
    db: AsyncSession = Depends(get_db),
) -> CommentRead:
    try:
        return await evaluation_service.create_response_comment(response_id, payload, db)
    except EvaluationResponseNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


@router.delete("/comments/{comment_id}", status_code=204)
async def delete_response_comment(
    comment_id: int,
    db: AsyncSession = Depends(get_db),
) -> Response:
    try:
        await evaluation_service.delete_response_comment(comment_id, db)
    except EvaluationCommentNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    return Response(status_code=204)
