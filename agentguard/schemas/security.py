from typing import Any, Literal

from pydantic import BaseModel, Field


Decision = Literal["ALLOW", "REVIEW", "DENY"]


class GuardRequest(BaseModel):
    agent_id: str = Field(min_length=1, max_length=128)
    user_id: str = Field(min_length=1, max_length=128)
    role: str = Field(min_length=1, max_length=64)
    task: str = Field(min_length=1, max_length=10_000)
    tool: str = Field(min_length=1, max_length=128)
    arguments: dict[str, Any] = Field(default_factory=dict)


class Finding(BaseModel):
    category: str
    severity: Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"]
    message: str
    field: str


class GuardResponse(BaseModel):
    request_id: str
    decision: Decision
    risk_score: int
    reasons: list[str]
    findings: list[Finding]
    tool: str
    executed: bool = False
    result: Any | None = None
    thinking: str | None = None
    explanation: str | None = None


class ApprovalDecision(BaseModel):
    approved: bool
    reviewer: str = Field(min_length=1, max_length=128)
    note: str = Field(default="", max_length=1000)


class AuditItem(BaseModel):
    request_id: str
    agent_id: str
    user_id: str
    role: str
    tool: str
    decision: str
    risk_score: int
    findings: list[dict[str, Any]]
    reasons: list[str]
    result_summary: str | None
    created_at: str
