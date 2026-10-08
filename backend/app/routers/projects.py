"""项目管理与源代码导入路由。"""
import io
import shutil
import zipfile
from typing import Any, Dict, List

from fastapi import APIRouter, HTTPException, UploadFile
from pydantic import BaseModel

from .. import database as db
from .. import auth, config
from ..services import code_engine

router = APIRouter(prefix="/api/projects", tags=["projects"])


class ProjectIn(BaseModel):
    full_name: str = ""
    short_name: str = ""
    version: str = "V1.0"
    completion_date: str = ""
    publish_date: str = ""
    dev_type: str = "独立开发"
    owner_name: str = ""
    owner_type: str = "个人"
    main_functions: str = ""
    tech_stack: str = ""
    ai_usage: str = "unknown"
    git_log: str = ""
    status: str = "draft"


class CodeIn(BaseModel):
    files: List[Dict[str, str]] = []
    replace: bool = True


def _decode(data: bytes) -> str:
    for enc in ("utf-8", "gb18030", "utf-16"):
        try:
            return data.decode(enc)
        except (UnicodeDecodeError, UnicodeError):
            continue
    return data.decode("utf-8", errors="replace")


def _store_files(pid: int, raw_files: List[Dict[str, Any]], replace: bool) -> Dict[str, Any]:
    cleaned: List[Dict[str, Any]] = []
    for f in raw_files:
        name = str(f.get("filename") or "code.txt")[:200]
        content, n = code_engine.clean_code(str(f.get("content") or ""))
        if n == 0:
            continue
        cleaned.append({"filename": name, "content": content, "line_count": n})
    if not cleaned:
        raise HTTPException(400, "清洗后没有有效源代码，原有文件已保留")
    if replace:
        db.replace_source_files(pid, cleaned)
    else:
        base = len(db.list_source_files(pid))
        for i, f in enumerate(cleaned):
            db.add_source_file(pid, f["filename"], f["content"], f["line_count"], base + i)
    stored = db.get_source_contents(pid)
    db.update_project(pid, {"code_lines_total": sum(f["line_count"] for f in stored)})
    pages = code_engine.build_pages(stored)
    return {"files_stored": len(cleaned), "total_lines": pages["total_lines"],
            "pages_submitted": pages["pages_submitted"], "mode": pages["mode"]}


@router.get("")
def list_projects():
    out = []
    ids = auth.owned_ids()
    for p in db.list_projects():
        if p["id"] not in ids:
            continue
        p["source_files"] = len(db.list_source_files(p["id"]))
        p["docs"] = {d["doc_type"]: d["title"] for d in db.list_docs(p["id"])}
        out.append(p)
    return {"projects": out}


@router.post("")
def create_project(body: ProjectIn):
    if not body.full_name.strip():
        raise HTTPException(400, "软件全称不能为空")
    pid = db.create_project(body.model_dump())
    return {"id": pid}


@router.get("/{pid}")
def get_project(pid: int):
    p = db.get_project(pid)
    if not p:
        raise HTTPException(404, "项目不存在")
    p["source_files"] = db.list_source_files(pid)
    p["docs"] = db.list_docs(pid)
    reports = db.list_reports(pid, limit=1)
    p["last_report"] = reports[0] if reports else None
    return p


@router.put("/{pid}")
def update_project(pid: int, body: ProjectIn):
    if not db.get_project(pid):
        raise HTTPException(404, "项目不存在")
    fields = body.model_dump(exclude_unset=True)
    if "full_name" in fields and not fields["full_name"].strip():
        raise HTTPException(400, "软件全称不能为空")
    if "status" in fields and fields["status"] not in ALLOWED_STATUS:
        raise HTTPException(400, "非法状态值")
    db.update_project(pid, fields)
    return {"ok": True}


@router.delete("/{pid}")
def delete_project(pid: int):
    db.delete_project(pid)
    shutil.rmtree(config.DATA_DIR / "shots" / f"project_{pid}", ignore_errors=True)
    shutil.rmtree(config.EXPORT_DIR / f"project_{pid}", ignore_errors=True)
    return {"ok": True}


ALLOWED_STATUS = {"draft", "ready", "submitted", "correction", "registered", "rejected"}


class StatusIn(BaseModel):
    status: str


@router.patch("/{pid}/status")
def patch_status(pid: int, body: StatusIn):
    """申请状态流转：draft 草稿 / ready 材料就绪 / submitted 已提交 /
    correction 补正中 / registered 已登记 / rejected 已驳回。"""
    if not db.get_project(pid):
        raise HTTPException(404, "项目不存在")
    if body.status not in ALLOWED_STATUS:
        raise HTTPException(400, "非法状态值")
    db.update_project(pid, {"status": body.status})
    return {"ok": True, "status": body.status}


@router.post("/{pid}/code")
def import_code(pid: int, body: CodeIn):
    if not db.get_project(pid):
        raise HTTPException(404, "项目不存在")
    if not body.files:
        raise HTTPException(400, "没有可导入的代码内容")
    return _store_files(pid, body.files, body.replace)


@router.post("/{pid}/code/upload")
async def upload_code(pid: int, files: List[UploadFile]):
    if not db.get_project(pid):
        raise HTTPException(404, "项目不存在")
    raw_files: List[Dict[str, Any]] = []
    for up in files:
        data = await up.read(20 * 1024 * 1024 + 1)
        if len(data) > 20 * 1024 * 1024:
            raise HTTPException(413, "单个上传文件不能超过 20MB")
        name = up.filename or "code.txt"
        if name.lower().endswith(".zip"):
            try:
                archive = zipfile.ZipFile(io.BytesIO(data))
            except zipfile.BadZipFile:
                raise HTTPException(400, "ZIP 文件损坏或格式无效，请重新打包上传")
            with archive as zf:
                entries = zf.infolist()
                if len(entries) > 5000 or sum(i.file_size for i in entries) > 100 * 1024 * 1024:
                    raise HTTPException(413, "ZIP 解压后不能超过 100MB 或 5000 个条目")
                for info in zf.infolist():
                    if info.is_dir():
                        continue
                    parts = info.filename.replace("\\", "/").split("/")
                    if any(seg in code_engine.SKIP_DIRS for seg in parts):
                        continue
                    if not any(info.filename.lower().endswith(ext)
                               for ext in code_engine.CODE_EXTENSIONS):
                        continue
                    if info.file_size > 1_500_000:
                        continue
                    try:
                        text = _decode(zf.read(info))
                    except Exception:
                        continue
                    raw_files.append({"filename": "/".join(parts[-3:]), "content": text})
        elif name.lower().endswith(tuple(code_engine.CODE_EXTENSIONS)):
            raw_files.append({"filename": name, "content": _decode(data)})
    if not raw_files:
        raise HTTPException(400, "未从上传内容中解析出源代码文件（支持常见源码扩展名与 zip 包）")
    raw_files.sort(key=lambda f: f["filename"])
    return _store_files(pid, raw_files, replace=True)


@router.get("/{pid}/code/stats")
def code_stats(pid: int):
    files = db.get_source_contents(pid)
    if not files:
        return {"total_lines": 0, "pages_submitted": 0, "mode": "all", "files": []}
    pages = code_engine.build_pages(files)
    ok, last = code_engine.last_page_ends_ok(pages["pages"])
    return {"total_lines": pages["total_lines"], "pages_submitted": pages["pages_submitted"],
            "pages_full": pages["total_pages_full"], "mode": pages["mode"],
            "files": pages["files"], "last_line_ok": ok, "last_line": last}
