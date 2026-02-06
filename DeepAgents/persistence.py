"""
Persistence Module for DeepAgents.
Provides Asynchronous Postgres Checkpointing for LangGraph Agents.
"""

import logging
import os
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from dotenv import load_dotenv
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

# We use psycopg_pool for the standard AsyncPostgresSaver
from psycopg_pool import AsyncConnectionPool

load_dotenv()
logger = logging.getLogger("DeepAgents-Persistence")


def get_connection_string() -> str:
    """Constructs the Postgres connection string from env vars."""
    host = os.getenv("POSTGRES_HOST", "localhost")
    port = os.getenv("POSTGRES_PORT", "5432")
    user = os.getenv("POSTGRES_USER", "postgres")
    password = os.getenv("POSTGRES_PASSWORD", "d1204l0723")
    dbname = os.getenv("POSTGRES_DB", "postgres")

    return f"postgresql://{user}:{password}@{host}:{port}/{dbname}"


@asynccontextmanager
async def get_postgres_checkpointer() -> AsyncGenerator[AsyncPostgresSaver, None]:
    """
    Async context manager that yields a PostgresSaver backed by a connection pool.
    Usage:
        async with get_postgres_checkpointer() as checkpointer:
            app = workflow.compile(checkpointer=checkpointer)
            await app.invoke(...)
    """
    conn_str = get_connection_string()

    # Initialize the pool
    # We set min_size=1, max_size=10 for typical agent usage
    # Enable autocommit=True to allow CREATE INDEX CONCURRENTLY and to let LangGraph manage transactions
    async with AsyncConnectionPool(
        conninfo=conn_str, min_size=1, max_size=10, kwargs={"autocommit": True}
    ) as pool:
        logger.info("💾 Connecting to Postgres Persistence Layer...")

        # Initialize the checkpointer
        checkpointer = AsyncPostgresSaver(pool)  # type: ignore[arg-type]

        # Ensure tables exist (AsyncPostgresSaver usually handles this on first use or setup)
        await checkpointer.setup()

        logger.info("✅ Postgres Checkpointer Ready.")
        yield checkpointer
