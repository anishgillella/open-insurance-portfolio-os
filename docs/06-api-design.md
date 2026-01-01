# API Design

## Overview

This document defines the REST API for Open Insurance. The API is built with FastAPI and follows RESTful conventions with some pragmatic exceptions for better usability.

---

## Design Principles

1. **Resource-oriented** — URLs represent resources (properties, policies, documents)
2. **Consistent responses** — Same structure for success and error
3. **Meaningful status codes** — 200/201/400/401/403/404/500
4. **Pagination by default** — Lists are always paginated
5. **Filtering and sorting** — Query params for common operations
6. **Async-first** — All endpoints are async

---

## Base URL & Versioning

```
Production: https://api.openinsurance.com/v1
Development: http://localhost:8000/v1
```

Versioning is in the URL path. Breaking changes require a new version.

---

## Authentication

### MVP: API Key

```
Authorization: Bearer <api_key>
```

API keys are scoped to an organization.

### Future: JWT + OAuth

```
Authorization: Bearer <jwt_token>
```

With refresh token flow and OAuth providers.

---

## Response Format

### Success Response

```json
{
  "success": true,
  "data": { ... },
  "meta": {
    "request_id": "uuid",
    "timestamp": "2024-01-15T10:30:00Z"
  }
}
```

### Paginated Response

```json
{
  "success": true,
  "data": [ ... ],
  "pagination": {
    "page": 1,
    "page_size": 20,
    "total_items": 150,
    "total_pages": 8,
    "has_next": true,
    "has_prev": false
  },
  "meta": {
    "request_id": "uuid",
    "timestamp": "2024-01-15T10:30:00Z"
  }
}
```

### Error Response

```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid property ID format",
    "details": {
      "field": "property_id",
      "reason": "Must be a valid UUID"
    }
  },
  "meta": {
    "request_id": "uuid",
    "timestamp": "2024-01-15T10:30:00Z"
  }
}
```

---

## Error Codes

| HTTP Status | Code | Meaning |
|-------------|------|---------|
| 400 | `VALIDATION_ERROR` | Invalid request data |
| 400 | `INVALID_FILE_TYPE` | Unsupported file format |
| 401 | `UNAUTHORIZED` | Missing or invalid auth |
| 403 | `FORBIDDEN` | No permission for resource |
| 404 | `NOT_FOUND` | Resource doesn't exist |
| 409 | `CONFLICT` | Resource already exists |
| 422 | `PROCESSING_ERROR` | Business logic error |
| 429 | `RATE_LIMITED` | Too many requests |
| 500 | `INTERNAL_ERROR` | Server error |

---

## Endpoints

### Properties

#### List Properties

```
GET /v1/properties
```

**Query Parameters:**

| Param | Type | Description |
|-------|------|-------------|
| `page` | int | Page number (default: 1) |
| `page_size` | int | Items per page (default: 20, max: 100) |
| `sort` | string | Sort field (default: `name`) |
| `order` | string | `asc` or `desc` (default: `asc`) |
| `status` | string | Filter by status |
| `state` | string | Filter by state |
| `search` | string | Search by name or address |

**Response:**

```json
{
  "success": true,
  "data": [
    {
      "id": "uuid",
      "name": "Buffalo Run",
      "address": "123 Main St",
      "city": "Abilene",
      "state": "TX",
      "zip": "79601",
      "property_type": "multifamily",
      "units": 200,
      "status": "active",
      "completeness_pct": 85.5,
      "current_program": {
        "id": "uuid",
        "program_year": 2024,
        "total_premium": 145000,
        "expiration_date": "2025-01-01",
        "status": "active"
      },
      "created_at": "2024-01-01T00:00:00Z"
    }
  ],
  "pagination": { ... }
}
```

#### Get Property

```
GET /v1/properties/{property_id}
```

**Response:**

```json
{
  "success": true,
  "data": {
    "id": "uuid",
    "name": "Buffalo Run",
    "address": "123 Main St",
    "city": "Abilene",
    "state": "TX",
    "zip": "79601",
    "county": "Taylor",
    "property_type": "multifamily",
    "units": 200,
    "sq_ft": 175000,
    "year_built": 1998,
    "construction_type": "frame",
    "has_sprinklers": true,
    "flood_zone": "X",
    "protection_class": "4",
    "status": "active",
    "completeness_pct": 85.5,
    "programs": [
      {
        "id": "uuid",
        "program_year": 2024,
        "total_premium": 145000,
        "total_insured_value": 35000000,
        "expiration_date": "2025-01-01",
        "status": "active",
        "policies_count": 3
      }
    ],
    "documents_count": 12,
    "gaps_count": 2,
    "created_at": "2024-01-01T00:00:00Z",
    "updated_at": "2024-01-15T10:30:00Z"
  }
}
```

#### Create Property

```
POST /v1/properties
```

**Request:**

```json
{
  "name": "New Property",
  "address": "456 Oak Ave",
  "city": "Austin",
  "state": "TX",
  "zip": "78701",
  "property_type": "multifamily",
  "units": 150
}
```

**Response:** `201 Created` with property object

#### Update Property

```
PATCH /v1/properties/{property_id}
```

**Request:** Partial property object

**Response:** Updated property object

#### Delete Property

```
DELETE /v1/properties/{property_id}
```

**Response:** `204 No Content`

---

### Documents

#### Initiate Upload

```
POST /v1/documents/initiate-upload
```

**Request:**

```json
{
  "filename": "policy_2024.pdf",
  "content_type": "application/pdf",
  "file_size_bytes": 2500000,
  "property_id": "uuid"
}
```

**Response:**

```json
{
  "success": true,
  "data": {
    "document_id": "uuid",
    "upload_url": "https://s3.amazonaws.com/...",
    "upload_method": "PUT",
    "upload_headers": {
      "Content-Type": "application/pdf"
    },
    "expires_at": "2024-01-15T10:45:00Z"
  }
}
```

#### Complete Upload

```
POST /v1/documents/{document_id}/complete-upload
```

**Request:**

```json
{
  "file_size_bytes": 2500000,
  "checksum_sha256": "abc123..."
}
```

**Response:**

```json
{
  "success": true,
  "data": {
    "document_id": "uuid",
    "status": "processing",
    "estimated_completion": "2024-01-15T10:35:00Z"
  }
}
```

#### Get Document

```
GET /v1/documents/{document_id}
```

**Response:**

```json
{
  "success": true,
  "data": {
    "id": "uuid",
    "property_id": "uuid",
    "file_name": "policy_2024.pdf",
    "file_url": "https://...",
    "file_size_bytes": 2500000,
    "page_count": 45,
    "document_type": "policy",
    "document_subtype": "property_policy",
    "carrier": "Seneca Insurance",
    "policy_number": "SPC-12345",
    "effective_date": "2024-01-01",
    "expiration_date": "2025-01-01",
    "upload_status": "uploaded",
    "ocr_status": "completed",
    "extraction_status": "completed",
    "extraction_confidence": 0.92,
    "needs_human_review": false,
    "created_at": "2024-01-15T10:30:00Z",
    "processed_at": "2024-01-15T10:31:00Z"
  }
}
```

#### List Documents

```
GET /v1/documents
GET /v1/properties/{property_id}/documents
```

**Query Parameters:**

| Param | Type | Description |
|-------|------|-------------|
| `property_id` | uuid | Filter by property |
| `document_type` | string | Filter by type |
| `status` | string | Filter by processing status |

#### Get Document Download URL

```
GET /v1/documents/{document_id}/download
```

**Response:**

```json
{
  "success": true,
  "data": {
    "download_url": "https://s3.amazonaws.com/...",
    "expires_at": "2024-01-15T11:00:00Z"
  }
}
```

#### Reprocess Document

```
POST /v1/documents/{document_id}/reprocess
```

**Request:**

```json
{
  "reprocess_ocr": false,
  "reprocess_extraction": true
}
```

---

### Policies

#### List Policies

```
GET /v1/policies
GET /v1/properties/{property_id}/policies
```

**Query Parameters:**

| Param | Type | Description |
|-------|------|-------------|
| `property_id` | uuid | Filter by property |
| `policy_type` | string | Filter by type |
| `program_year` | int | Filter by year |
| `expiring_within_days` | int | Expiring soon filter |

**Response:**

```json
{
  "success": true,
  "data": [
    {
      "id": "uuid",
      "property_id": "uuid",
      "property_name": "Buffalo Run",
      "policy_type": "property",
      "policy_number": "SPC-12345",
      "carrier_name": "Seneca Insurance",
      "effective_date": "2024-01-01",
      "expiration_date": "2025-01-01",
      "premium": 125000,
      "total_cost": 135000,
      "admitted": false,
      "coverages_count": 8,
      "source_document_id": "uuid"
    }
  ]
}
```

#### Get Policy Details

```
GET /v1/policies/{policy_id}
```

**Response:**

```json
{
  "success": true,
  "data": {
    "id": "uuid",
    "property_id": "uuid",
    "program_id": "uuid",
    "document_id": "uuid",
    "policy_type": "property",
    "policy_number": "SPC-12345",
    "carrier_id": "uuid",
    "carrier_name": "Seneca Insurance",
    "effective_date": "2024-01-01",
    "expiration_date": "2025-01-01",
    "premium": 125000,
    "taxes": 7500,
    "fees": 2500,
    "total_cost": 135000,
    "admitted": false,
    "form_type": "occurrence",
    "named_insured": "Buffalo Run Apartments LP",
    "coverages": [
      {
        "id": "uuid",
        "coverage_name": "Building",
        "limit_amount": 35989980,
        "deductible_amount": 50000,
        "deductible_type": "flat",
        "valuation_type": "replacement_cost",
        "extraction_confidence": 0.95
      },
      {
        "id": "uuid",
        "coverage_name": "Business Income",
        "limit_amount": 2500000,
        "waiting_period_hours": 72,
        "extraction_confidence": 0.92
      }
    ],
    "endorsements": [
      {
        "id": "uuid",
        "endorsement_number": "CP 10 30",
        "endorsement_name": "Causes of Loss - Special Form",
        "endorsement_type": "modification"
      }
    ],
    "extraction_confidence": 0.92
  }
}
```

---

### Coverages

#### List Coverages

```
GET /v1/coverages
GET /v1/policies/{policy_id}/coverages
```

#### Get Coverage

```
GET /v1/coverages/{coverage_id}
```

---

### Certificates

#### List Certificates

```
GET /v1/certificates
GET /v1/properties/{property_id}/certificates
```

#### Get Certificate

```
GET /v1/certificates/{certificate_id}
```

---

### Chat / RAG

#### Send Message

```
POST /v1/chat
```

**Request:**

```json
{
  "message": "Is flood covered at Buffalo Run?",
  "property_id": "uuid",
  "conversation_id": "uuid"
}
```

**Response:**

```json
{
  "success": true,
  "data": {
    "conversation_id": "uuid",
    "message_id": "uuid",
    "answer": "Based on your property policy, flood is NOT covered as a standard peril...",
    "confidence": 0.92,
    "sources": [
      {
        "document_id": "uuid",
        "document_type": "policy",
        "document_name": "Property Policy 2024",
        "page_number": 23,
        "excerpt": "We do not cover loss or damage caused by flood...",
        "relevance_score": 0.95
      }
    ],
    "follow_up_questions": [
      "Would you like information about adding flood coverage?",
      "What water damage is covered under your current policy?"
    ]
  }
}
```

#### Stream Message (SSE)

```
POST /v1/chat/stream
```

Returns Server-Sent Events for streaming response.

#### Get Conversation History

```
GET /v1/chat/conversations/{conversation_id}
```

---

### Coverage Gaps

#### List Gaps

```
GET /v1/gaps
GET /v1/properties/{property_id}/gaps
```

**Query Parameters:**

| Param | Type | Description |
|-------|------|-------------|
| `severity` | string | Filter by severity |
| `status` | string | `open`, `acknowledged`, `resolved` |
| `gap_type` | string | Filter by type |

**Response:**

```json
{
  "success": true,
  "data": [
    {
      "id": "uuid",
      "property_id": "uuid",
      "property_name": "Shoaff Park",
      "gap_type": "high_deductible",
      "severity": "warning",
      "title": "Wind deductible exceeds $100,000",
      "description": "Your wind deductible is 5% of building value ($180,000). This is above typical thresholds.",
      "coverage_name": "Wind/Hail",
      "current_value": "5% ($180,000)",
      "recommended_value": "2% ($72,000)",
      "status": "open",
      "detected_at": "2024-01-15T10:30:00Z"
    }
  ]
}
```

#### Acknowledge Gap

```
POST /v1/gaps/{gap_id}/acknowledge
```

#### Resolve Gap

```
POST /v1/gaps/{gap_id}/resolve
```

**Request:**

```json
{
  "resolution_notes": "Discussed with broker, will address at renewal"
}
```

---

### Compliance

#### Check Property Compliance

```
GET /v1/properties/{property_id}/compliance
```

**Response:**

```json
{
  "success": true,
  "data": {
    "property_id": "uuid",
    "property_name": "Buffalo Run",
    "overall_status": "non_compliant",
    "requirements": [
      {
        "id": "uuid",
        "lender_name": "Wells Fargo",
        "loan_number": "123456",
        "checks": [
          {
            "requirement": "Property coverage >= $30,000,000",
            "status": "compliant",
            "current_value": "$35,989,980",
            "required_value": "$30,000,000"
          },
          {
            "requirement": "Wind deductible <= 2%",
            "status": "non_compliant",
            "current_value": "5%",
            "required_value": "2%"
          }
        ]
      }
    ],
    "last_checked_at": "2024-01-15T10:30:00Z"
  }
}
```

#### Set Lender Requirements

```
POST /v1/properties/{property_id}/lender-requirements
```

**Request:**

```json
{
  "lender_id": "uuid",
  "loan_number": "123456",
  "requirements": {
    "min_property_limit": 30000000,
    "max_deductible_pct": 2,
    "requires_flood": true
  }
}
```

---

### Analytics

#### Get Property Summary

```
GET /v1/analytics/property-summary
```

**Response:**

```json
{
  "success": true,
  "data": {
    "total_properties": 7,
    "total_units": 1250,
    "total_insured_value": 125000000,
    "total_premium": 650000,
    "avg_premium_per_unit": 520,
    "expiring_30_days": 2,
    "open_gaps": 5,
    "non_compliant": 1
  }
}
```

#### Get Expiration Timeline

```
GET /v1/analytics/expirations
```

**Query Parameters:**

| Param | Type | Description |
|-------|------|-------------|
| `days_ahead` | int | Days to look ahead (default: 90) |

---

### Carriers

#### List Carriers

```
GET /v1/carriers
```

#### Get Carrier

```
GET /v1/carriers/{carrier_id}
```

---

### Lenders

#### List Lenders

```
GET /v1/lenders
```

#### Get Lender

```
GET /v1/lenders/{lender_id}
```

---

## Webhooks (Future)

### Event Types

| Event | Trigger |
|-------|---------|
| `document.processed` | Document extraction complete |
| `document.failed` | Document processing failed |
| `gap.detected` | New coverage gap found |
| `policy.expiring` | Policy expiring within threshold |
| `compliance.changed` | Compliance status changed |

### Webhook Payload

```json
{
  "event": "document.processed",
  "timestamp": "2024-01-15T10:30:00Z",
  "data": {
    "document_id": "uuid",
    "property_id": "uuid",
    "document_type": "policy",
    "extraction_confidence": 0.92
  }
}
```

---

## Rate Limiting

| Endpoint Category | Limit |
|-------------------|-------|
| Read endpoints | 1000 req/min |
| Write endpoints | 100 req/min |
| Chat endpoints | 30 req/min |
| Upload endpoints | 20 req/min |

Rate limit headers:
```
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 950
X-RateLimit-Reset: 1705312800
```

---

## OpenAPI Specification

Full OpenAPI 3.0 spec available at:
```
GET /v1/openapi.json
GET /v1/docs  (Swagger UI)
GET /v1/redoc (ReDoc)
```

---

## Key Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| REST over GraphQL | REST | Simpler for MVP, team familiarity |
| Presigned URLs | Yes | Scalable file uploads |
| Pagination default | Yes | Prevent accidental large responses |
| Soft deletes via API | No | Hard delete, use DB soft delete |
| Streaming for chat | SSE | Better UX for long responses |

---

## Next Steps

Proceed to [07-mvp-features.md](./07-mvp-features.md) for detailed feature specifications.