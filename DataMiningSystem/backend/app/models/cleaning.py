from pydantic import BaseModel
from typing import List, Optional, Any, Dict

class CleaningItem(BaseModel):
    id: str
    column: Optional[str] = None
    issue_type: str
    severity: str  # CRITICAL, HIGH, MEDIUM, LOW
    current_state: str
    proposed_action: str
    method: str
    reason: str
    confidence: int
    risk: str  # SAFE or REVIEW_REQUIRED
    affected_rows: int
    approved: bool = False
    category: str  # TYPE_CONVERSION, MISSING_VALUE, DUPLICATE, OUTLIER
    metadata: Optional[Dict[str, Any]] = None

class CleaningPlanResponse(BaseModel):
    total_items: int
    safe_count: int
    review_required_count: int
    items: List[CleaningItem]

class CleaningExecutionPayload(BaseModel):
    approved_item_ids: List[str]

class AuditLogEntry(BaseModel):
    timestamp: str
    column: str
    issue: str
    operation: str
    method: str
    old_type: str
    new_type: str
    rows_affected: int
    user_approved: bool
    reason: str
    confidence: int

class ValidationSummary(BaseModel):
    rows_before: int
    rows_after: int
    columns_before: int
    columns_after: int
    missing_cells_before: int
    missing_cells_after: int
    duplicates_before: int
    duplicates_after: int
    type_conversions_applied: int
    approved_operations_count: int
    rejected_operations_count: int
    remaining_issues_count: int

class ExecutionResponse(BaseModel):
    summary: ValidationSummary
    audit_log: List[AuditLogEntry]
    preview_data: List[Dict[str, Any]]