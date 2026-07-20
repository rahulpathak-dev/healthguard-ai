import uuid

import pytest
from fastapi import HTTPException

from app.dashboard.schemas import DashboardView
from app.dashboard.service import LIST_LIMIT, build_dashboard


class EmptyRows:
    def unique(self) -> "EmptyRows":
        return self

    def all(self) -> list[object]:
        return []


class EmptyDashboardSession:
    def __init__(self) -> None:
        self.execute_calls = 0
        self.scalar_calls = 0

    async def execute(self, statement: object) -> EmptyRows:
        self.execute_calls += 1
        return EmptyRows()

    async def scalar(self, statement: object) -> object:
        self.scalar_calls += 1
        raise AssertionError("No dashboard source query should run without an authorized profile")


@pytest.mark.asyncio
async def test_inaccessible_profile_stops_before_dashboard_queries() -> None:
    db = EmptyDashboardSession()
    with pytest.raises(HTTPException) as exc:
        await build_dashboard(db, uuid.uuid4(), uuid.uuid4())  # type: ignore[arg-type]
    assert exc.value.status_code == 404
    assert db.execute_calls == 1
    assert db.scalar_calls == 0


@pytest.mark.asyncio
async def test_dashboard_without_profiles_has_useful_empty_contract() -> None:
    db = EmptyDashboardSession()
    result = await build_dashboard(db, uuid.uuid4(), None)  # type: ignore[arg-type]
    assert result.active_profile is None
    assert result.upcoming_reminders == []
    assert result.recent_records == []
    assert result.education
    assert db.execute_calls == 1


def test_dashboard_contract_excludes_sensitive_content() -> None:
    fields = set(DashboardView.model_fields)
    forbidden = {
        "private_notes",
        "emergency_contacts",
        "allergies",
        "medicines",
        "conditions",
        "report_content",
        "conversation_messages",
        "file_url",
    }
    assert fields.isdisjoint(forbidden)


def test_dashboard_lists_are_strictly_bounded() -> None:
    assert LIST_LIMIT <= 5
