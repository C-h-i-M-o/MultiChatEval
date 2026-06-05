from app.services.rule_evaluator import rule_evaluator


def test_rule_evaluator_uses_documented_weights(monkeypatch) -> None:
    monkeypatch.setattr(rule_evaluator, "_relevance", lambda _prompt, _answer: 10)
    monkeypatch.setattr(rule_evaluator, "_clarity", lambda _answer: 8)
    monkeypatch.setattr(rule_evaluator, "_format_score", lambda _prompt, _answer: 6)

    result = rule_evaluator.evaluate(prompt="测试", answer="回答" * 80)

    assert result["final"] == 9.0


def test_rule_evaluator_penalizes_long_english_answer_for_chinese_prompt() -> None:
    english_answer = (
        "This answer explains the concept in a long English paragraph. "
        "It keeps using English sentences even though the user asked in Chinese. "
        "The response may contain useful content, but the language choice makes it hard "
        "for the expected Chinese audience to read and compare."
    )

    result = rule_evaluator.evaluate(prompt="请解释什么是设计模式", answer=english_answer)

    assert result["format"] <= 5
    assert "回答以英文为主" in "；".join(result["details"]["format"])


def test_rule_evaluator_allows_english_when_user_requests_it() -> None:
    english_answer = (
        "Design patterns are reusable solutions to common software design problems. "
        "They help developers communicate intent and structure code consistently."
    )

    result = rule_evaluator.evaluate(prompt="请用英文解释什么是设计模式", answer=english_answer)

    assert result["format"] == 8


def test_rule_evaluator_returns_dimension_details() -> None:
    result = rule_evaluator.evaluate(prompt="请用表格解释设计模式", answer="设计模式|作用\n---|---\n工厂模式|创建对象")

    assert set(result["details"]) == {"relevance", "completeness", "clarity", "format", "safety"}
    assert result["details"]["format"]
