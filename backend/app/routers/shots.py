"""界面截图库路由：上传 / 列表 / 删除 / 读取图片。

截图与说明书中的【截图占位：界面名称】按 label 匹配（精确 → 包含），
导出 docx 与打印视图时自动替换占位框嵌入真实截图。
"""
import uuid
from pathlib import Path

from fastapi import APIRouter, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse

from .. import database as db
from ..services import exporter

router = APIRouter(prefix="/api/projects", tags=["shots"])

ALLOWED_EXT = {".png", ".jpg", ".jpeg", ".webp", ".gif", ".bmp"}
MAX_SIZE = 5 * 1024 * 1024


@router.post("/{pid}/shots")
async def upload_shot(pid: int, file: UploadFile, label: str = Form("")):
    if not db.get_project(pid):
        raise HTTPException(404, "项目不存在")
    ext = Path(file.filename or "").suffix.lower()
    if ext not in ALLOWED_EXT:
        raise HTTPException(400, "仅支持图片文件（png/jpg/webp/gif/bmp）")
    data = await file.read()
    if not data:
        raise HTTPException(400, "空文件")
    if len(data) > MAX_SIZE:
        raise HTTPException(400, "图片不能超过 5MB")
    name = (label or Path(file.filename or "").stem).strip()[:100] or "界面截图"
    fname = uuid.uuid4().hex + ext
    (exporter.shots_dir(pid) / fname).write_bytes(data)
    return db.get_shot(db.add_shot(pid, name, fname))


@router.get("/{pid}/shots")
def list_shots(pid: int):
    shots = [{**s, "url": f"/api/projects/{pid}/shots/{s['id']}/image"}
             for s in db.list_shots(pid)]
    return {"shots": shots}


@router.get("/{pid}/shots/{shot_id}/image")
def shot_image(pid: int, shot_id: int):
    s = db.get_shot(shot_id)
    if not s or s["project_id"] != pid:
        raise HTTPException(404, "截图不存在")
    path = exporter.shots_dir(pid) / s["filename"]
    if not path.exists():
        raise HTTPException(404, "截图文件不存在")
    return FileResponse(str(path))


@router.delete("/{pid}/shots/{shot_id}")
def delete_shot(pid: int, shot_id: int):
    s = db.get_shot(shot_id)
    if not s or s["project_id"] != pid:
        raise HTTPException(404, "截图不存在")
    db.delete_shot(shot_id)
    path = exporter.shots_dir(pid) / s["filename"]
    if path.exists():
        path.unlink()
    return {"ok": True}
