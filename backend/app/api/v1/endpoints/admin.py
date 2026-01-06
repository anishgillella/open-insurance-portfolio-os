"""Admin API endpoints for system management.

Provides administrative operations like resetting all data.
"""

import logging
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import func, select, text, update

from app.core.dependencies import AsyncSessionDep
from app.models.coverage_gap import CoverageGap
from app.models.document import Document
from app.models.property import Property
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


# ============ Duplicate Property Detection & Merge ============


class DuplicatePropertyGroup(BaseModel):
    """A group of duplicate properties (same name, different IDs)."""

    normalized_name: str = Field(..., description="Normalized property name (lowercase, trimmed)")
    properties: list[dict[str, Any]] = Field(..., description="List of property info with id, name, document_count")


class DuplicatePropertiesResponse(BaseModel):
    """Response with duplicate property groups."""

    duplicate_groups: list[DuplicatePropertyGroup] = Field(
        default_factory=list, description="Groups of duplicate properties"
    )
    total_duplicates: int = Field(default=0, description="Total number of duplicate property records")


class MergePropertiesRequest(BaseModel):
    """Request to merge duplicate properties."""

    property_ids_to_merge: list[str] = Field(..., description="Property IDs to merge (documents will be moved)")
    target_property_id: str = Field(..., description="Property ID to keep (documents will be moved here)")


class MergePropertiesResponse(BaseModel):
    """Response from merging properties."""

    success: bool
    message: str
    documents_moved: int = 0
    properties_deleted: int = 0


@router.get("/duplicate-properties", response_model=DuplicatePropertiesResponse)
async def find_duplicate_properties(db: AsyncSessionDep) -> DuplicatePropertiesResponse:
    """Find duplicate properties (same name with different IDs).

    This detects properties that have the same name (case-insensitive, trimmed)
    but different IDs. These duplicates can occur when:
    - Property names differ only by case (AHJ vs ahj)
    - Property names have trailing/leading whitespace
    - Race conditions during concurrent uploads

    Returns groups of duplicate properties for review/merge.
    """
    # Find all properties grouped by normalized name
    # Using lowercase and trim for normalization
    stmt = (
        select(
            func.lower(func.trim(Property.name)).label("normalized_name"),
            func.count(Property.id).label("count"),
        )
        .where(Property.deleted_at.is_(None))
        .group_by(func.lower(func.trim(Property.name)))
        .having(func.count(Property.id) > 1)
    )

    result = await db.execute(stmt)
    duplicate_names = result.all()

    duplicate_groups = []
    total_duplicates = 0

    for row in duplicate_names:
        normalized_name = row.normalized_name
        # Get all properties with this normalized name
        props_stmt = (
            select(Property)
            .where(
                Property.deleted_at.is_(None),
                func.lower(func.trim(Property.name)) == normalized_name,
            )
            .order_by(Property.created_at)
        )
        props_result = await db.execute(props_stmt)
        properties = props_result.scalars().all()

        # Get document counts for each property
        property_infos = []
        for prop in properties:
            doc_count_stmt = select(func.count(Document.id)).where(
                Document.property_id == prop.id,
                Document.deleted_at.is_(None),
            )
            doc_count_result = await db.execute(doc_count_stmt)
            doc_count = doc_count_result.scalar() or 0

            property_infos.append({
                "id": prop.id,
                "name": prop.name,
                "document_count": doc_count,
                "created_at": prop.created_at.isoformat() if prop.created_at else None,
            })

        duplicate_groups.append(
            DuplicatePropertyGroup(
                normalized_name=normalized_name,
                properties=property_infos,
            )
        )
        total_duplicates += len(properties)

    return DuplicatePropertiesResponse(
        duplicate_groups=duplicate_groups,
        total_duplicates=total_duplicates,
    )


@router.post("/merge-properties", response_model=MergePropertiesResponse)
async def merge_duplicate_properties(
    request: MergePropertiesRequest,
    db: AsyncSessionDep,
) -> MergePropertiesResponse:
    """Merge duplicate properties by moving documents to a target property.

    This endpoint:
    1. Moves all documents from source properties to the target property
    2. Soft-deletes the source properties (sets deleted_at)

    Use GET /admin/duplicate-properties first to identify duplicates.

    WARNING: This operation modifies data. Review duplicates carefully before merging.
    """
    # Validate target property exists
    target_stmt = select(Property).where(
        Property.id == request.target_property_id,
        Property.deleted_at.is_(None),
    )
    target_result = await db.execute(target_stmt)
    target_property = target_result.scalar_one_or_none()

    if not target_property:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Target property {request.target_property_id} not found",
        )

    # Ensure target is not in the merge list
    if request.target_property_id in request.property_ids_to_merge:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Target property cannot be in the list of properties to merge",
        )

    # Validate source properties exist
    source_stmt = select(Property).where(
        Property.id.in_(request.property_ids_to_merge),
        Property.deleted_at.is_(None),
    )
    source_result = await db.execute(source_stmt)
    source_properties = source_result.scalars().all()

    if len(source_properties) != len(request.property_ids_to_merge):
        found_ids = {p.id for p in source_properties}
        missing_ids = set(request.property_ids_to_merge) - found_ids
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Properties not found: {list(missing_ids)}",
        )

    # Move documents from source properties to target
    documents_moved = 0
    for source_property in source_properties:
        update_stmt = (
            update(Document)
            .where(
                Document.property_id == source_property.id,
                Document.deleted_at.is_(None),
            )
            .values(property_id=request.target_property_id)
        )
        result = await db.execute(update_stmt)
        documents_moved += result.rowcount
        logger.info(
            f"Moved {result.rowcount} documents from property {source_property.id} "
            f"({source_property.name}) to {request.target_property_id}"
        )

    # Move coverage gaps from source properties to target
    gaps_moved = 0
    for source_property in source_properties:
        update_stmt = (
            update(CoverageGap)
            .where(
                CoverageGap.property_id == source_property.id,
                CoverageGap.deleted_at.is_(None),
            )
            .values(property_id=request.target_property_id)
        )
        result = await db.execute(update_stmt)
        gaps_moved += result.rowcount
        logger.info(
            f"Moved {result.rowcount} coverage gaps from property {source_property.id} "
            f"({source_property.name}) to {request.target_property_id}"
        )

    # Soft-delete source properties
    for source_property in source_properties:
        source_property.deleted_at = datetime.now(timezone.utc)

    await db.commit()

    logger.info(
        f"Merged {len(source_properties)} properties into {request.target_property_id}. "
        f"Moved {documents_moved} documents, {gaps_moved} coverage gaps."
    )

    return MergePropertiesResponse(
        success=True,
        message=f"Successfully merged {len(source_properties)} properties. Moved {documents_moved} documents and {gaps_moved} coverage gaps.",
        documents_moved=documents_moved,
        properties_deleted=len(source_properties),
    )


# ============ Orphaned Gaps Fix ============


class OrphanedGapsResponse(BaseModel):
    """Response from fixing orphaned gaps."""

    success: bool
    message: str
    gaps_reassigned: int = 0
    gaps_deleted: int = 0
    orphaned_property_ids: list[str] = Field(default_factory=list)


@router.post("/fix-orphaned-gaps", response_model=OrphanedGapsResponse)
async def fix_orphaned_gaps(db: AsyncSessionDep) -> OrphanedGapsResponse:
    """Fix coverage gaps that reference deleted properties.

    This finds gaps where the property_id points to a deleted property,
    and reassigns them to an active property with the same name.

    If no matching active property exists, the gaps are deleted.
    """
    # Find all gaps with their property status
    # Get gaps where property is deleted or doesn't exist
    gaps_stmt = (
        select(CoverageGap, Property)
        .outerjoin(Property, CoverageGap.property_id == Property.id)
        .where(CoverageGap.deleted_at.is_(None))
    )
    result = await db.execute(gaps_stmt)
    rows = result.all()

    # Separate orphaned gaps
    orphaned_gaps = []
    orphaned_property_ids = set()
    for gap, prop in rows:
        if prop is None or prop.deleted_at is not None:
            orphaned_gaps.append((gap, prop))
            orphaned_property_ids.add(gap.property_id)

    if not orphaned_gaps:
        return OrphanedGapsResponse(
            success=True,
            message="No orphaned gaps found.",
            gaps_reassigned=0,
            gaps_deleted=0,
            orphaned_property_ids=[],
        )

    logger.info(f"Found {len(orphaned_gaps)} orphaned gaps from {len(orphaned_property_ids)} deleted properties")

    # Build mapping of deleted property names to active property IDs
    # Get all active properties
    active_props_stmt = select(Property).where(Property.deleted_at.is_(None))
    active_props_result = await db.execute(active_props_stmt)
    active_properties = active_props_result.scalars().all()

    # Create name -> ID mapping (normalized)
    name_to_active_id: dict[str, str] = {}
    for prop in active_properties:
        normalized = prop.name.strip().lower()
        name_to_active_id[normalized] = prop.id

    # Process orphaned gaps
    gaps_reassigned = 0
    gaps_deleted = 0

    for gap, deleted_prop in orphaned_gaps:
        # Try to find matching active property by name
        target_id = None
        if deleted_prop and deleted_prop.name:
            normalized_name = deleted_prop.name.strip().lower()
            target_id = name_to_active_id.get(normalized_name)

        if target_id:
            # Reassign gap to active property
            gap.property_id = target_id
            gaps_reassigned += 1
            logger.info(f"Reassigned gap {gap.id} from deleted property to {target_id}")
        else:
            # No matching property - delete the gap
            gap.deleted_at = datetime.now(timezone.utc)
            gaps_deleted += 1
            logger.info(f"Deleted orphaned gap {gap.id} - no matching active property")

    await db.commit()

    return OrphanedGapsResponse(
        success=True,
        message=f"Fixed {len(orphaned_gaps)} orphaned gaps. Reassigned {gaps_reassigned}, deleted {gaps_deleted}.",
        gaps_reassigned=gaps_reassigned,
        gaps_deleted=gaps_deleted,
        orphaned_property_ids=list(orphaned_property_ids),
    )
