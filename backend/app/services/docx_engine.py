"""docx 导出引擎（python-docx）。

鉴别材料排版规格（对齐审查要求）：
- 源程序：A4、每页精确 50 行（等线 9pt / 行距固定 13.5 磅）、不留空行、
  页眉 = "软件全称 版本号"（与申请表一致）+ 右上角页码；
- 文档鉴别材料：A4、正文宋体 12pt / 行距固定 23 磅（约每页 30 行）、
  页眉含文档类型、截图占位框可替换。
"""
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
from docx.shared import Cm, Pt, RGBColor

from .. import config

# 可用正文高度：A4 29.7cm - 上下 2.54cm = 24.62cm ≈ 697.9pt
# 源程序 50 行 × 13.5pt = 675pt ✓   文档 30 行 × 23pt = 690pt ✓


def _set_run_font(run, ascii_font: str = "Times New Roman", east_font: str = "宋体",
                  size: float = 12, bold: bool = False, color: Optional[str] = None):
    run.font.name = ascii_font
    run.font.size = Pt(size)
    run.font.bold = bold
    rpr = run._element.get_or_add_rPr()
    rfonts = rpr.find(qn("w:rFonts"))
    if rfonts is None:
        rfonts = OxmlElement("w:rFonts")
        rpr.append(rfonts)
    rfonts.set(qn("w:ascii"), ascii_font)
    rfonts.set(qn("w:hAnsi"), ascii_font)
    rfonts.set(qn("w:eastAsia"), east_font)
    if color:
        run.font.color.rgb = RGBColor.from_string(color)


def _setup_section(doc: Document, header_text: str):
    section = doc.sections[0]
    section.page_width = Cm(21.0)
    section.page_height = Cm(29.7)
    section.top_margin = Cm(2.54)
    section.bottom_margin = Cm(2.54)
    section.left_margin = Cm(3.17)
    section.right_margin = Cm(3.17)
    header = section.header
    hp = header.paragraphs[0] if header.paragraphs else header.add_paragraph()
    hp.text = ""
    hp.paragraph_format.tab_stops.add_tab_stop(Cm(14.66), WD_ALIGN_PARAGRAPH.RIGHT)
    run = hp.add_run(header_text)
    _set_run_font(run, size=9)
    run2 = hp.add_run("\t第 ")
    _set_run_font(run2, size=9)
    run3 = hp.add_run()
    _set_run_font(run3, size=9)
    fld_begin = OxmlElement("w:fldChar")
    fld_begin.set(qn("w:fldCharType"), "begin")
    instr = OxmlElement("w:instrText")
    instr.set(qn("xml:space"), "preserve")
    instr.text = " PAGE "
    fld_end = OxmlElement("w:fldChar")
    fld_end.set(qn("w:fldCharType"), "end")
    run3._element.append(fld_begin)
    run3._element.append(instr)
    run3._element.append(fld_end)
    run4 = hp.add_run(" 页")
    _set_run_font(run4, size=9)
    return section


def _body_paragraph(doc: Document, text: str, size: float, line_pt: float,
                    ascii_font: str = "Times New Roman", east_font: str = "宋体",
                    bold: bool = False, align=None, first_line_indent: bool = False,
                    space_after: float = 0):
    p = doc.add_paragraph()
    pf = p.paragraph_format
    pf.line_spacing = Pt(line_pt)
    pf.space_before = Pt(0)
    pf.space_after = Pt(space_after)
    if align is not None:
        p.alignment = align
    if first_line_indent:
        pf.first_line_indent = Pt(size * 2)
    run = p.add_run(text)
    _set_run_font(run, ascii_font=ascii_font, east_font=east_font, size=size, bold=bold)
    return p


# ---------------- 源程序鉴别材料 ----------------

def export_source_docx(project: Dict[str, Any], pages: List[List[str]], path: Path) -> Path:
    doc = Document()
    header_text = f"{project['full_name']} {project['version']}"
    _setup_section(doc, header_text)
    for idx, page_lines in enumerate(pages):
        padded = list(page_lines) + [""] * max(0, config.CODE_LINES_PER_PAGE - len(page_lines))
        for j, line in enumerate(padded[:config.CODE_LINES_PER_PAGE]):
            first_of_page = (j == 0)
            p = _body_paragraph(doc, line if line.strip() else " ", size=9, line_pt=13.5,
                                ascii_font="Consolas", east_font="宋体")
            if first_of_page and idx > 0:
                p.paragraph_format.page_break_before = True
    doc.save(str(path))
    return path


# ---------------- 文档鉴别材料（说明书/设计说明/过程记录） ----------------

SHOT_RE = re.compile(r"^【截图占位[:：](.+?)】$")


def _norm_label(s: str) -> str:
    return re.sub(r"\s+", "", str(s or "")).lower()


def match_shot(label: str, shots: List[Dict[str, str]]) -> Optional[Dict[str, str]]:
    """为【截图占位：label】匹配已上传截图：先精确，后包含；返回命中的条目
    （docx 场景含 path 键，打印视图场景含 url 键）。"""
    if not shots:
        return None
    target = _norm_label(label)
    for s in shots:
        if _norm_label(s.get("label")) == target:
            return s
    for s in shots:
        lbl = _norm_label(s.get("label"))
        if target and lbl and (target in lbl or lbl in target):
            return s
    return None


def _add_picture(doc: Document, path: str, label: str):
    """插入真实界面截图（居中，宽 13.5cm）+ 图注；插入失败则回退为占位框。"""
    try:
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = p.add_run()
        run.add_picture(path, width=Cm(13.5))
        _body_paragraph(doc, f"图：{label}", size=10.5, line_pt=16,
                        align=WD_ALIGN_PARAGRAPH.CENTER, space_after=6)
    except Exception:
        _add_shot_placeholder(doc, label)


def _add_shot_placeholder(doc: Document, label: str):
    p = _body_paragraph(doc, f"【此处插入截图：{label}】", size=12, line_pt=23,
                        align=WD_ALIGN_PARAGRAPH.CENTER, space_after=0)
    ppr = p._p.get_or_add_pPr()
    pbdr = OxmlElement("w:pBdr")
    for edge in ("top", "left", "bottom", "right"):
        el = OxmlElement("w:" + edge)
        el.set(qn("w:val"), "dashed")
        el.set(qn("w:sz"), "8")
        el.set(qn("w:space"), "6")
        el.set(qn("w:color"), "808080")
        pbdr.append(el)
    ppr.append(pbdr)
    for _ in range(8):
        _body_paragraph(doc, " ", size=12, line_pt=23)


def _strip_inline(text: str) -> str:
    text = re.sub(r"\*\*(.+?)\*\*", r"\1", text)
    text = text.replace("`", "")
    return text


def export_markdown_docx(project: Dict[str, Any], markdown: str, path: Path,
                         doc_label: str, shots: Optional[List[Dict[str, str]]] = None) -> Path:
    """把 Markdown 说明书/设计说明/过程记录转成符合行数要求的 docx。

    shots: [{"label": 界面名称, "path": 图片路径}]，遇【截图占位：label】时
    自动嵌入匹配的真实截图，无匹配则保留虚线占位框。
    """
    doc = Document()
    header_text = f"{project['full_name']} {project['version']}（{doc_label}）"
    _setup_section(doc, header_text)
    lines = markdown.replace("\r\n", "\n").split("\n")
    i = 0
    first_h1_done = False
    while i < len(lines):
        raw = lines[i].rstrip()
        stripped = raw.strip()
        if not stripped:
            i += 1
            continue
        if stripped.startswith("|") and stripped.endswith("|"):
            rows = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                row = [c.strip() for c in lines[i].strip().strip("|").split("|")]
                if not all(re.fullmatch(r":?-{2,}:?", c) for c in row):
                    rows.append(row)
                i += 1
            if rows:
                width = max(len(r) for r in rows)
                table = doc.add_table(rows=len(rows), cols=width)
                table.style = "Table Grid"
                for r, row in enumerate(rows):
                    for c in range(width):
                        cell = table.cell(r, c)
                        cell.text = ""
                        p = cell.paragraphs[0]
                        p.paragraph_format.line_spacing = Pt(16)
                        run = p.add_run(_strip_inline(row[c] if c < len(row) else ""))
                        _set_run_font(run, size=10.5, bold=(r == 0))
            continue
        shot = SHOT_RE.match(stripped)
        if shot:
            hit = match_shot(shot.group(1), shots or [])
            if hit and hit.get("path"):
                _add_picture(doc, hit["path"], shot.group(1))
            else:
                _add_shot_placeholder(doc, shot.group(1))
            i += 1
            continue
        if stripped.startswith("### "):
            _body_paragraph(doc, _strip_inline(stripped[4:]), size=12.5, line_pt=26,
                            east_font="黑体", bold=True, space_after=4)
        elif stripped.startswith("## "):
            p = _body_paragraph(doc, _strip_inline(stripped[3:]), size=14, line_pt=30,
                                east_font="黑体", bold=True, space_after=4)
            p.paragraph_format.space_before = Pt(8)
        elif stripped.startswith("# "):
            if first_h1_done:
                p = _body_paragraph(doc, _strip_inline(stripped[2:]), size=15, line_pt=32,
                                    east_font="黑体", bold=True,
                                    align=WD_ALIGN_PARAGRAPH.CENTER, space_after=6)
                p.paragraph_format.page_break_before = True
            else:
                p = _body_paragraph(doc, _strip_inline(stripped[2:]), size=16, line_pt=34,
                                    east_font="黑体", bold=True,
                                    align=WD_ALIGN_PARAGRAPH.CENTER, space_after=10)
                first_h1_done = True
        elif re.match(r"^(\d+\.|[-*+])\s+", stripped):
            content = re.sub(r"^(\d+\.|[-*+])\s+", lambda m: m.group(1) + " ", stripped)
            _body_paragraph(doc, _strip_inline(content), size=12, line_pt=23)
        else:
            _body_paragraph(doc, _strip_inline(stripped), size=12, line_pt=23,
                            first_line_indent=True)
        i += 1
    doc.save(str(path))
    return path


# ---------------- 申请表预填清单 ----------------

def export_form_docx(project: Dict[str, Any], form: Dict[str, Any],
                     declaration: Optional[Dict[str, Any]], path: Path) -> Path:
    doc = Document()
    _setup_section(doc, f"{project['full_name']} {project['version']}（申请表预填清单）")
    title = doc.add_paragraph()
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    title.paragraph_format.space_after = Pt(6)
    run = title.add_run("计算机软件著作权登记申请表 · 预填内容")
    _set_run_font(run, east_font="黑体", size=16, bold=True)
    note = _body_paragraph(
        doc, "说明：本清单用于对照官网在线申请表逐项填写。正式提交必须在中国版权保护中心"
             "登记系统在线填写并打印（自动生成流水号），本清单内容可直接复制使用。",
        size=10.5, line_pt=18, color="C00000")
    note.paragraph_format.space_after = Pt(10)

    fields = [
        ("软件全称", project.get("full_name", "")),
        ("软件简称", project.get("short_name") or "无"),
        ("版本号", project.get("version", "")),
        ("开发完成日期", project.get("completion_date", "")),
        ("首次发表日期", project.get("publish_date") or "未发表"),
        ("开发方式", project.get("dev_type", "独立开发")),
        ("著作权人（申请主体）", project.get("owner_name", "")),
        ("开发的硬件环境", form.get("hardware_env", "")),
        ("运行的硬件环境", form.get("hardware_env", "")),
        ("开发该软件的操作系统", form.get("software_env", "")),
        ("软件开发环境/开发工具", form.get("software_env", "")),
        ("该软件的运行的硬件环境", form.get("hardware_env", "")),
        ("软件运行的软件环境", form.get("software_env", "")),
        ("编程语言", form.get("programming_language", "")),
        ("源程序量", form.get("source_lines_note", "")),
        ("主要功能和技术特点", form.get("main_functions_desc", "")),
        ("开发的用途和技术特点", form.get("development_purpose", "")),
        ("面向的使用对象/应用领域", form.get("target_users", "")),
    ]
    table = doc.add_table(rows=len(fields), cols=2)
    table.style = "Table Grid"
    for r, (label, value) in enumerate(fields):
        c0 = table.cell(r, 0)
        c0.text = ""
        p0 = c0.paragraphs[0]
        p0.paragraph_format.line_spacing = Pt(16)
        run0 = p0.add_run(label)
        _set_run_font(run0, size=10.5, bold=True)
        c1 = table.cell(r, 1)
        c1.text = ""
        p1 = c1.paragraphs[0]
        p1.paragraph_format.line_spacing = Pt(16)
        run1 = p1.add_run(str(value))
        _set_run_font(run1, size=10.5)
    table.columns[0].width = Cm(4.5)
    table.columns[1].width = Cm(10.1)

    doc.add_paragraph()
    h = doc.add_paragraph()
    run_h = h.add_run("附：AI 使用情况声明及人类实质性创作说明")
    _set_run_font(run_h, east_font="黑体", size=14, bold=True)
    h.paragraph_format.space_before = Pt(10)
    h.paragraph_format.space_after = Pt(6)
    if declaration:
        for key, label in (("ai_usage_summary", "一、AI 使用情况"),
                           ("human_contribution", "二、人类实质性创作说明"),
                           ("originality_statement", "三、独创性声明")):
            sub = doc.add_paragraph()
            run_s = sub.add_run(label)
            _set_run_font(run_s, east_font="黑体", size=12, bold=True)
            sub.paragraph_format.space_before = Pt(6)
            for chunk in str(declaration.get(key, "")).split("\n"):
                if chunk.strip():
                    _body_paragraph(doc, chunk.strip(), size=12, line_pt=23,
                                    first_line_indent=True)
        ev = doc.add_paragraph()
        run_ev = ev.add_run("四、支撑证据清单")
        _set_run_font(run_ev, east_font="黑体", size=12, bold=True)
        for item in declaration.get("evidence_list", []) or []:
            _body_paragraph(doc, "- " + str(item), size=12, line_pt=23)
    else:
        _body_paragraph(doc, "（尚未生成，请在平台'材料生成'页生成 AI 声明）", size=12, line_pt=23)
    doc.save(str(path))
    return path


# ---------------- 材料清单 ----------------

def checklist_text(project: Dict[str, Any], has_code_doc: bool, has_manual: bool,
                   has_form: bool, has_declaration: bool, has_evidence: bool) -> str:
    items = [
        ("软件著作权登记申请表", has_form, "官网在线填写并带流水号打印，单面，签字/盖章"),
        ("源程序鉴别材料（前30后30页/每页50行）", has_code_doc, f"源程序-{project['full_name']}-{project['version']}.docx"),
        ("文档鉴别材料（操作说明书或设计说明书）", has_manual, "替换全部【截图占位】后打印，单面"),
        ("AI 使用情况声明及人类实质性创作说明（2026 新规）", has_declaration, "可附在申请表后一并提交"),
        ("软件开发过程记录（证据链材料，备查）", has_evidence, "配合 Git 记录留存备查"),
        ("身份证明：营业执照复印件加盖公章 / 身份证正反面复印件", False, "线下准备"),
        ("合作/委托开发协议（如适用，签字盖章）", False, "开发方式非独立开发时必须提供"),
    ]
    lines = [
        f"《{project['full_name']} {project['version']}》软著申请材料清单",
        "=" * 60,
        "",
    ]
    for name, done, note in items:
        mark = "[平台已生成]" if done else "[需自备]  "
        lines.append(f"{mark} {name}")
        lines.append(f"           要求：{note}")
        lines.append("")
    lines += [
        "提交前检查：",
        "1. 申请表、源程序页眉、说明书页眉的软件全称+版本号完全一致；",
        "2. 源程序每页不少于50行、无空行，末页为程序结束页；",
        "3. 说明书截图清晰无水印，已替换全部占位框；",
        "4. 全部材料单面打印，右上角页码连续；",
        "5. AI 声明口径与实际开发过程一致，Git 记录等证据留存备查；",
        "6. 同一主体单日提交不超过 3 件，避免触发非正常申请预警。",
    ]
    return "\n".join(lines)
