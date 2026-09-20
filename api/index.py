import sys
from pathlib import Path

# Ensure project root is in sys.path so agentguard and config can be resolved
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from agentguard.main import app  # noqa: E402

# Export ASGI application instance for Vercel serverless runtime
__all__ = ["app"]
