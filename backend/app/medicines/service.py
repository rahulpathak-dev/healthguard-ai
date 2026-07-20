import difflib
import re
from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import User
from app.core.config import get_settings
from app.medicines.catalog import ALIASES, CATALOG, MedicineMonograph
from app.medicines.models import MedicineSearchHistory
from app.medicines.schemas import MedicineInformation, MedicineReference
from app.rag.service import retrieve

UNSAFE_ACTION_PATTERNS = (
    r"\b(start|stop|quit|change|increase|decrease|double|combine|mix|replace)\b",
    r"\bhow much\b",
    r"\bdos(e|age)\b",
)
SAFE_DISCLAIMER = (
    "Medicine information is educational and may not include all risks. Do not start, stop, "
    "change dosage, combine medicines, or replace professional advice based on this tool. "
    "Ask a clinician or pharmacist for guidance specific to you."
)


def normalize_query(value: str) -> str:
    return re.sub(r"[^a-z0-9 ]+", "", value.lower()).strip()


def spelling_suggestions(query: str) -> list[str]:
    choices = sorted({item.generic_name for item in CATALOG} | set(ALIASES))
    return difflib.get_close_matches(normalize_query(query), choices, n=4, cutoff=0.64)


def unsafe_action_query(query: str) -> bool:
    return any(re.search(pattern, query, flags=re.IGNORECASE) for pattern in UNSAFE_ACTION_PATTERNS)


def references(monograph: MedicineMonograph | None) -> list[MedicineReference]:
    if monograph is None:
        return []
    return [
        MedicineReference(title=title, source=source, url=url, excerpt=excerpt)
        for title, source, url, excerpt in monograph.references
    ]


async def search_medicine(db: AsyncSession, *, user: User, query: str) -> MedicineInformation:
    normalized = normalize_query(query)
    monograph = ALIASES.get(normalized)
    suggestions = [] if monograph else spelling_suggestions(query)
    evidence = await retrieve(
        db, query=f"{query} medicine drug information", user_id=user.id, limit=3
    )
    source_refs = references(monograph)
    for item in evidence.evidence:
        if item.url not in {reference.url for reference in source_refs}:
            source_refs.append(
                MedicineReference(
                    title=item.title,
                    source=item.source,
                    url=item.url,
                    excerpt=item.excerpt,
                )
            )
    unsupported = None
    if monograph is None:
        unsupported = (
            "Verified medicine details are not available in the local approved catalog for "
            "this search. "
            "Use a trusted source or ask a pharmacist."
        )
    action_warning = []
    if unsafe_action_query(query):
        action_warning.append(
            "This tool cannot advise starting, stopping, changing dosage, combining "
            "medicines, or replacing doctor advice."
        )
    info = MedicineInformation(
        query=query,
        generic_name=monograph.generic_name if monograph else None,
        brand_names=list(monograph.brand_names) if monograph else [],
        common_uses=list(monograph.common_uses) if monograph else [],
        common_side_effects=list(monograph.common_side_effects) if monograph else [],
        serious_warnings=action_warning + (list(monograph.serious_warnings) if monograph else []),
        precautions=list(monograph.precautions) if monograph else [],
        interactions=list(monograph.interactions) if monograph else [],
        storage_information=list(monograph.storage_information) if monograph else [],
        pregnancy_child_elderly_cautions=list(monograph.pregnancy_child_elderly_cautions)
        if monograph
        else [],
        spelling_suggestions=suggestions,
        source_references=source_refs,
        disclaimer=f"{get_settings().medical_disclaimer} {SAFE_DISCLAIMER}",
        unsupported_notice=unsupported,
    )
    db.add(
        MedicineSearchHistory(
            user_id=user.id,
            query=query[:160],
            normalized_query=normalized[:160],
            matched_generic_name=info.generic_name,
            source_count=len(info.source_references),
            created_at=datetime.now(UTC),
        )
    )
    return info
