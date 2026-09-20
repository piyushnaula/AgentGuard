from typing import Any

from agentguard.tools.registry import ToolSpec, register


def kb_search(arguments: dict[str, Any]) -> dict[str, Any]:
    query = str(arguments.get("query", ""))
    return {
        "status": "ok",
        "tool": "kb.search",
        "message": f"Demo knowledge-base search completed for: {query}",
        "matches": ["demo-policy.md", "demo-runbook.md"],
    }


def files_read(arguments: dict[str, Any]) -> dict[str, Any]:
    path = str(arguments.get("path", ""))
    return {
        "status": "ok",
        "tool": "files.read",
        "path": path,
        "content": "This is simulated file content used for AgentGuard demos.",
    }


def db_read(arguments: dict[str, Any]) -> dict[str, Any]:
    record_id = str(arguments.get("id", ""))
    return {
        "status": "ok",
        "tool": "db.read",
        "record_id": record_id,
        "record": {"status": "demo", "owner": "example-user"},
    }


def db_write(arguments: dict[str, Any]) -> dict[str, Any]:
    return {"status": "simulated", "tool": "db.write", "message": "Write accepted by demo executor."}


def db_delete(arguments: dict[str, Any]) -> dict[str, Any]:
    return {"status": "simulated", "tool": "db.delete", "message": "Delete would occur here in a real connector."}


def email_send(arguments: dict[str, Any]) -> dict[str, Any]:
    return {"status": "simulated", "tool": "email.send", "message": "Email send was simulated."}


def github_create_pr(arguments: dict[str, Any]) -> dict[str, Any]:
    return {"status": "simulated", "tool": "github.create_pr", "message": "PR creation was simulated."}


register(ToolSpec("kb.search", "Search the internal knowledge base.", kb_search))
register(ToolSpec("files.read", "Read a file from an approved workspace.", files_read))
register(ToolSpec("db.read", "Read a database record.", db_read))
register(ToolSpec("db.write", "Write a database record.", db_write))
register(ToolSpec("db.delete", "Delete a database record.", db_delete))
register(ToolSpec("email.send", "Send an outbound email.", email_send))
register(ToolSpec("github.create_pr", "Create a GitHub pull request.", github_create_pr))
