import secrets
from dataclasses import dataclass
from typing import Protocol, cast

from app.db.redis import get_redis


@dataclass(frozen=True)
class OAuthProfile:
    provider_subject: str
    email: str
    email_verified: bool


class OAuthProvider(Protocol):
    """Provider adapter boundary for authorization-code exchange and ID-token validation."""

    async def authorization_url(self, state: str, code_challenge: str) -> str: ...
    async def exchange_code(self, code: str, code_verifier: str) -> OAuthProfile: ...


async def issue_oauth_state(code_verifier_hash: str) -> str:
    state = secrets.token_urlsafe(32)
    await get_redis().setex(f"oauth:state:{state}", 600, code_verifier_hash)
    return state


async def consume_oauth_state(state: str) -> str | None:
    key = f"oauth:state:{state}"
    value = await get_redis().get(key)
    await get_redis().delete(key)
    if isinstance(value, bytes):
        return value.decode("utf-8")
    return cast(str | None, value)


# Provider callbacks must link by verified provider subject, never by an unverified email.
# New OAuth users always receive the USER role; privileged roles remain admin-assigned.
