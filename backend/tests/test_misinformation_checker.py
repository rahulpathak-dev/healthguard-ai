from app.misinformation.service import claim_hash, classify, summarize_claim


def test_harmful_claims_are_flagged_without_source_confidence() -> None:
    verdict = classify("Stop insulin and use a miracle cure", evidence_count=5, top_score=0.9)
    assert verdict == "potentially_harmful"


def test_absolute_claims_with_evidence_are_still_misleading() -> None:
    verdict = classify("This supplement always cures coughs", evidence_count=3, top_score=0.7)
    assert verdict == "misleading"


def test_no_evidence_does_not_become_unsupported_certainty() -> None:
    assert classify("A rare claim", evidence_count=0, top_score=0.0) == "insufficient_evidence"


def test_claim_summary_and_hash_are_bounded() -> None:
    claim = "x" * 700
    assert len(summarize_claim(claim)) == 500
    assert len(claim_hash("health claim")) == 64
