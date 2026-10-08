"""核心引擎单元测试（纯函数，不依赖数据库与 LLM）。

覆盖：
- code_engine：清洗、50行分页、前30后30截取、末页结束符、结构分析；
- llm.parse_json：JSON 稳健解析；
- kb_service.run_regex_rules：forbid / match / min_length 三种规则模式；
- docx_engine：docx 导出产物（页眉、截图占位）；
- seed_kb：内置规则结构完整性。
"""
import zipfile

import pytest

from app import config
from app.llm import LLMError, parse_json
from app.services import code_engine, docx_engine, kb_service
from app.services.seed_kb import SEED_RULES


# ---------------- code_engine ----------------

def test_clean_code_removes_empty_lines_and_tabs():
    raw = "def a():\n\n\treturn 1\n   \n\ndef b():\n\treturn 2\n"
    cleaned, n = code_engine.clean_code(raw)
    lines = cleaned.split("\n")
    assert n == 4
    assert all(ln.strip() for ln in lines)
    assert "    return 1" in lines  # tab 转四空格


def test_build_pages_all_mode_50_lines_per_page():
    code = "\n".join(f"line_{i}" for i in range(120))
    pages = code_engine.build_pages([{"filename": "a.py", "content": code}])
    assert pages["mode"] == "all"
    assert pages["total_lines"] == 121  # 120 行代码 + 1 行文件标记
    assert pages["pages_submitted"] == 3
    assert all(len(p) <= config.CODE_LINES_PER_PAGE for p in pages["pages"])
    assert pages["pages"][0][0].startswith("/* ===== 文件：a.py")


def test_build_pages_head_tail_over_60_pages():
    # 4000 行 → 81 页（含文件标记），触发 前30+后30 截取
    code = "\n".join(f"x = {i}" for i in range(4000))
    pages = code_engine.build_pages([{"filename": "big.py", "content": code}])
    assert pages["mode"] == "head_tail"
    assert pages["total_pages_full"] > config.CODE_MAX_PAGES
    assert pages["pages_submitted"] == config.CODE_HEAD_PAGES + config.CODE_TAIL_PAGES
    # 末页必须取自代码尾部（保证末页即程序结束页）
    tail_join = "\n".join(pages["pages"][-1])
    assert "x = 3999" in tail_join or "x = 399" in tail_join


def test_last_page_ends_ok():
    ok_pages = [["{", "}"]]
    assert code_engine.last_page_ends_ok(ok_pages) == (True, "}")
    bad_pages = [["def f():", "    pass  # 未闭合 {"]]
    ok, _ = code_engine.last_page_ends_ok(bad_pages)
    assert not ok
    ok, msg = code_engine.last_page_ends_ok([])
    assert not ok and msg == "源代码为空"


def test_analyze_files_extracts_identifiers():
    code = "class OrderSync:\n    def fetch(self):\n        pass\n"
    result = code_engine.analyze_files([{"filename": "s.py", "content": code}])
    f = result["files"][0]
    assert f["lines"] == 3
    assert "OrderSync" in f["identifiers"]
    assert "fetch" in f["identifiers"]


# ---------------- llm.parse_json ----------------

def test_parse_json_plain():
    assert parse_json('{"a": 1}') == {"a": 1}


def test_parse_json_fenced():
    text = "好的，结果如下：\n```json\n{\"issues\": [1, 2]}\n```\n以上。"
    assert parse_json(text) == {"issues": [1, 2]}


def test_parse_json_with_surrounding_prose():
    text = '分析结果 {"summary": "格式问题", "n": 2} 请查收'
    assert parse_json(text)["summary"] == "格式问题"


def test_parse_json_invalid_raises():
    with pytest.raises(LLMError):
        parse_json("完全不是 JSON")


# ---------------- kb_service.run_regex_rules ----------------

def _rule(pattern, mode, target="source", value=0):
    import json
    cfg = json.dumps({"target": target, "mode": mode, "pattern": pattern, "value": value})
    return {"id": 1, "check_type": "regex", "category": "格式规范",
            "problem": "测试规则", "solution": "修复方法", "check_config": cfg}


def test_regex_rule_forbid_mode_hits():
    rules = [_rule(r"ChatGPT", "forbid")]
    issues = kb_service.run_regex_rules(rules, {"source": "x = 1  # by ChatGPT"}, project_id=None)
    assert len(issues) == 1
    assert issues[0]["code"].startswith("KB-")


def test_regex_rule_match_mode_hits_when_missing():
    rules = [_rule(r"^V\d+(\.\d+){0,2}$", "match", target="version")]
    issues = kb_service.run_regex_rules(rules, {"version": "1.0"}, project_id=None)
    assert len(issues) == 1
    issues = kb_service.run_regex_rules(rules, {"version": "V1.0"}, project_id=None)
    assert issues == []


def test_regex_rule_min_length_mode():
    rules = [_rule("", "min_length", target="main_functions", value=500)]
    issues = kb_service.run_regex_rules(rules, {"main_functions": "太短的描述"}, project_id=None)
    assert len(issues) == 1
    issues = kb_service.run_regex_rules(rules, {"main_functions": "长" * 600}, project_id=None)
    assert issues == []


def test_regex_rule_bad_pattern_skipped():
    rules = [_rule("([unclosed", "forbid")]
    assert kb_service.run_regex_rules(rules, {"source": "任意文本"}, project_id=None) == []


def test_regex_rule_unknown_target_skipped():
    rules = [_rule("x", "forbid", target="不存在的字段")]
    assert kb_service.run_regex_rules(rules, {"source": "文本"}, project_id=None) == []


# ---------------- docx_engine ----------------

def _project():
    return {"full_name": "测试同步系统", "version": "V1.0"}


def test_export_source_docx_header_and_pages(tmp_path):
    pages = [[f"line_{i}" for i in range(50)], ["}", ""]]
    path = tmp_path / "src.docx"
    docx_engine.export_source_docx(_project(), pages, path)
    with zipfile.ZipFile(path) as zf:
        header = zf.read("word/header1.xml").decode("utf-8")
        doc = zf.read("word/document.xml").decode("utf-8")
    assert "测试同步系统 V1.0" in header
    assert "PAGE" in header          # 自动页码域
    assert "line_0" in doc


def test_export_markdown_docx_shot_placeholder(tmp_path):
    md = "# 测试同步系统 操作说明书\n\n## 功能一\n\n【截图占位：主界面】\n\n正文段落。\n"
    path = tmp_path / "manual.docx"
    docx_engine.export_markdown_docx(_project(), md, path, "操作说明书")
    with zipfile.ZipFile(path) as zf:
        doc = zf.read("word/document.xml").decode("utf-8")
    assert "此处插入截图：主界面" in doc


def test_checklist_text_lists_all_materials():
    text = docx_engine.checklist_text(_project(), True, True, False, True, False)
    assert "软著申请材料清单" in text
    assert "[平台已生成]" in text
    assert "[需自备]" in text
    assert "按官网要求上传" in text


# ---------------- seed_kb ----------------

CATEGORIES = {"格式规范", "材料一致性", "AI声明与原创性", "功能描述不足", "材料缺失", "其他"}


def test_seed_rules_structure():
    assert len(SEED_RULES) >= 14
    for r in SEED_RULES:
        assert r["category"] in CATEGORIES, r
        assert r["problem"].strip()
        assert r["solution"].strip()
        if r.get("check_type") == "regex":
            assert r.get("check_pattern") or r.get("check_mode") == "min_length"
            assert r.get("check_target") in {
                "full_name", "version", "main_functions", "manual", "form", "source"}


def test_seed_rules_regex_patterns_compile():
    import re
    for r in SEED_RULES:
        if r.get("check_type") == "regex" and r.get("check_pattern"):
            re.compile(r["check_pattern"])  # 编译不抛错即通过


# ---------------- review_engine 内置正则 ----------------

def test_review_regexes():
    from app.services.review_engine import AI_TRACE_RE, FORBIDDEN_NAME_WORDS, NAME_SUFFIX_RE, VERSION_RE
    assert AI_TRACE_RE.search("# generated by ChatGPT")
    assert not AI_TRACE_RE.search("# 正常注释")
    assert VERSION_RE.match("V1.0") and not VERSION_RE.match("1.0")
    assert NAME_SUFFIX_RE.search("数据同步系统")
    assert FORBIDDEN_NAME_WORDS.search("中国国家管理系统")


# ---------------- 截图匹配与 docx 嵌入 ----------------

import base64

_PNG_1PX = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg==")


def test_match_shot_exact_then_contains():
    shots = [{"label": "订单列表页", "path": "/a.png"}, {"label": "登录主界面", "path": "/b.png"}]
    assert docx_engine.match_shot("订单列表页", shots)["path"] == "/a.png"
    assert docx_engine.match_shot("主界面", shots)["path"] == "/b.png"   # 包含匹配
    assert docx_engine.match_shot("不存在的界面", shots) is None
    assert docx_engine.match_shot("任意", []) is None


def test_export_markdown_docx_embeds_real_screenshot(tmp_path):
    img = tmp_path / "login.png"
    img.write_bytes(_PNG_1PX)
    md = "# 说明书\n\n## 登录\n\n【截图占位：登录页】\n\n【截图占位：没有图的界面】\n"
    path = tmp_path / "manual.docx"
    docx_engine.export_markdown_docx(
        _project(), md, path, "操作说明书",
        shots=[{"label": "登录页", "path": str(img)}])
    with zipfile.ZipFile(path) as zf:
        media = [n for n in zf.namelist() if n.startswith("word/media/")]
        doc = zf.read("word/document.xml").decode("utf-8")
    assert len(media) == 1                       # 有匹配的截图已嵌入
    assert "此处插入截图：没有图的界面" in doc     # 无匹配的保留占位框


# ---------------- 打印视图 ----------------

def test_print_view_md_to_html():
    from app.services import print_view
    md = ("# 标题\n\n## 小节\n\n- 要点一\n- 要点二\n\n| 字段 | 说明 |\n|---|---|\n| a | b |\n\n"
          "【截图占位：主界面】\n")
    html = print_view._md_to_html(md, [{"label": "主界面", "url": "/img/1"}])
    assert "<h1" in html and "<h2" in html and "<li>" in html and "<table>" in html
    assert '<img class="shot" src="/img/1"' in html
    html2 = print_view._md_to_html("【截图占位：未上传】", [])
    assert "此处插入截图：未上传" in html2


def test_print_view_render_source(tmp_path, monkeypatch):
    """源程序打印视图：按页分块、页眉含名称版本。"""
    from app.services import print_view
    project = {"id": 1, "full_name": "测试同步系统", "version": "V1.0"}
    pages = [["x = 1", "y = 2"]]
    html = print_view._wrap("源程序", print_view._page_header(project) + "<pre class='code'>x</pre>")
    assert "测试同步系统 V1.0" in html and "window.print" in html
    # build_pages 打印分页与 docx 引擎一致（首行为文件标记）
    built = code_engine.build_pages([{"filename": "a.py", "content": "\n".join(l for p in pages for l in p)}])
    assert built["pages"][0][0].startswith("/* ===== 文件：a.py")
    assert built["pages"][0][2] == "y = 2"
