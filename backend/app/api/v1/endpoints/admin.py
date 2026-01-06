"""Admin API endpoints for system management.

Provides administrative operations like resetting all data.
"""

import logging

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import text

from app.core.dependencies import AsyncSessionDep
from app.services.pinecone_service import get_pinecone_service, PineconeServiceError

logger = logging.getLogger(__name__)

router = APIRouter()


class ResetResponse(BaseModel):
    """Response from reset operation."""

    success: bool
    message: str
    tables_cleared: list[str]
    vectors_deleted: bool
    vector_count_before: int | None = None


class ResetStatsResponse(BaseModel):
    """Current database and vector store statistics."""

    database_stats: dict[str, int]
    vector_stats: dict[str, int | str] | None


# Tables to clear in order (respecting foreign key constraints)
# Order matters: child tables first, parent tables last
# NOTE: organizations table is NOT cleared to preserve default org for uploads
TABLES_TO_CLEAR = [
    # Child tables (no foreign key references to them)
    "messages",
    "conversations",
    "document_chunks",
    "extracted_facts",
    "coverages",
    "endorsements",
    "claims",
    "coverage_gaps",
    "coverage_conflicts",
    "health_scores",
    "renewal_alerts",
    "renewal_forecasts",
    "renewal_readiness",
    "lender_requirements",
    "market_contexts",
    # Middle-tier tables
    "certificates",
    "financials",
    "valuations",
    "policies",
    # Parent tables
    "insurance_programs",
    "documents",
    "buildings",
    "properties",
    "insured_entities",
    "carriers",
    # "organizations",  # KEEP organizations - needed for uploads
    "renewal_alert_config",
]


@router.get("/stats", response_model=ResetStatsResponse)
async def get_system_stats(db: AsyncSessionDep) -> ResetStatsResponse:
    """Get current database and vector store statistics.

    Returns counts for all tables and Pinecone vector count.
    """
    # Get database table counts
    db_stats = {}
    for table in TABLES_TO_CLEAR:
        try:
            result = await db.execute(text(f"SELECT COUNT(*) FROM {table}"))
            count = result.scalar()
            db_stats[table] = count or 0
        except Exception:
            db_stats[table] = -1  # Table doesn't exist or error

    # Get Pinecone stats
    vector_stats = None
    try:
        pinecone = get_pinecone_service()
        if pinecone.api_key and pinecone.host:
            stats = await pinecone.describe_index_stats()
            vector_stats = {
                "total_vector_count": stats.get("totalVectorCount", 0),
                "dimension": stats.get("dimension", 0),
                "index_fullness": stats.get("indexFullness", 0),
            }
    except Exception as e:
        logger.warning(f"Could not get Pinecone stats: {e}")
        vector_stats = {"error": str(e)}

    return ResetStatsResponse(
        database_stats=db_stats,
        vector_stats=vector_stats,
    )


@router.post("/reset", response_model=ResetResponse)
async def reset_all_data(db: AsyncSessionDep) -> ResetResponse:
    """Reset all data in the database and vector store.

    WARNING: This operation is irreversible!

    Clears:
    - All PostgreSQL tables (properties, documents, policies, etc.)
    - All Pinecone vectors (embeddings)

    Returns summary of what was deleted.
    """
    logger.warning("RESET ALL DATA - Starting full system reset")

    tables_cleared = []
    vector_count_before = None
    vectors_deleted = False

    # Step 1: Get Pinecone stats and clear vectors
    try:
        pinecone = get_pinecone_service()
        if pinecone.api_key and pinecone.host:
            # Get count before deletion
            stats = await pinecone.describe_index_stats()
            vector_count_before = stats.get("totalVectorCount", 0)
            logger.info(f"Pinecone has {vector_count_before} vectors before reset")

            # Delete all vectors
            if vector_count_before > 0:
                await pinecone.delete(delete_all=True)
                vectors_deleted = True
                logger.info("Deleted all Pinecone vectors")
    except PineconeServiceError as e:
        logger.warning(f"Pinecone not configured or error: {e}")
    except Exception as e:
        logger.error(f"Error clearing Pinecone: {e}")
        # Continue with database reset even if Pinecone fails

    # Step 2: Clear all database tables
    # Filter out tables that don't exist to avoid errors
    existing_tables = []
    for table in TABLES_TO_CLEAR:
        try:
            result = await db.execute(text(f"SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = '{table}')"))
            exists = result.scalar()
            if exists:
                existing_tables.append(table)
        except Exception:
            pass

    logger.info(f"Found {len(existing_tables)} existing tables to clear")

    try:
        if existing_tables:
            # Truncate all existing tables in one statement
            all_tables = ", ".join(existing_tables)
            await db.execute(text(f"TRUNCATE TABLE {all_tables} RESTART IDENTITY CASCADE"))
            tables_cleared = list(existing_tables)
            logger.info(f"Truncated {len(tables_cleared)} tables in single statement")

        await db.commit()
        logger.info(f"Database commit successful. Cleared {len(tables_cleared)} tables")

    except Exception as e:
        logger.error(f"Database reset failed: {e}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database reset failed: {str(e)}",
        )

    logger.warning(f"RESET ALL DATA - Complete. Cleared {len(tables_cleared)} tables, vectors deleted: {vectors_deleted}")

    return ResetResponse(
        success=True,
        message=f"Successfully reset all data. Cleared {len(tables_cleared)} tables and {vector_count_before or 0} vectors.",
        tables_cleared=tables_cleared,
        vectors_deleted=vectors_deleted,
        vector_count_before=vector_count_before,
    )
