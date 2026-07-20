from fastapi import APIRouter

from app.admin.routes import router as admin_router
from app.api.routes import health, safety
from app.auth.routes import router as auth_router
from app.chat.routes import router as chat_router
from app.dashboard.routes import router as dashboard_router
from app.emergency.routes import router as emergency_router
from app.jobs.routes import router as jobs_router
from app.medicines.routes import router as medicine_router
from app.misinformation.routes import router as misinformation_router
from app.privacy.routes import router as privacy_router
from app.profiles.routes import router as profile_router
from app.records.routes import router as record_router
from app.reminders.routes import router as reminder_router
from app.reports.routes import router as report_router
from app.sharing.routes import router as sharing_router
from app.symptoms.routes import router as symptom_router

api_router = APIRouter()
api_router.include_router(health.router, tags=["health"])
api_router.include_router(safety.router, prefix="/safety", tags=["safety"])
api_router.include_router(auth_router, prefix="/auth", tags=["authentication"])
api_router.include_router(profile_router, prefix="/profiles", tags=["health profiles"])
api_router.include_router(dashboard_router, prefix="/dashboard", tags=["dashboard"])
api_router.include_router(chat_router, prefix="/chat", tags=["health education chat"])
api_router.include_router(symptom_router, prefix="/symptoms", tags=["symptom guidance"])

api_router.include_router(medicine_router, prefix="/medicines", tags=["medicine information"])

api_router.include_router(record_router, prefix="/records", tags=["medical records"])

api_router.include_router(report_router, prefix="/reports", tags=["report explanations"])
api_router.include_router(
    reminder_router, prefix="/reminders", tags=["reminders and notifications"]
)

api_router.include_router(emergency_router, prefix="/emergency", tags=["emergency guidance"])
api_router.include_router(
    misinformation_router, prefix="/misinformation", tags=["misinformation checker"]
)

api_router.include_router(sharing_router, prefix="/sharing", tags=["doctor record sharing"])
api_router.include_router(admin_router, prefix="/admin", tags=["administration"])

api_router.include_router(privacy_router, prefix="/privacy", tags=["privacy and data controls"])
api_router.include_router(jobs_router, prefix="/jobs", tags=["jobs and observability"])
