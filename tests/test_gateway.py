from agentguard.db.database import Base, SessionLocal, engine
from agentguard.schemas.security import GuardRequest
from agentguard.services.gateway import guard_request


def setup_module():
    Base.metadata.create_all(bind=engine)


def test_unauthorized_action_is_denied():
    db = SessionLocal()
    try:
        request = GuardRequest(
            agent_id="test-agent",
            user_id="test-user",
            role="support_agent",
            task="Delete the record",
            tool="db.delete",
            arguments={"id": "123"},
        )
        response = guard_request(request, db, execute=True)
        assert response.decision == "DENY"
        assert response.executed is False
    finally:
        db.close()


def test_safe_read_can_execute():
    db = SessionLocal()
    try:
        request = GuardRequest(
            agent_id="test-agent",
            user_id="test-user",
            role="support_agent",
            task="Read the customer record",
            tool="db.read",
            arguments={"id": "123"},
        )
        response = guard_request(request, db, execute=True)
        assert response.decision == "ALLOW"
        assert response.executed is True
    finally:
        db.close()
