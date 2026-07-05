from datetime import datetime, timezone
from importlib import import_module, util

import pytest


def _service_module() -> object:
    assert util.find_spec("app.services.feedback_stats_service") is not None
    return import_module("app.services.feedback_stats_service")


def test_resolve_range_uses_shanghai_natural_days() -> None:
    service_module = _service_module()
    window = service_module.feedback_stats_service.resolve_range(
        "7d",
        datetime(2026, 6, 18, 4, 0, tzinfo=timezone.utc),
    )

    assert window.start_at.isoformat() == "2026-06-12T00:00:00+08:00"
    assert window.end_at.isoformat() == "2026-06-18T12:00:00+08:00"
    assert window.start_at_utc == datetime(2026, 6, 11, 16, 0)


def test_build_dashboard_separates_scores_feedback_and_comments() -> None:
    service_module = _service_module()
    response_records = [
        service_module.ResponseStatRecord(
            task_id=1,
            response_id=11,
            model_config_id=3,
            model_name="模型 A",
            created_at=datetime(2026, 6, 18, 1, 0),
            final_score=8.0,
            rule_score=7.5,
            judge_score=None,
        ),
        service_module.ResponseStatRecord(
            task_id=1,
            response_id=12,
            model_config_id=3,
            model_name="模型 A",
            created_at=datetime(2026, 6, 18, 2, 0),
            final_score=9.0,
            rule_score=8.5,
            judge_score=9.5,
        ),
        service_module.ResponseStatRecord(
            task_id=2,
            response_id=13,
            model_config_id=4,
            model_name="模型 B",
            created_at=datetime(2026, 6, 17, 2, 0),
            final_score=None,
            rule_score=None,
            judge_score=None,
        ),
    ]
    feedback_records = [
        service_module.InteractionRecord(
            activity_id=21,
            activity_type="like",
            user_id=0,
            username="anonymous",
            task_id=1,
            response_id=11,
            model_config_id=3,
            model_name="模型 A",
            prompt="问题",
            content=None,
            created_at=datetime(2026, 6, 18, 3, 0),
        ),
        service_module.InteractionRecord(
            activity_id=22,
            activity_type="dislike",
            user_id=8,
            username="other",
            task_id=1,
            response_id=12,
            model_config_id=3,
            model_name="模型 A",
            prompt="问题",
            content=None,
            created_at=datetime(2026, 6, 18, 4, 0),
        ),
    ]
    comment_records = [
        service_module.InteractionRecord(
            activity_id=31,
            activity_type="comment",
            user_id=8,
            username="other",
            task_id=2,
            response_id=13,
            model_config_id=4,
            model_name="模型 B",
            prompt="问题二",
            content="评论",
            created_at=datetime(2026, 6, 18, 5, 0),
        )
    ]

    dashboard = service_module.feedback_stats_service.build_dashboard(
        response_records,
        feedback_records,
        comment_records,
    )

    assert dashboard.summary.task_count == 2
    assert dashboard.summary.call_count == 3
    assert dashboard.summary.scored_count == 2
    assert dashboard.summary.average_final_score == 8.5
    assert dashboard.summary.like_count == 1
    assert dashboard.summary.dislike_count == 1
    assert dashboard.summary.like_rate == 0.5
    assert dashboard.summary.comment_count == 1
    assert dashboard.models[0].model_name == "模型 A"
    assert dashboard.models[0].average_judge_score == 9.5
    assert dashboard.models[1].like_rate is None
    assert [point.date.isoformat() for point in dashboard.trend] == ["2026-06-17", "2026-06-18"]


def test_filter_activities_applies_type_model_and_pagination() -> None:
    service_module = _service_module()
    activities = [
        service_module.InteractionRecord(
            activity_id=index,
            activity_type="comment" if index % 2 else "like",
            user_id=7,
            username="user",
            task_id=1,
            response_id=10 + index,
            model_config_id=3 if index < 4 else 4,
            model_name="模型",
            prompt="问题",
            content="评论" if index % 2 else None,
            created_at=datetime(2026, 6, 18, index, 0),
        )
        for index in range(1, 6)
    ]

    page = service_module.feedback_stats_service.filter_activities(
        activities,
        activity_type="comment",
        model_config_id=3,
        page=1,
        page_size=1,
    )

    assert page.total == 2
    assert page.items[0].activity_id == 3
    assert page.items[0].content == "评论"


def test_failed_response_counts_as_call_but_not_as_scored() -> None:
    service_module = _service_module()
    dashboard = service_module.feedback_stats_service.build_dashboard(
        [
            service_module.ResponseStatRecord(
                task_id=1,
                response_id=11,
                model_config_id=3,
                model_name="模型 A",
                created_at=datetime(2026, 6, 18, 1, 0),
                final_score=0,
                rule_score=0,
                judge_score=None,
                status="failed",
            )
        ],
        [],
        [],
    )

    assert dashboard.summary.call_count == 1
    assert dashboard.summary.scored_count == 0
    assert dashboard.summary.average_final_score is None


def test_dashboard_only_scores_included_records() -> None:
    service_module = _service_module()
    records = [
        service_module.ResponseStatRecord(
            task_id=1,
            response_id=11,
            model_config_id=3,
            model_name="模型 A",
            created_at=datetime(2026, 6, 18, 1, 0),
            final_score=8.0,
            rule_score=8.0,
            judge_score=8.0,
            score_status="scored",
            excluded_from_stats=False,
        ),
        service_module.ResponseStatRecord(
            task_id=1,
            response_id=12,
            model_config_id=3,
            model_name="模型 A",
            created_at=datetime(2026, 6, 18, 2, 0),
            final_score=None,
            rule_score=8.0,
            judge_score=None,
            score_status="judge_failed",
            excluded_from_stats=True,
        ),
        service_module.ResponseStatRecord(
            task_id=2,
            response_id=13,
            model_config_id=3,
            model_name="模型 A",
            created_at=datetime(2026, 6, 18, 3, 0),
            final_score=None,
            rule_score=8.0,
            judge_score=None,
            score_status="judge_unstable",
            excluded_from_stats=True,
        ),
        service_module.ResponseStatRecord(
            task_id=3,
            response_id=14,
            model_config_id=3,
            model_name="模型 A",
            created_at=datetime(2026, 6, 18, 4, 0),
            final_score=None,
            rule_score=8.0,
            judge_score=None,
            score_status="judge_disabled",
            excluded_from_stats=True,
        ),
        service_module.ResponseStatRecord(
            task_id=4,
            response_id=15,
            model_config_id=3,
            model_name="模型 A",
            created_at=datetime(2026, 6, 18, 5, 0),
            final_score=None,
            rule_score=0.0,
            judge_score=None,
            score_status="model_failed",
            excluded_from_stats=True,
        ),
    ]

    dashboard = service_module.feedback_stats_service.build_dashboard(records, [], [])

    assert dashboard.summary.call_count == 5
    assert dashboard.summary.scored_count == 1
    assert dashboard.summary.average_final_score == 8.0
    assert dashboard.models[0].scored_count == 1


@pytest.mark.asyncio
async def test_personal_stats_separates_owned_tasks_from_own_interactions(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service_module = _service_module()
    service = service_module.FeedbackStatsService()
    calls: list[tuple[str, int | None, int | None]] = []

    async def fake_load_responses(_db: object, _window: object, owner_id: int | None = None) -> list[object]:
        calls.append(("responses", owner_id, None))
        return []

    async def fake_load_feedback(
        _db: object,
        _window: object,
        *,
        target_owner_id: int | None = None,
        actor_user_id: int | None = None,
    ) -> list[object]:
        calls.append(("feedback", target_owner_id, actor_user_id))
        return []

    async def fake_load_comments(
        _db: object,
        _window: object,
        *,
        target_owner_id: int | None = None,
        actor_user_id: int | None = None,
    ) -> list[object]:
        calls.append(("comments", target_owner_id, actor_user_id))
        return []

    monkeypatch.setattr(service, "_load_responses", fake_load_responses)
    monkeypatch.setattr(service, "_load_feedback", fake_load_feedback)
    monkeypatch.setattr(service, "_load_comments", fake_load_comments)

    result = await service.get_personal_stats(object(), 7, "30d")

    assert result.scope == "personal"
    assert ("responses", 7, None) in calls
    assert ("feedback", 7, None) in calls
    assert ("feedback", None, 7) in calls
    assert ("comments", 7, None) in calls
    assert ("comments", None, 7) in calls
