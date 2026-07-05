from sqlalchemy import func, select
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


class ScoringConfigNotFoundError(Exception):
    pass


class ScoringConfigService:
    async def list_rule_dictionaries(self, db: AsyncSession) -> list[RuleDictionaryRead]:
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
