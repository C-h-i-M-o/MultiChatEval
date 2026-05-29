import re


class RuleEvaluator:
    def evaluate(self, prompt: str, answer: str) -> dict[str, float]:
        relevance = self._relevance(prompt, answer)
        completeness = min(len(answer) / 120, 1) * 10
        clarity = self._clarity(answer)
        format_score = self._format_score(prompt, answer)
        safety = 10
        final = relevance * 0.3 + completeness * 0.25 + clarity * 0.2 + format_score * 0.15 + safety * 0.1

        return {
            "relevance": round(relevance, 2),
            "completeness": round(completeness, 2),
            "clarity": round(clarity, 2),
            "format": round(format_score, 2),
            "safety": round(safety, 2),
            "final": round(final, 2),
        }

    def _relevance(self, prompt: str, answer: str) -> float:
        prompt_words = set(re.findall(r"[\u4e00-\u9fa5A-Za-z0-9]+", prompt))
        if not prompt_words:
            return 5
        answer_words = set(re.findall(r"[\u4e00-\u9fa5A-Za-z0-9]+", answer))
        return min(len(prompt_words & answer_words) / len(prompt_words) * 10, 10)

    def _clarity(self, answer: str) -> float:
        score = 5
        if "\n" in answer:
            score += 2
        if any(marker in answer for marker in ["-", "*", "1.", "```", "|"]):
            score += 2
        if len(answer) > 20:
            score += 1
        return min(score, 10)

    def _format_score(self, prompt: str, answer: str) -> float:
        if "表格" in prompt:
            return 10 if "|" in answer else 4
        if "代码" in prompt:
            return 10 if "```" in answer else 4
        return 8


rule_evaluator = RuleEvaluator()
