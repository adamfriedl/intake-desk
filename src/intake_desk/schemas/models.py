from datetime import datetime
from enum import Enum
from typing import Literal
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class MatterType(str, Enum):
    TENANT_HOUSING = "tenant_housing"
    CONSUMER_DEBT = "consumer_debt"
    BENEFITS_DENIAL = "benefits_denial"
    UNKNOWN = "unknown"


class DraftSectionStatus(str, Enum):
    DRAFT = "draft"
    NEEDS_REVIEW = "needs_review"
    BLOCKED = "blocked"


class IntakeRecord(BaseModel):
    session_id: UUID = Field(default_factory=uuid4)
    parties: list[str] = Field(default_factory=list)
    jurisdiction: str | None = None
    facts: list[str] = Field(default_factory=list)
    relief_sought: str | None = None
    urgency: Literal["low", "medium", "high"] = "medium"
    flags: list[str] = Field(default_factory=list)


class MatterClassification(BaseModel):
    matter_type: MatterType
    confidence: float = Field(ge=0.0, le=1.0)
    routing: str
    human_review_required: bool = False
    rationale: str | None = None


class RetrievalCitation(BaseModel):
    chunk_id: str
    source: str
    quoted_span: str
    relevance_score: float = Field(ge=0.0, le=1.0)


class DraftSection(BaseModel):
    title: str
    content: str
    status: DraftSectionStatus = DraftSectionStatus.NEEDS_REVIEW


class DraftOutline(BaseModel):
    matter_type: MatterType
    sections: list[DraftSection] = Field(default_factory=list)
    disclaimer: str = (
        "This outline is decision-support only, not legal advice. "
        "Review with a qualified advocate before taking action."
    )


class PipelineStepLog(BaseModel):
    step: str
    started_at: datetime
    completed_at: datetime | None = None
    status: Literal["pending", "running", "completed", "failed", "skipped"] = "pending"
    detail: str | None = None


class PipelineResult(BaseModel):
    session_id: UUID = Field(default_factory=uuid4)
    intake: IntakeRecord
    classification: MatterClassification
    citations: list[RetrievalCitation] = Field(default_factory=list)
    draft_outline: DraftOutline | None = None
    answer: str | None = None
    refused: bool = False
    refusal_reason: str | None = None
    audit_log: list[PipelineStepLog] = Field(default_factory=list)
