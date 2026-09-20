from typing import Any, TypedDict

from agentguard.schemas.security import GuardRequest, GuardResponse


class AgentState(TypedDict, total=False):
    request: GuardRequest
    response: GuardResponse
    execute: bool
    explanation: str
    thinking: str
    error: str
    db: Any
