import os

os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://test:test@localhost:5432/test")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/15")
os.environ.setdefault("TOKEN_SECRET", "test-secret-that-is-longer-than-thirty-two-characters")
os.environ.setdefault("COOKIE_SECURE", "false")
