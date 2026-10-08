"""导出服务：把各类材料渲染为 docx 并打包 zip + 材料清单。"""
import zipfile
from pathlib import Path
from typing import Any, Dict, List

from .. import config
from .. import database as db
from . import code_engine, docx_engine


def shots_dir(project_id: int) -> Path:
    d = config.DATA_DIR / "shots" / f"project_{project_id}"
    d.mkdir(parents=True, exist_ok=True)
    return d


def project_shots(project_id: int) -> List[Dict[str, str]]:
    """返回 [{label, path}]，供 docx 导出时自动嵌入真实截图。"""
    out = []
    for s in db.list_shots(project_id):
        p = shots_dir(project_id) / s["filename"]
        if p.exists():
            out.append({"label": s["label"], "path": str(p)})
    return out


def _project_dir(project_id: int) -> Path:
    d = config.EXPORT_DIR / f"project_{project_id}"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _safe_name(s: str) -> str:
    for ch in '\\/:*?"<>| ':
        s = s.replace(ch, "_")
    return s[:80]


def export_source(project_id: int) -> Dict[str, Any]:
    project = db.get_project(project_id)
    if not project:
        raise ValueError("项目不存在")
    files = db.get_source_contents(project_id)
    if not files:
        raise ValueError("请先导入源代码")
    pages_info = code_engine.build_pages(files)
    path = _project_dir(project_id) / f"源程序-{_safe_name(project['full_name'])}-{_safe_name(project['version'])}.docx"
    docx_engine.export_source_docx(project, pages_info["pages"], path)
    return {"path": path.name, "pages": pages_info["pages_submitted"],
            "total_lines": pages_info["total_lines"], "mode": pages_info["mode"]}


def export_manual(project_id: int) -> Dict[str, Any]:
    project = db.get_project(project_id)
    doc = db.get_doc(project_id, "manual")
    kind, label = ("manual", "操作说明书")
    if not doc:
        doc = db.get_doc(project_id, "design")
        kind, label = ("design", "设计说明书")
    if not doc:
        raise ValueError("请先生成操作说明书或设计说明书")
    path = _project_dir(project_id) / f"{label}-{_safe_name(project['full_name'])}-{_safe_name(project['version'])}.docx"
    docx_engine.export_markdown_docx(project, doc["content"], path, label,
                                     shots=project_shots(project_id))
    return {"path": path.name, "doc_type": kind, "words": (doc.get("meta") or {}).get("words", 0),
            "shots_embedded": len(project_shots(project_id))}


def export_form(project_id: int) -> Dict[str, Any]:
    project = db.get_project(project_id)
    form = db.get_doc(project_id, "form")
    if not form:
        raise ValueError("请先生成申请表预填内容")
    declaration = db.get_doc(project_id, "declaration")
    decl_data = (declaration or {}).get("meta", {}).get("data") if declaration else None
    path = _project_dir(project_id) / f"申请表预填-{_safe_name(project['full_name'])}-{_safe_name(project['version'])}.docx"
    docx_engine.export_form_docx(project, (form.get("meta") or {}).get("data", {}), decl_data, path)
    return {"path": path.name}


def export_evidence(project_id: int) -> Dict[str, Any]:
    project = db.get_project(project_id)
    doc = db.get_doc(project_id, "evidence")
    if not doc:
        raise ValueError("请先生成开发过程记录")
    path = _project_dir(project_id) / f"开发过程记录-{_safe_name(project['full_name'])}-{_safe_name(project['version'])}.docx"
    docx_engine.export_markdown_docx(project, doc["content"], path, "开发过程记录",
                                     shots=project_shots(project_id))
    return {"path": path.name}


def export_all(project_id: int) -> Dict[str, Any]:
    project = db.get_project(project_id)
    if not project:
        raise ValueError("项目不存在")
    out_dir = _project_dir(project_id)
    files: List[Dict[str, str]] = []
    results = {}
    for key, fn in (("source", export_source), ("manual", export_manual),
                    ("form", export_form), ("evidence", export_evidence)):
        try:
            r = fn(project_id)
            results[key] = r
            files.append(r["path"])
        except ValueError as e:
            results[key] = {"error": str(e)}
    declaration = db.get_doc(project_id, "declaration")
    results["declaration"] = {"ready": bool(declaration)}
    checklist = docx_engine.checklist_text(
        project,
        has_code_doc="source" in results and "path" in results["source"],
        has_manual="manual" in results and "path" in results["manual"],
        has_form="form" in results and "path" in results["form"],
        has_declaration=bool(declaration),
        has_evidence="evidence" in results and "path" in results["evidence"],
    )
    from . import submission
    status = submission.state(project_id)
    checklist += "\n\n人工核对（材料变更后需重新确认）：\n"
    for key, label in submission.CHECKS.items():
        checklist += ("[已确认] " if status.get('checks', {}).get(key) else "[待核对] ") + label + "\n"
    if status.get('correction_due'):
        checklist += "补正指定期限：" + status['correction_due'] + "\n"
    checklist_path = out_dir / "材料清单与提交检查.txt"
    checklist_path.write_text(checklist, encoding="utf-8")
    files.append(checklist_path.name)
    zip_path = out_dir / f"软著申请材料包-{_safe_name(project['full_name'])}-{_safe_name(project['version'])}.zip"
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for name in files:
            p = out_dir / name
            if p.exists():
                zf.write(p, name)
    return {"files": files, "zip": zip_path.name, "detail": results}


def list_export_files(project_id: int) -> List[str]:
    d = _project_dir(project_id)
    return sorted([p.name for p in d.iterdir() if p.is_file()])


def export_file_path(project_id: int, filename: str) -> Path:
    d = _project_dir(project_id)
    p = (d / filename).resolve()
    if d.resolve() not in p.parents or not p.exists():
        raise ValueError("文件不存在")
    return p
