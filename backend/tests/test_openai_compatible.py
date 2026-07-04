from decimal import Decimal

import pytest
import httpx

from app.adapters.base import ModelRequest, ModelUsage
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


@pytest.mark.asyncio
async def test_stream_chat_yields_reasoning_and_answer_chunks(monkeypatch: pytest.MonkeyPatch) -> None:
    chunks = [
        'data: {"choices":[{"delta":{"reasoning_content":"先想"}}]}\n\n',
        'data: {"choices":[{"delta":{"reasoning_content":"一下"}}]}\n\n',
        'data: {"choices":[{"delta":{"content":"最终"}}]}\n\n',
        'data: {"choices":[{"delta":{"content":"回答"}}],"usage":{"prompt_tokens":10,"completion_tokens":4}}\n\n',
        "data: [DONE]\n\n",
    ]

    class FakeStreamResponse:
        def raise_for_status(self) -> None:
            pass

        async def aiter_lines(self):
            for chunk in chunks:
                for line in chunk.splitlines():
                    yield line

    class FakeStreamContext:
        async def __aenter__(self) -> FakeStreamResponse:
            return FakeStreamResponse()

        async def __aexit__(self, _exc_type: object, _exc: object, _traceback: object) -> None:
            pass

    class FakeAsyncClient:
        def __init__(self, timeout: float) -> None:
            assert timeout == 60

        async def __aenter__(self) -> "FakeAsyncClient":
            return self

        async def __aexit__(self, _exc_type: object, _exc: object, _traceback: object) -> None:
            pass

        def stream(self, method: str, url: str, json: dict[str, object], headers: dict[str, str]) -> FakeStreamContext:
            assert method == "POST"
            assert url == "https://example.com/v1/chat/completions"
            assert json["stream"] is True
            assert headers["Authorization"] == "Bearer sk-test"
            return FakeStreamContext()

    monkeypatch.setattr(httpx, "AsyncClient", FakeAsyncClient)
    client = OpenAICompatibleClient(
        model_name="test-model",
        base_url="https://example.com/v1",
        api_key="sk-test",
    )

    events = []
    async for event in client.stream_chat(
        ModelRequest(
            prompt="问题",
            model_name="test-model",
            max_tokens=128,
            temperature=0.7,
        )
    ):
        events.append(event)

    assert [event.delta for event in events if event.delta] == ["<think>\n先想", "一下", "\n</think>\n\n最终", "回答"]
    assert events[-1].reply is not None
    assert events[-1].reply.answer == "<think>\n先想一下\n</think>\n\n最终回答"
    assert events[-1].reply.usage == ModelUsage(input_tokens=10, output_tokens=4)
