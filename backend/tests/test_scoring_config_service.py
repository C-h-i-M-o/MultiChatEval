from app.services import text_analysis
from app.services.scoring_config_service import (
    RULE_SEED_FILE,
    build_default_rule_seed,
    load_default_rule_seed_from_file,
    plan_default_rule_deduplication,
)


def test_default_rule_seed_is_persisted_for_first_deploy_import() -> None:
    dictionaries, terms = load_default_rule_seed_from_file()

    assert RULE_SEED_FILE.exists()
    assert len(dictionaries) == 7
    assert len(terms) == 390


def test_default_rule_seed_exposes_builtin_terms_for_admin_panel() -> None:
    dictionaries, terms = build_default_rule_seed()

    dictionary_types = {item["dictionary_type"] for item in dictionaries}

    assert {"format_requirement", "dangerous_pattern", "high_risk_domain"}.issubset(dictionary_types)
    assert len(terms) >= 20
    assert all(term["dictionary_type"] in dictionary_types for term in terms)


def test_default_rule_seed_covers_all_text_analysis_rule_sources() -> None:
    dictionaries, terms = build_default_rule_seed()
    dictionary_types = {item["dictionary_type"] for item in dictionaries}
    terms_by_dictionary = {
        dictionary_type: [item for item in terms if item["dictionary_type"] == dictionary_type]
        for dictionary_type in dictionary_types
    }

    assert "intent_marker" in dictionary_types
    for intent, markers in text_analysis.INTENT_MARKERS.items():
        seeded_markers = {item["content"] for item in terms_by_dictionary["intent_marker"] if item["category"] == intent}
        assert set(markers).issubset(seeded_markers)

    assert len(terms_by_dictionary["dangerous_pattern"]) >= sum(
        len(patterns) for patterns in text_analysis.ACTIONABLE_HARM_PATTERNS.values()
    )
    assert len(terms_by_dictionary["high_risk_domain"]) >= sum(
        len(patterns) for patterns in text_analysis.HIGH_RISK_DOMAIN_PATTERNS.values()
    )
    assert len(terms_by_dictionary["professional_caution"]) >= len(text_analysis.PROFESSIONAL_CAUTION_MARKERS)


def test_default_rule_seed_expands_common_admin_lexicons() -> None:
    _, terms = build_default_rule_seed()
    terms_by_dictionary = {}
    for item in terms:
        terms_by_dictionary.setdefault(item["dictionary_type"], []).append(item)

    assert len(terms) >= 180
    assert {"translate", "rewrite", "extract", "classify", "evaluate"}.issubset(
        {item["category"] for item in terms_by_dictionary["intent_marker"]}
    )
    assert {"cyber", "illegal", "privacy", "hate_harassment", "sexual_minors"}.issubset(
        {item["category"] for item in terms_by_dictionary["dangerous_pattern"]}
    )


def test_default_rule_deduplication_keeps_oldest_dictionary_and_term() -> None:
    plan = plan_default_rule_deduplication(
        dictionaries=[
            {"id": 1, "dictionary_type": "dangerous_pattern"},
            {"id": 2, "dictionary_type": "dangerous_pattern"},
            {"id": 3, "dictionary_type": "high_risk_domain"},
        ],
        terms=[
            {"id": 10, "dictionary_id": 1, "category": "privacy", "content": "token", "match_type": "keyword"},
            {"id": 11, "dictionary_id": 2, "category": "privacy", "content": "token", "match_type": "keyword"},
            {"id": 12, "dictionary_id": 2, "category": "cyber", "content": "扫描端口", "match_type": "keyword"},
        ],
    )

    assert plan.dictionary_id_replacements == {2: 1}
    assert plan.term_ids_to_delete == [11]
    assert plan.term_dictionary_updates == {12: 1}
