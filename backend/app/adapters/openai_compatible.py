from decimal import Decimal

from app.adapters.base import ModelClient, ModelReply, ModelRequest, ModelUsage


class OpenAICompatibleClient(ModelClient):
    def __init__(self, model_name: str, input_price: Decimal = Decimal("0"), output_price: Decimal = Decimal("0")) -> None:
        self.model_name = model_name
        self.input_price = input_price
        self.output_price = output_price

    async def chat(self, request: ModelRequest) -> ModelReply:
        answer = f"当前为 {request.model_name} 的模拟回答，后续会替换为真实 OpenAI-compatible API 调用。"
        usage = ModelUsage(input_tokens=len(request.prompt), output_tokens=len(answer))
        return ModelReply(answer=answer, usage=usage, latency_ms=0)

    def get_model_name(self) -> str:
        return self.model_name

    def estimate_cost(self, usage: ModelUsage) -> Decimal:
        return Decimal(usage.input_tokens) * self.input_price + Decimal(usage.output_tokens) * self.output_price
