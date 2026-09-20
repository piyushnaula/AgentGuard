import os
import sys
from pathlib import Path

# Ensure project root is in sys.path so agentguard and config can be resolved
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

# Ensure VERCEL indicator is recognized
if not os.getenv("VERCEL"):
    os.environ["VERCEL"] = "1"

try:
    from agentguard.main import app  # noqa: E402
except Exception as exc:
    import traceback
    error_trace = traceback.format_exc()
    print("FATAL ERROR INITIALIZING AGENTGUARD ON VERCEL:", error_trace, file=sys.stderr)

    from fastapi import FastAPI
    from fastapi.responses import HTMLResponse

    app = FastAPI(title="AgentGuard - Error Diagnostics")

    @app.api_route("/{full_path:path}", methods=["GET", "POST", "PUT", "DELETE"])
    async def error_page(full_path: str = ""):
        return HTMLResponse(
            f"""
            <!doctype html>
            <html>
              <head><title>AgentGuard Startup Error</title></head>
              <body style="background:#000000;color:#fca5a5;font-family:monospace;padding:32px;">
                <h1 style="color:#ef4444;">AgentGuard Startup Diagnostics</h1>
                <p style="color:#c084fc;">A Python exception occurred while initializing the application on Vercel:</p>
                <pre style="background:#0d061a;border:1px solid #7c3aed;padding:16px;border-radius:8px;color:#e9d5ff;overflow-x:auto;">{error_trace}</pre>
              </body>
            </html>
            """,
            status_code=500,
        )

# Export ASGI application instance for Vercel serverless runtime
__all__ = ["app"]
