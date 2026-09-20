from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

from agentguard.core.config import get_settings


@lru_cache
def load_policies() -> dict[str, Any]:
    path: Path = get_settings().policy_path
    if not path.exists():
        raise FileNotFoundError(f"Policy file not found: {path}")
    with path.open("r", encoding="utf-8") as file:
        data = yaml.safe_load(file) or {}
    return data


def reload_policies() -> dict[str, Any]:
    load_policies.cache_clear()
    return load_policies()
