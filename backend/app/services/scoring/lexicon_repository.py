from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.scoring import RuleDictionary, RuleTerm
from app.services.scoring.lexicon_matcher import LexiconTerm


class LexiconRepository:
    async def list_enabled_terms(self, db: AsyncSession) -> list[LexiconTerm]:
        result = await db.execute(
            select(RuleTerm, RuleDictionary.dictionary_type)
            .join(RuleDictionary, RuleDictionary.id == RuleTerm.dictionary_id)
            .where(RuleTerm.enabled.is_(True), RuleDictionary.enabled.is_(True))
            .order_by(RuleTerm.id)
        )
        return [
            LexiconTerm(
                id=term.id,
                dictionary_type=dictionary_type,
                category=term.category,
                content=term.content,
                match_type=term.match_type,
                severity=term.severity,
                enabled=term.enabled,
            )
            for term, dictionary_type in result.all()
        ]


lexicon_repository = LexiconRepository()
