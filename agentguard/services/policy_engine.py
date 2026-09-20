from dataclasses import dataclass

from agentguard.core.policies import load_policies


@dataclass
class PolicyResult:
    allowed: bool
    reasons: list[str]
    require_approval: bool
    tool_risk: int


def evaluate(role: str, tool: str) -> PolicyResult:
    policies = load_policies()
    role_config = policies.get("roles", {}).get(role)
    tool_config = policies.get("tools", {}).get(tool)

    if not role_config:
        return PolicyResult(False, [f"Unknown role: {role}"], False, 100)

    if not tool_config:
        return PolicyResult(False, [f"Unknown tool: {tool}"], False, 100)

    allowed_tools = set(role_config.get("allowed_tools", []))
    if tool not in allowed_tools:
        return PolicyResult(
            False,
            [f"Role '{role}' is not authorized to use '{tool}'."],
            False,
            int(tool_config.get("risk", 100)),
        )

    tool_risk = int(tool_config.get("risk", 50))
    role_max = int(role_config.get("max_risk", 50))
    require_approval = bool(tool_config.get("require_approval", False)) or tool_risk > role_max

    reasons = [f"Role '{role}' is authorized for '{tool}'."]
    if require_approval:
        reasons.append("Tool policy requires human approval before execution.")

    return PolicyResult(True, reasons, require_approval, tool_risk)
