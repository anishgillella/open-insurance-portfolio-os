"""FastAPI dependencies."""

from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_session

# Type alias for database session dependency
AsyncSessionDep = Annotated[AsyncSession, Depends(get_async_session)]

# Alias for backward compatibility with endpoints using get_db
get_db = get_async_session
