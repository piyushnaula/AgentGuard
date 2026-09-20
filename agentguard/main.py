from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from agentguard.api.routes import router
from agentguard.core.config import get_settings
from agentguard.db.database import init_db
from agentguard import tools  # noqa: F401


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


BASE_DIR = Path(__file__).resolve().parent
app = FastAPI(title=get_settings().app_name, version="0.1.0", lifespan=lifespan)
app.include_router(router)

static_dir = BASE_DIR / "ui" / "static"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

templates_dir = BASE_DIR / "ui" / "templates"
templates = Jinja2Templates(directory=templates_dir) if templates_dir.exists() else None


@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    if templates and (templates_dir / "index.html").exists():
        return templates.TemplateResponse(request=request, name="index.html")
    index_file = BASE_DIR / "ui" / "templates" / "index.html"
    if index_file.exists():
        return HTMLResponse(content=index_file.read_text(encoding="utf-8"))
    return HTMLResponse("<h1>AgentGuard is active</h1><p>API documentation available at <a href='/docs'>/docs</a></p>")
