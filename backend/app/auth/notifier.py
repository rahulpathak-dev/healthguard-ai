import asyncio
import smtplib
from email.message import EmailMessage
from typing import Protocol
from urllib.parse import quote

from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger()


class AuthNotifier(Protocol):
    async def send_verification(self, email: str, token: str) -> None: ...
    async def send_password_reset(self, email: str, token: str) -> None: ...


class SmtpAuthNotifier:
    async def send_verification(self, email: str, token: str) -> None:
        await self._send(
            email,
            "Verify your HealthGuard AI email",
            "/auth/verify-email",
            token,
            "Use this one-time link to verify your email. It expires in 24 hours.",
        )

    async def send_password_reset(self, email: str, token: str) -> None:
        await self._send(
            email,
            "Reset your HealthGuard AI password",
            "/auth/reset-password",
            token,
            "Use this one-time link to reset your password. It expires in 30 minutes.",
        )

    async def _send(self, recipient: str, subject: str, path: str, token: str, intro: str) -> None:
        settings = get_settings()
        if not settings.smtp_host:
            logger.warning("auth_email_not_sent", reason="smtp_not_configured", recipient=recipient)
            return
        link = f"{settings.web_app_url.rstrip('/')}{path}#token={quote(token)}"
        message = EmailMessage()
        message["From"] = settings.smtp_from_email
        message["To"] = recipient
        message["Subject"] = subject
        message.set_content(f"{intro}\n\n{link}\n\nIf you did not request this, ignore this email.")
        await asyncio.to_thread(self._deliver, message)

    @staticmethod
    def _deliver(message: EmailMessage) -> None:
        settings = get_settings()
        if settings.smtp_host is None:
            return
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=10) as smtp:
            smtp.starttls()
            if settings.smtp_username and settings.smtp_password:
                smtp.login(settings.smtp_username, settings.smtp_password.get_secret_value())
            smtp.send_message(message)


notifier: AuthNotifier = SmtpAuthNotifier()
