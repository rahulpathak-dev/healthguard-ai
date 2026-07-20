# Security Policy

HealthGuard AI is a safety-first health information platform. The project handles sensitive health-adjacent data and must be operated with privacy-by-design, least privilege, and defense-in-depth controls. This document describes how to report security issues and summarizes the security controls expected for development, deployment, and operations.

HealthGuard AI provides educational health information only. This policy does not claim HIPAA, GDPR, SOC 2, ISO 27001, or any other legal/regulatory compliance by default. Compliance depends on deployment, contracts, procedures, jurisdiction, and independent assessment.

## Supported Versions

Until a formal release process exists, security fixes are accepted for the active `main` branch only.

| Version | Supported |
| --- | --- |
| main | Yes |
| unreleased local branches | Best effort |

## Reporting a Vulnerability

Please report suspected vulnerabilities privately. Do not open a public issue containing exploit details, patient data, secrets, or proof-of-concept payloads.

Include, when safe:

- Affected component: frontend, backend, API route, Docker image, CI, AI/RAG pipeline, storage, or documentation.
- Impact and likely severity.
- Reproduction steps with sanitized data.
- Logs or screenshots with secrets, tokens, PHI, and personal data redacted.
- Suggested remediation, if known.

Expected response targets after a maintained security mailbox is configured:

- Acknowledgement: 2 business days.
- Initial triage: 5 business days.
- Critical fix target: as soon as practical, with deployment priority.

## Security Principles

- Least privilege for users, doctors, admins, jobs, and storage access.
- Explicit ownership checks on user, profile, record, conversation, report, reminder, export, and sharing resources.
- Read-only doctor access by default and only via user-generated, selected-record, unexpired, non-revoked grants.
- Admin views should minimize patient data and prefer redacted summaries.
- Secure-by-default cookies and production configuration validation.
- Short-lived signed URLs for private objects and exports.
- No public medical record object URLs.
- No plaintext passwords, refresh tokens, reset tokens, or export tokens in storage or logs.
- Medical AI output must preserve uncertainty, cite approved sources where relevant, and escalate emergencies.

## Implemented Application Controls

### Access Control and IDOR

- Authenticated API routes use server-side cookie authentication.
- Role checks gate admin and doctor endpoints.
- Profile, record, conversation, report, reminder, sharing, export, and deletion operations are scoped by owner or explicit grant.
- Missing or unauthorized resources intentionally return generic not-found style errors where appropriate.
- Doctor role alone does not grant unrestricted record access.

### Authentication and Tokens

- Passwords are hashed with Argon2-compatible password hashing.
- Access and refresh tokens are not stored in plaintext.
- Refresh token rotation and revocation are implemented.
- Logout-all and deletion flows revoke active sessions.
- Login failures are generic to reduce enumeration.
- Rate limits are applied to sensitive auth flows.

### Browser and HTTP Security

The backend sets security headers including:

- `Content-Security-Policy`
- `Strict-Transport-Security` in production
- `Referrer-Policy`
- `Permissions-Policy`
- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`
- `Cross-Origin-Opener-Policy`
- `Cross-Origin-Resource-Policy`

CORS must be configured with explicit trusted origins. Production configuration rejects localhost origins, insecure cookies, HTTP web app URLs, and enabled API docs.

### Upload and Storage Security

- File extension, MIME type, signature, filename, size, and storage path are validated.
- Uploads are quarantined until scanning/availability status permits access.
- Private storage abstraction avoids public object URLs.
- Signed download URLs are short-lived.
- Record deletion deletes private storage objects where possible and clears storage paths.

### Injection, XSS, SSRF, and Path Traversal

- SQLAlchemy query construction is used instead of string-built SQL in application code.
- Pydantic schemas use bounded fields and forbid unexpected fields in sensitive mutations where practical.
- Markdown and AI-rendered content must be treated as untrusted by the frontend.
- File path traversal is blocked by filename and storage path validation.
- Source ingestion should only use approved public-health/medical sources; arbitrary user-provided scraping is not allowed.

### AI, Prompt, and RAG Security

- AI requests pass through centralized safety analysis.
- Prompt injection patterns are classified and logged as safety events.
- Medical answers must separate evidence, general explanation, uncertainty, next steps, and disclaimer.
- RAG retrieval is restricted to approved knowledge sources.
- Misinformation checks use retrieved/source evidence; the model's own belief is not evidence.
- RAG poisoning risk is managed through source approval status, metadata, freshness review, and admin governance.

### Privacy and Consent

- Privacy Center exposes sessions, sharing grants, consent history, exports, deletion status, and preferences.
- Consent and admin actions are audit logged with minimized medical content.
- Exports use short-lived tokenized downloads and no-store responses.
- Account deletion has a configurable grace period and explicit confirmation phrase.
- The platform does not claim automatic legal compliance.

### Logging and Monitoring

- Logs are structured and include request IDs.
- Sensitive payloads, passwords, tokens, upload bytes, and medical file contents must not be logged.
- Metrics-ready request counters and job health endpoints are available.
- Error monitoring hooks should be configured by deployment operators without sending sensitive data.

## CI Security Scanning

The CI workflow includes or is prepared to include:

- Backend linting, formatting, typing, and tests.
- Frontend linting, type checking, tests, and build.
- Python dependency scanning with `pip-audit`.
- Node dependency scanning with `npm audit`.
- Secret scanning with TruffleHog.
- Code scanning with GitHub CodeQL.
- Filesystem and container scanning with Trivy.
- Docker Compose validation and image builds.

Security gates should fail on verified secrets and high/critical dependency or container vulnerabilities unless a documented, time-bound exception is approved.

## Deployment Requirements

Production deployments must configure:

- `ENVIRONMENT=production`
- `COOKIE_SECURE=true`
- `DOCS_ENABLED=false`
- Strong `TOKEN_SECRET` of at least 32 characters, generated randomly.
- HTTPS `WEB_APP_URL`.
- Explicit HTTPS CORS origins only.
- Private record/export storage.
- Redis and PostgreSQL with authentication, network restrictions, backups, and encryption appropriate for the environment.
- Centralized logs with secret/PHI redaction.
- Malware scanning before medical records become available.
- Dependency, container, code, and secret scanning in CI/CD.

## Security Review Checklist

Review each release for:

- Broken access control and IDOR.
- Authentication and refresh token failures.
- Insecure token/cookie settings.
- SQL injection and unsafe raw SQL.
- XSS and unsafe rendering of markdown/AI output.
- CSRF risk for cookie-authenticated state changes.
- SSRF through ingestion, OCR, or URL processing.
- Path traversal and unrestricted upload bypasses.
- Malware upload workflow gaps.
- CORS overbreadth.
- Rate limit coverage on auth and abuse-prone routes.
- Mass assignment in schemas and role/profile mutations.
- Missing security headers.
- Dependency, container, and code vulnerabilities.
- Secret exposure in code, logs, CI, and Docker layers.
- Insecure object storage or long-lived public URLs.
- Prompt injection, model output injection, and RAG poisoning.
- Privacy leaks in exports, admin views, logs, and audit records.
- Admin and doctor privilege abuse.

## Known Operational Responsibilities

Some safeguards require deployment infrastructure or vendor integrations and cannot be guaranteed by application code alone:

- TLS termination and certificate management.
- WAF/bot controls.
- Malware scanning engine and quarantine review operations.
- Cloud bucket policies and KMS configuration.
- SIEM/error-monitoring redaction rules.
- Legal/regulatory compliance program.
- Incident response process and contact mailbox.

## Local Security Commands

From the repository root or relevant package directories:

```bash
# Backend
cd backend
python -m ruff check .
python -m pytest --no-cov -q
pip-audit -r requirements.txt -r requirements-dev.txt

# Frontend
cd frontend
npm ci --ignore-scripts
npm audit --audit-level=high
npm run lint
npm run typecheck
npm test

# Containers / repo
trivy fs .
docker compose config --quiet
docker compose build
```
