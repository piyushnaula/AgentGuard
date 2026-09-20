from sqlalchemy import select

from agentguard.schemas.security import GuardRequest
from sqlalchemy.orm import Session

from agentguard.db.models import ApprovalRequest


def create(db: Session, request_id: str, request: GuardRequest) -> ApprovalRequest:
    item = ApprovalRequest(
        request_id=request_id,
        status="PENDING",
        payload=request.model_dump(),
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


def get(db: Session, request_id: str) -> ApprovalRequest | None:
    stmt = select(ApprovalRequest).where(ApprovalRequest.request_id == request_id)
    return db.scalar(stmt)


def decide(db: Session, request_id: str, approved: bool, reviewer: str, note: str) -> ApprovalRequest | None:
    item = get(db, request_id)
    if not item:
        return None
    item.status = "APPROVED" if approved else "REJECTED"
    item.reviewer = reviewer
    item.note = note
    db.commit()
    db.refresh(item)
    return item
