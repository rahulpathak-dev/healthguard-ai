# Architecture

The monorepo separates the Next.js presentation layer from a versioned FastAPI API. PostgreSQL is the system of record; Redis supports cache, rate limits, temporary state, and queues. Medical files belong in private S3-compatible storage. AI providers must be accessed through a future provider abstraction after input safety screening and trusted-source retrieval.

## Request safety sequence

1. Authenticate and authorize ownership.
2. Validate and rate-limit input.
3. Screen for emergencies and prompt attacks.
4. Escalate red flags before ordinary generation.
5. Retrieve trusted, attributable sources.
6. Generate with safety constraints and citations.
7. Validate output and persist non-sensitive safety metadata.

This foundation intentionally implements only health and safety-screen endpoints. Authentication, domain entities, persistence, RAG, workers, and the remaining product modules require subsequent reviewed increments.
