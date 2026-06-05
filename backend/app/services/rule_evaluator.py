import re


class RuleEvaluator:
    def evaluate(self, prompt: str, answer: str) -> dict[str, object]:
        relevance = self._relevance(prompt, answer)
        completeness = min(len(answer) / 120, 1) * 10
        clarity = self._clarity(answer)
        format_score = self._format_score(prompt, answer)
        safety = 10
        final = relevance * 0.2 + completeness * 0.3 + clarity * 0.2 + format_score * 0.15 + safety * 0.15

        return {
            "relevance": round(relevance, 2),
            "completeness": round(completeness, 2),
            "clarity": round(clarity, 2),
            "format": round(format_score, 2),
            "safety": round(safety, 2),
            "final": round(final, 2),
            "details": {
                "relevance": self._relevance_details(prompt, answer, relevance),
                "completeness": self._completeness_details(answer, completeness),
                "clarity": self._clarity_details(answer, clarity),
                "format": self._format_details(prompt, answer, format_score),
                "safety": ["当前未命中安全扣分规则，安全性按默认满分计算"],
            },
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
        language_penalty = self._long_english_answer_penalty(prompt, answer)
        if "表格" in prompt:
            score = 10 if "|" in answer else 4
            return min(score, language_penalty)
        if "代码" in prompt:
            score = 10 if "```" in answer else 4
            return min(score, language_penalty)
        return min(8, language_penalty)

    def _long_english_answer_penalty(self, prompt: str, answer: str) -> float:
        if self._allows_english_answer(prompt):
            return 10

        chinese_chars = len(re.findall(r"[\u4e00-\u9fff]", answer))
        english_letters = len(re.findall(r"[A-Za-z]", answer))
        if english_letters < 120:
            return 10

        total_language_chars = chinese_chars + english_letters
        if total_language_chars == 0:
            return 10

        english_ratio = english_letters / total_language_chars
        if english_ratio >= 0.7 and chinese_chars < 40:
            return 5
        return 10

    def _relevance_details(self, prompt: str, answer: str, score: float) -> list[str]:
        prompt_words = set(re.findall(r"[\u4e00-\u9fa5A-Za-z0-9]+", prompt))
        answer_words = set(re.findall(r"[\u4e00-\u9fa5A-Za-z0-9]+", answer))
        if not prompt_words:
            return ["问题关键词不足，相关性使用中性分"]

        matched_words = sorted(prompt_words & answer_words)
        details = [f"关键词覆盖 {len(matched_words)}/{len(prompt_words)}，相关性得分 {round(score, 2)}"]
        if matched_words:
            details.append(f"已覆盖关键词：{'、'.join(matched_words[:6])}")
        return details

    def _completeness_details(self, answer: str, score: float) -> list[str]:
        length = len(answer)
        if length >= 120:
            return [f"回答长度 {length}，达到完整性满分区间"]
        return [f"回答长度 {length}，按 120 字符目标折算完整性得分 {round(score, 2)}"]

    def _clarity_details(self, answer: str, score: float) -> list[str]:
        details = [f"清晰度得分 {round(score, 2)}"]
        if "\n" in answer:
            details.append("回答包含换行，结构更清晰")
        if any(marker in answer for marker in ["-", "*", "1.", "```", "|"]):
            details.append("回答包含列表、代码块或表格等结构化标记")
        if len(answer) > 20:
            details.append("回答长度超过 20 字符，表达有基本展开")
        return details

    def _format_details(self, prompt: str, answer: str, score: float) -> list[str]:
        details = []
        if "表格" in prompt:
            details.append("满足表格要求" if "|" in answer else "问题要求表格，但回答未包含 Markdown 表格标记")
        elif "代码" in prompt:
            details.append("满足代码块要求" if "```" in answer else "问题要求代码，但回答未包含代码块标记")
        else:
            details.append("未发现强制表格或代码格式要求，使用默认格式分")

        if self._long_english_answer_penalty(prompt, answer) < 10:
            details.append("回答以英文为主，且用户未要求英文输出，格式分扣减")
        details.append(f"格式得分 {round(score, 2)}")
        return details

    def _allows_english_answer(self, prompt: str) -> bool:
        return any(
            marker in prompt.lower()
            for marker in [
                "英文",
                "英语",
                "english",
                "translate",
                "翻译成英",
                "用英",
                "中英",
                "双语",
            ]
        )


rule_evaluator = RuleEvaluator()
