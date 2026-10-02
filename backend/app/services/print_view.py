"""打印视图：把材料渲染为 A4 排版 HTML，浏览器"打印 → 另存为 PDF"即为 PDF 版材料。

零依赖替代 LibreOffice/Word 转换：排版规则与 docx 引擎一致
（源程序每页 50 行 + 页眉名称版本 + 右上角页码；文档行距近似每页 30 行）。
"""
import html as _html
import re
from typing import Any, Dict, List, Optional

from .. import config
from .. import database as db
from . import code_engine, docx_engine


def _esc(s: Any) -> str:
    return _html.escape(str(s if s is not None else ""))


def _inline(s: str) -> str:
    return re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", _esc(s))


_CSS = """
@page { size: A4; margin: 2.2cm 2.4cm; }
* { box-sizing: border-box; }
html { background: #ffffff; color-scheme: light; }
body { font-family: "Songti SC", SimSun, serif; color: #111111; background: #ffffff;
  margin: 0; font-size: 12pt; line-height: 1.9; }
.toolbar { position: fixed; top: 0; left: 0; right: 0; background: #1a2332; color: #fff;
  padding: 10px 18px; font-family: -apple-system, "PingFang SC", sans-serif; font-size: 13px;
  display: flex; gap: 14px; align-items: center; z-index: 9; }
.toolbar button { background: #2969ff; color: #fff; border: none; border-radius: 7px;
  padding: 7px 16px; font-size: 13px; cursor: pointer; font-family: inherit; }
.toolbar .tip { color: #9fb0cc; }
.main { margin-top: 56px; }
.doc-header { display: flex; justify-content: space-between; font-size: 9pt; color: #333;
  border-bottom: 1px solid #999; padding-bottom: 4px; margin-bottom: 14px;
  font-family: -apple-system, "PingFang SC", sans-serif; }
.page { page-break-after: always; }
.page:last-child { page-break-after: auto; }
pre.code { font-family: "SF Mono", Menlo, Consolas, monospace; font-size: 9pt; line-height: 1.55;
  white-space: pre-wrap; word-break: break-all; margin: 0; }
h1.doc-title { text-align: center; font-size: 16pt; margin: 6px 0 18px; }
h2 { font-size: 13.5pt; border-bottom: 1px solid #ccc; padding-bottom: 4px; margin: 18px 0 10px; }
h3 { font-size: 12.5pt; margin: 14px 0 6px; }
p { margin: 6px 0; text-indent: 2em; }
p.noindent { text-indent: 0; }
ul, ol { margin: 6px 0; padding-left: 2.2em; }
li { margin: 3px 0; }
table { border-collapse: collapse; width: 100%; margin: 10px 0; font-size: 10.5pt; }
th, td { border: 1px solid #666; padding: 5px 8px; text-align: left; vertical-align: top; }
th { background: #f2f2f2; }
.shot-ph { border: 1.5px dashed #888; color: #555; text-align: center; padding: 42px 10px;
  margin: 12px 0; font-family: -apple-system, "PingFang SC", sans-serif; font-size: 11pt; }
img.shot { display: block; max-width: 100%; width: 14cm; margin: 10px auto 2px; }
.fig-cap { text-align: center; font-size: 9.5pt; color: #444; margin: 0 0 12px; }
.note { color: #c00000; font-size: 10pt; text-indent: 0; }
@media print { .toolbar { display: none; } .main { margin-top: 0; } }
"""


def _page_header(project: Dict[str, Any], label: str = "") -> str:
    right = f"（{label}）" if label else ""
    return (f'<div class="doc-header"><span>{_esc(project["full_name"])} '
            f'{_esc(project["version"])}{right}</span><span></span></div>')


def _md_to_html(md: str, shots: List[Dict[str, str]]) -> str:
    """极简 Markdown → HTML（标题/列表/表格/粗体/截图占位），与前端渲染口径一致。"""
    out: List[str] = []
    in_list = False
    in_table = False
    header_re = re.compile(r"^【截图占位[:：](.+?)】$")

    def close() -> None:
        nonlocal in_list, in_table
        if in_list:
            out.append("</ul>")
            in_list = False
        if in_table:
            out.append("</tbody></table>")
            in_table = False

    for raw in (md or "").replace("\r\n", "\n").split("\n"):
        line = raw.strip()
        if not line:
            close()
            continue
        if line.startswith("|"):
            cells = [c.strip() for c in line.strip("|").split("|")]
            if all(re.fullmatch(r":?-{2,}:?", c) for c in cells):
                continue
            if not in_table:
                close()
                out.append("<table><tbody>")
                in_table = True
            out.append("<tr>" + "".join(f"<td>{_inline(c)}</td>" for c in cells) + "</tr>")
            continue
        close()
        shot = header_re.match(line)
        if shot:
            label = shot.group(1)
            hit = docx_engine.match_shot(label, shots)  # type: ignore[arg-type]
            url = (hit or {}).get("url")
            if url:
                out.append(f'<img class="shot" src="{_esc(url)}" alt="{_esc(label)}">'
                           f'<div class="fig-cap">图：{_esc(label)}</div>')
            else:
                out.append(f'<div class="shot-ph">【此处插入截图：{_esc(label)}】</div>')
            continue
        if line.startswith("### "):
            out.append(f"<h3>{_inline(line[4:])}</h3>")
        elif line.startswith("## "):
            out.append(f"<h2>{_inline(line[3:])}</h2>")
        elif line.startswith("# "):
            out.append(f'<h1 class="doc-title">{_inline(line[2:])}</h1>')
        elif re.match(r"^[-*+]\s+", line):
            if not in_list:
                out.append("<ul>")
                in_list = True
            item = re.sub(r"^[-*+]\s+", "", line)
            out.append(f"<li>{_inline(item)}</li>")
        elif re.match(r"^\d+\.\s+", line):
            if not in_list:
                out.append("<ul>")
                in_list = True
            out.append(f"<li>{_inline(line)}</li>")
        else:
            out.append(f"<p>{_inline(line)}</p>")
    close()
    return "\n".join(out)


def _shot_urls(project_id: int) -> List[Dict[str, str]]:
    return [{"label": s["label"],
             "url": f"/api/projects/{project_id}/shots/{s['id']}/image"}
            for s in db.list_shots(project_id)]


def _wrap(title: str, body: str) -> str:
    return f"""<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="UTF-8"><title>{_esc(title)}</title>
<style>{_CSS}</style></head><body>
<div class="toolbar"><b>{_esc(title)}</b>
<button onclick="window.print()">🖨 打印 / 另存为 PDF</button>
<span class="tip">打印设置：A4 · 单面 · 边距默认；"更多设置"中可去掉页眉页脚</span></div>
<div class="main">{body}</div>
</body></html>"""


def render(project_id: int, doc_type: str) -> str:
    project = db.get_project(project_id)
    if not project:
        raise ValueError("项目不存在")
    header = f"{project['full_name']} {project['version']}"

    if doc_type == "source":
        files = db.get_source_contents(project_id)
        if not files:
            raise ValueError("请先导入源代码")
        pages = code_engine.build_pages(files)["pages"]
        parts = []
        for i, page in enumerate(pages, 1):
            lines = "\n".join(_esc(ln) if ln.strip() else " " for ln in page)
            parts.append(
                f'<div class="page">{_page_header(project)}'
                f'<pre class="code">{lines}</pre></div>')
        return _wrap(f"源程序鉴别材料 - {header}", "\n".join(parts))

    if doc_type in ("manual", "design", "evidence"):
        doc = db.get_doc(project_id, doc_type)
        if not doc:
            raise ValueError("该材料尚未生成")
        label = {"manual": "操作说明书", "design": "设计说明书", "evidence": "开发过程记录"}[doc_type]
        body = _md_to_html(doc["content"], _shot_urls(project_id))
        return _wrap(f"{label} - {header}",
                     f'{_page_header(project, label)}<div class="doc">{body}</div>')

    if doc_type == "form":
        form = db.get_doc(project_id, "form")
        if not form:
            raise ValueError("请先生成申请表预填内容")
        data = (form.get("meta") or {}).get("data") or {}
        fields = [
            ("软件全称", project.get("full_name", "")),
            ("软件简称", project.get("short_name") or "无"),
            ("版本号", project.get("version", "")),
            ("开发完成日期", project.get("completion_date", "")),
            ("首次发表日期", project.get("publish_date") or "未发表"),
            ("开发方式", project.get("dev_type", "独立开发")),
            ("著作权人（申请主体）", project.get("owner_name", "")),
            ("开发的硬件环境", data.get("hardware_env", "")),
            ("开发该软件的操作系统", data.get("software_env", "")),
            ("软件开发环境/开发工具", data.get("software_env", "")),
            ("软件运行的软件环境", data.get("software_env", "")),
            ("编程语言", data.get("programming_language", "")),
            ("源程序量", data.get("source_lines_note", "")),
            ("主要功能和技术特点", data.get("main_functions_desc", "")),
            ("开发的用途和技术特点", data.get("development_purpose", "")),
            ("面向的使用对象/应用领域", data.get("target_users", "")),
        ]
        rows = "".join(f"<tr><th style='width:24%'>{_esc(k)}</th><td>{_esc(v)}</td></tr>"
                       for k, v in fields)
        decl = db.get_doc(project_id, "declaration")
        decl_html = ""
        if decl:
            d = (decl.get("meta") or {}).get("data") or {}
            sections = "".join(
                f"<h2>{_esc(lbl)}</h2>" +
                "".join(f"<p>{_inline(ln)}</p>" for ln in str(d.get(key, "")).split("\n") if ln.strip())
                for key, lbl in (("ai_usage_summary", "一、AI 使用情况"),
                                 ("human_contribution", "二、人类实质性创作说明"),
                                 ("originality_statement", "三、独创性声明")))
            ev = "".join(f"<li>{_esc(x)}</li>" for x in (d.get("evidence_list") or []))
            decl_html = f"<h2>四、支撑证据清单</h2><ul>{ev}</ul>" + sections
        body = (f"<h1 class='doc-title'>计算机软件著作权登记申请表 · 预填内容</h1>"
                f"<p class='note'>说明：正式提交必须在中国版权保护中心登记系统在线填写并打印（自动生成流水号），"
                f"本页内容可直接对照复制。</p><table><tbody>{rows}</tbody></table>{decl_html}")
        return _wrap(f"申请表预填 - {header}", _page_header(project, "申请表预填") + body)

    if doc_type == "declaration":
        decl = db.get_doc(project_id, "declaration")
        if not decl:
            raise ValueError("请先生成 AI 声明")
        d = (decl.get("meta") or {}).get("data") or {}
        sections = "".join(
            f"<h2>{_esc(lbl)}</h2>" +
            "".join(f"<p>{_inline(ln)}</p>" for ln in str(d.get(key, "")).split("\n") if ln.strip())
            for key, lbl in (("ai_usage_summary", "一、AI 使用情况"),
                             ("human_contribution", "二、人类实质性创作说明"),
                             ("originality_statement", "三、独创性声明")))
        ev = "".join(f"<li>{_esc(x)}</li>" for x in (d.get("evidence_list") or []))
        body = (f"<h1 class='doc-title'>AI 使用情况声明及人类实质性创作说明</h1>"
                f"<p class='noindent'>申请软件：{_esc(header)}</p>{sections}"
                f"<h2>四、支撑证据清单</h2><ul>{ev}</ul>")
        return _wrap(f"AI 声明 - {header}", _page_header(project, "AI 声明") + body)

    raise ValueError("不支持的打印类型")
