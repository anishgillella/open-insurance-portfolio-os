"""SQLAlchemy models package.

All models are imported here for Alembic to discover them.
"""

from app.core.database import Base
from app.models.base import BaseModel
from app.models.building import Building
from app.models.carrier import Carrier
from app.models.certificate import Certificate
from app.models.claim import Claim
from app.models.coverage import Coverage
from app.models.coverage_gap import CoverageGap
from app.models.document import Document
from app.models.document_chunk import DocumentChunk
from app.models.endorsement import Endorsement
from app.models.extracted_fact import ExtractedFact
from app.models.financial import Financial
from app.models.insurance_program import InsuranceProgram
from app.models.insured_entity import InsuredEntity
from app.models.lender import Lender
from app.models.lender_requirement import LenderRequirement
from app.models.organization import Organization
from app.models.policy import Policy
from app.models.property import Property
from app.models.valuation import Valuation

__all__ = [
    "Base",
    "BaseModel",
    "Building",
    "Carrier",
    "Certificate",
    "Claim",
    "Coverage",
    "CoverageGap",
    "Document",
    "DocumentChunk",
    "Endorsement",
    "ExtractedFact",
    "Financial",
    "InsuranceProgram",
    "InsuredEntity",
    "Lender",
    "LenderRequirement",
    "Organization",
    "Policy",
    "Property",
    "Valuation",
]
