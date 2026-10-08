"""Real API workflow with isolated users, database and export directory."""
import io
import json
import zipfile

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app import auth, config, database as db
from app.main import app
from app.services import seed_kb, submission


@pytest.fixture
def client(tmp_path, monkeypatch):
    engine = create_engine(f"sqlite:///{tmp_path / 'app.db'}", connect_args={'check_same_thread': False})
    monkeypatch.setattr(db, 'engine', engine)
    monkeypatch.setattr(db, 'SessionLocal', sessionmaker(bind=engine, expire_on_commit=False))
    monkeypatch.setattr(config, 'DATA_DIR', tmp_path / 'data')
    monkeypatch.setattr(config, 'EXPORT_DIR', tmp_path / 'exports')
    monkeypatch.setenv('ADMIN_PASSWORD', 'test-admin-password')
    monkeypatch.setenv('COOKIE_SECURE', 'false')
    with TestClient(app) as c:
        yield c
    engine.dispose()


def login(c, username='admin', password='test-admin-password'):
    assert c.post('/api/auth/login', json={'username': username, 'password': password}).status_code == 200


def create(c):
    return c.post('/api/projects', json={'full_name':'库存管理系统', 'owner_name':'测试人', 'completion_date':'2025-01-01'}).json()['id']


def test_accounts_isolate_projects_cases_exports_and_rules(client):
    c = client
    assert c.get('/api/projects').status_code == 401
    login(c)
    pid = create(c)
    assert c.post('/api/auth/users', json={'username':'member', 'password':'test-member-password'}).status_code == 200
    result = c.post('/api/kb/analyze', json={'raw_text':'说明书功能不一致', 'project_id':pid})
    rid = result.json()['rule_ids'][0]
    login(c, 'member', 'test-member-password')
    assert c.get('/api/projects').json()['projects'] == []
    for suffix in ('', '/docs', '/shots', '/code/stats', '/files', '/export/bundle', '/submission'):
        assert c.get(f'/api/projects/{pid}' + suffix).status_code == 404
    assert c.post('/api/kb/analyze', json={'raw_text':'通知', 'project_id':pid}).status_code == 404
    assert c.patch(f'/api/kb/rules/{rid}', json={'enabled':False}).status_code == 404
    assert c.get('/api/kb/cases').json()['cases'] == []
    assert all(r['id'] != rid for r in c.get('/api/kb/rules').json()['rules'])
    assert c.post('/api/auth/users', json={'username':'x', 'password':'test-member-password'}).status_code == 403
    assert c.post('/api/projects', json={'full_name':'x'}, headers={'Origin':'https://evil.example'}).status_code == 403
    c.post('/api/auth/logout')
    assert c.get('/api/projects').status_code == 401


def test_manual_application_without_llm_and_stale_checks(client):
    c = client; login(c); pid = create(c)
    url = f'/api/projects/{pid}'
    assert c.post(url + '/code', json={'files':[{'filename':'app.py', 'content':'def stock():\n    return 1'}]}).status_code == 200
    assert c.put(url + '/docs/design', json={'content':'# 库存管理系统 V1.0\n## 设计\nstock函数返回库存。'}).status_code == 200
    form = {'development_purpose':'管理库存', 'main_functions_desc':'查询库存', 'programming_language':'Python'}
    assert c.put(url + '/docs/form', json={'content':json.dumps(form)}).status_code == 200
    assert c.get(url + '/docs/form').json()['meta']['data'] == form
    assert c.put(url + '/docs/form', json={'content':'not json'}).status_code == 400
    checks = {key:True for key in submission.CHECKS}
    assert c.put(url + '/submission', json={'checks':checks}).status_code == 200
    report = c.post(url + '/review', json={'include_llm':False}).json()
    assert report['passed'], report
    assert not any(i['code'] in ('C-TOO-FEW','C-THIN','F-FUNC','F-PURP') for i in report['issues'])
    exported = c.get(url + '/export/bundle')
    assert exported.status_code == 200
    with zipfile.ZipFile(io.BytesIO(exported.content)) as bundle:
        names = bundle.namelist()
        assert any(n.startswith('源程序-') for n in names)
        assert any(n.startswith('设计说明书-') for n in names)
        assert any(n.startswith('申请表预填-') for n in names)
        assert '[已确认]' in bundle.read('材料清单与提交检查.txt').decode()
    assert c.put(url, json={'full_name':'新库存系统'}).status_code == 200
    assert c.get(url + '/submission').json()['checks'] == {}
    report = c.post(url + '/review', json={'include_llm':False}).json()
    assert not report['passed'] and any(i['code'] == 'DOC-STALE' for i in report['issues'])


def test_seed_upgrade_is_idempotent_and_preserves_cases(client):
    login(client)
    pid = create(client)
    legacy = json.loads((__import__('pathlib').Path(seed_kb.__file__).with_name('legacy_seed_problems.json')).read_text())[0]
    rid = db.create_rule(None, None, '其他', legacy, 'old', 'none', {})
    user_rid = db.create_rule(123, pid, '其他', legacy, 'custom', 'none', {})
    assert seed_kb.seed_if_empty(db) == 0
    assert db.get_rule(rid)['enabled'] is False
    assert db.get_rule(user_rid)['enabled'] is True
    assert seed_kb.seed_if_empty(db) == 0
    assert all(r['source_url'].startswith('https://') for r in seed_kb.SEED_RULES)


def test_login_rate_limit_persists(client):
    for _ in range(10):
        assert client.post('/api/auth/login', json={'username':'admin','password':'incorrect-password'}).status_code == 401
    assert client.post('/api/auth/login', json={'username':'admin','password':'incorrect-password'}).status_code == 429


def test_missing_llm_returns_actionable_error(client, monkeypatch):
    monkeypatch.setattr(config, 'LLM_API_KEY', '')
    login(client); pid = create(client)
    client.post(f'/api/projects/{pid}/code', json={'files':[{'content':'x = 1'}]})
    assert client.post(f'/api/projects/{pid}/generate/form').status_code == 503


def test_ai_pipeline_persists_materials_and_streams_export(client, monkeypatch):
    from app import llm
    async def fake_json(messages, **kwargs):
        return {'modules':[{'name':'库存查询','description':'返回库存','functions':['stock']}],
                'development_purpose':'管理库存','main_functions_desc':'查询库存'}
    async def fake_text(messages, **kwargs):
        return '## 库存功能\n调用stock查询库存。'
    monkeypatch.setattr(llm, 'chat_json', fake_json)
    monkeypatch.setattr(llm, 'chat', fake_text)
    monkeypatch.setattr(llm, 'configured', lambda: False)
    login(client); pid = create(client)
    client.post(f'/api/projects/{pid}/code', json={'files':[{'content':'def stock():\n    return 1'}]})
    response = client.post(f'/api/projects/{pid}/generate/all?doc_kind=design')
    events = [json.loads(line[6:]) for line in response.text.splitlines() if line.startswith('data: ')]
    assert not any(e['status'] == 'error' for e in events), events
    assert events[-1]['step'] == 'pipeline' and events[-1]['status'] == 'done'
    assert events[-1]['data']['passed'] is False  # human verification is still required
    assert {d['doc_type'] for d in client.get(f'/api/projects/{pid}/docs').json()['docs']} == {'analysis','design','form','declaration','evidence'}


def test_screenshot_content_is_validated(client):
    login(client); pid = create(client)
    assert client.post(f'/api/projects/{pid}/shots', files={'file':('fake.png', b'<html>bad</html>')}).status_code == 400


def test_deleted_project_id_cannot_reveal_new_user_materials(client):
    c = client; login(c); pid = create(c)
    c.put(f'/api/projects/{pid}/submission', json={'checks':{k:True for k in submission.CHECKS}})
    export_dir = config.EXPORT_DIR / f'project_{pid}'
    export_dir.mkdir(parents=True); (export_dir / 'old.docx').write_bytes(b'old material')
    assert c.delete(f'/api/projects/{pid}').status_code == 200
    assert not export_dir.exists()
    c.post('/api/auth/users', json={'username':'member','password':'test-member-password'})
    login(c, 'member', 'test-member-password')
    new_pid = create(c)
    assert c.get(f'/api/projects/{new_pid}').status_code == 200
    assert c.get(f'/api/projects/{new_pid}/submission').json()['checks'] == {}
    login(c)
    assert c.get(f'/api/projects/{new_pid}').status_code == 404
    assert c.get('/api/projects').json()['projects'] == []


def test_generation_does_not_mark_old_input_as_current(client, monkeypatch):
    from app import llm
    login(client); pid = create(client)
    client.post(f'/api/projects/{pid}/code', json={'files':[{'content':'x = 1'}]})
    async def changed_while_generating(messages, **kwargs):
        db.update_project(pid, {'full_name':'新库存系统'})
        return {'modules':[{'name':'旧库存功能'}]}
    monkeypatch.setattr(llm, 'chat_json', changed_while_generating)
    response = client.post(f'/api/projects/{pid}/generate/analysis')
    assert response.status_code == 400
    assert '变化' in response.json()['detail']
    assert client.get(f'/api/projects/{pid}/docs/analysis').status_code == 404
