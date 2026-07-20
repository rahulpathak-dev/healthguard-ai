<div align="center">

# HealthGuard AI

### Trusted health information, safer decisions, and privacy-first health management

AI-powered health education, medical information, report explanation, emergency guidance for India, reminders, misinformation detection, and secure personal health record management.

[![Next.js](https://img.shields.io/badge/Next.js-App_Router-black?logo=next.js)](#technology-stack)
[![FastAPI](https://img.shields.io/badge/FastAPI-Python-009688?logo=fastapi)](#technology-stack)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Database-4169E1?logo=postgresql)](#technology-stack)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?logo=docker)](#running-with-docker)
[![TypeScript](https://img.shields.io/badge/TypeScript-Frontend-3178C6?logo=typescript)](#technology-stack)
[![License](https://img.shields.io/badge/License-MIT-green)](#license)

[Live Demo](https://your-demo-url.com) · [API Documentation](https://your-api-url.com/docs) · [Report a Bug](https://github.com/YOUR_USERNAME/healthguard-ai/issues) · [Request a Feature](https://github.com/YOUR_USERNAME/healthguard-ai/issues)

</div>

---

## Overview

HealthGuard AI is a full-stack, AI-powered health information platform designed to help users better understand health topics while preserving medical safety, privacy, and user control.

The platform combines verified medical knowledge retrieval, a centralized AI safety layer, secure health-record management, medical-report explanation, medicine information, appointment reminders, India-focused emergency guidance, and health misinformation analysis.

HealthGuard AI is an educational and informational platform. It does not diagnose diseases, prescribe treatment, or replace qualified healthcare professionals.

> In India, call `112` for urgent emergency help. Do not wait for an app response during a medical emergency.

---

## Problem Statement

People often face several challenges when searching for health information:

- medical terminology is difficult to understand;
- online health content may be misleading or unsafe;
- important medical documents are scattered across devices;
- users forget appointments, tests, vaccinations, and medicines;
- medical reports are difficult for non-specialists to read;
- emergency instructions are not always easy to access;
- sharing health records may create privacy risks;
- general-purpose AI systems may provide overconfident medical responses.

HealthGuard AI addresses these problems through verified retrieval, transparent safety controls, privacy-first record management, and clear escalation to professional or emergency care.

---

## Solution

HealthGuard AI provides one secure platform where users can:

- ask health education questions;
- understand symptoms without receiving a diagnosis;
- search verified medicine information;
- upload and organize health records;
- receive simple explanations of medical reports;
- create health and appointment reminders;
- access emergency guidance for India using `112`;
- verify viral health claims;
- manage family health profiles;
- securely share selected records with a doctor;
- control consent, data export, and account deletion.

---

## Key Features

### AI Health Education Chatbot

Ask general health questions and receive easy-to-understand, citation-aware responses supported by trusted medical knowledge.

### Non-Diagnostic Symptom Guidance

Enter symptoms and receive:

- general educational explanations;
- red-flag warnings;
- urgency guidance;
- questions to discuss with a doctor;
- clear medical disclaimers.

The system avoids final diagnosis and false certainty.

### Verified Medicine Information

Search medicine information including:

- common uses;
- precautions;
- side effects;
- warnings;
- interactions;
- storage guidance;
- special population cautions.

The platform does not prescribe medicines or encourage self-medication.

### Medical Report Explanation

Upload a supported medical report and receive:

- OCR-based text extraction;
- structured report values;
- simple-language explanations;
- highlighted out-of-range values;
- OCR confidence indicators;
- questions to ask a healthcare professional.

### Secure Health Record Organizer

Store and manage:

- prescriptions;
- laboratory reports;
- vaccination records;
- discharge summaries;
- doctor notes;
- scans;
- other medical documents.

Records remain private and are accessed through authenticated, permission-controlled workflows.

### Appointment and Medicine Reminders

Create reminders for:

- doctor appointments;
- medicines;
- vaccinations;
- tests;
- health checkups;
- follow-up visits.

### Emergency Guidance for India

Quickly access clear emergency instructions for situations such as:

- chest pain;
- stroke signs;
- breathing difficulty;
- severe bleeding;
- choking;
- burns;
- poisoning;
- seizures;
- severe allergic reactions.

The project defaults to India’s national emergency response number: `112`.

### Health Misinformation Detector

Paste a health claim or forwarded message and receive an evidence-based assessment:

- likely accurate;
- misleading;
- unsupported;
- potentially harmful;
- insufficient evidence.

### Family Health Profiles

Manage separate profiles, records, reminders, allergies, medicines, and emergency contacts for family members.

### Doctor Review Mode

Share selected records with a doctor or reviewer using:

- explicit consent;
- limited permissions;
- optional expiry;
- access history;
- instant revocation.

### Privacy Center

Users can:

- review active sessions;
- manage consent;
- revoke shared access;
- request data export;
- delete records;
- request account deletion.

### Administrative Governance

The admin console supports:

- doctor verification;
- knowledge-source management;
- safety-event review;
- audit log review;
- notification monitoring;
- ingestion-job monitoring;
- system health monitoring.

---

## What Makes HealthGuard AI Different?

HealthGuard AI is designed around safety and trust rather than unrestricted AI generation.

Key differentiators include:

- verified Retrieval-Augmented Generation;
- source-aware medical responses;
- centralized medical AI safety engine;
- emergency red-flag detection;
- non-diagnostic symptom guidance;
- OCR confidence handling;
- health misinformation verification;
- consent-based doctor sharing;
- privacy-first medical record storage;
- multilingual-ready architecture;
- accessibility-conscious user experience;
- complete audit and governance layer.

---

## Medical Safety Principles

HealthGuard AI follows these core rules:

- never provide a definitive diagnosis;
- never prescribe medication;
- never recommend unsafe dosage changes;
- never fabricate medical references;
- clearly communicate uncertainty;
- detect emergency warning signs;
- direct users to professional care when appropriate;
- use verified knowledge sources;
- display educational-use disclaimers;
- protect user health information from unauthorized access.

---

## Security and Privacy

HealthGuard AI is designed using privacy-by-design and least-privilege principles.

Security features include:

- password hashing;
- JWT access and refresh token architecture;
- refresh token rotation;
- role-based access control;
- object-level authorization;
- private object storage architecture;
- signed record access patterns;
- secure file validation;
- upload quarantine architecture;
- API rate limiting;
- input validation;
- audit logs;
- session management;
- record-sharing expiration;
- consent revocation;
- data export controls;
- account deletion workflow;
- security headers;
- environment-based secret management.

This repository does not claim formal HIPAA, GDPR, or other regulatory certification. Production deployment in a regulated environment requires independent legal, security, privacy, and compliance assessment.

---

## System Architecture

```text
+---------------------------+
|      Next.js Frontend     |
| Landing · Dashboard · AI  |
| Records · Emergency · UI  |
+-------------+-------------+
              |
              | HTTPS / REST
              v
+---------------------------+
|       FastAPI Backend     |
| Auth · Profiles · Safety  |
| RAG · Reports · Records   |
| Sharing · Privacy · Admin |
+------+------+-------------+
       |      |
       |      +-------------------+
       |                          |
       v                          v
+-------------+            +-------------+
| PostgreSQL  |            | Redis       |
| App + RAG   |            | Jobs/Cache  |
+-------------+            +-------------+
       |
       v
+---------------------------+
| Private Object Storage    |
| Medical files and exports |
+---------------------------+
```

---

## AI Response Pipeline

```text
User input
  -> request validation
  -> prompt-injection and abuse detection
  -> emergency red-flag classification
  -> trusted knowledge retrieval
  -> controlled generation
  -> medical safety review
  -> citation validation
  -> disclaimer and escalation formatting
  -> user response
```

---

## Technology Stack

### Frontend

- Next.js App Router;
- React;
- TypeScript;
- CSS-based responsive design system;
- Zod;
- React Testing Library;
- Vitest.

### Backend

- FastAPI;
- Python 3.12;
- Pydantic and Pydantic Settings;
- SQLAlchemy async ORM;
- Alembic migrations;
- Redis;
- structured logging.

### Data

- PostgreSQL;
- Redis;
- pgvector-ready RAG architecture;
- private local/S3-compatible storage architecture.

### AI and Document Processing

- configurable LLM-provider architecture;
- Retrieval-Augmented Generation;
- embeddings-ready source model;
- citation mapping;
- OCR/report extraction scaffolding;
- medical safety guardrails;
- misinformation analysis.

### Testing and DevOps

- Pytest;
- HTTPX/TestClient;
- Vitest;
- React Testing Library;
- static type checking;
- Ruff;
- MyPy;
- Docker and Docker Compose;
- GitHub Actions with dependency, secret, code, and container scanning.

---

## Project Structure

```text
healthguard-ai/
├── frontend/
│   ├── app/
│   ├── components/
│   ├── lib/
│   └── test/
├── backend/
│   ├── app/
│   │   ├── admin/
│   │   ├── ai_safety/
│   │   ├── api/
│   │   ├── auth/
│   │   ├── chat/
│   │   ├── core/
│   │   ├── dashboard/
│   │   ├── db/
│   │   ├── emergency/
│   │   ├── jobs/
│   │   ├── medicines/
│   │   ├── misinformation/
│   │   ├── privacy/
│   │   ├── profiles/
│   │   ├── rag/
│   │   ├── records/
│   │   ├── reminders/
│   │   ├── reports/
│   │   ├── sharing/
│   │   ├── symptoms/
│   │   └── main.py
│   ├── alembic/
│   └── tests/
├── docs/
├── e2e/
├── .github/workflows/
├── docker-compose.yml
├── .env.example
├── CONTRIBUTING.md
├── SECURITY.md
├── LICENSE
└── README.md
```

---

## Getting Started

### Prerequisites

Install the following:

- Node.js 22 or newer;
- Python 3.12;
- PostgreSQL;
- Redis;
- Git;
- Docker Desktop, recommended.

---

## Running with Docker

### 1. Clone the repository

```bash
git clone https://github.com/YOUR_USERNAME/healthguard-ai.git
cd healthguard-ai
```

### 2. Create the environment file

Windows:

```powershell
Copy-Item .env.example .env
```

macOS/Linux:

```bash
cp .env.example .env
```

### 3. Configure environment variables

Open `.env` and provide the required local credentials and API keys.

Never commit the completed `.env` file.

### 4. Start the complete platform

```bash
docker compose up --build
```

### 5. Open the services

| Service | URL |
| --- | --- |
| Frontend | `http://localhost:3000` |
| Backend | `http://localhost:8000` |
| API Documentation | `http://localhost:8000/docs` |
| Backend Liveness | `http://localhost:8000/api/v1/health/live` |
| Backend Readiness | `http://localhost:8000/api/v1/health/ready` |
| PostgreSQL | `localhost:5432` inside Docker network as `postgres:5432` |
| Redis | `localhost:6379` inside Docker network as `redis:6379` |

### 6. Stop the services

```bash
docker compose down
```

To also remove local Docker volumes:

```bash
docker compose down -v
```

---

## Manual Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

Frontend:

```text
http://localhost:3000
```

Production validation:

```bash
npm run lint
npm run typecheck
npm run test
npm run build
```

From the repository root, you can also run:

```bash
npm run lint
npm run type-check
npm run test
npm run frontend:build
```

---

## Manual Backend Setup

Manual setup needs PostgreSQL and Redis already running. For local manual development, set `DATABASE_URL`, `REDIS_URL`, `TOKEN_SECRET`, `COOKIE_SECURE=false`, `CORS_ORIGINS=["http://localhost:3000"]`, and `WEB_APP_URL=http://localhost:3000` in your shell or `.env` file.

### Windows

```powershell
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload
```

### macOS/Linux

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload
```

Backend:

```text
http://localhost:8000
```

API documentation:

```text
http://localhost:8000/docs
```

---

## Root Scripts

```bash
npm run dev              # docker compose up --build
npm run up               # docker compose up -d --build
npm run down             # docker compose down
npm run logs             # docker compose logs -f
npm run build            # docker compose build
npm run lint             # frontend lint
npm run type-check       # frontend TypeScript check
npm run test             # frontend tests
npm run frontend:build   # frontend production build
npm run backend:lint     # backend Ruff check
npm run backend:typecheck # backend MyPy check
npm run backend:test     # backend Pytest suite
npm run backend:migrate  # alembic upgrade head
```

---

## Environment Variables

Create a local `.env` using `.env.example`.

Important variables include:

```env
APP_NAME="HealthGuard AI"
APP_ENV=development
ENVIRONMENT=development
FRONTEND_URL=http://localhost:3000
WEB_APP_URL=http://localhost:3000
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1

DATABASE_URL=postgresql+asyncpg://healthguard:healthguard@postgres:5432/healthguard
REDIS_URL=redis://redis:6379/0

TOKEN_SECRET=replace-with-at-least-32-random-characters
JWT_SECRET_KEY=replace-with-at-least-32-random-characters
ACCESS_TOKEN_MINUTES=15
REFRESH_TOKEN_DAYS=7

LLM_PROVIDER=openai
OPENAI_API_KEY=
OPENAI_MODEL=
EMBEDDING_MODEL=

VECTOR_DATABASE_PROVIDER=pgvector
VECTOR_DATABASE_URL=

STORAGE_PROVIDER=local-private
S3_ENDPOINT_URL=
S3_REGION=
S3_BUCKET=
S3_ACCESS_KEY_ID=
S3_SECRET_ACCESS_KEY=

EMERGENCY_NUMBER=112
ENCRYPTION_KEY=
FILE_MAX_SIZE_MB=10
```

Refer to `.env.example` for the full documented configuration.

Never commit:

- real `.env` files;
- API keys;
- passwords;
- private keys;
- production database URLs;
- cloud credentials;
- user health data;
- uploaded medical reports.

---

## Database Migrations

Create a migration:

```bash
cd backend
alembic revision --autogenerate -m "describe migration"
```

Apply migrations:

```bash
alembic upgrade head
```

Rollback one migration:

```bash
alembic downgrade -1
```

Review generated migrations before applying them to production.

---

## Running Tests

### Backend

```bash
cd backend
pytest
```

With coverage:

```bash
pytest --cov=app --cov-report=term-missing
```

Backend quality checks:

```bash
ruff check .
mypy app
```

### Frontend

```bash
cd frontend
npm run lint
npm run typecheck
npm run test
npm run build
```

### End-to-End

```bash
cd e2e
# add provider-specific Playwright setup before running browser E2E tests
```

---

## API Documentation

During local development, Swagger documentation is available at:

```text
http://localhost:8000/docs
```

ReDoc documentation is available at:

```text
http://localhost:8000/redoc
```

The API is versioned under:

```text
/api/v1
```

Production deployments should set `DOCS_ENABLED=false`.

---

## Screenshots

Add real project screenshots before publishing the repository.

Recommended screenshots:

```text
docs/screenshots/landing-page.png
docs/screenshots/dashboard.png
docs/screenshots/health-chatbot.png
docs/screenshots/symptom-assistant.png
docs/screenshots/report-analysis.png
docs/screenshots/records.png
docs/screenshots/misinformation-checker.png
docs/screenshots/admin-dashboard.png
```

Example:

```markdown
![HealthGuard AI Dashboard](docs/screenshots/dashboard.png)
```

---

## Deployment

A recommended production deployment architecture is:

- frontend: Vercel or equivalent;
- backend API: Render, Railway, AWS, Azure, GCP, Fly.io, or equivalent;
- PostgreSQL: managed PostgreSQL provider;
- Redis: managed Redis provider;
- storage: private S3-compatible object storage;
- workers: separate background-worker process;
- monitoring: error monitoring and structured logs.

Before deployment:

```bash
npm run lint
npm run type-check
npm run test
npm run frontend:build
cd backend
ruff check .
mypy app
pytest
cd ..
docker compose build --no-cache
```

Deployment documentation is available in:

```text
docs/deployment.md
```

---

## Development Roadmap

### Core Modules

- [x] Project architecture and monorepo foundation
- [x] Landing page and branding
- [x] Authentication and RBAC
- [x] User and family profiles
- [x] Health dashboard
- [x] AI health education chatbot
- [x] Verified medical RAG
- [x] Central AI medical safety engine
- [x] Symptom understanding assistant
- [x] Medicine information module
- [x] Secure medical record organizer
- [x] OCR and report explanation
- [x] Appointment and medicine reminders
- [x] Emergency guidance for India
- [x] Health misinformation detector
- [x] Doctor review and secure sharing
- [x] Admin and governance console
- [x] Privacy and consent center
- [x] Background jobs and observability
- [x] Accessibility and multilingual support

### Future Enhancements

- country-specific health-resource directories;
- voice input and read-aloud support;
- offline emergency guide;
- additional Indian-language support;
- provider-integrated appointment workflows;
- user-controlled wearable data import;
- advanced document redaction;
- federated or privacy-preserving AI research;
- independently reviewed clinical-safety rules;
- mobile applications.

---

## Contributing

Contributions are welcome.

Before contributing:

1. Read `CONTRIBUTING.md`.
2. Create a feature branch.
3. Add or update tests.
4. Run linting and builds.
5. Avoid adding real health records or credentials.
6. Submit a clear pull request.

Example:

```bash
git checkout -b feature/your-feature
git add .
git commit -m "feat: add your feature"
git push origin feature/your-feature
```

Open a pull request against the `main` branch.

---

## Security

Do not publicly disclose security vulnerabilities through GitHub issues.

Follow the responsible-disclosure process in:

```text
SECURITY.md
```

Never include real:

- API keys;
- database passwords;
- cloud credentials;
- private keys;
- access tokens;
- medical records;
- user health information.

---

## Medical Disclaimer

HealthGuard AI provides general health education and medical information only.

It is not a medical device, doctor, emergency service, diagnostic system, prescription service, or substitute for professional medical advice.

Do not use this platform to make urgent or high-risk medical decisions.

Seek immediate professional or emergency assistance for severe, sudden, worsening, or life-threatening symptoms. In India, call `112` for emergency help.

Never start, stop, or change medication based solely on information provided by this platform.

---

## Responsible AI Notice

AI-generated responses may be incomplete, incorrect, or unsuitable for an individual situation.

HealthGuard AI therefore uses:

- trusted knowledge retrieval;
- citation mapping;
- emergency red-flag detection;
- uncertainty messaging;
- output safety checks;
- user feedback and reporting;
- professional-care escalation.

Users should verify important health decisions with qualified healthcare professionals.

---

## Troubleshooting

### Port conflicts

If ports 3000, 8000, 5432, or 6379 are already in use, stop the conflicting process or change the exposed host port in `docker-compose.yml`. Keep internal service URLs unchanged inside Docker: `postgres`, `redis`, and `backend`.

### Database connection errors

Check that `DATABASE_URL` points to PostgreSQL and uses the async driver form expected by the backend, for example `postgresql+asyncpg://healthguard:healthguard@postgres:5432/healthguard` in Docker.

### Redis errors

Check `REDIS_URL`. In Docker use `redis://redis:6379/0`; outside Docker use `redis://localhost:6379/0` if Redis is installed locally.

### Migration failures

Run migrations from the `backend` directory after environment variables are loaded. If a migration partially applied, inspect `alembic_version` before retrying. Do not delete migration files or reset production databases.

### Missing environment variables

The backend intentionally fails fast when required secrets are absent. `DATABASE_URL`, `REDIS_URL`, and `TOKEN_SECRET` are required. `TOKEN_SECRET` must be at least 32 characters. Production also requires secure cookies, HTTPS `WEB_APP_URL`, no localhost CORS origins, and docs disabled.

### CORS errors

Add the exact frontend origin to `CORS_ORIGINS`, including scheme and port. For local development use `["http://localhost:3000"]`. Do not use wildcard CORS with credentials.

### LLM provider errors

AI flows are routed through backend safety/orchestration services, never directly from the browser. If provider credentials are not configured, use safe fallback behavior and verify no medical answer is presented as a diagnosis.

### OCR dependency errors

OCR/report explanation is asynchronous and should surface retryable status instead of blocking the request. Verify OCR binaries or provider credentials in the worker environment, and ensure unreadable values are not invented.

### Docker build errors

Rebuild from a clean context with `docker compose build --no-cache`. If frontend builds fail, run `npm --prefix frontend run build` locally. If backend builds fail, verify `backend/requirements.txt` and Python 3.12 compatibility.

---

## License

This project is released under the MIT License unless a different license is specified in the repository.

See:

```text
LICENSE
```

Third-party medical content, medicine data, APIs, datasets, models, and libraries may have separate licensing requirements.

---

## Author

### Rahul Pathak

B.Tech Computer Science and Engineering student focused on full-stack development, artificial intelligence, cloud engineering, and secure software systems.

- GitHub: `https://github.com/YOUR_USERNAME`
- LinkedIn: `https://www.linkedin.com/in/YOUR_PROFILE`
- Email: `YOUR_EMAIL`

---

## Support the Project

A star helps other developers discover the project.

You can also support HealthGuard AI by:

- reporting bugs;
- suggesting responsible features;
- improving accessibility;
- adding tests;
- reviewing security;
- improving documentation;
- contributing verified public-health resources.

---

<div align="center">

Built with a focus on responsible AI, secure engineering, privacy, accessibility, and user trust.

**HealthGuard AI — Trusted information, safer decisions.**

</div>
