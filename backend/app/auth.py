"""Cookie sessions and project access for the multi-user deployment."""
import hashlib
import hmac
import re
import secrets
import time
from contextvars import ContextVar

from fastapi import APIRouter, HTTPException, Request, Response
from pydantic import BaseModel, Field
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from . import config, database as db

current_user = ContextVar('current_user', default=None)
router = APIRouter(prefix='/api/auth', tags=['auth'])


class User(db.Base):
    __tablename__ = 'users'
    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(80), unique=True)
    password_hash: Mapped[str] = mapped_column(String(256))
    admin: Mapped[bool] = mapped_column(default=False)


class LoginSession(db.Base):
    __tablename__ = 'login_sessions'
    token_hash: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[int]
    expires: Mapped[int]


class ProjectOwner(db.Base):
    __tablename__ = 'project_owners'
    project_id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(index=True)


class LoginAttempt(db.Base):
    __tablename__ = 'login_attempts'
    key: Mapped[str] = mapped_column(String(64), primary_key=True)
    count: Mapped[int] = mapped_column(default=0)
    until: Mapped[int]


def hash_password(password, salt=None):
    salt = salt or secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 600000).hex()
    return salt + ':' + digest


def bootstrap():
    with db.get_session() as s:
        admin = s.query(User).filter_by(admin=True).first()
        if not admin:
            password = config._get('ADMIN_PASSWORD')
            if len(password) < 12:
                raise RuntimeError('请在 .env 设置至少12位的 ADMIN_PASSWORD 后启动')
            admin = User(username=config._get('ADMIN_USERNAME', 'admin'), password_hash=hash_password(password), admin=True)
            s.add(admin)
            s.flush()
        # Existing single-user projects become the administrator's projects.
        for project in s.query(db.Project).all():
            if not s.get(ProjectOwner, project.id):
                s.add(ProjectOwner(project_id=project.id, user_id=admin.id))


def owned_ids():
    user = current_user.get()
    if user is None:
        return []
    with db.get_session() as s:
        return [r.project_id for r in s.query(ProjectOwner).filter_by(user_id=user['id']).all()]


def require_project(pid):
    if pid not in owned_ids():
        raise HTTPException(404, '项目不存在')


def require_admin():
    if not (current_user.get() or {}).get('admin'):
        raise HTTPException(403, '仅管理员可管理公共知识库和账号')


def register_project(pid):
    user = current_user.get()
    if user:
        with db.get_session() as s:
            s.add(ProjectOwner(project_id=pid, user_id=user['id']))


def identify(token):
    if not token:
        return None
    with db.get_session() as s:
        session = s.get(LoginSession, hashlib.sha256(token.encode()).hexdigest())
        if not session or session.expires <= time.time():
            return None
        user = s.get(User, session.user_id)
        return {'id': user.id, 'username': user.username, 'admin': user.admin} if user else None


class Credentials(BaseModel):
    username: str = Field(min_length=1, max_length=80, pattern=r'^[A-Za-z0-9_.@-]+$')
    password: str = Field(min_length=12, max_length=256)


@router.post('/login')
def login(body: Credentials, request: Request, response: Response):
    # Persist rate limits across workers; use socket peer, not untrusted forwarded headers.
    key = hashlib.sha256((request.client.host + ':' + body.username).encode()).hexdigest()
    now = int(time.time())
    with db.get_session() as s:
        attempt = s.get(LoginAttempt, key)
        if attempt and attempt.until > now and attempt.count >= 10:
            raise HTTPException(429, '尝试过多，请15分钟后重试')
        if not attempt:
            attempt = LoginAttempt(key=key, count=0, until=now + 900)
            s.add(attempt)
        if attempt.until <= now:
            attempt.count, attempt.until = 0, now + 900
        user = s.query(User).filter_by(username=body.username).first()
        stored = user.password_hash if user else hash_password('unmatched-password')
        valid = hmac.compare_digest(stored, hash_password(body.password, stored.split(':')[0])) and user is not None
        if not valid:
            attempt.count += 1
        else:
            attempt.count = 0
            token = secrets.token_urlsafe(32)
            s.query(LoginSession).filter(LoginSession.expires <= now).delete()
            s.add(LoginSession(token_hash=hashlib.sha256(token.encode()).hexdigest(), user_id=user.id, expires=now + 43200))
    if not valid:
        raise HTTPException(401, '账号或密码错误')
    response.set_cookie('rz_session', token, httponly=True, secure=config._get('COOKIE_SECURE', 'true').lower() == 'true', samesite='strict', max_age=43200)
    return {'ok': True}


@router.get('/me')
def me():
    return current_user.get()


@router.post('/logout')
def logout(request: Request, response: Response):
    token = request.cookies.get('rz_session', '')
    with db.get_session() as s:
        s.query(LoginSession).filter_by(token_hash=hashlib.sha256(token.encode()).hexdigest()).delete()
    response.delete_cookie('rz_session')
    return {'ok': True}


@router.post('/users')
def create_user(body: Credentials):
    require_admin()
    with db.get_session() as s:
        if s.query(User).filter_by(username=body.username).first():
            raise HTTPException(409, '账号已存在')
        user = User(username=body.username, password_hash=hash_password(body.password), admin=False)
        s.add(user)
        s.flush()
        return {'id': user.id, 'username': user.username}
