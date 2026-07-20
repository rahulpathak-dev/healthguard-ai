# Authentication and authorization

HealthGuard uses server-managed browser sessions. Access JWTs live for 15 minutes by default and are stored in an HTTP-only cookie. Refresh credentials are opaque random values in a narrower-path HTTP-only cookie; only their SHA-256 digests are persisted.

Every refresh rotates the credential and session row. Reuse of a replaced credential revokes its entire token family. Logout, password reset, role change, per-device revocation, and logout-all update persisted session state, so access checks reject revoked sessions.

Passwords use Argon2 through `pwdlib`. Login failures use generic responses, per-IP and per-account Redis limits, and a 15-minute database lock after five consecutive failures. Registration always assigns `user`; only an authenticated administrator can assign `doctor` or `admin`, and role changes revoke all target sessions.

Verification and reset secrets are single-use, hashed in storage, and expire after 24 hours and 30 minutes respectively. Configure SMTP variables to deliver links. Tokens use URL fragments so they do not enter server access logs. Security logs contain user/session IDs and event types, never passwords or token values.

For production, set a unique `TOKEN_SECRET`, enable `COOKIE_SECURE`, use HTTPS, configure the intended cookie domain and exact CORS origins, run Alembic migrations, and place the API behind a trusted proxy configuration. Create the first administrator through a controlled deployment process?not public registration.

Google OAuth support is isolated behind the `OAuthProvider` protocol. One-time state is stored in Redis for ten minutes and provider adapters must use authorization code flow with PKCE, validate issuer/audience/signature/nonce, require a provider-verified email, link by provider subject, and assign only the regular user role.

## Endpoints

- `POST /api/v1/auth/register`, `/login`, `/refresh`, `/logout`, `/logout-all`
- `POST /api/v1/auth/verify-email`, `/forgot-password`, `/reset-password`
- `GET /api/v1/auth/me`, `/sessions`
- `DELETE /api/v1/auth/sessions/{session_id}`
- `PATCH /api/v1/auth/users/{user_id}/role` (admin only)
