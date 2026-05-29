import asyncio
from decimal import Decimal

import httpx

from app.adapters.base import ModelClient, ModelRequest
from app.adapters.openai_compatible import OpenAICompatibleClient
from app.core.config import settings
from app.schemas.evaluation import EvaluationScoreRead, EvaluationTaskCreate, EvaluationTaskRead, ModelResponseRead
from app.services.rule_evaluator import rule_evaluator


class EvaluationService:
    async def create_task(self, payload: EvaluationTaskCreate) -> EvaluationTaskRead:
        selected_models = self._resolve_selected_models(payload.model_ids)
        tasks = [
            self._call_model(index=index, prompt=payload.prompt, model=model)
            for index, model in enumerate(selected_models, start=1)
        ]
        responses = await asyncio.gather(*tasks)
        task_status = "completed" if any(response.status == "success" for response in responses) else "failed"

        return EvaluationTaskRead(taskId=1, status=task_status, prompt=payload.prompt, responses=responses)

    async def get_task(self, task_id: int) -> EvaluationTaskRead:
        return EvaluationTaskRead(taskId=task_id, status="completed", prompt="示例问题", responses=[])

    async def _call_model(self, index: int, prompt: str, model: dict[str, str | ModelClient]) -> ModelResponseRead:
        client = model["client"]
        model_name = str(model["model_name"])
        provider = str(model["provider"])
        display_name = str(model["display_name"])

        try:
            reply = await asyncio.wait_for(
                client.chat(ModelRequest(prompt=prompt, model_name=model_name)),
                timeout=settings.model_request_timeout + 5,
            )
            estimated_cost = float(client.estimate_cost(reply.usage))
            score = rule_evaluator.evaluate(prompt=prompt, answer=reply.answer)

            return ModelResponseRead(
                id=index,
                modelName=display_name,
                provider=provider,
                answer=reply.answer,
                latencyMs=reply.latency_ms,
                outputTokens=reply.usage.output_tokens,
                estimatedCost=estimated_cost,
                status="success",
                score=EvaluationScoreRead(**score),
            )
        except TimeoutError:
            answer = f"模型调用超时：{display_name} 超过 {settings.model_request_timeout} 秒未返回"
            score = rule_evaluator.evaluate(prompt=prompt, answer="")
            return ModelResponseRead(
                id=index,
                modelName=display_name,
                provider=provider,
                answer=answer,
                latencyMs=0,
                outputTokens=0,
                estimatedCost=0,
                status="failed",
                score=EvaluationScoreRead(**score),
            )
        except (httpx.HTTPError, ValueError, KeyError, IndexError) as error:
            answer = f"模型调用失败：{error}"
            score = rule_evaluator.evaluate(prompt=prompt, answer="")
            return ModelResponseRead(
                id=index,
                modelName=display_name,
                provider=provider,
                answer=answer,
                latencyMs=0,
                outputTokens=0,
                estimatedCost=0,
                status="failed",
                score=EvaluationScoreRead(**score),
            )

    def _resolve_selected_models(self, model_ids: list[int]) -> list[dict[str, str | ModelClient]]:
        provider_map = self._provider_map()
        selected_ids = model_ids or [1, 2]
        selected_models = [provider_map[model_id] for model_id in selected_ids if model_id in provider_map]
        return selected_models or [provider_map[1], provider_map[2]]

    def _provider_map(self) -> dict[int, dict[str, str | ModelClient]]:
        timeout = settings.model_request_timeout
        return {
            1: {
                "provider": "deepseek",
                "display_name": settings.deepseek_model,
                "model_name": settings.deepseek_model,
                "client": OpenAICompatibleClient(
                    model_name=settings.deepseek_model,
                    base_url=settings.deepseek_base_url,
                    api_key=settings.deepseek_api_key,
                    input_price=Decimal("0"),
                    output_price=Decimal("0"),
                    timeout=timeout,
                ),
            },
            2: {
                "provider": "minimax",
                "display_name": settings.minimax_model,
                "model_name": settings.minimax_model,
                "client": OpenAICompatibleClient(
                    model_name=settings.minimax_model,
                    base_url=settings.minimax_base_url,
                    api_key=settings.minimax_api_key,
                    input_price=Decimal("0"),
                    output_price=Decimal("0"),
                    timeout=timeout,
                ),
            },
            3: {
                "provider": "zhipu",
                "display_name": settings.zhipu_model,
                "model_name": settings.zhipu_model,
                "client": OpenAICompatibleClient(
                    model_name=settings.zhipu_model,
                    base_url=settings.zhipu_base_url,
                    api_key=settings.zhipu_api_key,
                    input_price=Decimal("0"),
                    output_price=Decimal("0"),
                    timeout=timeout,
                ),
            },
        }


evaluation_service = EvaluationService()
