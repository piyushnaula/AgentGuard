import json
import time
from collections import Counter
from pathlib import Path

from agentguard.db.database import SessionLocal
from agentguard.schemas.security import GuardRequest
from agentguard.services.gateway import guard_request

DATASET = Path(__file__).resolve().parent / "dataset.json"
RESULTS = Path(__file__).resolve().parent / "results.json"


def main() -> None:
    if not DATASET.exists():
        from evaluation.generate_dataset import main as generate_main
        generate_main()

    cases = json.loads(DATASET.read_text(encoding="utf-8"))
    db = SessionLocal()
    confusion = Counter()
    category_stats: dict[str, dict[str, int]] = {}
    timings: list[float] = []

    try:
        for case in cases:
            request = GuardRequest(
                agent_id=f"eval-{case['category']}",
                user_id="evaluation",
                role=case["role"],
                task=case["task"],
                tool=case["tool"],
                arguments=case["arguments"],
            )
            start = time.perf_counter()
            response = guard_request(request, db, execute=False)
            timings.append((time.perf_counter() - start) * 1000)
            confusion[(case["expected"], response.decision)] += 1
            stats = category_stats.setdefault(case["category"], {"total": 0, "correct": 0})
            stats["total"] += 1
            stats["correct"] += int(case["expected"] == response.decision)
    finally:
        db.close()

    total = len(cases)
    accuracy = sum(confusion[(case_expected, case_expected)] for case_expected in {"ALLOW", "DENY", "REVIEW"}) / total
    blocked_attacks = sum(
        stats["correct"] for category, stats in category_stats.items() if category != "legitimate"
    )
    attack_cases = total - category_stats.get("legitimate", {"total": 0})["total"]
    false_positive = confusion[("ALLOW", "DENY")] + confusion[("ALLOW", "REVIEW")]

    report = {
        "total_cases": total,
        "overall_accuracy": round(accuracy, 4),
        "attack_detection_rate": round(blocked_attacks / attack_cases, 4) if attack_cases else 0,
        "false_positive_rate": round(false_positive / max(category_stats.get("legitimate", {"total": 1})["total"], 1), 4),
        "average_decision_latency_ms": round(sum(timings) / max(len(timings), 1), 3),
        "confusion_matrix": {f"{a}->{b}": n for (a, b), n in sorted(confusion.items())},
        "categories": category_stats,
    }
    RESULTS.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
