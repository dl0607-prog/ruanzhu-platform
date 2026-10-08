"""数据层：SQLAlchemy ORM（Query API 风格），模型即表结构，读写全部走 ORM 会话。"""
import json
import hashlib
from contextlib import contextmanager
from datetime import datetime
from typing import Any, Dict, Iterator, List, Optional

from sqlalchemy import String, Text, create_engine
from sqlalchemy.orm import (DeclarativeBase, Mapped, Session, mapped_column,
                            sessionmaker)

from . import config


class Base(DeclarativeBase):
    pass


class Project(Base):
    __tablename__ = "projects"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    full_name: Mapped[str] = mapped_column(String(200), default="")
    short_name: Mapped[str] = mapped_column(String(100), default="")
    version: Mapped[str] = mapped_column(String(20), default="V1.0")
    completion_date: Mapped[str] = mapped_column(String(20), default="")
    publish_date: Mapped[str] = mapped_column(String(20), default="")
    dev_type: Mapped[str] = mapped_column(String(20), default="独立开发")
    owner_name: Mapped[str] = mapped_column(String(100), default="")
    owner_type: Mapped[str] = mapped_column(String(20), default="个人")
    main_functions: Mapped[str] = mapped_column(Text, default="")
    tech_stack: Mapped[str] = mapped_column(Text, default="")
    ai_usage: Mapped[str] = mapped_column(String(30), default="ai_assisted")
    git_log: Mapped[str] = mapped_column(Text, default="")
    code_lines_total: Mapped[int] = mapped_column(default=0)
    status: Mapped[str] = mapped_column(String(20), default="draft")
    created_at: Mapped[str] = mapped_column(String(30), default="")
    updated_at: Mapped[str] = mapped_column(String(30), default="")


class SourceFile(Base):
    __tablename__ = "source_files"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(default=0, index=True)
    filename: Mapped[str] = mapped_column(String(300), default="")
    content: Mapped[str] = mapped_column(Text, default="")
    line_count: Mapped[int] = mapped_column(default=0)
    sort_order: Mapped[int] = mapped_column(default=0)


class GeneratedDoc(Base):
    __tablename__ = "generated_docs"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(default=0, index=True)
    doc_type: Mapped[str] = mapped_column(String(30), default="")
    title: Mapped[str] = mapped_column(String(200), default="")
    content: Mapped[str] = mapped_column(Text, default="")
    meta_json: Mapped[str] = mapped_column(Text, default="{}")
    created_at: Mapped[str] = mapped_column(String(30), default="")
    updated_at: Mapped[str] = mapped_column(String(30), default="")


class KbCase(Base):
    __tablename__ = "kb_cases"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    project_id: Mapped[Optional[int]] = mapped_column(default=None)
    raw_text: Mapped[str] = mapped_column(Text, default="")
    source_type: Mapped[str] = mapped_column(String(30), default="补正通知")
    analysis_json: Mapped[str] = mapped_column(Text, default="{}")
    created_at: Mapped[str] = mapped_column(String(30), default="")


class KbRule(Base):
    __tablename__ = "kb_rules"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    case_id: Mapped[Optional[int]] = mapped_column(default=None)
    project_id: Mapped[Optional[int]] = mapped_column(default=None)
    category: Mapped[str] = mapped_column(String(30), default="其他")
    problem: Mapped[str] = mapped_column(Text, default="")
    solution: Mapped[str] = mapped_column(Text, default="")
    check_type: Mapped[str] = mapped_column(String(20), default="none")
    check_config: Mapped[str] = mapped_column(Text, default="{}")
    enabled: Mapped[bool] = mapped_column(default=True)
    hit_count: Mapped[int] = mapped_column(default=0)
    created_at: Mapped[str] = mapped_column(String(30), default="")


class ReviewReport(Base):
    __tablename__ = "review_reports"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(default=0, index=True)
    passed: Mapped[bool] = mapped_column(default=False)
    blockers: Mapped[int] = mapped_column(default=0)
    warnings: Mapped[int] = mapped_column(default=0)
    result_json: Mapped[str] = mapped_column(Text, default="[]")
    created_at: Mapped[str] = mapped_column(String(30), default="")


class SourceShot(Base):
    """界面截图库：label 与说明书中的【截图占位：label】匹配，导出 docx 时自动嵌入。"""
    __tablename__ = "source_shots"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(default=0, index=True)
    label: Mapped[str] = mapped_column(String(200), default="")
    filename: Mapped[str] = mapped_column(String(300), default="")
    created_at: Mapped[str] = mapped_column(String(30), default="")


engine = create_engine(
    "sqlite:///" + str(config.DB_PATH),
    connect_args={"check_same_thread": False},
)
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)

PROJECT_FIELDS = (
    "full_name", "short_name", "version", "completion_date", "publish_date",
    "dev_type", "owner_name", "owner_type", "main_functions", "tech_stack",
    "ai_usage", "git_log", "status",
)
# 允许 update_project 写入的统计字段（如源码导入后回填总行数）
PROJECT_STAT_FIELDS = ("code_lines_total",)
RULE_FIELDS = ("category", "problem", "solution", "check_type", "enabled", "project_id")
DOC_TYPES = ("analysis", "manual", "design", "form", "declaration", "evidence")


def now() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def init_db() -> None:
    Base.metadata.create_all(engine)


@contextmanager
def get_session() -> Iterator[Session]:
    s = SessionLocal()
    try:
        yield s
        s.commit()
    except Exception:
        s.rollback()
        raise
    finally:
        s.close()


def jloads(text: str, default: Any = None) -> Any:
    try:
        return json.loads(text) if text else default
    except (json.JSONDecodeError, TypeError):
        return default


def jdumps(obj: Any) -> str:
    return json.dumps(obj, ensure_ascii=False)


def _row(obj: Any) -> Dict[str, Any]:
    return {c: getattr(obj, c) for c in obj.__table__.columns.keys()}


# ---------------- projects ----------------

def create_project(fields: Dict[str, Any]) -> int:
    f = {k: fields.get(k, "") for k in PROJECT_FIELDS if k != "status"}
    with get_session() as s:
        p = Project(**f,
                    status=fields.get("status") or "draft",
                    created_at=now(), updated_at=now())
        s.add(p)
        s.flush()
        from . import auth
        user = auth.current_user.get()
        if user:
            s.add(auth.ProjectOwner(project_id=p.id, user_id=user["id"]))
        return p.id


def get_project(project_id: int) -> Optional[Dict[str, Any]]:
    with get_session() as s:
        p = s.get(Project, project_id)
        return _row(p) if p else None


def list_projects() -> List[Dict[str, Any]]:
    with get_session() as s:
        return [_row(p) for p in s.query(Project).order_by(Project.id.desc()).all()]


def update_project(project_id: int, fields: Dict[str, Any]) -> None:
    with get_session() as s:
        p = s.get(Project, project_id)
        if not p:
            return
        for k in PROJECT_FIELDS + PROJECT_STAT_FIELDS:
            if k in fields:
                setattr(p, k, fields[k])
        p.updated_at = now()


def delete_project(project_id: int) -> None:
    from .auth import ProjectOwner
    from .services.submission import SubmissionState
    with get_session() as s:
        p = s.get(Project, project_id)
        if p:
            s.delete(p)
        for model in (SourceFile, GeneratedDoc, ReviewReport, KbRule, KbCase, SourceShot, ProjectOwner, SubmissionState):
            q = s.query(model).filter(model.project_id == project_id).all()
            for row in q:
                s.delete(row)


# ---------------- source files ----------------

def add_source_file(project_id: int, filename: str, content: str, line_count: int, sort_order: int) -> int:
    with get_session() as s:
        f = SourceFile(project_id=project_id, filename=filename, content=content,
                       line_count=line_count, sort_order=sort_order)
        s.add(f)
        s.flush()
        return f.id


def list_source_files(project_id: int) -> List[Dict[str, Any]]:
    with get_session() as s:
        rows = (s.query(SourceFile).filter(SourceFile.project_id == project_id)
                .order_by(SourceFile.sort_order, SourceFile.id).all())
        return [{k: v for k, v in _row(f).items() if k != "content"} for f in rows]


def get_source_contents(project_id: int) -> List[Dict[str, Any]]:
    with get_session() as s:
        rows = (s.query(SourceFile).filter(SourceFile.project_id == project_id)
                .order_by(SourceFile.sort_order, SourceFile.id).all())
        return [{"filename": f.filename, "content": f.content, "line_count": f.line_count}
                for f in rows]


def replace_source_files(project_id: int, files: List[Dict[str, Any]]) -> None:
    with get_session() as s:
        for f in s.query(SourceFile).filter(SourceFile.project_id == project_id).all():
            s.delete(f)
        for i, f in enumerate(files):
            s.add(SourceFile(project_id=project_id, filename=f.get("filename", "code.txt"),
                             content=f.get("content", ""), line_count=f.get("line_count", 0),
                             sort_order=i))


# ---------------- generated docs ----------------

def input_fingerprint(project_id: int) -> str:
    project = get_project(project_id) or {}
    fields = {k: project.get(k) for k in PROJECT_FIELDS if k != "status"}
    from .auth import ProjectOwner
    with get_session() as session:
        owner = session.get(ProjectOwner, project_id)
        owner_id = owner.user_id if owner else None
    payload = jdumps([owner_id, fields, get_source_contents(project_id)])
    return hashlib.sha256(payload.encode()).hexdigest()


def upsert_doc(project_id: int, doc_type: str, title: str, content: str, meta: Dict[str, Any]) -> int:
    meta = {"input_fingerprint": input_fingerprint(project_id), **meta}
    with get_session() as s:
        d = (s.query(GeneratedDoc)
             .filter(GeneratedDoc.project_id == project_id, GeneratedDoc.doc_type == doc_type)
             .first())
        if d:
            d.title = title
            d.content = content
            d.meta_json = jdumps(meta)
            d.updated_at = now()
            return d.id
        d = GeneratedDoc(project_id=project_id, doc_type=doc_type, title=title,
                         content=content, meta_json=jdumps(meta),
                         created_at=now(), updated_at=now())
        s.add(d)
        s.flush()
        return d.id


def get_doc(project_id: int, doc_type: str) -> Optional[Dict[str, Any]]:
    with get_session() as s:
        d = (s.query(GeneratedDoc)
             .filter(GeneratedDoc.project_id == project_id, GeneratedDoc.doc_type == doc_type)
             .first())
        if not d:
            return None
        row = _row(d)
        row["meta"] = jloads(row.pop("meta_json"), {})
        return row


def list_docs(project_id: int) -> List[Dict[str, Any]]:
    with get_session() as s:
        rows = (s.query(GeneratedDoc).filter(GeneratedDoc.project_id == project_id)
                .order_by(GeneratedDoc.id).all())
        return [{"id": d.id, "doc_type": d.doc_type, "title": d.title,
                 "updated_at": d.updated_at, "size": len(d.content or "")} for d in rows]


def delete_doc(project_id: int, doc_type: str) -> None:
    with get_session() as s:
        d = (s.query(GeneratedDoc)
             .filter(GeneratedDoc.project_id == project_id, GeneratedDoc.doc_type == doc_type)
             .first())
        if d:
            s.delete(d)


def update_doc(project_id: int, doc_type: str, content: str, title: Optional[str] = None) -> bool:
    """人工编辑已生成材料（AI 辅助 + 人类实质性修改的证据之一）。"""
    with get_session() as s:
        d = (s.query(GeneratedDoc)
             .filter(GeneratedDoc.project_id == project_id, GeneratedDoc.doc_type == doc_type)
             .first())
        if not d:
            return False
        d.content = content
        if title is not None:
            d.title = title
        d.updated_at = now()
        return True


# ---------------- knowledge base ----------------

def create_case(project_id: Optional[int], raw_text: str, source_type: str, analysis: Dict[str, Any]) -> int:
    with get_session() as s:
        c = KbCase(project_id=project_id, raw_text=raw_text, source_type=source_type,
                   analysis_json=jdumps(analysis), created_at=now())
        s.add(c)
        s.flush()
        return c.id


def get_case(case_id: int) -> Optional[Dict[str, Any]]:
    with get_session() as s:
        c = s.get(KbCase, case_id)
        if not c:
            return None
        row = _row(c)
        row["analysis"] = jloads(row.pop("analysis_json"), {})
        return row


def list_cases(limit: int = 100) -> List[Dict[str, Any]]:
    with get_session() as s:
        rows = s.query(KbCase).order_by(KbCase.id.desc()).limit(limit).all()
        out = []
        for c in rows:
            row = _row(c)
            row["analysis"] = jloads(row.pop("analysis_json"), {})
            row["raw_text"] = (row["raw_text"] or "")[:400]
            out.append(row)
        return out


def create_rule(case_id: Optional[int], project_id: Optional[int], category: str,
                problem: str, solution: str, check_type: str, check_config: Dict[str, Any]) -> int:
    with get_session() as s:
        r = KbRule(case_id=case_id, project_id=project_id, category=category,
                   problem=problem, solution=solution, check_type=check_type,
                   check_config=jdumps(check_config), enabled=True, created_at=now())
        s.add(r)
        s.flush()
        return r.id


def list_rules(project_id: Optional[int] = None, enabled_only: bool = False) -> List[Dict[str, Any]]:
    with get_session() as s:
        rows = s.query(KbRule).order_by(KbRule.id.desc()).all()
        out = []
        for r in rows:
            if enabled_only and not r.enabled:
                continue
            if project_id is not None and r.project_id not in (None, project_id):
                continue
            out.append(_row(r))
        return out


def get_rule(rule_id: int) -> Optional[Dict[str, Any]]:
    with get_session() as s:
        r = s.get(KbRule, rule_id)
        return _row(r) if r else None


def update_rule(rule_id: int, fields: Dict[str, Any]) -> None:
    with get_session() as s:
        r = s.get(KbRule, rule_id)
        if not r:
            return
        for k in RULE_FIELDS:
            if k in fields:
                setattr(r, k, fields[k])


def delete_rule(rule_id: int) -> None:
    with get_session() as s:
        r = s.get(KbRule, rule_id)
        if r:
            s.delete(r)


def incr_rule_hit(rule_id: int) -> None:
    with get_session() as s:
        r = s.get(KbRule, rule_id)
        if r:
            r.hit_count = (r.hit_count or 0) + 1


# ---------------- 界面截图库 ----------------

def add_shot(project_id: int, label: str, filename: str) -> int:
    with get_session() as s:
        shot = SourceShot(project_id=project_id, label=label, filename=filename, created_at=now())
        s.add(shot)
        s.flush()
        return shot.id


def list_shots(project_id: int) -> List[Dict[str, Any]]:
    with get_session() as s:
        rows = (s.query(SourceShot).filter(SourceShot.project_id == project_id)
                .order_by(SourceShot.id).all())
        return [_row(r) for r in rows]


def get_shot(shot_id: int) -> Optional[Dict[str, Any]]:
    with get_session() as s:
        r = s.get(SourceShot, shot_id)
        return _row(r) if r else None


def delete_shot(shot_id: int) -> None:
    with get_session() as s:
        r = s.get(SourceShot, shot_id)
        if r:
            s.delete(r)


# ---------------- review reports ----------------

def create_report(project_id: int, passed: bool, blockers: int, warnings: int,
                  result: List[Dict[str, Any]]) -> int:
    with get_session() as s:
        r = ReviewReport(project_id=project_id, passed=passed, blockers=blockers,
                         warnings=warnings, result_json=jdumps(result), created_at=now())
        s.add(r)
        s.flush()
        return r.id


def list_reports(project_id: int, limit: int = 20) -> List[Dict[str, Any]]:
    with get_session() as s:
        rows = (s.query(ReviewReport).filter(ReviewReport.project_id == project_id)
                .order_by(ReviewReport.id.desc()).limit(limit).all())
        out = []
        for r in rows:
            row = _row(r)
            row.pop("result_json")
            out.append(row)
        return out


def get_report(report_id: int) -> Optional[Dict[str, Any]]:
    with get_session() as s:
        r = s.get(ReviewReport, report_id)
        if not r:
            return None
        row = _row(r)
        row["result"] = jloads(row.pop("result_json"), [])
        return row
