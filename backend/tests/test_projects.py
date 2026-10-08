"""Project API regressions, using a fresh database for each test."""
import io
import zipfile

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app import database as db
from app.routers import projects


@pytest.fixture
def client(tmp_path, monkeypatch):
    engine = create_engine(f"sqlite:///{tmp_path / 'test.db'}", connect_args={"check_same_thread": False})
    db.Base.metadata.create_all(engine)
    monkeypatch.setattr(db, "SessionLocal", sessionmaker(bind=engine, expire_on_commit=False))
    app = FastAPI()
    app.include_router(projects.router)
    with TestClient(app) as client:
        yield client
    engine.dispose()


def project(client):
    return client.post('/api/projects', json={"full_name": "测试平台", "status": "submitted", "owner_type": "企业"}).json()['id']


def test_save_preserves_status_and_omitted_fields(client):
    pid = project(client)
    assert client.put(f'/api/projects/{pid}', json={"full_name": "新版平台"}).status_code == 200
    data = client.get(f'/api/projects/{pid}').json()
    assert (data['full_name'], data['status'], data['owner_type']) == ('新版平台', 'submitted', '企业')


@pytest.mark.parametrize('fields', [{"full_name": " "}, {"status": "unknown"}])
def test_invalid_update_leaves_project_unchanged(client, fields):
    pid = project(client)
    assert client.put(f'/api/projects/{pid}', json=fields).status_code == 400
    assert client.get(f'/api/projects/{pid}').json()['full_name'] == '测试平台'


def test_append_counts_all_source_and_empty_import_preserves_it(client):
    pid = project(client)
    url = f'/api/projects/{pid}/code'
    client.post(url, json={"files": [{"filename": "a.py", "content": "a = 1\na = 2"}]})
    result = client.post(url, json={"replace": False, "files": [{"filename": "b.py", "content": "b = 1"}]}).json()
    stats = client.get(url + '/stats').json()
    assert result['total_lines'] == stats['total_lines'] == 5
    assert client.get(f'/api/projects/{pid}').json()['code_lines_total'] == 3
    assert client.post(url, json={"files": [{"content": " \n "}]}).status_code == 400
    assert len(client.get(f'/api/projects/{pid}').json()['source_files']) == 2


def test_invalid_zip_is_reported_and_source_preserved(client):
    pid = project(client)
    url = f'/api/projects/{pid}/code'
    client.post(url, json={"files": [{"content": "x = 1"}]})
    assert client.post(url + '/upload', files={'files': ('bad.zip', b'not a zip')}).status_code == 400
    assert len(client.get(f'/api/projects/{pid}').json()['source_files']) == 1


def test_zip_upload_skips_dependencies(client):
    pid = project(client)
    data = io.BytesIO()
    with zipfile.ZipFile(data, 'w') as archive:
        archive.writestr('src/main.py', 'x = 1')
        archive.writestr('node_modules/lib/index.js', 'dependency()')
    result = client.post(f'/api/projects/{pid}/code/upload', files={'files': ('src.zip', data.getvalue())})
    assert result.status_code == 200
    assert result.json()['files_stored'] == 1


def test_archive_entry_limit(client, monkeypatch):
    pid = project(client)
    data = io.BytesIO()
    with zipfile.ZipFile(data, 'w') as archive:
        archive.writestr('main.py', 'x = 1')
    original = zipfile.ZipFile.infolist
    monkeypatch.setattr(zipfile.ZipFile, 'infolist', lambda self: original(self) * 5001)
    assert client.post(f'/api/projects/{pid}/code/upload', files={'files': ('src.zip', data.getvalue())}).status_code == 413
