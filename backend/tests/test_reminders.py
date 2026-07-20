from datetime import UTC, datetime

import pytest
from fastapi import HTTPException

from app.reminders.service import next_due, unsafe_medicine_wording, validate_timezone


def test_recurrence_next_due_is_predictable() -> None:
    due = datetime(2026, 7, 13, 9, tzinfo=UTC)
    assert next_due(due, "daily").day == 14
    assert next_due(due, "weekly").day == 20
    assert next_due(due, "none") is None


def test_timezone_validation_rejects_unknown_zone() -> None:
    assert validate_timezone("Asia/Calcutta") == "Asia/Calcutta"
    with pytest.raises(HTTPException):
        validate_timezone("Mars/Olympus")


def test_medicine_reminders_block_unsafe_wording() -> None:
    assert unsafe_medicine_wording("double dose tonight", "medicine_schedule")
    assert not unsafe_medicine_wording("take medicine as prescribed", "medicine_schedule")
    assert not unsafe_medicine_wording("double check appointment time", "doctor_appointment")
