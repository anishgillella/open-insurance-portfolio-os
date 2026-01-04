"""Gap Detection Thresholds Configuration.

Industry-standard thresholds for coverage gap detection based on:
- Fannie Mae Multifamily Guide
- NAIOP Coinsurance Standards
- Insurance Broker Best Practices
- Commercial RE Insurance Standards
"""

from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class UnderinsuranceThresholds:
    """Thresholds for underinsurance gap detection."""

    # Coverage as percentage of building value
    CRITICAL_PCT: float = 0.80  # < 80% = critical
    WARNING_PCT: float = 0.90  # 80-90% = warning, >= 90% = OK


@dataclass(frozen=True)
class DeductibleThresholds:
    """Thresholds for high deductible gap detection."""

    # Deductible as percentage of TIV
    CRITICAL_PCT: float = 0.05  # > 5% of TIV = critical
    WARNING_PCT: float = 0.03  # 3-5% of TIV = warning

    # Flat deductible thresholds
    WARNING_FLAT: Decimal = Decimal("250000")  # > $250K flat = warning
    CRITICAL_FLAT: Decimal = Decimal("500000")  # > $500K flat = critical


@dataclass(frozen=True)
class ExpirationThresholds:
    """Thresholds for expiration gap detection (in days)."""

    CRITICAL_DAYS: int = 30  # <= 30 days = critical
    WARNING_DAYS: int = 60  # 31-60 days = warning
    INFO_DAYS: int = 90  # 61-90 days = info


@dataclass(frozen=True)
class CoverageRequirements:
    """Required and recommended coverage types."""

    # Must have these coverages
    REQUIRED: tuple = ("property", "general_liability")

    # Recommended based on property characteristics
    UMBRELLA_TIV_THRESHOLD: Decimal = Decimal("5000000")  # Recommend if TIV > $5M
    FLOOD_ZONES: tuple = ("A", "AE", "AH", "AO", "AR", "A99", "V", "VE")  # High-risk zones


@dataclass(frozen=True)
class ValuationThresholds:
    """Thresholds for outdated valuation detection (in years)."""

    WARNING_YEARS: int = 2  # > 2 years = warning
    CRITICAL_YEARS: int = 3  # > 3 years = critical


@dataclass(frozen=True)
class ComplianceTemplates:
    """Lender compliance requirement templates."""

    STANDARD: dict = None  # Set in __post_init__
    FANNIE_MAE: dict = None
    CONSERVATIVE: dict = None

    def __post_init__(self):
        # Standard commercial lender requirements
        object.__setattr__(self, "STANDARD", {
            "name": "Standard Commercial",
            "min_property_coverage_pct": 1.0,  # 100% of building value
            "min_gl_limit": Decimal("1000000"),  # $1M GL minimum
            "min_umbrella_limit": None,  # Not required
            "max_deductible_pct": 0.05,  # 5% max deductible
            "max_deductible_amount": None,
            "requires_flood": False,  # Only if in flood zone
            "requires_earthquake": False,
            "requires_terrorism": False,
            "requires_business_income": False,
        })

        # Fannie Mae multifamily requirements
        object.__setattr__(self, "FANNIE_MAE", {
            "name": "Fannie Mae Multifamily",
            "min_property_coverage_pct": 1.0,  # 100% replacement cost
            "min_gl_limit": Decimal("1000000"),
            "min_umbrella_limit_per_unit": Decimal("1000000"),  # Varies by unit count
            "umbrella_unit_thresholds": {
                50: Decimal("1000000"),  # 1-50 units: $1M
                100: Decimal("2000000"),  # 51-100 units: $2M
                200: Decimal("5000000"),  # 101-200 units: $5M
                999999: Decimal("10000000"),  # 200+ units: $10M
            },
            "max_deductible_pct": 0.05,  # 5% max
            "max_deductible_amount": Decimal("100000"),  # Or $100K, whichever is greater
            "requires_flood": True,  # If in flood zone
            "requires_earthquake": False,  # Market dependent
            "requires_terrorism": False,
            "requires_business_income": True,  # 12 months BI required
        })

        # Conservative/strict lender requirements
        object.__setattr__(self, "CONSERVATIVE", {
            "name": "Conservative",
            "min_property_coverage_pct": 1.0,
            "min_gl_limit": Decimal("2000000"),  # Higher GL
            "min_umbrella_limit": Decimal("5000000"),  # Always require umbrella
            "max_deductible_pct": 0.02,  # 2% max - stricter
            "max_deductible_amount": Decimal("50000"),  # $50K max
            "requires_flood": True,  # Always require
            "requires_earthquake": True,  # Always require
            "requires_terrorism": True,
            "requires_business_income": True,
        })


# Singleton instances for easy import
UNDERINSURANCE = UnderinsuranceThresholds()
DEDUCTIBLE = DeductibleThresholds()
EXPIRATION = ExpirationThresholds()
COVERAGE_REQUIREMENTS = CoverageRequirements()
VALUATION = ValuationThresholds()
COMPLIANCE_TEMPLATES = ComplianceTemplates()


# Gap type constants
class GapType:
    """Gap type identifiers."""

    UNDERINSURANCE = "underinsurance"
    HIGH_DEDUCTIBLE = "high_deductible"
    EXPIRATION = "expiration"
    MISSING_COVERAGE = "missing_coverage"
    MISSING_FLOOD = "missing_flood"
    OUTDATED_VALUATION = "outdated_valuation"
    COMPLIANCE = "compliance"


# Severity levels
class Severity:
    """Severity level identifiers."""

    CRITICAL = "critical"
    WARNING = "warning"
    INFO = "info"
