"""应用入口：FastAPI + 前端静态托管。

启动：cd backend && ../.venv/bin/python -m uvicorn app.main:app --port 8310
"""
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from . import config, database, auth, llm
import re
from urllib.parse import urlsplit
from .routers import export, generate, projects, review, shots
from .services import seed_kb, submission

app = FastAPI(title="软著申请辅助平台", version="1.0.0")

@app.middleware("http")
async def authenticate(request: Request, call_next):
    path = request.url.path
    if path.startswith('/api/'):
        if request.method not in ('GET', 'HEAD', 'OPTIONS'):
            origin = request.headers.get('origin')
            if origin and urlsplit(origin).netloc != request.headers.get('host'):
                return JSONResponse({'detail': '不允许跨站请求'}, status_code=403)
        public = path in ('/api/health', '/api/auth/login')
        user = auth.identify(request.cookies.get('rz_session'))
        if not public and not user:
            return JSONResponse({'detail': '请先登录'}, status_code=401)
        token = auth.current_user.set(user)
        try:
            match = re.match(r'^/api/projects/(\d+)(?:/|$)', path)
            if match:
                auth.require_project(int(match.group(1)))
            return await call_next(request)
        except HTTPException as exc:
            return JSONResponse({'detail': exc.detail}, status_code=exc.status_code)
        finally:
            auth.current_user.reset(token)
    response = await call_next(request)
    if path == "/" or path.startswith("/static/"):
        response.headers["Cache-Control"] = "no-cache"
    return response


@app.exception_handler(llm.LLMNotConfigured)
async def llm_missing(request, exc):
    return JSONResponse({'detail': 'AI服务未配置，请联系管理员或使用人工录入材料'}, status_code=503)


@app.exception_handler(llm.LLMError)
async def llm_failed(request, exc):
    return JSONResponse({'detail': 'AI服务调用失败，请稍后重试或人工录入材料'}, status_code=502)


app.include_router(auth.router)
app.include_router(submission.router)
app.include_router(projects.router)
app.include_router(generate.router)
app.include_router(review.router)
app.include_router(export.router)
app.include_router(shots.router)

SEEDED = {"count": 0}


@app.on_event("startup")
def startup():
    database.init_db()
    auth.bootstrap()
    SEEDED["count"] = seed_kb.seed_if_empty(database)


@app.get("/api/health")
def health():
    from . import llm
    return {"ok": True, "llm_configured": llm.configured(),
            "llm_model": config.LLM_MODEL, "seeded_rules": SEEDED["count"]}



if config.FRONTEND_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(config.FRONTEND_DIR)), name="static")

    @app.get("/")
    def index():
        index_html = config.FRONTEND_DIR / "index.html"
        if index_html.exists():
            return FileResponse(str(index_html))
        return HTMLResponse("<h3>软著申请辅助平台：前端未找到（frontend/index.html）</h3>")
