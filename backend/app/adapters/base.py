from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from decimal import Decimal


@dataclass(frozen=True)
class ModelRequest:
    prompt: str
    model_name: str
    max_tokens: int = 1024
    extra_body: dict[str, object] = field(default_factory=dict)


@dataclass(frozen=True)
class ModelUsage:
    input_tokens: int
    output_tokens: int


@dataclass(frozen=True)
class ModelReply:
    answer: str
    usage: ModelUsage
    latency_ms: int


class ModelClient(ABC):
    @abstractmethod
    async def chat(self, request: ModelRequest) -> ModelReply:
        raise NotImplementedError

    @abstractmethod
    def get_model_name(self) -> str:
        raise NotImplementedError

    @abstractmethod
    def estimate_cost(self, usage: ModelUsage) -> Decimal:
        raise NotImplementedError
