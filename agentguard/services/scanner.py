import re
from typing import Any

from agentguard.schemas.security import Finding


PATTERNS: list[tuple[str, str, str, str]] = [
    (
        "prompt_injection",
        "CRITICAL",
        "Instruction override attempt detected.",
        r"ignore\s+(all\s+|any\s+|previous\s+|prior\s+)?instructions",
    ),
    (
        "prompt_injection",
        "HIGH",
        "Attempt to imitate a privileged instruction source detected.",
        r"(system|developer)\s*(message|prompt)\s*[:=]",
    ),
    (
        "prompt_injection",
        "HIGH",
        "Attempt to reveal hidden instructions detected.",
        r"(reveal|show|print|dump)\s+(the\s+)?(system|developer|hidden)\s+(prompt|instructions)",
    ),
    (
        "policy_bypass",
        "HIGH",
        "Attempt to bypass a security control detected.",
        r"(bypass|disable|skip|turn off)\s+(security|policy|guard|approval)",
    ),
    (
        "secret",
        "CRITICAL",
        "API-key-like secret detected.",
        r"\bsk-[A-Za-z0-9_-]{20,}\b",
    ),
    (
        "secret",
        "CRITICAL",
        "GitHub-token-like secret detected.",
        r"\bgh[pousr]_[A-Za-z0-9]{20,}\b",
    ),
    (
        "secret",
        "CRITICAL",
        "Private key material detected.",
        r"-----BEGIN\s+(RSA|EC|OPENSSH|PRIVATE)\s+KEY-----",
    ),
    (
        "secret",
        "HIGH",
        "Bearer token detected.",
        r"\bBearer\s+[A-Za-z0-9._~-]{20,}\b",
    ),
    (
        "pii",
        "MEDIUM",
        "Email address detected.",
        r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b",
    ),
    (
        "pii",
        "HIGH",
        "Indian mobile-number-like value detected.",
        r"(?<!\d)(?:\+91[- ]?)?[6-9]\d{9}(?!\d)",
    ),
    (
        "pii",
        "HIGH",
        "Aadhaar-like 12-digit identifier detected.",
        r"(?<!\d)\d{4}[ -]?\d{4}[ -]?\d{4}(?!\d)",
    ),
    (
        "financial",
        "HIGH",
        "Payment-card-like number detected.",
        r"(?<!\d)(?:\d[ -]?){13,19}(?!\d)",
    ),
]


def _flatten(value: Any, prefix: str = "arguments") -> list[tuple[str, str]]:
    output: list[tuple[str, str]] = []
    if isinstance(value, dict):
        for key, item in value.items():
            output.extend(_flatten(item, f"{prefix}.{key}"))
    elif isinstance(value, list):
        for index, item in enumerate(value):
            output.extend(_flatten(item, f"{prefix}[{index}]"))
    else:
        output.append((prefix, str(value)))
    return output


def scan_text(value: str, field: str) -> list[Finding]:
    findings: list[Finding] = []
    for category, severity, message, pattern in PATTERNS:
        if re.search(pattern, value, flags=re.IGNORECASE):
            findings.append(
                Finding(
                    category=category,
                    severity=severity,  # type: ignore[arg-type]
                    message=message,
                    field=field,
                )
            )
    return findings


def scan_request(task: str, arguments: dict[str, Any]) -> list[Finding]:
    findings = scan_text(task, "task")
    for field, value in _flatten(arguments):
        findings.extend(scan_text(value, field))
    return _deduplicate(findings)


def scan_result(result: Any) -> list[Finding]:
    text = result if isinstance(result, str) else str(result)
    return _deduplicate(scan_text(text, "result"))


def _deduplicate(findings: list[Finding]) -> list[Finding]:
    unique: dict[tuple[str, str, str], Finding] = {}
    for finding in findings:
        key = (finding.category, finding.field, finding.message)
        unique[key] = finding
    return list(unique.values())
