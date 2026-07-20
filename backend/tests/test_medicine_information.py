import re

from app.medicines.catalog import ALIASES, CATALOG
from app.medicines.service import normalize_query, spelling_suggestions, unsafe_action_query


def test_generic_and_brand_names_map_to_same_verified_monograph() -> None:
    assert ALIASES["tylenol"].generic_name == "acetaminophen"
    assert ALIASES["acetaminophen"].generic_name == "acetaminophen"
    assert ALIASES["advil"].generic_name == "ibuprofen"


def test_spelling_suggestions_support_common_misspelling() -> None:
    suggestions = spelling_suggestions("ibuprofenn")
    assert "ibuprofen" in suggestions


def test_normalization_removes_punctuation_without_case_sensitivity() -> None:
    assert normalize_query("  Advil!!! ") == "advil"


def test_unsafe_action_queries_are_detected() -> None:
    for query in (
        "should I stop metformin",
        "can I double my dose",
        "combine ibuprofen and aspirin",
        "how much acetaminophen",
    ):
        assert unsafe_action_query(query)


def test_curated_monographs_do_not_display_specific_dosage_instructions() -> None:
    dosage_pattern = re.compile(r"\btake \d+|\b\d+\s?(mg|mcg|g|ml)\b", flags=re.IGNORECASE)
    for item in CATALOG:
        fields = (
            item.common_uses
            + item.common_side_effects
            + item.serious_warnings
            + item.precautions
            + item.interactions
            + item.storage_information
            + item.pregnancy_child_elderly_cautions
        )
        assert not any(dosage_pattern.search(text) for text in fields)


def test_every_verified_monograph_has_source_reference() -> None:
    for item in CATALOG:
        assert item.references
        for _, source, url, _ in item.references:
            assert source == "MedlinePlus"
            assert url.startswith("https://medlineplus.gov/")
