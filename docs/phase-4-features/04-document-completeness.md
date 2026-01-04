# Document Completeness Tracker

## Overview

The Document Completeness Tracker shows what insurance documents are present vs expected for each property. It helps users understand their documentation status and identify missing documents that should be uploaded.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                     DOCUMENT COMPLETENESS SYSTEM                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                    EXPECTED DOCUMENTS CONFIG                         │   │
│  │  ┌──────────────────────────────────────────────────────────────┐   │   │
│  │  │  REQUIRED DOCUMENTS                                          │   │   │
│  │  │  ├── Property Policy (or Certificate)                       │   │   │
│  │  │  ├── GL Policy (or Certificate)                             │   │   │
│  │  │  └── Certificate of Insurance (COI)                         │   │   │
│  │  └──────────────────────────────────────────────────────────────┘   │   │
│  │  ┌──────────────────────────────────────────────────────────────┐   │   │
│  │  │  OPTIONAL DOCUMENTS                                          │   │   │
│  │  │  ├── Umbrella Policy                                         │   │   │
│  │  │  ├── Statement of Values (SOV)                               │   │   │
│  │  │  ├── Loss Runs                                               │   │   │
│  │  │  ├── Invoice                                                 │   │   │
│  │  │  ├── Insurance Proposal                                      │   │   │
│  │  │  └── Endorsements                                            │   │   │
│  │  └──────────────────────────────────────────────────────────────┘   │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                        │
│                                    ▼                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                    COMPLETENESS CALCULATOR                           │   │
│  │                                                                     │   │
│  │  Score = (Required Present / Required Total × 60%)                  │   │
│  │        + (Optional Present / Optional Total × 40%)                  │   │
│  │                                                                     │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                        │
│                                    ▼                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                    COMPLETENESS REPORT                               │   │
│  │  ┌──────────────────────────────────────────────────────────────┐   │   │
│  │  │  Property: Buffalo Run                                       │   │   │
│  │  │  Completeness: 85%  ████████░░                              │   │   │
│  │  │  Required: 3/3 ✓    Optional: 4/6                           │   │   │
│  │  │  Missing: Invoice, Endorsements                              │   │   │
│  │  └──────────────────────────────────────────────────────────────┘   │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Expected Documents Configuration

### Default Configuration

```yaml
# document_completeness_config.yaml

required_documents:
  - type: policy
    subtypes:
      - property
      - general_liability
    description: "Full policy documents for property and liability coverage"
    importance: "Required for complete coverage verification"

  - type: coi
    description: "Certificate of Insurance showing current coverage"
    importance: "Required for lender and vendor verification"

optional_documents:
  - type: policy
    subtypes:
      - umbrella
    description: "Umbrella/excess liability policy"
    importance: "Provides additional liability protection"

  - type: sov
    description: "Statement of Values listing all properties and values"
    importance: "Ensures accurate property valuations"

  - type: loss_run
    description: "Claims history from carriers"
    importance: "Needed for renewals and risk assessment"

  - type: invoice
    description: "Premium invoices and payment records"
    importance: "Verifies premium amounts and payment status"

  - type: proposal
    description: "Insurance proposals from brokers"
    importance: "Useful for comparing coverage options"

  - type: endorsement
    description: "Policy endorsements and amendments"
    importance: "Documents coverage modifications"

# Weight for completeness calculation
weights:
  required: 60  # Required documents = 60% of score
  optional: 40  # Optional documents = 40% of score
```

---

## Completeness Calculation

### Formula

```
Completeness % = (Required Score × 0.6) + (Optional Score × 0.4)

Where:
  Required Score = (Required Documents Present / Required Documents Total) × 100
  Optional Score = (Optional Documents Present / Optional Documents Total) × 100
```

### Examples

**Example 1: Fully Complete**
```
Required: 3/3 (Policy, GL, COI) = 100%
Optional: 6/6 (Umbrella, SOV, Loss Runs, Invoice, Proposal, Endorsements) = 100%

Completeness = (100 × 0.6) + (100 × 0.4) = 100%
```

**Example 2: Minimum Required Only**
```
Required: 3/3 = 100%
Optional: 0/6 = 0%

Completeness = (100 × 0.6) + (0 × 0.4) = 60%
```

**Example 3: Missing Required Documents**
```
Required: 2/3 (missing GL) = 66.7%
Optional: 3/6 = 50%

Completeness = (66.7 × 0.6) + (50 × 0.4) = 60%
```

---

## Document Matching Logic

### Matching Documents to Expected Types

```python
def get_document_completeness(
    property_id: UUID,
    documents: List[Document]
) -> CompletenessResult:
    """Calculate document completeness for a property."""

    config = get_completeness_config()

    # Track what we have
    present = {
        "property_policy": False,
        "gl_policy": False,
        "umbrella_policy": False,
        "coi": False,
        "sov": False,
        "loss_run": False,
        "invoice": False,
        "proposal": False,
        "endorsement": False,
    }

    for doc in documents:
        if doc.document_type == "policy":
            if doc.policy_type == "property":
                present["property_policy"] = True
            elif doc.policy_type == "general_liability":
                present["gl_policy"] = True
            elif doc.policy_type == "umbrella":
                present["umbrella_policy"] = True
        elif doc.document_type == "coi":
            present["coi"] = True
        elif doc.document_type == "sov":
            present["sov"] = True
        elif doc.document_type == "loss_run":
            present["loss_run"] = True
        elif doc.document_type == "invoice":
            present["invoice"] = True
        elif doc.document_type == "proposal":
            present["proposal"] = True
        elif doc.document_type == "endorsement":
            present["endorsement"] = True

    # Calculate scores
    required_docs = ["property_policy", "gl_policy", "coi"]
    optional_docs = ["umbrella_policy", "sov", "loss_run", "invoice", "proposal", "endorsement"]

    required_present = sum(1 for d in required_docs if present[d])
    optional_present = sum(1 for d in optional_docs if present[d])

    required_score = (required_present / len(required_docs)) * 100
    optional_score = (optional_present / len(optional_docs)) * 100

    completeness = (required_score * 0.6) + (optional_score * 0.4)

    return CompletenessResult(
        property_id=property_id,
        percentage=round(completeness, 1),
        required_present=required_present,
        required_total=len(required_docs),
        optional_present=optional_present,
        optional_total=len(optional_docs),
        documents_status=present,
        missing_required=[d for d in required_docs if not present[d]],
        missing_optional=[d for d in optional_docs if not present[d]]
    )
```

---

## API Endpoints

### Get Property Completeness

#### `GET /v1/properties/{id}/completeness`

Returns document completeness for a property.

**Response:**
```json
{
  "property_id": "uuid",
  "property_name": "Buffalo Run",
  "completeness": {
    "percentage": 85.0,
    "grade": "B",
    "required_present": 3,
    "required_total": 3,
    "optional_present": 4,
    "optional_total": 6
  },
  "documents": {
    "required": [
      {
        "type": "property_policy",
        "label": "Property Policy",
        "status": "present",
        "document_id": "uuid",
        "filename": "buffalo_run_property_2024.pdf",
        "uploaded_at": "2024-02-20T10:00:00Z"
      },
      {
        "type": "gl_policy",
        "label": "General Liability Policy",
        "status": "present",
        "document_id": "uuid",
        "filename": "buffalo_run_gl_2024.pdf",
        "uploaded_at": "2024-02-20T10:05:00Z"
      },
      {
        "type": "coi",
        "label": "Certificate of Insurance",
        "status": "present",
        "document_id": "uuid",
        "filename": "buffalo_run_coi.pdf",
        "uploaded_at": "2024-02-20T10:10:00Z"
      }
    ],
    "optional": [
      {
        "type": "umbrella_policy",
        "label": "Umbrella Policy",
        "status": "present",
        "document_id": "uuid",
        "filename": "umbrella_2024.pdf"
      },
      {
        "type": "sov",
        "label": "Statement of Values",
        "status": "present",
        "document_id": "uuid",
        "filename": "sov_2024.xlsx"
      },
      {
        "type": "loss_run",
        "label": "Loss Runs",
        "status": "present",
        "document_id": "uuid",
        "filename": "loss_runs_5yr.pdf"
      },
      {
        "type": "invoice",
        "label": "Premium Invoice",
        "status": "present",
        "document_id": "uuid",
        "filename": "invoice_2024.pdf"
      },
      {
        "type": "proposal",
        "label": "Insurance Proposal",
        "status": "missing",
        "document_id": null,
        "importance": "Useful for comparing coverage options"
      },
      {
        "type": "endorsement",
        "label": "Endorsements",
        "status": "missing",
        "document_id": null,
        "importance": "Documents coverage modifications"
      }
    ]
  },
  "calculated_at": "2025-01-15T10:00:00Z"
}
```

**Grades:**
| Percentage | Grade |
|------------|-------|
| 90-100% | A |
| 80-89% | B |
| 70-79% | C |
| 60-69% | D |
| < 60% | F |

---

### Get Portfolio Completeness

#### `GET /v1/completeness/summary`

Returns completeness summary across all properties.

**Response:**
```json
{
  "summary": {
    "average_completeness": 78.5,
    "fully_complete_count": 3,
    "missing_required_count": 2,
    "total_properties": 7
  },
  "distribution": {
    "A": 2,
    "B": 3,
    "C": 1,
    "D": 1,
    "F": 0
  },
  "most_common_missing": [
    {
      "type": "loss_run",
      "label": "Loss Runs",
      "missing_count": 4,
      "percentage_missing": 57.1
    },
    {
      "type": "proposal",
      "label": "Insurance Proposal",
      "missing_count": 5,
      "percentage_missing": 71.4
    }
  ],
  "properties": [
    {
      "id": "uuid",
      "name": "Buffalo Run",
      "completeness": 85.0,
      "grade": "B",
      "missing_required": 0,
      "missing_optional": 2
    },
    {
      "id": "uuid",
      "name": "Shoaff Park",
      "completeness": 60.0,
      "grade": "D",
      "missing_required": 1,
      "missing_optional": 3
    }
  ]
}
```

---

### Mark Document as N/A

#### `POST /v1/properties/{id}/completeness/not-applicable`

Mark a document type as not applicable for this property.

**Request Body:**
```json
{
  "document_type": "endorsement",
  "reason": "No endorsements for this policy period"
}
```

**Response:**
```json
{
  "property_id": "uuid",
  "document_type": "endorsement",
  "status": "not_applicable",
  "reason": "No endorsements for this policy period",
  "marked_at": "2025-01-15T10:00:00Z"
}
```

**Effect:** Document is excluded from completeness calculation.

---

## Implementation

### Completeness Service

```python
# app/services/completeness/service.py

from dataclasses import dataclass
from typing import List, Optional
from uuid import UUID

@dataclass
class DocumentStatus:
    type: str
    label: str
    status: str  # "present", "missing", "not_applicable"
    document_id: Optional[UUID]
    filename: Optional[str]
    importance: Optional[str]

@dataclass
class CompletenessResult:
    property_id: UUID
    percentage: float
    grade: str
    required_present: int
    required_total: int
    optional_present: int
    optional_total: int
    required_documents: List[DocumentStatus]
    optional_documents: List[DocumentStatus]


class CompletenessService:
    REQUIRED_DOCUMENTS = [
        ("property_policy", "Property Policy"),
        ("gl_policy", "General Liability Policy"),
        ("coi", "Certificate of Insurance"),
    ]

    OPTIONAL_DOCUMENTS = [
        ("umbrella_policy", "Umbrella Policy"),
        ("sov", "Statement of Values"),
        ("loss_run", "Loss Runs"),
        ("invoice", "Premium Invoice"),
        ("proposal", "Insurance Proposal"),
        ("endorsement", "Endorsements"),
    ]

    def __init__(
        self,
        document_repo: DocumentRepository,
        na_repo: NotApplicableRepository
    ):
        self.document_repo = document_repo
        self.na_repo = na_repo

    async def get_completeness(
        self,
        property_id: UUID
    ) -> CompletenessResult:
        """Calculate document completeness for a property."""

        documents = await self.document_repo.get_by_property(property_id)
        na_items = await self.na_repo.get_by_property(property_id)
        na_types = {item.document_type for item in na_items}

        # Map documents to types
        doc_map = self._map_documents_to_types(documents)

        # Build required documents status
        required_docs = []
        required_present = 0
        for doc_type, label in self.REQUIRED_DOCUMENTS:
            if doc_type in na_types:
                continue  # Skip N/A items

            doc = doc_map.get(doc_type)
            if doc:
                required_docs.append(DocumentStatus(
                    type=doc_type,
                    label=label,
                    status="present",
                    document_id=doc.id,
                    filename=doc.filename,
                    importance=None
                ))
                required_present += 1
            else:
                required_docs.append(DocumentStatus(
                    type=doc_type,
                    label=label,
                    status="missing",
                    document_id=None,
                    filename=None,
                    importance=self._get_importance(doc_type)
                ))

        # Build optional documents status
        optional_docs = []
        optional_present = 0
        for doc_type, label in self.OPTIONAL_DOCUMENTS:
            if doc_type in na_types:
                optional_docs.append(DocumentStatus(
                    type=doc_type,
                    label=label,
                    status="not_applicable",
                    document_id=None,
                    filename=None,
                    importance=None
                ))
                continue

            doc = doc_map.get(doc_type)
            if doc:
                optional_docs.append(DocumentStatus(
                    type=doc_type,
                    label=label,
                    status="present",
                    document_id=doc.id,
                    filename=doc.filename,
                    importance=None
                ))
                optional_present += 1
            else:
                optional_docs.append(DocumentStatus(
                    type=doc_type,
                    label=label,
                    status="missing",
                    document_id=None,
                    filename=None,
                    importance=self._get_importance(doc_type)
                ))

        # Calculate percentage
        required_total = len([d for d in required_docs if d.status != "not_applicable"])
        optional_total = len([d for d in optional_docs if d.status != "not_applicable"])

        required_score = (required_present / required_total * 100) if required_total > 0 else 100
        optional_score = (optional_present / optional_total * 100) if optional_total > 0 else 100

        percentage = (required_score * 0.6) + (optional_score * 0.4)
        grade = self._calculate_grade(percentage)

        return CompletenessResult(
            property_id=property_id,
            percentage=round(percentage, 1),
            grade=grade,
            required_present=required_present,
            required_total=required_total,
            optional_present=optional_present,
            optional_total=optional_total,
            required_documents=required_docs,
            optional_documents=optional_docs
        )

    def _map_documents_to_types(
        self,
        documents: List[Document]
    ) -> dict:
        """Map documents to expected document types."""
        doc_map = {}

        for doc in documents:
            if doc.document_type == "policy":
                if doc.policy_type == "property":
                    doc_map["property_policy"] = doc
                elif doc.policy_type == "general_liability":
                    doc_map["gl_policy"] = doc
                elif doc.policy_type == "umbrella":
                    doc_map["umbrella_policy"] = doc
            elif doc.document_type == "coi":
                doc_map["coi"] = doc
            elif doc.document_type == "sov":
                doc_map["sov"] = doc
            elif doc.document_type == "loss_run":
                doc_map["loss_run"] = doc
            elif doc.document_type == "invoice":
                doc_map["invoice"] = doc
            elif doc.document_type == "proposal":
                doc_map["proposal"] = doc
            elif doc.document_type == "endorsement":
                doc_map["endorsement"] = doc

        return doc_map

    def _calculate_grade(self, percentage: float) -> str:
        if percentage >= 90:
            return "A"
        elif percentage >= 80:
            return "B"
        elif percentage >= 70:
            return "C"
        elif percentage >= 60:
            return "D"
        else:
            return "F"

    def _get_importance(self, doc_type: str) -> str:
        importance_map = {
            "property_policy": "Required for complete coverage verification",
            "gl_policy": "Required for complete coverage verification",
            "coi": "Required for lender and vendor verification",
            "umbrella_policy": "Provides additional liability protection",
            "sov": "Ensures accurate property valuations",
            "loss_run": "Needed for renewals and risk assessment",
            "invoice": "Verifies premium amounts and payment status",
            "proposal": "Useful for comparing coverage options",
            "endorsement": "Documents coverage modifications",
        }
        return importance_map.get(doc_type, "")
```

---

## Integration Points

### Dashboard Summary

The completeness data feeds into the dashboard summary:

```python
# In dashboard service
completeness_stats = {
    "average_completeness": await completeness_service.get_portfolio_average(),
    "fully_complete_properties": await completeness_service.count_fully_complete(),
    "properties_missing_required_docs": await completeness_service.count_missing_required()
}
```

### Health Score

Completeness contributes to the Insurance Health Score:

```python
# Documentation quality component (10% of health score)
documentation_score = completeness.percentage / 10  # Max 10 points
```

---

## UI Considerations

### Progress Visualization

```
Buffalo Run                              85% ████████░░
├── Required Documents: 3/3 ✓
│   ✓ Property Policy
│   ✓ General Liability Policy
│   ✓ Certificate of Insurance
└── Optional Documents: 4/6
    ✓ Umbrella Policy
    ✓ Statement of Values
    ✓ Loss Runs
    ✓ Invoice
    ✗ Insurance Proposal     [Upload]
    ✗ Endorsements           [Upload]
```

### Quick Actions

- **Upload Missing** - Direct upload link for each missing document
- **Mark as N/A** - Mark document as not applicable
- **View Document** - Open existing document

---

## Related Documents

- [01-dashboard-api.md](./01-dashboard-api.md) - Completeness in dashboard summary
- [05-insurance-health-score.md](./05-insurance-health-score.md) - Completeness affects health score
- [02-gap-detection.md](./02-gap-detection.md) - Missing documents can create gaps
