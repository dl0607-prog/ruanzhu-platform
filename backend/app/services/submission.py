"""Human verification checklist bound to the actual material revision."""
import hashlib
from datetime import date

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import Text
from sqlalchemy.orm import Mapped, mapped_column

from .. import database as db

router = APIRouter(prefix='/api/projects', tags=['submission'])
CHECKS = {
    'identity_rights': '身份和权属：申请人信息正确，代码及相关协议有合法依据',
    'software_materials': '软件和材料：软件已实际运行，说明书、截图及开发记录都符合真实情况',
    'portal_files': '官网和文件：已核对官网申请表、签章要求及最终提交文件的分页和清晰度',
}


class SubmissionState(db.Base):
    __tablename__ = 'submission_states'
    project_id: Mapped[int] = mapped_column(primary_key=True)
    data_json: Mapped[str] = mapped_column(Text, default='{}')


def fingerprint(pid):
    docs = [db.get_doc(pid, d['doc_type'])['content'] for d in db.list_docs(pid)]
    return hashlib.sha256(db.jdumps([db.input_fingerprint(pid), docs, db.list_shots(pid)]).encode()).hexdigest()


def state(pid):
    with db.get_session() as session:
        row = session.get(SubmissionState, pid)
        data = db.jloads(row.data_json, {}) if row else {}
    stale = data.get('fingerprint') != fingerprint(pid)
    return {**data, 'checks': {} if stale else data.get('checks', {}), 'stale': stale, 'items': CHECKS}


class ChecklistIn(BaseModel):
    checks: dict[str, bool] = Field(default_factory=dict)
    correction_due: str = ''
    correction_notes: str = Field(default='', max_length=10000)


@router.get('/{pid}/submission')
def get_submission(pid: int):
    return state(pid)


@router.put('/{pid}/submission')
def save_submission(pid: int, body: ChecklistIn):
    if body.correction_due:
        try:
            date.fromisoformat(body.correction_due)
        except ValueError:
            raise HTTPException(400, '补正截止日期格式应为 YYYY-MM-DD')
    if any(key not in CHECKS for key in body.checks):
        raise HTTPException(400, '未知核对项')
    data = body.model_dump()
    data['fingerprint'] = fingerprint(pid)
    with db.get_session() as session:
        row = session.get(SubmissionState, pid)
        if row is None:
            row = SubmissionState(project_id=pid)
            session.add(row)
        row.data_json = db.jdumps(data)
    return state(pid)
