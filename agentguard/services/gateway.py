from uuid import uuid4

from sqlalchemy.orm import Session

from agentguard.core.policies import load_policies
from agentguard.schemas.security import Finding, GuardRequest, GuardResponse
from agentguard.services import approval_service, audit_service, policy_engine, risk_engine
from agentguard.services.scanner import scan_request, scan_result
from agentguard.tools.registry import get_tool


def guard_request(request: GuardRequest, db: Session, execute: bool = True) -> GuardResponse:
    request_id = uuid4().hex
    policy = policy_engine.evaluate(request.role, request.tool)
    findings = scan_request(request.task, request.arguments)
    unauthorized = not policy.allowed

    risk_score, risk_reasons = risk_engine.calculate(policy.tool_risk, findings, unauthorized)
    reasons = policy.reasons + risk_reasons

    thresholds = load_policies().get("thresholds", {})
    deny_threshold = int(thresholds.get("deny", 80))

    hard_stop_categories = {"prompt_injection", "policy_bypass", "secret", "pii", "financial"}
    hard_stop = any(item.category in hard_stop_categories for item in findings)

    if unauthorized or hard_stop or risk_score >= deny_threshold:
        decision = "DENY"
    elif policy.require_approval or risk_score >= int(thresholds.get("review", 45)):
        decision = "REVIEW"
    else:
        decision = "ALLOW"

    response = GuardResponse(
        request_id=request_id,
        decision=decision,  # type: ignore[arg-type]
        risk_score=risk_score,
        reasons=reasons,
        findings=findings,
        tool=request.tool,
    )

    if decision == "REVIEW":
        approval_service.create(db, request_id, request)
        audit_service.record(db, request, response)
        return response

    if decision == "DENY" or not execute:
        audit_service.record(db, request, response)
        return response

    tool = get_tool(request.tool)
    if not tool:
        response.decision = "DENY"
        response.reasons.append("Tool implementation is not registered.")
        audit_service.record(db, request, response)
        return response

    result = tool.handler(request.arguments)
    output_findings = scan_result(result)
    if output_findings:
        response.findings.extend(output_findings)
        response.reasons.append("Output scanner found sensitive content; execution result was withheld.")
        response.decision = "DENY"
        audit_service.record(db, request, response, "withheld due to output scan")
        return response

    response.executed = True
    response.result = result
    audit_service.record(db, request, response, str(result)[:1000])
    return response


def approve_and_execute(request_id: str, db: Session) -> GuardResponse:
    approval = approval_service.get(db, request_id)
    if not approval:
        raise ValueError("Approval request not found")

    if approval.status != "APPROVED":
        raise ValueError(f"Approval is not approved: {approval.status}")

    request = GuardRequest.model_validate(approval.payload)
    tool = get_tool(request.tool)
    if not tool:
        raise ValueError("Tool implementation is not registered")

    result = tool.handler(request.arguments)
    findings = scan_result(result)
    response = GuardResponse(
        request_id=request_id,
        decision="ALLOW" if not findings else "DENY",
        risk_score=0,
        reasons=["Human approval granted."] if not findings else ["Output scanner blocked the result."],
        findings=findings,
        tool=request.tool,
        executed=not findings,
        result=None if findings else result,
    )
    audit_service.record(
        db,
        request,
        response,
        str(result)[:1000] if not findings else "withheld due to output scan",
    )
    return response
