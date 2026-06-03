import asyncio
from collections.abc import AsyncIterator
from datetime import datetime
from decimal import Decimal

import httpx
from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.adapters.base import ModelRequest
from app.adapters.openai_compatible import OpenAICompatibleClient
from app.core.config import settings
from app.models.evaluation import EvaluationResult, EvaluationTask
from app.models.feedback import UserFeedback
from app.models.model_config import ModelConfig
from app.models.response import ModelResponse
from app.schemas.evaluation import (
    EvaluationFeedbackRead,
    EvaluationScoreRead,
    FeedbackToggleRead,
    EvaluationTaskCreate,
    EvaluationTaskListItemRead,
    EvaluationTaskListRead,
    EvaluationTaskRead,
    ModelResponseRead,
)
from app.services.model_config_service import RuntimeModelConfig, model_config_service
from app.services.rule_evaluator import rule_evaluator


BUILTIN_SYSTEM_PROMPT = """你是一个严谨、清晰、负责任的 AI 助手。请基于用户问题直接作答，并遵守以下要求：

1. 优先回答用户真正的问题，不要回避核心诉求。
2. 保持中文表达清晰、自然、结构化；如果用户明确要求其他语言，则按用户要求回复。
3. 如果问题适合分步骤、分点或对比说明，请使用清晰的段落、列表或表格组织答案。
4. 如果用户要求代码、JSON、表格、步骤、方案或对比，请严格遵守对应格式。
5. 不要编造不确定的信息。遇到无法确认的事实、数据、时间、版本或来源时，请明确说明不确定性。
6. 对涉及医疗、法律、金融、安全等高风险内容的问题，请给出谨慎、一般性的信息，并提醒用户寻求专业意见。
7. 避免输出违法、有害、危险操作指导、隐私泄露、凭据泄露或恶意攻击相关内容。
8. 回答应兼顾完整性和简洁性：必要时解释原因、给出示例或注意事项，但不要无意义冗长。
9. 如果用户问题本身含糊，请先基于最合理的理解回答，并指出关键假设；不要反复追问导致无法推进。

用户问题如下："""


class EvaluationTaskNotFoundError(Exception):
    pass


class EvaluationService:
    async def create_task(self, payload: EvaluationTaskCreate, db: AsyncSession) -> EvaluationTaskRead:
        selected_models = await model_config_service.resolve_runtime_models(db, payload.model_ids)
        task_id = await self._create_task_record(db, payload)
        responses = await self._collect_model_responses(
            db=db,
            task_id=task_id,
            prompt=payload.prompt,
            models=selected_models,
            extra_body=self._thinking_extra_body(payload),
        )
        task_status = "completed" if any(response.status == "success" for response in responses) else "failed"
        await self._finish_task_record(db, task_id, task_status)

        return EvaluationTaskRead(taskId=task_id, status=task_status, prompt=payload.prompt, responses=responses)

    async def stream_task_events(
        self,
        payload: EvaluationTaskCreate,
        db: AsyncSession,
    ) -> AsyncIterator[dict[str, object]]:
        selected_models = await model_config_service.resolve_runtime_models(db, payload.model_ids)
        task_id = await self._create_task_record(db, payload)
        model_ids = [model.id for model in selected_models]
        extra_body = self._thinking_extra_body(payload)
        responses: list[ModelResponseRead] = []

        yield {
            "type": "task_started",
            "taskId": task_id,
            "prompt": payload.prompt,
            "modelIds": model_ids,
            "total": len(selected_models),
        }

        tasks = [
            asyncio.create_task(self._call_model(prompt=payload.prompt, model=model, extra_body=extra_body))
            for model in selected_models
        ]
        for completed_task in asyncio.as_completed(tasks):
            response = await completed_task
            persisted_response = await self._persist_response(db, task_id, response)
            responses.append(persisted_response)
            yield {"type": "model_response", "response": persisted_response}

        task_status = "completed" if any(response.status == "success" for response in responses) else "failed"
        await self._finish_task_record(db, task_id, task_status)
        yield {
            "type": "task_completed",
            "task": EvaluationTaskRead(taskId=task_id, status=task_status, prompt=payload.prompt, responses=responses),
        }

    async def get_task(self, task_id: int, db: AsyncSession) -> EvaluationTaskRead:
        result = await db.execute(self._task_detail_query().where(EvaluationTask.id == task_id))
        task = result.scalar_one_or_none()
        if task is None:
            raise EvaluationTaskNotFoundError("评测任务不存在")

        return self._serialize_task(task)

    async def list_tasks(self, db: AsyncSession, page: int, page_size: int) -> EvaluationTaskListRead:
        normalized_page = max(page, 1)
        normalized_page_size = min(max(page_size, 1), 100)
        offset = (normalized_page - 1) * normalized_page_size

        total_result = await db.execute(select(func.count(EvaluationTask.id)))
        total = int(total_result.scalar_one())
        rows_result = await db.execute(
            select(EvaluationTask, func.count(ModelResponse.id))
            .outerjoin(ModelResponse, ModelResponse.task_id == EvaluationTask.id)
            .group_by(EvaluationTask.id)
            .order_by(EvaluationTask.created_at.desc(), EvaluationTask.id.desc())
            .offset(offset)
            .limit(normalized_page_size)
        )

        items = [
            EvaluationTaskListItemRead(
                taskId=task.id,
                status=task.status,
                prompt=task.prompt,
                createdAt=task.created_at,
                completedAt=task.completed_at,
                responseCount=int(response_count),
            )
            for task, response_count in rows_result.all()
        ]

        return EvaluationTaskListRead(
            items=items,
            total=total,
            page=normalized_page,
            pageSize=normalized_page_size,
        )

    async def toggle_feedback(
        self,
        response_id: int,
        feedback_type: str,
        comment: str | None,
        db: AsyncSession,
    ) -> FeedbackToggleRead:
        result = await db.execute(select(ModelResponse.id).where(ModelResponse.id == response_id))
        if result.scalar_one_or_none() is None:
            raise EvaluationTaskNotFoundError("模型回答不存在")

        existing_result = await db.execute(
            select(UserFeedback).where(
                UserFeedback.response_id == response_id,
                UserFeedback.feedback_type == feedback_type,
                UserFeedback.user_id.is_(None),
            )
        )
        existing_feedback = existing_result.scalar_one_or_none()

        if existing_feedback is None:
            db.add(
                UserFeedback(
                    user_id=None,
                    response_id=response_id,
                    feedback_type=feedback_type,
                    comment=comment,
                )
            )
            active = True
        else:
            await db.delete(existing_feedback)
            active = False

        await db.commit()
        feedback = await self._feedback_summary(db, response_id)

        return FeedbackToggleRead(
            responseId=response_id,
            feedbackType=feedback_type,
            active=active,
            feedback=feedback,
        )

    async def _collect_model_responses(
        self,
        db: AsyncSession,
        task_id: int,
        prompt: str,
        models: list[RuntimeModelConfig],
        extra_body: dict[str, object],
    ) -> list[ModelResponseRead]:
        tasks = [self._call_model(prompt=prompt, model=model, extra_body=extra_body) for model in models]
        responses = await asyncio.gather(*tasks)
        persisted_responses = []
        for response in responses:
            persisted_responses.append(await self._persist_response(db, task_id, response))
        return persisted_responses

    async def _call_model(
        self,
        prompt: str,
        model: RuntimeModelConfig,
        extra_body: dict[str, object],
    ) -> ModelResponseRead:
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
                client.chat(
                    ModelRequest(
                        prompt=self._model_prompt(prompt),
                        model_name=model.model_name,
                        max_tokens=model.max_tokens,
                        extra_body=extra_body,
                    )
                ),
                timeout=settings.model_request_timeout + 5,
            )
            estimated_cost = float(client.estimate_cost(reply.usage))
            score = rule_evaluator.evaluate(prompt=prompt, answer=reply.answer)

            return ModelResponseRead(
                id=model.id,
                modelConfigId=model.id,
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
                modelConfigId=model.id,
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
                modelConfigId=model.id,
                modelName=model.display_name,
                provider=model.provider_name,
                answer=answer,
                latencyMs=0,
                outputTokens=0,
                estimatedCost=0,
                status="failed",
                score=EvaluationScoreRead(**score),
            )

    def _thinking_extra_body(self, payload: EvaluationTaskCreate) -> dict[str, object]:
        thinking_type = "enabled" if payload.enable_thinking else "disabled"
        return {"thinking": {"type": thinking_type}}

    def _model_prompt(self, prompt: str) -> str:
        return f"{BUILTIN_SYSTEM_PROMPT}\n\n{prompt.strip()}"

    async def _create_task_record(self, db: AsyncSession, payload: EvaluationTaskCreate) -> int:
        task = EvaluationTask(
            conversation_id=payload.conversation_id,
            prompt=payload.prompt,
            status="pending",
        )
        db.add(task)
        await db.commit()
        return task.id

    async def _persist_response(
        self,
        db: AsyncSession,
        task_id: int,
        response: ModelResponseRead,
    ) -> ModelResponseRead:
        answer_text = response.answer if response.status == "success" else ""
        error_message = None if response.status == "success" else response.answer
        response_record = ModelResponse(
            task_id=task_id,
            model_config_id=response.model_config_id,
            answer_text=answer_text,
            latency_ms=response.latency_ms,
            input_tokens=0,
            output_tokens=response.output_tokens,
            estimated_cost=Decimal(str(response.estimated_cost)),
            status=response.status,
            error_message=error_message,
        )
        db.add(response_record)
        await db.flush()

        score = response.score
        db.add(
            EvaluationResult(
                response_id=response_record.id,
                relevance_score=Decimal(str(score.relevance)),
                completeness_score=Decimal(str(score.completeness)),
                clarity_score=Decimal(str(score.clarity)),
                format_score=Decimal(str(score.format)),
                safety_score=Decimal(str(score.safety)),
                rule_score=Decimal(str(score.final)),
                final_score=Decimal(str(score.final)),
            )
        )
        await db.commit()

        return ModelResponseRead(
            id=response_record.id,
            modelConfigId=response.model_config_id,
            modelName=response.model_name,
            provider=response.provider,
            answer=response.answer,
            latencyMs=response.latency_ms,
            outputTokens=response.output_tokens,
            estimatedCost=response.estimated_cost,
            status=response.status,
            score=response.score,
            feedback=EvaluationFeedbackRead(),
        )

    async def _finish_task_record(self, db: AsyncSession, task_id: int, status: str) -> None:
        result = await db.execute(select(EvaluationTask).where(EvaluationTask.id == task_id))
        task = result.scalar_one_or_none()
        if task is None:
            raise EvaluationTaskNotFoundError("评测任务不存在")

        task.status = status
        task.completed_at = datetime.utcnow()
        await db.commit()

    def _task_detail_query(self) -> Select[tuple[EvaluationTask]]:
        return select(EvaluationTask).options(
            selectinload(EvaluationTask.responses)
            .selectinload(ModelResponse.model_config)
            .selectinload(ModelConfig.provider),
            selectinload(EvaluationTask.responses).selectinload(ModelResponse.evaluation_result),
            selectinload(EvaluationTask.responses).selectinload(ModelResponse.feedback),
        )

    def _serialize_task(self, task: EvaluationTask) -> EvaluationTaskRead:
        responses = sorted(task.responses, key=lambda response: (response.created_at, response.id))
        return EvaluationTaskRead(
            taskId=task.id,
            status=task.status,
            prompt=task.prompt,
            responses=[self._serialize_response(task.prompt, response) for response in responses],
        )

    def _serialize_response(self, prompt: str, response: ModelResponse) -> ModelResponseRead:
        model_config = response.model_config
        provider = model_config.provider if model_config is not None else None
        answer = response.answer_text if response.status == "success" else response.error_message or response.answer_text
        score = self._serialize_score(response.evaluation_result, prompt, response.answer_text)

        return ModelResponseRead(
            id=response.id,
            modelConfigId=response.model_config_id,
            modelName=model_config.display_name if model_config is not None else "未知模型",
            provider=provider.name if provider is not None else "unknown",
            answer=answer,
            latencyMs=response.latency_ms,
            outputTokens=response.output_tokens,
            estimatedCost=float(response.estimated_cost),
            status=response.status,
            score=score,
            feedback=self._serialize_feedback(response.feedback),
        )

    def _serialize_score(self, result: EvaluationResult | None, prompt: str = "", answer: str = "") -> EvaluationScoreRead:
        details = rule_evaluator.evaluate(prompt=prompt, answer=answer).get("details", {})
        if result is None:
            return EvaluationScoreRead(relevance=0, completeness=0, clarity=0, format=0, safety=0, final=0, details=details)

        return EvaluationScoreRead(
            relevance=float(result.relevance_score),
            completeness=float(result.completeness_score),
            clarity=float(result.clarity_score),
            format=float(result.format_score),
            safety=float(result.safety_score),
            final=float(result.final_score),
            details=details,
        )

    def _serialize_feedback(self, feedback_rows: list[UserFeedback]) -> EvaluationFeedbackRead:
        like_count = sum(1 for feedback in feedback_rows if feedback.feedback_type == "like")
        accepted_count = sum(1 for feedback in feedback_rows if feedback.feedback_type == "accepted")
        return EvaluationFeedbackRead(
            liked=like_count > 0,
            accepted=accepted_count > 0,
            likeCount=like_count,
            acceptedCount=accepted_count,
        )

    async def _feedback_summary(self, db: AsyncSession, response_id: int) -> EvaluationFeedbackRead:
        result = await db.execute(
            select(UserFeedback.feedback_type, func.count(UserFeedback.id))
            .where(UserFeedback.response_id == response_id)
            .group_by(UserFeedback.feedback_type)
        )
        counts = {feedback_type: int(count) for feedback_type, count in result.all()}
        like_count = counts.get("like", 0)
        accepted_count = counts.get("accepted", 0)
        return EvaluationFeedbackRead(
            liked=like_count > 0,
            accepted=accepted_count > 0,
            likeCount=like_count,
            acceptedCount=accepted_count,
        )


evaluation_service = EvaluationService()
