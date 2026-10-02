"""合规审查与知识库路由。"""
from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from .. import database as db
from .. import llm
from ..services import kb_service, review_engine

router = APIRouter(tags=["review-kb"])


class ReviewIn(BaseModel):
    include_llm: bool = True


@router.post("/api/projects/{pid}/review")
async def run_review(pid: int, body: ReviewIn):
    if not db.get_project(pid):
        raise HTTPException(404, "项目不存在")
    include_llm = body.include_llm and llm.configured()
    try:
        report = await review_engine.run_review(pid, include_llm=include_llm)
    except ValueError as e:
        raise HTTPException(400, str(e))
    report["llm_used"] = include_llm
    return report


@router.get("/api/projects/{pid}/reports")
def list_reports(pid: int):
    return {"reports": db.list_reports(pid)}


@router.get("/api/projects/{pid}/reports/{rid}")
def get_report(pid: int, rid: int):
    r = db.get_report(rid)
    if not r or r["project_id"] != pid:
        raise HTTPException(404, "报告不存在")
    return r


# ---------------- 知识库 ----------------

class CaseIn(BaseModel):
    raw_text: str
    source_type: str = "补正通知"
    project_id: Optional[int] = None


class RuleIn(BaseModel):
    category: str = "其他"
    problem: str
    solution: str = ""
    project_id: Optional[int] = None
    check_type: str = "none"
    check_target: str = ""
    check_mode: str = "forbid"
    check_pattern: str = ""


class RulePatch(BaseModel):
    category: Optional[str] = None
    problem: Optional[str] = None
    solution: Optional[str] = None
    enabled: Optional[bool] = None
    project_id: Optional[int] = None


@router.post("/api/kb/analyze")
async def kb_analyze(body: CaseIn):
    if not body.raw_text.strip():
        raise HTTPException(400, "请粘贴补正/驳回通知原文")
    try:
        result = await kb_service.analyze_and_store(
            body.raw_text.strip(), body.source_type, body.project_id)
    except Exception as e:
        raise HTTPException(500, f"归因失败：{str(e)[:300]}")
    return result


@router.get("/api/kb/rules")
def kb_rules(project_id: Optional[int] = None, enabled_only: bool = False):
    return {"rules": db.list_rules(project_id, enabled_only)}


@router.post("/api/kb/rules")
def kb_add_rule(body: RuleIn):
    check_config: Dict[str, Any] = {}
    if body.check_type == "regex" and body.check_pattern:
        check_config = {"target": body.check_target, "mode": body.check_mode,
                        "pattern": body.check_pattern, "value": 0}
    rid = db.create_rule(None, body.project_id, body.category, body.problem,
                         body.solution, body.check_type, check_config)
    return {"id": rid}


@router.patch("/api/kb/rules/{rid}")
def kb_patch_rule(rid: int, body: RulePatch):
    fields = {k: v for k, v in body.model_dump().items() if v is not None}
    if not fields:
        raise HTTPException(400, "没有需要更新的字段")
    db.update_rule(rid, fields)
    return db.get_rule(rid)


@router.delete("/api/kb/rules/{rid}")
def kb_delete_rule(rid: int):
    db.delete_rule(rid)
    return {"ok": True}


@router.get("/api/kb/cases")
def kb_cases():
    return {"cases": db.list_cases()}
