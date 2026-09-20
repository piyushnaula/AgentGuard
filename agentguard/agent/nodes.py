import re
from langchain_core.prompts import ChatPromptTemplate
from agentguard.agent.state import AgentState
from agentguard.services.gateway import guard_request


SECURITY_SYSTEM_PROMPT = """You are AgentGuard AI Security Officer, an authoritative automated cybersecurity gateway auditor.
Your job is to review past agent transactions and provide a clean, rigorous, and readable security analysis.

CRITICAL INSTRUCTIONS:
- You are an AUDITOR reviewing a completed transaction. Do NOT execute, call, or invoke any tools.
- Do NOT output JSON tool calls or tool-use syntax. Only output clear, analytical text.
- Never contradict or attempt to alter the given Decision or Risk score.

You MUST follow Chain-of-Thought (CoT) reasoning using these exact section headers:
[THINKING]
Step-by-step reasoning evaluating:
1. Agent identity and role authorization boundary.
2. Target action permissions and policy compliance.
3. Scanner findings (prompt injections, leaked credentials, PII).
4. Cumulative risk calculation and threshold comparison.
[/THINKING]

[SUMMARY]
Provide a clean, structured executive summary using markdown:
- **Verdict**: [State ALLOWED, DENIED, or REQUIRES HUMAN REVIEW with 1-line summary]
- **Key Analysis**: [2-3 concise bullet points on permissions, findings, and risk]
- **Risk Assessment**: [Explain the risk score and primary factors]
- **Recommended Next Steps**: [Clear guidance for the user or administrator]
[/SUMMARY]
"""

HUMAN_PROMPT_TEMPLATE = """Please audit the following completed gateway transaction:

- Decision: {decision}
- Risk Score: {risk_score} / 100
- Agent ID: {agent_id}
- User ID: {user_id}
- Assigned Role: {role}
- Target Action: {tool}
- Stated Task: {task}
- Parameters Checked: {arguments}
- Policy Reasons: {reasons}
- Scanner Findings: {findings}

Remember:
1. First show your step-by-step reasoning under [THINKING] ... [/THINKING].
2. Then show your clean executive report under [SUMMARY] ... [/SUMMARY].
"""


def _parse_cot(raw_content: str) -> tuple[str | None, str]:
    t_match = re.search(r"\[THINKING\]\s*(.*?)(?=\[SUMMARY\]|\[/THINKING\]|$)", raw_content, re.DOTALL | re.IGNORECASE)
    s_match = re.search(r"\[SUMMARY\]\s*(.*?)(?=\[/SUMMARY\]|$)", raw_content, re.DOTALL | re.IGNORECASE)

    if not t_match:
        t_match = re.search(r"<thinking>(.*?)</thinking>", raw_content, re.DOTALL | re.IGNORECASE)
    if not s_match:
        s_match = re.search(r"<output>(.*?)</output>", raw_content, re.DOTALL | re.IGNORECASE)

    thinking = t_match.group(1).strip() if t_match else None

    if s_match:
        explanation = s_match.group(1).strip()
    elif thinking:
        clean = re.sub(r"\[THINKING\].*?\[/THINKING\]", "", raw_content, flags=re.DOTALL | re.IGNORECASE)
        clean = re.sub(r"<thinking>.*?</thinking>", "", clean, flags=re.DOTALL | re.IGNORECASE)
        explanation = clean.strip()
    else:
        explanation = raw_content.strip()

    return thinking, explanation


def gateway_node(state: AgentState) -> AgentState:
    request = state["request"]
    db = state["db"]
    response = guard_request(request, db, execute=state.get("execute", True))
    return {"response": response}


def explanation_node(state: AgentState) -> AgentState:
    response = state["response"]
    request = state.get("request")
    from agentguard.core.config import get_settings

    settings = get_settings()
    api_key = settings.effective_api_key

    if not api_key or not settings.llm_model:
        fallback_exp = (
            f"Decision={response.decision}. Risk={response.risk_score}. "
            "Deterministic policy and scanner rules produced this decision."
        )
        response.explanation = fallback_exp
        return {"explanation": fallback_exp, "thinking": None}

    try:
        provider = settings.llm_provider.lower().strip()
        if api_key.startswith("xai-") or provider in ("grok", "xai"):
            from langchain_openai import ChatOpenAI

            llm_kwargs = {
                "model": settings.llm_model,
                "api_key": api_key,
                "base_url": settings.llm_base_url or "https://api.x.ai/v1",
                "temperature": 0,
            }
            llm = ChatOpenAI(**llm_kwargs)
        elif provider == "groq" or api_key.startswith("gsk_"):
            from langchain_groq import ChatGroq

            llm_kwargs = {
                "model": settings.llm_model,
                "api_key": api_key,
                "temperature": 0,
            }
            if settings.llm_base_url:
                llm_kwargs["base_url"] = settings.llm_base_url

            llm = ChatGroq(**llm_kwargs)
        else:
            from langchain_openai import ChatOpenAI

            llm_kwargs = {
                "model": settings.llm_model,
                "api_key": api_key,
                "temperature": 0,
            }
            if settings.llm_base_url:
                llm_kwargs["base_url"] = settings.llm_base_url

            llm = ChatOpenAI(**llm_kwargs)

        full_prompt = f"{SECURITY_SYSTEM_PROMPT}\n\n" + HUMAN_PROMPT_TEMPLATE.format(
            decision=response.decision,
            risk_score=response.risk_score,
            agent_id=getattr(request, "agent_id", "unknown"),
            user_id=getattr(request, "user_id", "unknown"),
            role=getattr(request, "role", "unknown"),
            tool=response.tool,
            task=getattr(request, "task", ""),
            arguments=getattr(request, "arguments", {}),
            reasons="; ".join(response.reasons),
            findings=[item.model_dump() for item in response.findings],
        )

        try:
            result = llm.invoke(full_prompt)
            raw_text = result.content if isinstance(result.content, str) else str(result.content)
        except Exception as api_err:
            err_str = str(api_err)
            if "failed_generation" in err_str:
                match = re.search(r'"arguments":\s*(.*?)(?:\'\}\}|\}\})', err_str, re.DOTALL)
                if match:
                    raw_text = match.group(1).replace("\\n", "\n")
                else:
                    raise api_err
            else:
                raise api_err

        thinking, explanation = _parse_cot(raw_text)

        response.thinking = thinking
        response.explanation = explanation

        return {"explanation": explanation, "thinking": thinking}
    except Exception as exc:
        err_msg = f"LLM explanation unavailable: {exc.__class__.__name__} - {str(exc)}"
        response.explanation = err_msg
        return {"explanation": err_msg, "thinking": None}
