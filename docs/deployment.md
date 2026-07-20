# HealthGuard AI Deployment Guide

This guide describes a production-ready deployment process for HealthGuard AI. It is intentionally provider-neutral: Vercel, Render, Railway, AWS, Azure, GCP, Fly.io, and equivalent platforms can be used if they satisfy the controls below.

HealthGuard AI handles sensitive health information. Do not claim HIPAA, GDPR, or other legal compliance without a formal legal, security, and operational review.

## 1. Production architecture

Recommended production services:

- Frontend: Vercel or equivalent static/SSR Next.js hosting.
- Backend API: container hosting with HTTPS, private environment variables, health checks, and non-root runtime.
- Worker: separate backend image/process for background jobs such as report processing, notifications, ingestion, OCR, exports, and deletion.
- Database: managed PostgreSQL with backups, SSL, restricted credentials, and private networking where supported.
- Redis: managed Redis with TLS/authentication where supported and isolated per environment.
- Storage: private object storage bucket with encryption, signed URLs, lifecycle rules, restricted IAM, and malware scanning/quarantine design.
- Observability: structured logs, request IDs, error monitoring, uptime checks, and security-event review.

## 2. Frontend deployment

Use Vercel or an equivalent platform that supports Next.js production builds.

Required production settings:

- Set `NEXT_PUBLIC_API_URL` to the public backend API base URL, for example `https://api.example.com/api/v1`.
- Do not place secrets in `NEXT_PUBLIC_*` variables.
- Run `npm --prefix frontend run build` before deployment or as the platform build command.
- Keep CSP and security headers compatible with the backend and any frontend platform headers.
- Verify all public pages, authenticated route guards, emergency pages, and error pages after deploy.

Suggested build settings:

```bash
cd frontend
npm ci --ignore-scripts
npm run lint
npm run typecheck
npm test
npm run build
```

## 3. Backend deployment

Deploy the backend as a production Docker image.

Required controls:

- Run as a non-root container user.
- Expose only the application port, usually `8000`.
- Terminate HTTPS at the platform load balancer or ingress.
- Configure trusted proxy headers only for known platform proxies.
- Use structured logs and preserve request IDs.
- Disable API docs in production with `DOCS_ENABLED=false`.
- Set `COOKIE_SECURE=true` and use HTTPS `WEB_APP_URL`.
- Restrict `CORS_ORIGINS` to exact frontend origins; never use wildcard CORS with credentials.
- Configure liveness and readiness health checks:
  - Liveness: `/api/v1/health/live`
  - Readiness: `/api/v1/health/ready`

Suggested backend build and startup:

```bash
docker build -t healthguard-ai-backend:prod ./backend
docker run --env-file .env -p 8000:8000 healthguard-ai-backend:prod
```

Migration command:

```bash
cd backend
alembic upgrade head
```

Run migrations as a one-off release job before routing production traffic to a new backend version.

## 4. Worker deployment

Run workers as a separate process/image using the same codebase and production environment variables. Workers should not expose public HTTP routes unless a platform health endpoint is required.

Worker requirements:

- Use Redis-backed queues and idempotency keys.
- Use dead-letter handling for exhausted retries.
- Avoid caching user-specific medical data under shared keys.
- Redact sensitive data from logs.
- Run report-processing, notification, ingestion, OCR, export, and deletion jobs outside the request path where possible.

If a dedicated worker command is not yet implemented for a provider, deploy the API first and keep asynchronous features on safe fallback/background-task behavior until a worker process is added.

## 5. Database

Use managed PostgreSQL in production.

Required controls:

- Automated backups enabled.
- Point-in-time recovery where available.
- SSL required for application connections.
- Private networking where supported.
- Separate database users per environment.
- Restricted application credentials: no superuser credentials in app runtime.
- Migration strategy: apply migrations once per release before traffic cutover.
- Regular restore drills to verify backups are usable.

Connection examples:

```bash
DATABASE_URL=postgresql+asyncpg://app_user:change-me@private-db-host:5432/healthguard
```

The current backend dependency set uses `asyncpg`. If a provider requires `postgresql+psycopg`, add and test the psycopg driver before changing production URLs.

## 6. Redis

Use managed Redis in production.

Required controls:

- TLS where available.
- Authentication enabled.
- Separate Redis instances or logical databases per environment.
- Network access restricted to backend/worker services.
- Persistence configured according to job durability requirements.
- Memory limits and eviction policy reviewed for queues, locks, and rate limits.

## 7. Storage

Use private object storage for medical records and exports.

Required controls:

- Bucket is private; no public object URLs.
- Server-side encryption enabled.
- Signed URLs are short-lived and scoped.
- Storage paths are generated server-side; never trust user-controlled paths.
- IAM role/key has least privilege for the exact bucket/prefix.
- Lifecycle rules remove expired exports and quarantined files according to retention policy.
- Malware scanning/quarantine occurs before files become available.
- Audit logs track access, deletion, and sharing events.

## 8. Environment variables

Start from `.env.example` and configure provider-specific secret stores. Never paste production secrets into source control, issue trackers, chat, screenshots, or client-visible variables.

Production minimums:

- `ENVIRONMENT=production`
- `DOCS_ENABLED=false`
- `COOKIE_SECURE=true`
- `WEB_APP_URL=https://<frontend-domain>`
- `FRONTEND_URL=https://<frontend-domain>`
- `NEXT_PUBLIC_API_URL=https://<backend-domain>/api/v1`
- `CORS_ORIGINS=["https://<frontend-domain>"]`
- `DATABASE_URL=<managed-postgres-url>`
- `REDIS_URL=<managed-redis-url>`
- `TOKEN_SECRET=<32+ random bytes>`
- `JWT_SECRET_KEY=<same value if used by deployment templates>`
- provider keys for LLM, email, SMS, storage, OCR, and observability only when those integrations are enabled.

## 9. Deployment process

Perform every production release in this order:

1. Run all tests.
2. Run frontend production build.
3. Build Docker images.
4. Scan dependencies and containers.
5. Confirm no secrets are exposed.
6. Apply database migrations as a one-off release job.
7. Deploy backend API.
8. Deploy worker process.
9. Deploy frontend.
10. Configure/verify environment variables.
11. Verify backend liveness and readiness checks.
12. Verify frontend loads and points to the production API.
13. Verify CORS from the production frontend origin.
14. Run smoke tests.
15. Test authentication.
16. Test record upload and signed access.
17. Test chatbot safety and citation behavior.
18. Test emergency pages without login.
19. Test data export/deletion workflow.
20. Monitor logs, metrics, jobs, and security events after release.

Suggested local pre-release commands:

```bash
npm run lint
npm run type-check
npm run test
npm run frontend:build
cd backend
ruff check .
mypy app
pytest
alembic upgrade head
cd ..
docker compose build --no-cache
```

## 10. Smoke test checklist

After deployment, verify:

- Frontend homepage loads over HTTPS.
- Backend `/api/v1/health/live` returns 200.
- Backend `/api/v1/health/ready` returns 200 after DB/Redis are reachable.
- API docs are unavailable in production and available only in development.
- CORS allows only the configured frontend origin.
- Registration/login/logout work.
- Refresh-token rotation works.
- User A cannot access User B resources.
- Family profile switching respects ownership.
- Emergency guidance is accessible without login.
- Medical record upload rejects invalid file type, MIME, signature, size, and path.
- Uploaded records are private and accessed only through signed/authorized flows.
- Chatbot refuses diagnosis-like, unsafe medication, and emergency-misrouting behavior.
- Symptom red flags escalate appropriately.
- Medicine module does not recommend starting/stopping/changing medicines.
- Misinformation verdicts cite trusted evidence and avoid false certainty.
- Doctor sharing grants are scoped, expiring, revocable, and audited.
- Privacy export links expire and account deletion revokes sessions.

## 11. Rollback plan

Use a rollback when a release causes user-impacting errors, security regressions, broken migrations, failed health checks, or unsafe medical outputs.

Rollback steps:

1. Stop new deployment rollout.
2. Keep the previous known-good image/version available.
3. Route traffic back to the previous backend version if the database schema remains compatible.
4. Roll back the frontend to the previous deployment if API contract changes caused breakage.
5. Pause workers if they are producing bad jobs, duplicate notifications, unsafe outputs, or destructive actions.
6. If a migration is backward-incompatible, follow the migration-specific downgrade or forward-fix plan; do not manually edit production tables without review.
7. Verify health checks, authentication, emergency pages, record access, and data deletion after rollback.
8. Record an incident note with cause, impact, timeline, and prevention items.

Rollback requirements:

- Every release must identify the previous backend image, worker image, frontend deployment, and migration revision.
- Database migrations should be backward-compatible whenever possible.
- Destructive migrations require a backup and explicit approval.

## 12. Backup plan

Database backups:

- Enable daily automated backups at minimum.
- Enable point-in-time recovery for production where supported.
- Retain backups according to the product retention policy.
- Restrict backup access to authorized operators.
- Test restores regularly in a non-production environment.

Storage backups:

- Enable versioning or equivalent recovery where appropriate.
- Use lifecycle rules for expired exports and quarantined files.
- Keep medical records private during backup/restore.

Redis backups:

- Treat Redis as operational state for queues, locks, rate limits, and cache.
- Configure persistence if queued jobs must survive provider restarts.
- Ensure job idempotency protects against replay after restore.

## 13. Disaster recovery notes

Prepare for these scenarios:

- Database outage: fail health readiness, pause writes/jobs, communicate degraded state, restore/fail over managed DB.
- Redis outage: disable job processing and rate-limit dependent workflows safely; avoid losing destructive jobs.
- Storage outage: disable upload/download workflows, preserve metadata, prevent public fallback URLs.
- LLM outage: use safe fallback responses; never bypass safety layers to restore AI features.
- OCR outage: keep report analyses queued/retryable; surface uncertainty and retry state.
- Credential leak: rotate affected key, revoke sessions/tokens as needed, inspect logs, and document incident.
- Unsafe medical output incident: disable affected AI feature, preserve audit evidence, review prompts/retrieval/safety logs, and patch before re-enabling.

Recovery targets should be defined by the product owner and operations team before launch, including RTO, RPO, communication contacts, and escalation paths.

## 14. Production checklist

Before launch:

- [ ] Production `.env` exists only in provider secret stores.
- [ ] No real secrets are committed.
- [ ] `ENVIRONMENT=production`.
- [ ] `DOCS_ENABLED=false`.
- [ ] `COOKIE_SECURE=true`.
- [ ] `WEB_APP_URL` and `FRONTEND_URL` use HTTPS.
- [ ] `CORS_ORIGINS` contains only exact trusted origins.
- [ ] Managed PostgreSQL uses SSL, backups, restricted credentials, and private networking where available.
- [ ] Managed Redis uses TLS/authentication where available.
- [ ] Storage bucket is private, encrypted, and IAM-restricted.
- [ ] Signed URL expiration is short.
- [ ] Malware scanning/quarantine design is active or launch-blocking limitations are documented.
- [ ] Dependency scan passes.
- [ ] Secret scan passes.
- [ ] Container scan passes.
- [ ] Code scan passes.
- [ ] Frontend build passes.
- [ ] Backend lint, typecheck, and tests pass.
- [ ] Migrations apply cleanly.
- [ ] Backend and worker deploy successfully.
- [ ] Health/readiness checks pass.
- [ ] Authentication smoke tests pass.
- [ ] Record upload/access smoke tests pass.
- [ ] AI safety smoke tests pass.
- [ ] Emergency pages work without login.
- [ ] Export/deletion smoke tests pass.
- [ ] Rollback version is identified.
- [ ] Backup restore drill has been completed or scheduled before handling real user health data.
