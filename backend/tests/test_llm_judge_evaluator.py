import pytest

from app.services.llm_judge_evaluator import llm_judge_evaluator


def test_judge_prompt_requires_plain_json_without_think() -> None:
    prompt = llm_judge_evaluator._judge_prompt(prompt="问题", answer="回答")

    assert "第一个字符必须是 {" in prompt
    assert "最后一个字符必须是 }" in prompt
    assert "不要输出 <think>" in prompt


def test_parse_json_accepts_think_block_before_json() -> None:
    result = llm_judge_evaluator._parse_json(
        '<think>评审思考过程</think>\n{"score": 8, "strengths": [], "weaknesses": [], "recommendation": "可用"}'
    )

    assert result["score"] == 8


def test_parse_json_extracts_first_complete_object_with_extra_text() -> None:
    result = llm_judge_evaluator._parse_json(
        '{"score": 7, "strengths": []}\n额外解释文字\n{"score": 1}'
    )

    assert result["score"] == 7


def test_parse_json_reports_empty_output_summary() -> None:
    with pytest.raises(ValueError, match="输出摘要：<空>"):
        llm_judge_evaluator._parse_json("   ")
