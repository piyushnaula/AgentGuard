from sqlalchemy import select
from sqlalchemy.orm import Session

from agentguard.db.models import AuditEvent
from agentguard.schemas.security import GuardRequest, GuardResponse


def record(
    db: Session,
    request: GuardRequest,
    response: GuardResponse,
    result_summary: str | None = None,
) -> AuditEvent:
    event = AuditEvent(
        request_id=response.request_id,
        agent_id=request.agent_id,
        user_id=request.user_id,
        role=request.role,
        tool=request.tool,
        decision=response.decision,
        risk_score=response.risk_score,
        findings=[item.model_dump() for item in response.findings],
        reasons=response.reasons,
        result_summary=result_summary,
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    return event


def recent(db: Session, limit: int = 50) -> list[AuditEvent]:
    stmt = select(AuditEvent).order_by(AuditEvent.id.desc()).limit(max(1, min(limit, 200)))
    return list(db.scalars(stmt).all())
