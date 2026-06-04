from datetime import datetime

from fastapi.testclient import TestClient
import pytest

from app.main import app
from app.schemas.evaluation import EvaluationFeedbackRead, EvaluationTaskListItemRead, EvaluationTaskListRead
from app.services.evaluation_service import EvaluationTaskNotFoundError, evaluation_service


def test_get_evaluation_task_returns_404_when_task_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    async def fake_get_task(task_id: int, _db: object) -> None:
        assert task_id == 404
        raise EvaluationTaskNotFoundError("评测任务不存在")

    monkeypatch.setattr(evaluation_service, "get_task", fake_get_task)

    response = TestClient(app).get("/api/evaluation/tasks/404")

    assert response.status_code == 404
    assert response.json() == {"detail": "评测任务不存在"}


def test_list_evaluation_tasks_returns_paginated_result(monkeypatch: pytest.MonkeyPatch) -> None:
    created_at = datetime(2026, 6, 3, 12, 0, 0)

    async def fake_list_tasks(_db: object, page: int, page_size: int) -> EvaluationTaskListRead:
        assert page == 2
        assert page_size == 20
        return EvaluationTaskListRead(
            items=[
                EvaluationTaskListItemRead(
                    taskId=10,
                    status="completed",
                    prompt="历史问题",
                    createdAt=created_at,
                    completedAt=created_at,
                    responseCount=3,
                )
            ],
            total=21,
            page=2,
            pageSize=20,
        )

    monkeypatch.setattr(evaluation_service, "list_tasks", fake_list_tasks)

    response = TestClient(app).get("/api/evaluation/tasks?page=2&pageSize=20")

    assert response.status_code == 200
    assert response.json() == {
        "items": [
            {
                "taskId": 10,
                "status": "completed",
                "prompt": "历史问题",
                "createdAt": "2026-06-03T12:00:00",
                "completedAt": "2026-06-03T12:00:00",
                "responseCount": 3,
            }
        ],
        "total": 21,
        "page": 2,
        "pageSize": 20,
    }


def test_create_feedback_returns_updated_feedback(monkeypatch: pytest.MonkeyPatch) -> None:
    async def fake_toggle_feedback(response_id: int, feedback_type: str, comment: str | None, _db: object) -> dict[str, object]:
        assert response_id == 5001
        assert feedback_type == "like"
        assert comment is None
        return {
            "responseId": response_id,
            "feedbackType": feedback_type,
            "active": True,
            "feedback": EvaluationFeedbackRead(liked=True, accepted=False, likeCount=1, acceptedCount=0),
        }

    monkeypatch.setattr(evaluation_service, "toggle_feedback", fake_toggle_feedback)

    response = TestClient(app).post("/api/evaluation/responses/5001/feedback", json={"feedbackType": "like"})

    assert response.status_code == 200
    assert response.json() == {
        "responseId": 5001,
        "feedbackType": "like",
        "active": True,
        "feedback": {
            "liked": True,
            "accepted": False,
            "likeCount": 1,
            "acceptedCount": 0,
        },
    }


def test_create_feedback_rejects_unknown_feedback_type() -> None:
    response = TestClient(app).post("/api/evaluation/responses/5001/feedback", json={"feedbackType": "favorite"})

    assert response.status_code == 422


def test_create_feedback_returns_404_when_response_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    async def fake_toggle_feedback(response_id: int, feedback_type: str, comment: str | None, _db: object) -> None:
        assert response_id == 404
        assert feedback_type == "accepted"
        assert comment is None
        raise EvaluationTaskNotFoundError("模型回答不存在")

    monkeypatch.setattr(evaluation_service, "toggle_feedback", fake_toggle_feedback)

    response = TestClient(app).post("/api/evaluation/responses/404/feedback", json={"feedbackType": "accepted"})

    assert response.status_code == 404
    assert response.json() == {"detail": "模型回答不存在"}
