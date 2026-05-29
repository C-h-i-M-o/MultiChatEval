from app.schemas.evaluation import EvaluationScoreRead, EvaluationTaskCreate, EvaluationTaskRead, ModelResponseRead
from app.services.rule_evaluator import rule_evaluator


class EvaluationService:
    async def create_task(self, payload: EvaluationTaskCreate) -> EvaluationTaskRead:
        demo_answers = [
            ("DeepSeek", "deepseek", "这是一个模拟回答。后续会接入真实模型适配器，并保存耗时、成本和评分。"),
            ("Qwen", "qwen", "这是另一个模拟回答，用于展示多模型对比卡片和规则评分结果。"),
        ]
        responses: list[ModelResponseRead] = []

        for index, (model_name, provider, answer) in enumerate(demo_answers, start=1):
            score = rule_evaluator.evaluate(prompt=payload.prompt, answer=answer)
            responses.append(
                ModelResponseRead(
                    id=index,
                    modelName=model_name,
                    provider=provider,
                    answer=answer,
                    latencyMs=900 + index * 360,
                    outputTokens=len(answer),
                    estimatedCost=0.002 * index,
                    status="success",
                    score=EvaluationScoreRead(**score),
                )
            )

        return EvaluationTaskRead(taskId=1, status="completed", prompt=payload.prompt, responses=responses)

    async def get_task(self, task_id: int) -> EvaluationTaskRead:
        return EvaluationTaskRead(taskId=task_id, status="completed", prompt="示例问题", responses=[])


evaluation_service = EvaluationService()
