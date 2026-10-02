"""应用入口：FastAPI + 前端静态托管。

启动：cd backend && ../.venv/bin/python -m uvicorn app.main:app --port 8310
"""
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles

from . import config, database
from .routers import export, generate, projects, review, shots
from .services import seed_kb

app = FastAPI(title="软著申请辅助平台", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(projects.router)
app.include_router(generate.router)
app.include_router(review.router)
app.include_router(export.router)
app.include_router(shots.router)

SEEDED = {"count": 0}


@app.on_event("startup")
def startup():
    database.init_db()
    SEEDED["count"] = seed_kb.seed_if_empty(database)


@app.get("/api/health")
def health():
    from . import llm
    masked = (config.LLM_API_KEY[:6] + "***") if config.LLM_API_KEY else ""
    return {
        "ok": True,
        "llm_configured": llm.configured(),
        "llm_base_url": config.LLM_BASE_URL,
        "llm_model": config.LLM_MODEL,
        "llm_key_masked": masked,
        "seeded_rules": SEEDED["count"],
        "kb_rules_total": len(database.list_rules()),
    }


if config.FRONTEND_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(config.FRONTEND_DIR)), name="static")

    @app.get("/")
    def index():
        index_html = config.FRONTEND_DIR / "index.html"
        if index_html.exists():
            return FileResponse(str(index_html))
        return HTMLResponse("<h3>软著申请辅助平台：前端未找到（frontend/index.html）</h3>")
