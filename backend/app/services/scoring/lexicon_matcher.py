import re
from dataclasses import dataclass


@dataclass(frozen=True)
class LexiconTerm:
    id: int
    dictionary_type: str
    category: str
    content: str
    match_type: str
    severity: int
    enabled: bool = True


class LexiconMatcher:
    def match(self, text: str, terms: list[LexiconTerm], dictionary_type: str | None = None) -> list[LexiconTerm]:
        matched_terms = []
        for term in terms:
            if not term.enabled:
                continue
            if dictionary_type is not None and term.dictionary_type != dictionary_type:
                continue
            if self._matches(text, term):
                matched_terms.append(term)
        return matched_terms

    def _matches(self, text: str, term: LexiconTerm) -> bool:
        if term.match_type == "regex":
            return re.search(term.content, text, flags=re.IGNORECASE) is not None
        return term.content.lower() in text.lower()
