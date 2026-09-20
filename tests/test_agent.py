from unittest.mock import MagicMock, patch
from agentguard.agent.nodes import explanation_node
from agentguard.schemas.security import Finding, GuardResponse


def test_explanation_node_fallback_without_api_key():
    response = GuardResponse(
        request_id="req-123",
        decision="DENY",
        risk_score=90,
        reasons=["Unauthorized tool attempt"],
        findings=[Finding(category="prompt_injection", severity="CRITICAL", message="Test", field="task")],
        tool="db.delete",
    )
    with patch("agentguard.core.config.get_settings") as mock_settings:
        mock_settings.return_value.effective_api_key = ""
        mock_settings.return_value.llm_model = "openai/gpt-oss-20b"
        mock_settings.return_value.llm_provider = "groq"
        state = {"response": response}
        result = explanation_node(state)
        assert "Decision=DENY" in result["explanation"]
        assert "Deterministic policy and scanner rules" in result["explanation"]


def test_explanation_node_with_groq():
    response = GuardResponse(
        request_id="req-123",
        decision="ALLOW",
        risk_score=10,
        reasons=["Allowed"],
        findings=[],
        tool="kb.search",
    )
    mock_llm_instance = MagicMock()
    mock_llm_instance.invoke.return_value.content = (
        "<thinking>\nStep 1: Check role.\nStep 2: Check risk.\n</thinking>\n"
        "<output>\n**Verdict**: ALLOWED\nAction is safe and permitted.\n</output>"
    )

    with patch("agentguard.core.config.get_settings") as mock_settings:
        mock_settings.return_value.effective_api_key = "gsk_test_key"
        mock_settings.return_value.llm_model = "openai/gpt-oss-20b"
        mock_settings.return_value.llm_provider = "groq"
        mock_settings.return_value.llm_base_url = ""

        with patch("langchain_groq.ChatGroq", return_value=mock_llm_instance) as mock_chat_groq:
            state = {"response": response}
            result = explanation_node(state)
            mock_chat_groq.assert_called_once_with(
                model="openai/gpt-oss-20b",
                api_key="gsk_test_key",
                temperature=0,
            )
            assert "Action is safe and permitted." in result["explanation"]
            assert "Step 1: Check role." in result["thinking"]
