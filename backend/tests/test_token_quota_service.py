from datetime import datetime, timezone

from app.services.token_quota_service import DEFAULT_DAILY_TOKEN_LIMIT, token_quota_service


def test_usage_date_uses_asia_shanghai_natural_day() -> None:
    utc_time = datetime(2026, 6, 11, 16, 30, tzinfo=timezone.utc)

    assert token_quota_service.usage_date(utc_time).isoformat() == "2026-06-12"


def test_default_daily_limit_is_one_hundred_thousand_tokens() -> None:
    assert DEFAULT_DAILY_TOKEN_LIMIT == 100_000


class FakeResult:
    def one(self) -> tuple[int, int]:
        return 0, 0


class FakeDb:
    async def execute(self, _statement: object) -> FakeResult:
        return FakeResult()


async def test_explicit_zero_daily_limit_is_not_replaced_by_default() -> None:
    used_tokens, daily_limit = await token_quota_service._usage_and_limit(
        FakeDb(),
        user_id=7,
        usage_date=token_quota_service.usage_date(),
    )

    assert used_tokens == 0
    assert daily_limit == 0
