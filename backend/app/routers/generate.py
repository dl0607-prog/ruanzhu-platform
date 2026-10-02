"""材料生成路由：SSE 流式进度 + 同步生成端点 + 材料人工编辑。"""
import json
from typing import AsyncIterator, Dict, Optional

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from .. import database as db
from ..services import pipeline

router = APIRouter(prefix="/api/projects", tags=["generate"])

DOC_TYPES = ("analysis", "manual", "design", "form", "declaration", "evidence")


class DocUpdate(BaseModel):
    content: str
    title: Optional[str] = None


def _sse(gen: AsyncIterator[Dict]) -> StreamingResponse:
    async def wrapper():
        try:
            async for ev in gen:
                yield "data: " + json.dumps(ev, ensure_ascii=False) + "\n\n"
        except Exception as e:
            err = {"step": "pipeline", "status": "error", "message": str(e)[:400], "data": {}}
            yield "data: " + json.dumps(err, ensure_ascii=False) + "\n\n"

    return StreamingResponse(wrapper(), media_type="text/event-stream",
                             headers={"Cache-Control": "no-cache",
                                      "X-Accel-Buffering": "no"})


@router.post("/{pid}/generate/analysis")
async def gen_analysis(pid: int):
    from ..services.pipeline import ensure_analysis
    try:
        doc = await ensure_analysis(pid)
        return {"ok": True, "doc": doc}
    except ValueError as e:
        raise HTTPException(400, str(e))


@router.post("/{pid}/generate/manual")
async def gen_manual(pid: int):
    return _sse(pipeline.stream_manual(pid, "manual"))


@router.post("/{pid}/generate/design")
async def gen_design(pid: int):
    return _sse(pipeline.stream_manual(pid, "design"))


@router.post("/{pid}/generate/form")
async def gen_form(pid: int):
    try:
        return await pipeline.gen_form(pid)
    except ValueError as e:
        raise HTTPException(400, str(e))


@router.post("/{pid}/generate/declaration")
async def gen_declaration(pid: int):
    try:
        return await pipeline.gen_declaration(pid)
    except ValueError as e:
        raise HTTPException(400, str(e))


@router.post("/{pid}/generate/evidence")
async def gen_evidence(pid: int):
    try:
        return await pipeline.gen_evidence(pid)
    except ValueError as e:
        raise HTTPException(400, str(e))


@router.post("/{pid}/generate/all")
async def gen_all(pid: int, doc_kind: str = "manual"):
    if doc_kind not in ("manual", "design"):
        raise HTTPException(400, "doc_kind 仅支持 manual（操作说明书）或 design（设计说明书）")
    return _sse(pipeline.stream_all(pid, doc_kind))


@router.get("/{pid}/docs")
def list_docs(pid: int):
    return {"docs": db.list_docs(pid)}


@router.get("/{pid}/docs/{doc_type}")
def get_doc(pid: int, doc_type: str):
    doc = db.get_doc(pid, doc_type)
    if not doc:
        raise HTTPException(404, "文档尚未生成")
    return doc


@router.delete("/{pid}/docs/{doc_type}")
def delete_doc(pid: int, doc_type: str):
    db.delete_doc(pid, doc_type)
    return {"ok": True}


@router.put("/{pid}/docs/{doc_type}")
def update_doc(pid: int, doc_type: str, body: DocUpdate):
    """人工编辑材料正文（AI 辅助 + 人类实质性修改，是 2026 新规下的必要动作）。"""
    if doc_type not in DOC_TYPES:
        raise HTTPException(400, "未知的材料类型")
    if not body.content.strip():
        raise HTTPException(400, "内容不能为空")
    ok = db.update_doc(pid, doc_type, body.content, body.title)
    if not ok:
        raise HTTPException(404, "文档尚未生成")
    return {"ok": True}
