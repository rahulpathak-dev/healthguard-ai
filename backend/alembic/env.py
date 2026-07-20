import asyncio
from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from alembic import context
from app.admin import models as admin_models  # noqa: F401
from app.ai_safety import models as ai_safety_models  # noqa: F401
from app.auth import models as auth_models  # noqa: F401
from app.chat import models as chat_models  # noqa: F401
from app.core.config import get_settings
from app.dashboard import models as dashboard_models  # noqa: F401
from app.db.base import Base
from app.jobs import models as jobs_models  # noqa: F401
from app.medicines import models as medicine_models  # noqa: F401
from app.misinformation import models as misinformation_models  # noqa: F401
from app.privacy import models as privacy_models  # noqa: F401
from app.profiles import models as profile_models  # noqa: F401
from app.rag import models as rag_models  # noqa: F401
from app.reminders import models as reminder_models  # noqa: F401
from app.sharing import models as sharing_models  # noqa: F401
from app.symptoms import models as symptom_models  # noqa: F401

config = context.config
config.set_main_option("sqlalchemy.url", get_settings().database_url.get_secret_value())
if config.config_file_name:
    fileConfig(config.config_file_name)
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    context.configure(
        url=config.get_main_option("sqlalchemy.url"),
        target_metadata=target_metadata,
        literal_binds=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata, compare_type=True)
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_async_migrations())
