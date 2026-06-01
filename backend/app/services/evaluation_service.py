import asyncio

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from app.adapters.base import ModelRequest
from app.adapters.openai_compatible import OpenAICompatibleClient
from app.core.config import settings
from app.schemas.evaluation import EvaluationScoreRead, EvaluationTaskCreate, EvaluationTaskRead, ModelResponseRead
from app.services.model_config_service import RuntimeModelConfig, model_config_service
from app.services.rule_evaluator import rule_evaluator


class EvaluationService:
    async def create_task(self, payload: EvaluationTaskCreate, db: AsyncSession) -> EvaluationTaskRead:
        selected_models = await model_config_service.resolve_runtime_models(db, payload.model_ids)
        tasks = [self._call_model(prompt=payload.prompt, model=model) for model in selected_models]
        responses = await asyncio.gather(*tasks)
        task_status = "completed" if any(response.status == "success" for response in responses) else "failed"

        return EvaluationTaskRead(taskId=1, status=task_status, prompt=payload.prompt, responses=responses)

    async def get_task(self, task_id: int) -> EvaluationTaskRead:
        return EvaluationTaskRead(taskId=task_id, status="completed", prompt="示例问题", responses=[])

    async def _call_model(self, prompt: str, model: RuntimeModelConfig) -> ModelResponseRead:
        client = OpenAICompatibleClient(
            model_name=model.model_name,
            base_url=model.base_url,
            api_key=model.api_key,
            input_price=model.input_price,
            output_price=model.output_price,
            timeout=settings.model_request_timeout,
            extra_body=model.extra_body,
        )

        try:
            reply = await asyncio.wait_for(
                client.chat(ModelRequest(prompt=prompt, model_name=model.model_name, max_tokens=model.max_tokens)),
                timeout=settings.model_request_timeout + 5,
            )
            estimated_cost = float(client.estimate_cost(reply.usage))
            score = rule_evaluator.evaluate(prompt=prompt, answer=reply.answer)

            return ModelResponseRead(
                id=model.id,
                modelName=model.display_name,
                provider=model.provider_name,
                answer=reply.answer,
                latencyMs=reply.latency_ms,
                outputTokens=reply.usage.output_tokens,
                estimatedCost=estimated_cost,
                status="success",
                score=EvaluationScoreRead(**score),
            )
        except TimeoutError:
            answer = f"模型调用超时：{model.display_name} 超过 {settings.model_request_timeout} 秒未返回"
            score = rule_evaluator.evaluate(prompt=prompt, answer="")
            return ModelResponseRead(
                id=model.id,
                modelName=model.display_name,
                provider=model.provider_name,
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
                id=model.id,
                modelName=model.display_name,
                provider=model.provider_name,
                answer=answer,
                latencyMs=0,
                outputTokens=0,
                estimatedCost=0,
                status="failed",
                score=EvaluationScoreRead(**score),
            )


evaluation_service = EvaluationService()
