from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import require_admin
from app.db.session import get_db
from app.schemas.scoring import (
    JudgePromptGroupRead,
    JudgePromptTemplatePayload,
    JudgePromptTemplateRead,
    JudgePromptValidationRead,
    RuleDictionaryRead,
    RuleTermListRead,
    RuleTermPayload,
    RuleTermRead,
    RuleTermStatusPayload,
)
from app.services.scoring_config_service import ScoringConfigNotFoundError, scoring_config_service

router = APIRouter(dependencies=[Depends(require_admin)])


@router.get("/rule-dictionaries", response_model=list[RuleDictionaryRead])
async def list_rule_dictionaries(db: AsyncSession = Depends(get_db)) -> list[RuleDictionaryRead]:
    return await scoring_config_service.list_rule_dictionaries(db)


@router.get("/rule-terms", response_model=RuleTermListRead)
async def list_rule_terms(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, alias="pageSize", ge=1, le=100),
    keyword: str | None = Query(default=None, max_length=100),
    dictionary_type: str | None = Query(default=None, alias="dictionaryType"),
    category: str | None = None,
    enabled: bool | None = None,
    db: AsyncSession = Depends(get_db),
) -> RuleTermListRead:
    return await scoring_config_service.list_rule_terms(
        db,
        page=page,
        page_size=page_size,
        keyword=keyword,
        dictionary_type=dictionary_type,
        category=category,
        enabled=enabled,
    )


@router.post("/rule-terms", response_model=RuleTermRead, status_code=status.HTTP_201_CREATED)
async def create_rule_term(payload: RuleTermPayload, db: AsyncSession = Depends(get_db)) -> RuleTermRead:
    try:
        return await scoring_config_service.create_rule_term(db, payload)
    except ScoringConfigNotFoundError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error)) from error


@router.put("/rule-terms/{term_id}", response_model=RuleTermRead)
async def update_rule_term(term_id: int, payload: RuleTermPayload, db: AsyncSession = Depends(get_db)) -> RuleTermRead:
    try:
        return await scoring_config_service.update_rule_term(db, term_id, payload)
    except ScoringConfigNotFoundError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error)) from error


@router.patch("/rule-terms/{term_id}/status", response_model=RuleTermRead)
async def set_rule_term_status(term_id: int, payload: RuleTermStatusPayload, db: AsyncSession = Depends(get_db)) -> RuleTermRead:
    try:
        return await scoring_config_service.set_rule_term_status(db, term_id, payload.enabled)
    except ScoringConfigNotFoundError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error)) from error


@router.delete("/rule-terms/{term_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_rule_term(term_id: int, db: AsyncSession = Depends(get_db)) -> None:
    try:
        await scoring_config_service.delete_rule_term(db, term_id)
    except ScoringConfigNotFoundError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error)) from error


@router.get("/judge-prompt-groups", response_model=list[JudgePromptGroupRead])
async def list_judge_prompt_groups(db: AsyncSession = Depends(get_db)) -> list[JudgePromptGroupRead]:
    return await scoring_config_service.list_judge_prompt_groups(db)


@router.get("/judge-prompt-templates", response_model=list[JudgePromptTemplateRead])
async def list_judge_prompt_templates(db: AsyncSession = Depends(get_db)) -> list[JudgePromptTemplateRead]:
    return await scoring_config_service.list_judge_prompt_templates(db)


@router.put("/judge-prompt-templates/{template_id}", response_model=JudgePromptTemplateRead)
async def update_judge_prompt_template(
    template_id: int,
    payload: JudgePromptTemplatePayload,
    db: AsyncSession = Depends(get_db),
) -> JudgePromptTemplateRead:
    try:
        return await scoring_config_service.update_judge_prompt_template(db, template_id, payload)
    except ScoringConfigNotFoundError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error)) from error


@router.post("/judge-prompt-groups/{group_id}/validate", response_model=JudgePromptValidationRead)
async def validate_judge_prompt_group(group_id: int, db: AsyncSession = Depends(get_db)) -> JudgePromptValidationRead:
    try:
        return await scoring_config_service.validate_judge_prompt_group(db, group_id)
    except ScoringConfigNotFoundError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error)) from error
