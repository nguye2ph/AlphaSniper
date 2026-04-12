"""FastAPI dependency injection for database sessions."""

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import async_session_factory


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Yield an async PostgreSQL session, auto-closes after request."""
    async with async_session_factory() as session:
        yield session
