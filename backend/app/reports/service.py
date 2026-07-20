import uuid
from datetime import UTC, datetime

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import User
from app.core.config import get_settings
from app.dashboard.models import MedicalRecord, ReportAnalysis
from app.records.service import accessible_record
from app.records.storage import storage
from app.reports.ocr import extract_text_from_bytes, extract_values
from app.reports.schemas import ReportAnalysisCreate, ReportExplanation


async def create_analysis(
    db: AsyncSession, *, user: User, payload: ReportAnalysisCreate
) -> ReportAnalysis:
    record = await accessible_record(db, record_id=payload.record_id, user_id=user.id)
    status = (
        "pending"
        if record.status == "available" and record.scan_status == "clean"
        else "awaiting_scan"
    )
    analysis = ReportAnalysis(
        profile_id=record.profile_id,
        owner_user_id=user.id,
        record_id=record.id,
        title=payload.title or f"Explanation for {record.title}",
        status=status,
        ocr_status="queued" if status == "pending" else "blocked_until_scan_clean",
        ocr_confidence=None,
        extracted_values_json=[],
        explanation_json={},
        error_message=None,
        created_at=datetime.now(UTC),
    )
    db.add(analysis)
    await db.flush()
    return analysis


async def owned_analysis(
    db: AsyncSession, analysis_id: uuid.UUID, user_id: uuid.UUID
) -> ReportAnalysis:
    analysis = await db.scalar(
        select(ReportAnalysis).where(
            ReportAnalysis.id == analysis_id,
            ReportAnalysis.owner_user_id == user_id,
        )
    )
    if analysis is None:
        raise HTTPException(status_code=404, detail="Analysis not found")
    return analysis


async def process_analysis(db: AsyncSession, analysis_id: uuid.UUID) -> ReportAnalysis:
    analysis = await db.get(ReportAnalysis, analysis_id)
    if analysis is None or analysis.record_id is None:
        raise HTTPException(status_code=404, detail="Analysis not found")
    record = await db.get(MedicalRecord, analysis.record_id)
    if record is None or record.deleted_at is not None:
        analysis.status = "failed"
        analysis.ocr_status = "source_missing"
        analysis.error_message = "Source report is unavailable."
        return analysis
    if record.status != "available" or record.scan_status != "clean":
        analysis.status = "awaiting_scan"
        analysis.ocr_status = "blocked_until_scan_clean"
        analysis.error_message = "OCR will run after malware scanning marks the file clean."
        return analysis
    try:
        target = storage()._resolve(record.storage_path)
        text, confidence = extract_text_from_bytes(target.read_bytes(), record.mime_type)
        if not text.strip():
            analysis.status = "failed"
            analysis.ocr_status = "unsupported_file_type"
            analysis.error_message = "No OCR engine is configured for this file type yet."
            return analysis
        values = extract_values(text, confidence)
        explanation = ReportExplanation(
            summary=(
                "This explanation summarizes values that could be read from the report. "
                "It does not diagnose, confirm, or rule out any condition."
            ),
            ocr_uncertainty=(
                f"OCR confidence is {confidence:.0%}. Review the original report because OCR can "
                "misread numbers, units, and labels."
            ),
            values=values,
            questions_for_doctor=[
                "Which values matter most for my history and symptoms?",
                "Do any results need repeat testing or follow-up?",
                "Could medicines, hydration, pregnancy, age, or recent illness affect "
                "these values?",
                "Are the report's reference ranges appropriate for me?",
            ],
            disclaimer=get_settings().medical_disclaimer,
        )
        analysis.status = "complete"
        analysis.ocr_status = "complete"
        analysis.ocr_confidence = confidence
        analysis.extracted_values_json = [item.model_dump(mode="json") for item in values]
        analysis.explanation_json = explanation.model_dump(mode="json")
        analysis.error_message = None
        analysis.completed_at = datetime.now(UTC)
    except Exception as exc:
        analysis.status = "failed"
        analysis.ocr_status = "failed"
        analysis.error_message = type(exc).__name__
    return analysis
