from decimal import Decimal
from time import perf_counter

import httpx

from app.adapters.base import ModelClient, ModelReply, ModelRequest, ModelUsage


class OpenAICompatibleClient(ModelClient):
    def __init__(
        self,
        model_name: str,
        base_url: str,
        api_key: str,
        input_price: Decimal = Decimal("0"),
        output_price: Decimal = Decimal("0"),
        timeout: float = 60,
        extra_body: dict[str, object] | None = None,
    ) -> None:
        self.model_name = model_name
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.input_price = input_price
        self.output_price = output_price
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
            "temperature": 0.7,
            "stream": False,
        }
        payload.update(self.extra_body)
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(f"{self.base_url}/chat/completions", json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()

        answer = data["choices"][0]["message"]["content"]
        usage_data = data.get("usage", {})
        usage = ModelUsage(
            input_tokens=int(usage_data.get("prompt_tokens") or len(request.prompt)),
            output_tokens=int(usage_data.get("completion_tokens") or len(answer)),
        )
        latency_ms = int((perf_counter() - started_at) * 1000)
        return ModelReply(answer=answer, usage=usage, latency_ms=latency_ms)

    def get_model_name(self) -> str:
        return self.model_name

    def estimate_cost(self, usage: ModelUsage) -> Decimal:
        return Decimal(usage.input_tokens) * self.input_price + Decimal(usage.output_tokens) * self.output_price
