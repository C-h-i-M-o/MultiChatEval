from decimal import Decimal
from time import perf_counter

import httpx

from app.adapters.base import ModelClient, ModelCostDetails, ModelReply, ModelRequest, ModelUsage

TOKENS_PER_MILLION = Decimal("1000000")


class OpenAICompatibleClient(ModelClient):
    def __init__(
        self,
        model_name: str,
        base_url: str,
        api_key: str,
        input_price: Decimal = Decimal("0"),
        output_price: Decimal = Decimal("0"),
        cache_hit_price: Decimal = Decimal("0"),
        cache_creation_price: Decimal = Decimal("0"),
        timeout: float = 60,
        extra_body: dict[str, object] | None = None,
    ) -> None:
        self.model_name = model_name
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.input_price = input_price
        self.output_price = output_price
        self.cache_hit_price = cache_hit_price
        self.cache_creation_price = cache_creation_price
        self.timeout = timeout
        self.extra_body = extra_body or {}

    async def chat(self, request: ModelRequest) -> ModelReply:
        if not self.api_key:
            raise ValueError(f"{self.model_name} 未配置 API Key")
        if not self.base_url:
            raise ValueError(f"{self.model_name} 未配置 Base URL")

        started_at = perf_counter()
        payload = {
            "model": request.model_name,
            "messages": [{"role": "user", "content": request.prompt}],
            "max_tokens": request.max_tokens,
            "temperature": request.temperature,
            "stream": False,
        }
        payload.update(self.extra_body)
        payload.update(request.extra_body)
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(f"{self.base_url}/chat/completions", json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()

        message = data["choices"][0]["message"]
        answer = message.get("content") or ""
        reasoning_content = (message.get("reasoning_content") or "").strip()
        if reasoning_content:
            answer = f"<think>\n{reasoning_content}\n</think>\n\n{answer}".strip()
        usage = self.normalize_usage(
            data.get("usage", {}),
            prompt_fallback=len(request.prompt),
            answer_fallback=len(answer),
        )
        latency_ms = int((perf_counter() - started_at) * 1000)
        return ModelReply(answer=answer, usage=usage, latency_ms=latency_ms)

    def get_model_name(self) -> str:
        return self.model_name

    def estimate_cost(self, usage: ModelUsage) -> Decimal:
        return self.estimate_cost_details(usage).total_cost

    def estimate_cost_details(self, usage: ModelUsage) -> ModelCostDetails:
        return ModelCostDetails(
            input_cost=Decimal(usage.input_tokens) * self.input_price / TOKENS_PER_MILLION,
            output_cost=Decimal(usage.output_tokens) * self.output_price / TOKENS_PER_MILLION,
            cache_hit_cost=Decimal(usage.cache_hit_tokens) * self.cache_hit_price / TOKENS_PER_MILLION,
            cache_creation_cost=(
                Decimal(usage.cache_creation_tokens) * self.cache_creation_price / TOKENS_PER_MILLION
            ),
        )

    @staticmethod
    def normalize_usage(
        usage_data: dict[str, object],
        prompt_fallback: int,
        answer_fallback: int,
    ) -> ModelUsage:
        prompt_details = usage_data.get("prompt_tokens_details")
        details = prompt_details if isinstance(prompt_details, dict) else {}
        cache_hit_tokens = int(
            details.get("cached_tokens")
            or usage_data.get("cache_read_input_tokens")
            or usage_data.get("prompt_cache_hit_tokens")
            or 0
        )
        cache_creation_tokens = int(
            details.get("cache_creation_tokens")
            or usage_data.get("cache_creation_input_tokens")
            or usage_data.get("prompt_cache_creation_tokens")
            or 0
        )
        prompt_tokens = int(usage_data.get("prompt_tokens") or usage_data.get("input_tokens") or 0)
        output_tokens = int(usage_data.get("completion_tokens") or usage_data.get("output_tokens") or 0)
        input_tokens = max(prompt_tokens - cache_hit_tokens - cache_creation_tokens, 0)
        return ModelUsage(
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cache_hit_tokens=cache_hit_tokens,
            cache_creation_tokens=cache_creation_tokens,
        )
