import uuid
from datetime import UTC, date, datetime

from fastapi import HTTPException
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.dashboard.models import Conversation, MedicalRecord, Notification, Reminder, ReportAnalysis
from app.dashboard.schemas import (
    AnalysisSummary,
    ConversationSummary,
    DashboardView,
    EducationCard,
    EmergencyShortcut,
    FamilySummary,
    NotificationSummary,
    PrivacySummary,
    ProfileOption,
    QuickAction,
    RecordSummary,
    ReminderSummary,
)
from app.profiles.models import HealthProfile, PermissionLevel, ProfileKind, ProfilePermission

LIST_LIMIT = 5


def age_on(birth_date: date | None) -> int | None:
    if birth_date is None:
        return None
    today = date.today()
    return (
        today.year
        - birth_date.year
        - ((today.month, today.day) < (birth_date.month, birth_date.day))
    )


async def profile_options(
    db: AsyncSession, user_id: uuid.UUID
) -> list[tuple[HealthProfile, bool, bool]]:
    permission = ProfilePermission
    rows = (
        (
            await db.execute(
                select(HealthProfile, permission.level)
                .outerjoin(
                    permission,
                    (permission.profile_id == HealthProfile.id)
                    & (permission.grantee_user_id == user_id),
                )
                .where(
                    or_(
                        HealthProfile.owner_user_id == user_id,
                        permission.grantee_user_id == user_id,
                    )
                )
                .order_by(HealthProfile.kind, HealthProfile.display_name)
            )
        )
        .unique()
        .all()
    )
    return [
        (
            profile,
            profile.owner_user_id == user_id,
            profile.owner_user_id == user_id or level == PermissionLevel.EDIT,
        )
        for profile, level in rows
    ]


def option(profile: HealthProfile, owner: bool, edit: bool) -> ProfileOption:
    return ProfileOption(
        id=profile.id,
        display_name=profile.display_name,
        kind=profile.kind.value,
        relationship=profile.relationship,
        is_owner=owner,
        can_edit=edit,
    )


async def build_dashboard(
    db: AsyncSession, user_id: uuid.UUID, selected_profile_id: uuid.UUID | None
) -> DashboardView:
    available = await profile_options(db, user_id)
    selected = None
    if selected_profile_id:
        selected = next((entry for entry in available if entry[0].id == selected_profile_id), None)
        if selected is None:
            raise HTTPException(status_code=404, detail="Profile not found")
    elif available:
        selected = next(
            (entry for entry in available if entry[0].kind == ProfileKind.PERSONAL), available[0]
        )

    options = [option(*entry) for entry in available]
    education = [
        EducationCard(
            slug="understanding-lab-ranges",
            title="Understanding reference ranges",
            description="Why a result outside a range does not always mean something is wrong.",
            reading_minutes=4,
        ),
        EducationCard(
            slug="prepare-for-an-appointment",
            title="Prepare for a health appointment",
            description="A practical checklist for clearer conversations with your care team.",
            reading_minutes=3,
        ),
        EducationCard(
            slug="medicine-safety-basics",
            title="Medicine safety basics",
            description="Simple habits for keeping an accurate medicine list.",
            reading_minutes=5,
        ),
    ]
    quick_actions = [
        QuickAction(label="Manage profiles", href="/profiles", available=True),
        QuickAction(label="Add medical record", href="#records", available=False),
        QuickAction(label="Ask HealthGuard AI", href="/chat", available=True),
        QuickAction(label="Create reminder", href="#reminders", available=False),
    ]
    emergency = [
        EmergencyShortcut(
            label="Emergency help",
            description="Contact local emergency services for urgent or life-threatening symptoms.",
            action="emergency-services",
        ),
        EmergencyShortcut(
            label="Prepare key details",
            description="Keep medicines, allergies, and an emergency contact ready to share.",
            action="open-profile",
        ),
    ]
    if selected is None:
        return DashboardView(
            welcome_name="there",
            profiles=options,
            active_profile=None,
            upcoming_reminders=[],
            recent_records=[],
            report_analyses=[],
            recent_conversations=[],
            notifications=[],
            unread_notification_count=0,
            family=[],
            privacy=None,
            education=education,
            quick_actions=quick_actions,
            emergency_shortcuts=emergency,
        )

    profile, is_owner, can_edit = selected
    now = datetime.now(UTC)
    reminders = (
        await db.scalars(
            select(Reminder)
            .where(
                Reminder.profile_id == profile.id,
                Reminder.status == "pending",
                Reminder.due_at >= now,
            )
            .order_by(Reminder.due_at)
            .limit(LIST_LIMIT)
        )
    ).all()
    records = (
        await db.scalars(
            select(MedicalRecord)
            .where(MedicalRecord.profile_id == profile.id)
            .order_by(MedicalRecord.created_at.desc())
            .limit(LIST_LIMIT)
        )
    ).all()
    analyses = (
        await db.scalars(
            select(ReportAnalysis)
            .where(ReportAnalysis.profile_id == profile.id)
            .order_by(ReportAnalysis.created_at.desc())
            .limit(LIST_LIMIT)
        )
    ).all()
    conversations = (
        await db.scalars(
            select(Conversation)
            .where(Conversation.profile_id == profile.id, Conversation.owner_user_id == user_id)
            .order_by(Conversation.last_message_at.desc())
            .limit(4)
        )
    ).all()
    notification_filter = (
        Notification.user_id == user_id,
        or_(Notification.profile_id.is_(None), Notification.profile_id == profile.id),
    )
    notifications = (
        await db.scalars(
            select(Notification)
            .where(*notification_filter, Notification.read_at.is_(None))
            .order_by(Notification.created_at.desc())
            .limit(LIST_LIMIT)
        )
    ).all()
    unread_count = (
        await db.scalar(
            select(func.count())
            .select_from(Notification)
            .where(*notification_filter, Notification.read_at.is_(None))
        )
        or 0
    )
    permission_count = 0
    if is_owner:
        permission_count = (
            await db.scalar(
                select(func.count())
                .select_from(ProfilePermission)
                .where(ProfilePermission.profile_id == profile.id)
            )
            or 0
        )
    family = [
        FamilySummary(
            id=item.id,
            display_name=item.display_name,
            relationship=item.relationship,
            age=age_on(item.date_of_birth),
        )
        for item, owner, _ in available
        if owner and item.kind == ProfileKind.FAMILY
    ][:8]
    privacy = PrivacySummary(
        access_label="Owned by you"
        if is_owner
        else "Shared edit access"
        if can_edit
        else "Shared view access",
        permission_count=permission_count,
        doctor_sharing_enabled=profile.allow_doctor_access,
        family_sharing_enabled=profile.share_with_family,
    )
    return DashboardView(
        welcome_name=profile.display_name,
        profiles=options,
        active_profile=option(*selected),
        upcoming_reminders=[
            ReminderSummary.model_validate(item, from_attributes=True) for item in reminders
        ],
        recent_records=[
            RecordSummary.model_validate(item, from_attributes=True) for item in records
        ],
        report_analyses=[
            AnalysisSummary.model_validate(item, from_attributes=True) for item in analyses
        ],
        recent_conversations=[
            ConversationSummary.model_validate(item, from_attributes=True) for item in conversations
        ],
        notifications=[
            NotificationSummary.model_validate(item, from_attributes=True) for item in notifications
        ],
        unread_notification_count=unread_count,
        family=family,
        privacy=privacy,
        education=education,
        quick_actions=quick_actions,
        emergency_shortcuts=emergency,
    )
