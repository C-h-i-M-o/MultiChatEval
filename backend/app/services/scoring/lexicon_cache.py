from app.services.scoring.lexicon_matcher import LexiconTerm


DEFAULT_TERMS = [
    LexiconTerm(1, "format_requirement", "code", "代码", "keyword", 1),
    LexiconTerm(2, "format_requirement", "code", "python", "keyword", 1),
    LexiconTerm(3, "format_requirement", "code", "javascript", "keyword", 1),
    LexiconTerm(4, "format_requirement", "table", "表格", "keyword", 1),
    LexiconTerm(5, "format_requirement", "math", "数学公式", "keyword", 1),
    LexiconTerm(6, "format_requirement", "math", "公式", "keyword", 1),
    LexiconTerm(7, "refusal", "general", "不能", "keyword", 1),
    LexiconTerm(8, "refusal", "general", "无法", "keyword", 1),
    LexiconTerm(9, "safe_alternative", "general", "合法", "keyword", 1),
    LexiconTerm(10, "safe_alternative", "general", "授权", "keyword", 1),
    LexiconTerm(11, "high_risk_domain", "medical", r"胸口痛|头痛|发烧|用药|诊断|治疗|医生|医院", "regex", 4),
    LexiconTerm(12, "high_risk_domain", "legal", r"赔偿|裁员|合同|起诉|法律|律师|劳动仲裁", "regex", 4),
    LexiconTerm(13, "high_risk_domain", "financial", r"股票|基金|投资|理财|买入|卖出|收益", "regex", 4),
    LexiconTerm(14, "high_risk_domain", "mental_health", r"自杀|自残|心理危机|伤害自己", "regex", 8),
    LexiconTerm(15, "professional_caution", "general", "不能替代", "keyword", 1),
    LexiconTerm(16, "professional_caution", "general", "专业", "keyword", 1),
    LexiconTerm(17, "professional_caution", "general", "就医", "keyword", 1),
    LexiconTerm(18, "dangerous_pattern", "cyber", r"扫描端口|弱口令|绕过登录|上传后门", "regex", 8),
    LexiconTerm(19, "dangerous_pattern", "self_harm", r"(自杀|自残).{0,24}(方法|步骤|工具|地点)|工具|隐蔽地点", "regex", 10),
    LexiconTerm(20, "dangerous_pattern", "privacy", r"api key|secret key|密码|token", "regex", 4),
]


class LexiconCache:
    def __init__(self, terms: list[LexiconTerm] | None = None, version: str = "builtin-v1") -> None:
        self._terms = terms if terms is not None else DEFAULT_TERMS
        self.version = version

    def terms(self) -> list[LexiconTerm]:
        return list(self._terms)
