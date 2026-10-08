"""材料生成服务：代码分析 / 操作说明书 / 设计说明书 / 申请表 / AI声明 / 开发过程记录。

统一以 SSE 事件流输出进度；所有生成自动注入驳回知识库规避清单。
"""
import json
from typing import Any, AsyncIterator, Dict, List, Optional

from .. import database as db
from .. import llm
from . import code_engine, kb_service, prompts

DOC_LABELS = {
    "analysis": "代码分析", "manual": "操作说明书", "design": "设计说明书",
    "form": "申请表预填", "declaration": "AI声明", "evidence": "开发过程记录",
}


def _event(step: str, status: str, message: str = "", data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    return {"step": step, "status": status, "message": message, "data": data or {}}


def _require_project(project_id: int) -> Dict[str, Any]:
    p = db.get_project(project_id)
    if not p:
        raise ValueError("项目不存在")
    if not (p.get("full_name") or "").strip():
        raise ValueError("请先在项目信息中填写软件全称")
    return p


def _save_generated(project_id, doc_type, title, content, meta, fingerprint):
    if db.input_fingerprint(project_id) != fingerprint:
        raise ValueError("生成期间项目信息或源码已变化，旧结果未覆盖材料；请重新生成")
    return db.upsert_doc(project_id, doc_type, title, content,
                         {**meta, "input_fingerprint": fingerprint})


def _modules_text(analysis_meta: Dict[str, Any]) -> str:
    mods = analysis_meta.get("modules") or []
    lines = []
    for i, m in enumerate(mods, 1):
        fns = "、".join((m.get("functions") or [])[:10])
        lines.append(f"{i}. {m.get('name', '')}：{m.get('description', '')}" + (f"（涉及：{fns}）" if fns else ""))
    return "\n".join(lines) if lines else "（尚未完成代码分析）"


async def ensure_analysis(project_id: int) -> Dict[str, Any]:
    """获取或生成代码分析（模块划分等），返回 analysis doc。"""
    fingerprint = db.input_fingerprint(project_id)
    existing = db.get_doc(project_id, "analysis")
    if existing and (existing.get("meta") or {}).get("modules") and existing["meta"].get("input_fingerprint") == db.input_fingerprint(project_id):
        return existing
    project = _require_project(project_id)
    files = db.get_source_contents(project_id)
    if not files:
        raise ValueError("请先在“源代码”页导入源代码")
    kb_text = await kb_service.get_kb_context(project_id)
    ctx = {"project": project, "kb_text": kb_text,
           "code_analysis": code_engine.analyze_files(files)}
    ctx["code_samples"] = "\n\n".join(f["filename"] + "\n" + code_engine.snippet(f["content"], 80) for f in files[:15])
    msgs = prompts.code_analysis_messages(ctx)
    data = await llm.chat_json(msgs, max_tokens=3000)
    meta = {
        "modules": data.get("modules", []),
        "architecture": data.get("architecture", ""),
        "highlights": data.get("highlights", []),
        "suggestions": data.get("suggestions", []),
        "positioning": data.get("software_positioning", ""),
    }
    content = json.dumps(data, ensure_ascii=False, indent=2)
    _save_generated(project_id, "analysis", "代码结构分析", content, meta, fingerprint)
    return db.get_doc(project_id, "analysis")


def _base_ctx(project_id: int, project: Dict[str, Any], analysis: Dict[str, Any],
              kb_text: str) -> Dict[str, Any]:
    meta = analysis.get("meta") or {}
    return {
        "project": project,
        "kb_text": kb_text,
        "modules_text": _modules_text(meta),
        "code_analysis": code_engine.analyze_files(db.get_source_contents(project_id)),
        "code_samples": "\n\n".join(f["filename"] + "\n" + code_engine.snippet(f["content"], 80) for f in db.get_source_contents(project_id)[:15]),
        "git_log": project.get("git_log", ""),
        "total_lines": project.get("code_lines_total", 0),
    }


async def stream_manual(project_id: int, doc_kind: str = "manual") -> AsyncIterator[Dict[str, Any]]:
    """逐章节生成操作说明书（doc_kind=manual）或设计说明书（doc_kind=design）。"""
    fingerprint = db.input_fingerprint(project_id)
    project = _require_project(project_id)
    yield _event("analysis", "start", "分析源代码结构…")
    analysis = await ensure_analysis(project_id)
    meta = analysis.get("meta") or {}
    modules: List[Dict[str, Any]] = meta.get("modules") or []
    kb_text = await kb_service.get_kb_context(project_id)
    ctx = _base_ctx(project_id, project, analysis, kb_text)
    label = "操作说明书" if doc_kind == "manual" else "设计说明书"
    chapters: List[Dict[str, str]] = []
    if doc_kind == "manual":
        if not modules:
            raise ValueError("代码分析未识别出功能模块，请确认源代码已导入后重试")
        for ch in prompts.MANUAL_CHAPTERS:
            chapters.append(ch)
        for m in modules:
            chapters.append({"key": f"mod_{m.get('name')}", "title": str(m.get("name", "功能模块")),
                             "hint": "", "module": m})
    else:
        chapters = list(prompts.DESIGN_CHAPTERS)
    yield _event("chapters", "start", f"共 {len(chapters)} 个章节待生成", {"total": len(chapters)})
    parts: List[str] = [f"# {project['full_name']} {project['version']} {label}"]
    total_words = 0
    for i, ch in enumerate(chapters, 1):
        title = ch["title"]
        yield _event("chapter", "start", f"[{i}/{len(chapters)}] 生成：{title}", {"index": i, "title": title})
        if ch.get("module"):
            msgs = prompts.manual_module_messages(ctx, ch["module"])
        elif doc_kind == "manual":
            msgs = prompts.manual_chapter_messages(ctx, ch["title"], ch["hint"])
        else:
            msgs = prompts.design_chapter_messages(ctx, ch["title"], ch["hint"])
        text = await llm.chat(msgs, max_tokens=3500)
        text = text.strip()
        if not text.startswith("#"):
            text = f"## {ch['title']}\n\n" + text
        parts.append(text)
        total_words += len(text)
        yield _event("chapter", "done", f"{title} 完成（{len(text)}字）",
                     {"index": i, "title": title, "words": len(text)})
    content = "\n\n".join(parts)
    doc_id = _save_generated(project_id, doc_kind, f"{project['full_name']} {label}", content,
                           {"words": total_words, "chapters": len(chapters)}, fingerprint)
    yield _event("doc", "done", f"{label}生成完成，共 {total_words} 字",
                 {"doc_id": doc_id, "words": total_words, "doc_type": doc_kind})


async def gen_form(project_id: int) -> Dict[str, Any]:
    fingerprint = db.input_fingerprint(project_id)
    project = _require_project(project_id)
    analysis = await ensure_analysis(project_id)
    files = db.get_source_contents(project_id)
    kb_text = await kb_service.get_kb_context(project_id)
    ctx = _base_ctx(project_id, project, analysis, kb_text)
    ctx["code_analysis"] = code_engine.analyze_files(files)
    msgs = prompts.form_messages(ctx)
    data = await llm.chat_json(msgs, max_tokens=3500)
    doc_id = _save_generated(project_id, "form", "申请表预填内容",
                           json.dumps(data, ensure_ascii=False, indent=2), {"data": data}, fingerprint)
    db.update_project(project_id, {"code_lines_total": code_engine.analyze_files(files)["total_lines"]})
    return {"doc_id": doc_id, "data": data}


async def gen_declaration(project_id: int) -> Dict[str, Any]:
    fingerprint = db.input_fingerprint(project_id)
    project = _require_project(project_id)
    analysis = await ensure_analysis(project_id)
    kb_text = await kb_service.get_kb_context(project_id)
    ctx = _base_ctx(project_id, project, analysis, kb_text)
    msgs = prompts.declaration_messages(ctx)
    data = await llm.chat_json(msgs, max_tokens=2500)
    doc_id = _save_generated(project_id, "declaration", "AI使用情况声明及人类实质性创作说明",
                           json.dumps(data, ensure_ascii=False, indent=2), {"data": data}, fingerprint)
    return {"doc_id": doc_id, "data": data}


async def gen_evidence(project_id: int) -> Dict[str, Any]:
    fingerprint = db.input_fingerprint(project_id)
    project = _require_project(project_id)
    analysis = await ensure_analysis(project_id)
    kb_text = await kb_service.get_kb_context(project_id)
    ctx = _base_ctx(project_id, project, analysis, kb_text)
    msgs = prompts.evidence_messages(ctx)
    text = await llm.chat(msgs, max_tokens=3000)
    doc_id = _save_generated(project_id, "evidence", "软件开发过程记录", text.strip(),
                           {"words": len(text)}, fingerprint)
    return {"doc_id": doc_id, "words": len(text)}


async def stream_all(project_id: int, doc_kind: str = "manual") -> AsyncIterator[Dict[str, Any]]:
    """一键生成全套材料：分析 → 说明书 → 申请表 → AI声明 → 过程记录 → 审查 → 导出。"""
    project = _require_project(project_id)
    files = db.get_source_contents(project_id)
    if not files:
        yield _event("pipeline", "error", "请先导入源代码再一键生成")
        return
    if doc_kind not in ("manual", "design"):
        doc_kind = "design" if (project.get("status") or "") == "no_ui" else "manual"
    steps = [
        ("analysis", "代码分析", None),
        ("manual" if doc_kind == "manual" else "design", "生成鉴别文档", None),
        ("form", "申请表字段", None),
        ("declaration", "AI声明", None),
        ("evidence", "开发过程记录", None),
    ]
    yield _event("pipeline", "start", f"开始一键生成全套材料（共 {len(steps)}+2 步）",
                 {"doc_kind": doc_kind})
    for step, label, _fn in steps:
        yield _event(step, "start", f"{label}…")
        try:
            if step == "analysis":
                await ensure_analysis(project_id)
                yield _event(step, "done", "代码分析完成")
            elif step in ("manual", "design"):
                async for ev in stream_manual(project_id, doc_kind):
                    if ev["step"] == "chapter":
                        yield ev
                yield _event(step, "done", "鉴别文档生成完成")
            elif step == "form":
                r = await gen_form(project_id)
                yield _event(step, "done", "申请表字段生成完成", {"doc_id": r["doc_id"]})
            elif step == "declaration":
                r = await gen_declaration(project_id)
                yield _event(step, "done", "AI声明生成完成", {"doc_id": r["doc_id"]})
            elif step == "evidence":
                r = await gen_evidence(project_id)
                yield _event(step, "done", "开发过程记录生成完成", {"doc_id": r["doc_id"]})
        except llm.LLMNotConfigured as e:
            yield _event("pipeline", "error", str(e))
            return
        except Exception as e:
            yield _event("pipeline", "error", f"{label}失败：{str(e)[:300]}")
            return
    yield _event("review", "start", "执行合规审查预检…")
    from . import review_engine
    report = await review_engine.run_review(project_id, include_llm=True)
    yield _event("review", "done",
                 f"审查完成：{'通过' if report['passed'] else '存在阻断项'}"
                 f"（阻断 {report['blockers']} / 提醒 {report['warnings']}）",
                 {"passed": report["passed"], "blockers": report["blockers"],
                  "warnings": report["warnings"]})
    from . import exporter
    yield _event("export", "start", "导出全套 docx 与打包…")
    out = exporter.export_all(project_id)
    yield _event("export", "done", f"已导出 {len(out['files'])} 个文件", out)
    yield _event("pipeline", "done", "材料草稿已导出，请处理预检问题并完成人工核对",
                 {"passed": report["passed"], **out})
