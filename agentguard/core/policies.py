from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

from agentguard.core.config import get_settings


@lru_cache
def load_policies() -> dict[str, Any]:
    try:
        path: Path = get_settings().policy_path
        if path.exists():
            with path.open("r", encoding="utf-8") as file:
                data = yaml.safe_load(file) or {}
                if data:
                    return data
    except Exception as e:
        import sys
        print(f"Warning: could not read policy file from disk: {e}", file=sys.stderr)

    # Embedded fallback policies for serverless runtimes
    return {
        "roles": {
            "support_agent": {
                "allowed_tools": ["kb.search", "files.read", "db.read"]
            },
            "developer_agent": {
                "allowed_tools": ["kb.search", "files.read", "db.read", "db.write", "github.create_pr"]
            },
            "admin_agent": {
                "allowed_tools": ["kb.search", "files.read", "db.read", "db.write", "db.delete", "email.send", "github.create_pr"]
            }
        },
        "thresholds": {
            "deny": 80,
            "review": 60
        },
        "tools": {
            "kb.search": {"base_risk": 10, "destructive": False},
            "files.read": {"base_risk": 20, "destructive": False},
            "db.read": {"base_risk": 30, "destructive": False},
            "db.write": {"base_risk": 55, "destructive": False},
            "db.delete": {"base_risk": 85, "destructive": True},
            "email.send": {"base_risk": 65, "destructive": False},
            "github.create_pr": {"base_risk": 60, "destructive": False}
        }
    }


def reload_policies() -> dict[str, Any]:
    load_policies.cache_clear()
    return load_policies()
