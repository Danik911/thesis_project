"""Focused tests for L8 retrieval enhancements: metadata boost and query augmentation."""

from __future__ import annotations

from main.src.lims import rag_loader


def test_build_augmented_queries_adds_domain_expansions() -> None:
    query = "ACS_DYE identity control meta components"
    variants = rag_loader._build_augmented_queries(query, max_queries=4)

    assert len(variants) >= 2
    assert variants[0] == query
    assert any("ctl" in v.lower() or "metadata" in v.lower() for v in variants)


def test_metadata_boost_rewards_file_token_matches() -> None:
    query_tokens = rag_loader._tokens_for_matching("ACS_DYE identity control")

    boosted = rag_loader._metadata_boost(
        {
            "source_file": "AND_ACS_DYE-LAB-2499.xlsx",
            "sheet_name": "Component",
            "is_priority": True,
        },
        query_tokens,
        priority_sheet_boost=0.15,
        token_match_boost=0.2,
    )

    baseline = rag_loader._metadata_boost(
        {
            "source_file": "FRE_UNRELATED-LAB-0001.xlsx",
            "sheet_name": "Other",
            "is_priority": False,
        },
        query_tokens,
        priority_sheet_boost=0.15,
        token_match_boost=0.2,
    )

    assert boosted > baseline
