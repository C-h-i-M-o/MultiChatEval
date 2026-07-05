from app.services import text_analysis
from app.services.scoring.lexicon_matcher import LexiconTerm


FORMAT_REQUIREMENT_MARKERS = {
    "code": [
        "代码",
        "函数",
        "脚本",
        "实现",
        "示例代码",
        "伪代码",
        "python",
        "javascript",
        "typescript",
        "java",
        "go",
        "golang",
        "rust",
        "c",
        "c++",
        "c#",
        "php",
        "ruby",
        "swift",
        "kotlin",
        "scala",
        "r",
        "matlab",
        "dart",
        "lua",
        "perl",
        "objective-c",
        "shell",
        "bash",
        "powershell",
        "sql",
        "html",
        "css",
        "vue",
        "react",
        "svelte",
        "angular",
        "node",
        "express",
        "fastapi",
        "django",
        "flask",
        "spring",
        "gin",
        "laravel",
        "rails",
        "pytest",
        "vitest",
        "jest",
        "单元测试",
        "测试用例",
    ],
    "table": ["表格", "表", "二维表", "表头", "列", "行", "markdown 表", "用表展示", "对照表", "矩阵"],
    "math": ["数学公式", "公式", "准确率", "召回率", "精确率", "F1", "均值", "方差", "概率", "复杂度", "O(", "LaTeX"],
    "json": ["json", "schema", "字段", "对象", "数组", "payload", "接口返回", "结构化"],
    "list": ["列表", "要点", "步骤", "清单", "bullet", "条目", "分点", "checklist"],
    "markdown": ["markdown", "标题", "小标题", "引用块", "代码块"],
    "diagram": ["流程图", "时序图", "架构图", "ER 图", "UML", "mermaid"],
}


def _term_severity(dictionary_type: str, category: str) -> int:
    if dictionary_type == "dangerous_pattern":
        return {
            "self_harm": 10,
            "weapons": 10,
            "sexual_minors": 10,
            "cyber": 8,
            "illegal": 8,
            "hate_harassment": 7,
            "privacy": 4,
            "dangerous_prompt": 6,
        }.get(category, 6)
    if dictionary_type == "high_risk_domain":
        return 8 if category == "mental_health" else 4
    return 1


def _build_default_terms() -> list[LexiconTerm]:
    terms: list[LexiconTerm] = []
    seen: set[tuple[str, str, str, str]] = set()

    def add(dictionary_type: str, category: str, content: str, match_type: str = "keyword") -> None:
        key = (dictionary_type, category, content, match_type)
        if key in seen:
            return
        seen.add(key)
        terms.append(
            LexiconTerm(
                id=len(terms) + 1,
                dictionary_type=dictionary_type,
                category=category,
                content=content,
                match_type=match_type,
                severity=_term_severity(dictionary_type, category),
            )
        )

    for category, markers in FORMAT_REQUIREMENT_MARKERS.items():
        for marker in markers:
            add("format_requirement", category, marker)

    for intent, markers in text_analysis.INTENT_MARKERS.items():
        for marker in markers:
            add("intent_marker", intent, marker)

    for marker in text_analysis.REFUSAL_MARKERS:
        add("refusal", "general", marker)

    for marker in text_analysis.SAFE_ALTERNATIVE_MARKERS:
        add("safe_alternative", "general", marker)

    for category, patterns in text_analysis.HIGH_RISK_DOMAIN_PATTERNS.items():
        for pattern in patterns:
            add("high_risk_domain", category, pattern, "regex")

    for marker in text_analysis.PROFESSIONAL_CAUTION_MARKERS:
        add("professional_caution", "general", marker)

    for pattern in text_analysis.DANGEROUS_PROMPT_PATTERNS:
        add("dangerous_pattern", "dangerous_prompt", pattern, "regex")
    for category, patterns in text_analysis.ACTIONABLE_HARM_PATTERNS.items():
        for pattern in patterns:
            add("dangerous_pattern", category, pattern, "regex")
    for pattern in text_analysis.SENSITIVE_DATA_PATTERNS:
        add("dangerous_pattern", "privacy", pattern, "regex")

    return terms


DEFAULT_TERMS = _build_default_terms()


class LexiconCache:
    def __init__(self, terms: list[LexiconTerm] | None = None, version: str = "builtin-v1") -> None:
        self._terms = terms if terms is not None else DEFAULT_TERMS
        self.version = version

    def terms(self) -> list[LexiconTerm]:
        return list(self._terms)
