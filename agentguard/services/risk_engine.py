from agentguard.core.policies import load_policies
from agentguard.schemas.security import Finding

SEVERITY_POINTS = {
    "LOW": 5,
    "MEDIUM": 15,
    "HIGH": 30,
    "CRITICAL": 55,
}


def calculate(tool_risk: int, findings: list[Finding], unauthorized: bool = False) -> tuple[int, list[str]]:
    score = tool_risk
    reasons: list[str] = [f"Base tool risk: {tool_risk}"]

    for finding in findings:
        points = SEVERITY_POINTS[finding.severity]
        score += points
        reasons.append(f"{finding.category}: +{points}")

    if unauthorized:
        score += 50
        reasons.append("Unauthorized tool attempt: +50")

    score = min(score, 100)
    thresholds = load_policies().get("thresholds", {})
    review = int(thresholds.get("review", 45))
    deny = int(thresholds.get("deny", 80))

    if score >= deny:
        reasons.append(f"Score >= deny threshold ({deny}).")
    elif score >= review:
        reasons.append(f"Score >= review threshold ({review}).")

    return score, reasons
