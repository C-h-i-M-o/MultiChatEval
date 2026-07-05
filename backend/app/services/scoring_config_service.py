import asyncio
import json
from dataclasses import dataclass
from pathlib import Path

from sqlalchemy import delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.scoring import JudgePromptGroup, JudgePromptTemplate, RuleDictionary, RuleTerm
from app.schemas.scoring import (
    JudgePromptGroupRead,
    JudgePromptTemplatePayload,
    JudgePromptTemplateRead,
    JudgePromptValidationRead,
    RuleDictionaryRead,
    RuleTermListRead,
    RuleTermPayload,
    RuleTermRead,
)
from app.services.scoring.lexicon_cache import DEFAULT_TERMS


RULE_SEED_FILE = Path(__file__).resolve().parent / "scoring" / "default_rule_seed.json"

DEFAULT_DICTIONARY_NAMES = {
    "format_requirement": "格式要求词典",
    "intent_marker": "用户意图词典",
    "refusal": "拒答表达词典",
    "safe_alternative": "安全替代表达词典",
    "high_risk_domain": "高风险领域词典",
    "professional_caution": "专业提醒词典",
    "dangerous_pattern": "危险输出词典",
}

_rule_seed_lock = asyncio.Lock()


class ScoringConfigNotFoundError(Exception):
    pass


@dataclass(frozen=True)
class RuleSeedDeduplicationPlan:
    dictionary_id_replacements: dict[int, int]
    term_ids_to_delete: list[int]
    term_dictionary_updates: dict[int, int]


def _int_field(row: dict[str, object], field: str) -> int:
    value = row[field]
    if not isinstance(value, int):
        raise TypeError(f"{field} 必须是整数")
    return value


def _str_field(row: dict[str, object], field: str) -> str:
    value = row[field]
    if not isinstance(value, str):
        raise TypeError(f"{field} 必须是字符串")
    return value


def plan_default_rule_deduplication(
    *,
    dictionaries: list[dict[str, object]],
    terms: list[dict[str, object]],
) -> RuleSeedDeduplicationPlan:
    keeper_by_type: dict[str, int] = {}
    dictionary_id_replacements: dict[int, int] = {}
    for dictionary in sorted(dictionaries, key=lambda item: _int_field(item, "id")):
        dictionary_id = _int_field(dictionary, "id")
        dictionary_type = _str_field(dictionary, "dictionary_type")
        keeper_id = keeper_by_type.setdefault(dictionary_type, dictionary_id)
        if dictionary_id != keeper_id:
            dictionary_id_replacements[dictionary_id] = keeper_id

    seen_terms: dict[tuple[int, str, str, str], int] = {}
    term_ids_to_delete: list[int] = []
    term_dictionary_updates: dict[int, int] = {}
    for term in sorted(terms, key=lambda item: _int_field(item, "id")):
        term_id = _int_field(term, "id")
        dictionary_id = _int_field(term, "dictionary_id")
        canonical_dictionary_id = dictionary_id_replacements.get(dictionary_id, dictionary_id)
        key = (
            canonical_dictionary_id,
            _str_field(term, "category"),
            _str_field(term, "content"),
            _str_field(term, "match_type"),
        )
        if key in seen_terms:
            term_ids_to_delete.append(term_id)
            continue
        seen_terms[key] = term_id
        if canonical_dictionary_id != dictionary_id:
            term_dictionary_updates[term_id] = canonical_dictionary_id

    return RuleSeedDeduplicationPlan(
        dictionary_id_replacements=dictionary_id_replacements,
        term_ids_to_delete=term_ids_to_delete,
        term_dictionary_updates=term_dictionary_updates,
    )


def build_default_rule_seed() -> tuple[list[dict[str, str]], list[dict[str, str | int | bool]]]:
    if RULE_SEED_FILE.exists():
        return load_default_rule_seed_from_file()

    dictionary_types = sorted({term.dictionary_type for term in DEFAULT_TERMS})
    dictionaries = [
        {
            "dictionary_type": dictionary_type,
            "name": DEFAULT_DICTIONARY_NAMES.get(dictionary_type, dictionary_type),
            "version": "builtin-v1",
        }
        for dictionary_type in dictionary_types
    ]
    terms = [
        {
            "dictionary_type": term.dictionary_type,
            "category": term.category,
            "content": term.content,
            "match_type": term.match_type,
            "severity": term.severity,
            "enabled": term.enabled,
        }
        for term in DEFAULT_TERMS
    ]
    return dictionaries, terms


def load_default_rule_seed_from_file() -> tuple[list[dict[str, str]], list[dict[str, str | int | bool]]]:
    raw_payload = json.loads(RULE_SEED_FILE.read_text(encoding="utf-8"))
    dictionaries = raw_payload.get("dictionaries")
    terms = raw_payload.get("terms")
    if not isinstance(dictionaries, list) or not isinstance(terms, list):
        raise ValueError("默认规则词表种子文件格式不正确")

    return [_normalize_seed_dictionary(item) for item in dictionaries], [_normalize_seed_term(item) for item in terms]


def _normalize_seed_dictionary(item: object) -> dict[str, str]:
    if not isinstance(item, dict):
        raise ValueError("默认规则词典必须是对象")
    return {
        "dictionary_type": _seed_str(item, "dictionary_type"),
        "name": _seed_str(item, "name"),
        "version": _seed_str(item, "version"),
    }


def _normalize_seed_term(item: object) -> dict[str, str | int | bool]:
    if not isinstance(item, dict):
        raise ValueError("默认规则词条必须是对象")
    return {
        "dictionary_type": _seed_str(item, "dictionary_type"),
        "category": _seed_str(item, "category"),
        "content": _seed_str(item, "content"),
        "match_type": _seed_str(item, "match_type"),
        "severity": _seed_int(item, "severity"),
        "enabled": _seed_bool(item, "enabled"),
    }


def _seed_str(item: dict[object, object], field: str) -> str:
    value = item.get(field)
    if not isinstance(value, str) or not value:
        raise ValueError(f"默认规则词表字段 {field} 必须是非空字符串")
    return value


def _seed_int(item: dict[object, object], field: str) -> int:
    value = item.get(field)
    if not isinstance(value, int):
        raise ValueError(f"默认规则词表字段 {field} 必须是整数")
    return value


def _seed_bool(item: dict[object, object], field: str) -> bool:
    value = item.get(field)
    if not isinstance(value, bool):
        raise ValueError(f"默认规则词表字段 {field} 必须是布尔值")
    return value


class ScoringConfigService:
    async def list_rule_dictionaries(self, db: AsyncSession) -> list[RuleDictionaryRead]:
        await self._ensure_default_rule_seed(db)
        result = await db.execute(select(RuleDictionary).order_by(RuleDictionary.id))
        return [self._dictionary_read(item) for item in result.scalars().all()]

    async def list_rule_terms(
        self,
        db: AsyncSession,
        *,
        page: int,
        page_size: int,
        keyword: str | None,
        dictionary_type: str | None,
        category: str | None,
        enabled: bool | None,
    ) -> RuleTermListRead:
        await self._ensure_default_rule_seed(db)
        statement = select(RuleTerm).options(selectinload(RuleTerm.dictionary)).join(RuleDictionary)
        count_statement = select(func.count(RuleTerm.id)).join(RuleDictionary)
        filters = []
        if keyword:
            filters.append(RuleTerm.content.like(f"%{keyword}%"))
        if dictionary_type:
            filters.append(RuleDictionary.dictionary_type == dictionary_type)
        if category:
            filters.append(RuleTerm.category == category)
        if enabled is not None:
            filters.append(RuleTerm.enabled.is_(enabled))
        for item in filters:
            statement = statement.where(item)
            count_statement = count_statement.where(item)
        total = int((await db.execute(count_statement)).scalar_one())
        rows = await db.execute(statement.order_by(RuleTerm.id.desc()).offset((page - 1) * page_size).limit(page_size))
        return RuleTermListRead(
            items=[self._term_read(item) for item in rows.scalars().all()],
            total=total,
            page=page,
            pageSize=page_size,
        )

    async def create_rule_term(self, db: AsyncSession, payload: RuleTermPayload) -> RuleTermRead:
        dictionary = await self._get_dictionary(db, payload.dictionary_id)
        term = RuleTerm(
            dictionary_id=dictionary.id,
            category=payload.category,
            content=payload.content,
            match_type=payload.match_type,
            severity=payload.severity,
            enabled=payload.enabled,
        )
        db.add(term)
        await db.commit()
        await db.refresh(term, attribute_names=["dictionary"])
        return self._term_read(term)

    async def update_rule_term(self, db: AsyncSession, term_id: int, payload: RuleTermPayload) -> RuleTermRead:
        term = await self._get_term(db, term_id)
        await self._get_dictionary(db, payload.dictionary_id)
        term.dictionary_id = payload.dictionary_id
        term.category = payload.category
        term.content = payload.content
        term.match_type = payload.match_type
        term.severity = payload.severity
        term.enabled = payload.enabled
        await db.commit()
        await db.refresh(term, attribute_names=["dictionary"])
        return self._term_read(term)

    async def set_rule_term_status(self, db: AsyncSession, term_id: int, enabled: bool) -> RuleTermRead:
        term = await self._get_term(db, term_id)
        term.enabled = enabled
        await db.commit()
        await db.refresh(term, attribute_names=["dictionary"])
        return self._term_read(term)

    async def delete_rule_term(self, db: AsyncSession, term_id: int) -> None:
        term = await self._get_term(db, term_id)
        await db.delete(term)
        await db.commit()

    async def _ensure_default_rule_seed(self, db: AsyncSession) -> None:
        async with _rule_seed_lock:
            await self._ensure_default_rule_seed_locked(db)

    async def _ensure_default_rule_seed_locked(self, db: AsyncSession) -> None:
        changed = await self._deduplicate_rule_seed(db)
        dictionary_rows = (await db.execute(select(RuleDictionary))).scalars().all()
        dictionary_by_type = {item.dictionary_type: item for item in dictionary_rows}
        default_dictionaries, default_terms = build_default_rule_seed()

        for item in default_dictionaries:
            dictionary_type = str(item["dictionary_type"])
            if dictionary_type in dictionary_by_type:
                continue
            dictionary = RuleDictionary(
                dictionary_type=dictionary_type,
                name=str(item["name"]),
                version=str(item["version"]),
                enabled=True,
            )
            db.add(dictionary)
            dictionary_by_type[dictionary_type] = dictionary
            changed = True

        if changed:
            await db.flush()

        existing_term_rows = await db.execute(select(RuleTerm, RuleDictionary.dictionary_type).join(RuleDictionary))
        existing_terms = {
            (dictionary_type, term.category, term.content, term.match_type)
            for term, dictionary_type in existing_term_rows.all()
        }
        for item in default_terms:
            dictionary_type = str(item["dictionary_type"])
            key = (dictionary_type, str(item["category"]), str(item["content"]), str(item["match_type"]))
            if key in existing_terms:
                continue
            dictionary = dictionary_by_type[dictionary_type]
            db.add(
                RuleTerm(
                    dictionary_id=dictionary.id,
                    category=str(item["category"]),
                    content=str(item["content"]),
                    match_type=str(item["match_type"]),
                    severity=int(item["severity"]),
                    enabled=bool(item["enabled"]),
                )
            )
            changed = True

        if changed:
            await db.commit()

    async def _deduplicate_rule_seed(self, db: AsyncSession) -> bool:
        dictionary_rows = (await db.execute(select(RuleDictionary.id, RuleDictionary.dictionary_type))).all()
        term_rows = (
            await db.execute(
                select(RuleTerm.id, RuleTerm.dictionary_id, RuleTerm.category, RuleTerm.content, RuleTerm.match_type)
            )
        ).all()
        plan = plan_default_rule_deduplication(
            dictionaries=[{"id": row.id, "dictionary_type": row.dictionary_type} for row in dictionary_rows],
            terms=[
                {
                    "id": row.id,
                    "dictionary_id": row.dictionary_id,
                    "category": row.category,
                    "content": row.content,
                    "match_type": row.match_type,
                }
                for row in term_rows
            ],
        )

        changed = False
        if plan.term_ids_to_delete:
            await db.execute(delete(RuleTerm).where(RuleTerm.id.in_(plan.term_ids_to_delete)))
            changed = True

        for term_id, dictionary_id in plan.term_dictionary_updates.items():
            await db.execute(update(RuleTerm).where(RuleTerm.id == term_id).values(dictionary_id=dictionary_id))
            changed = True

        duplicate_dictionary_ids = list(plan.dictionary_id_replacements)
        if duplicate_dictionary_ids:
            await db.execute(delete(RuleDictionary).where(RuleDictionary.id.in_(duplicate_dictionary_ids)))
            changed = True

        if changed:
            await db.flush()
        return changed

    async def list_judge_prompt_groups(self, db: AsyncSession) -> list[JudgePromptGroupRead]:
        result = await db.execute(select(JudgePromptGroup).order_by(JudgePromptGroup.id))
        return [self._group_read(item) for item in result.scalars().all()]

    async def list_judge_prompt_templates(self, db: AsyncSession) -> list[JudgePromptTemplateRead]:
        result = await db.execute(
            select(JudgePromptTemplate).options(selectinload(JudgePromptTemplate.group)).order_by(JudgePromptTemplate.id)
        )
        return [self._template_read(item) for item in result.scalars().all()]

    async def update_judge_prompt_template(
        self,
        db: AsyncSession,
        template_id: int,
        payload: JudgePromptTemplatePayload,
    ) -> JudgePromptTemplateRead:
        template = await self._get_template(db, template_id)
        template.content = payload.content
        template.output_schema = payload.output_schema
        template.enabled = payload.enabled
        await db.commit()
        await db.refresh(template, attribute_names=["group"])
        return self._template_read(template)

    async def validate_judge_prompt_group(self, db: AsyncSession, group_id: int) -> JudgePromptValidationRead:
        group = await self._get_group(db, group_id)
        enabled_templates = [template for template in group.templates if template.enabled]
        issues = []
        if len(enabled_templates) != 3:
            issues.append("启用模板数量必须正好为 3")
        versions = {group.version}
        schemas = {str(template.output_schema) for template in enabled_templates}
        if len(schemas) > 1:
            issues.append("三个模板必须使用同一 output_schema")
        for template in enabled_templates:
            if "{{ user_prompt }}" not in template.content or "{{ candidate_answer }}" not in template.content:
                issues.append(f"{template.code} 缺少必要占位符")
        if len(versions) != 1:
            issues.append("模板必须属于同一版本")
        return JudgePromptValidationRead(valid=not issues, issues=issues)

    async def _get_dictionary(self, db: AsyncSession, dictionary_id: int) -> RuleDictionary:
        result = await db.execute(select(RuleDictionary).where(RuleDictionary.id == dictionary_id))
        dictionary = result.scalar_one_or_none()
        if dictionary is None:
            raise ScoringConfigNotFoundError("词典不存在")
        return dictionary

    async def _get_term(self, db: AsyncSession, term_id: int) -> RuleTerm:
        result = await db.execute(select(RuleTerm).options(selectinload(RuleTerm.dictionary)).where(RuleTerm.id == term_id))
        term = result.scalar_one_or_none()
        if term is None:
            raise ScoringConfigNotFoundError("词条不存在")
        return term

    async def _get_group(self, db: AsyncSession, group_id: int) -> JudgePromptGroup:
        result = await db.execute(
            select(JudgePromptGroup).options(selectinload(JudgePromptGroup.templates)).where(JudgePromptGroup.id == group_id)
        )
        group = result.scalar_one_or_none()
        if group is None:
            raise ScoringConfigNotFoundError("Prompt Group 不存在")
        return group

    async def _get_template(self, db: AsyncSession, template_id: int) -> JudgePromptTemplate:
        result = await db.execute(
            select(JudgePromptTemplate).options(selectinload(JudgePromptTemplate.group)).where(JudgePromptTemplate.id == template_id)
        )
        template = result.scalar_one_or_none()
        if template is None:
            raise ScoringConfigNotFoundError("Prompt 模板不存在")
        return template

    def _dictionary_read(self, item: RuleDictionary) -> RuleDictionaryRead:
        return RuleDictionaryRead(
            id=item.id,
            dictionaryType=item.dictionary_type,
            name=item.name,
            version=item.version,
            enabled=item.enabled,
        )

    def _term_read(self, item: RuleTerm) -> RuleTermRead:
        return RuleTermRead(
            id=item.id,
            dictionaryId=item.dictionary_id,
            dictionaryType=item.dictionary.dictionary_type,
            category=item.category,
            content=item.content,
            matchType=item.match_type,
            severity=item.severity,
            enabled=item.enabled,
            updatedAt=item.updated_at.isoformat(),
        )

    def _group_read(self, item: JudgePromptGroup) -> JudgePromptGroupRead:
        return JudgePromptGroupRead(
            id=item.id,
            code=item.code,
            name=item.name,
            rubric=item.rubric,
            version=item.version,
            enabled=item.enabled,
        )

    def _template_read(self, item: JudgePromptTemplate) -> JudgePromptTemplateRead:
        return JudgePromptTemplateRead(
            id=item.id,
            groupId=item.group_id,
            groupCode=item.group.code,
            code=item.code,
            content=item.content,
            outputSchema=item.output_schema,
            enabled=item.enabled,
            updatedAt=item.updated_at.isoformat(),
        )


scoring_config_service = ScoringConfigService()
