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
    """人工录入或修订材料；结构化字段同步到导出数据。"""
    if not db.get_project(pid):
        raise HTTPException(404, "项目不存在")
    if doc_type not in DOC_TYPES:
        raise HTTPException(400, "未知的材料类型")
    if not body.content.strip():
        raise HTTPException(400, "内容不能为空")
    existing = db.get_doc(pid, doc_type) or {}
    meta = existing.get('meta') or {}
    if doc_type in ('analysis', 'form', 'declaration'):
        try:
            data = json.loads(body.content)
            if not isinstance(data, dict):
                raise ValueError()
        except (ValueError, TypeError):
            raise HTTPException(400, "该材料需要 JSON 对象，请保留字段名并修改值")
        if doc_type == 'form' and any(not isinstance(value, str) for value in data.values()):
            raise HTTPException(400, '申请表字段必须填写文本')
        meta['data'] = data
        if doc_type == 'analysis':
            meta.update(data)
    meta['manually_edited'] = True
    db.upsert_doc(pid, doc_type, body.title or existing.get('title') or pipeline.DOC_LABELS[doc_type], body.content, meta)
    return {"ok": True}
