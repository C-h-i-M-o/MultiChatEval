from decimal import Decimal

from app.adapters.base import ModelUsage
from app.adapters.openai_compatible import OpenAICompatibleClient


def test_normalize_usage_splits_cached_and_created_input_tokens() -> None:
    usage = OpenAICompatibleClient.normalize_usage(
        {
            "prompt_tokens": 1000,
            "completion_tokens": 200,
            "prompt_tokens_details": {
                "cached_tokens": 300,
                "cache_creation_tokens": 100,
            },
        },
        prompt_fallback=0,
        answer_fallback=0,
    )

    assert usage == ModelUsage(
        input_tokens=600,
        output_tokens=200,
        cache_hit_tokens=300,
        cache_creation_tokens=100,
    )
    assert usage.total_tokens == 1200


def test_normalize_usage_uses_zero_for_missing_cache_categories() -> None:
    usage = OpenAICompatibleClient.normalize_usage(
        {"prompt_tokens": 80, "completion_tokens": 20},
        prompt_fallback=0,
        answer_fallback=0,
    )

    assert usage.input_tokens == 80
    assert usage.output_tokens == 20
    assert usage.cache_hit_tokens == 0
    assert usage.cache_creation_tokens == 0
    assert usage.total_tokens == 100


def test_normalize_usage_does_not_invent_tokens_when_usage_is_missing() -> None:
    usage = OpenAICompatibleClient.normalize_usage(
        {},
        prompt_fallback=120,
        answer_fallback=80,
    )

    assert usage.total_tokens == 0


def test_estimate_cost_uses_per_million_token_prices() -> None:
    client = OpenAICompatibleClient(
        model_name="test-model",
        base_url="https://example.com/v1",
        api_key="sk-test",
        input_price=Decimal("2"),
        output_price=Decimal("8"),
        cache_hit_price=Decimal("0.5"),
        cache_creation_price=Decimal("3"),
    )
    usage = ModelUsage(
        input_tokens=1_000_000,
        output_tokens=500_000,
        cache_hit_tokens=200_000,
        cache_creation_tokens=100_000,
    )

    details = client.estimate_cost_details(usage)

    assert details.input_cost == Decimal("2")
    assert details.output_cost == Decimal("4")
    assert details.cache_hit_cost == Decimal("0.1")
    assert details.cache_creation_cost == Decimal("0.3")
    assert details.total_cost == Decimal("6.4")
