from agentguard.services.policy_engine import evaluate


def test_support_role_cannot_delete():
    result = evaluate("support_agent", "db.delete")
    assert result.allowed is False


def test_admin_can_use_delete_but_requires_approval():
    result = evaluate("admin_agent", "db.delete")
    assert result.allowed is True
    assert result.require_approval is True


def test_unknown_tool_is_denied():
    result = evaluate("admin_agent", "root.shell")
    assert result.allowed is False
