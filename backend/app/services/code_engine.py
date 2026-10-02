"""源代码文档引擎：清洗、分页（每页50行、前30后30共60页）、统计与结构分析。"""
import re
from typing import Any, Dict, List, Tuple

from .. import config

# 常见源码扩展名（zip 上传时过滤）
CODE_EXTENSIONS = {
    ".py", ".js", ".ts", ".jsx", ".tsx", ".vue", ".java", ".kt", ".go", ".rs",
    ".c", ".h", ".cpp", ".hpp", ".cs", ".php", ".rb", ".swift", ".m", ".mm",
    ".sql", ".sh", ".bat", ".ps1", ".html", ".css", ".scss", ".less", ".dart",
    ".scala", ".pl", ".lua", ".groovy", ".json", ".yaml", ".yml", ".xml",
}

SKIP_DIRS = ("node_modules", ".git", "dist", "build", "__pycache__", ".venv",
             "venv", "vendor", ".idea", ".vscode", "target", "bin", "obj")


def clean_code(content: str) -> Tuple[str, int]:
    """清洗单个文件代码：统一换行、去行尾空白、删除空行（审查要求源码不留空行）。"""
    text = content.replace("\r\n", "\n").replace("\r", "\n").replace("\t", "    ")
    lines = [ln.rstrip() for ln in text.split("\n")]
    lines = [ln for ln in lines if ln.strip()]
    cleaned = "\n".join(lines)
    return cleaned, len(lines)


def build_pages(files: List[Dict[str, Any]]) -> Dict[str, Any]:
    """把项目所有源码文件按顺序合并分页。

    规则（鉴别材料审查要求）：
    - 每页 50 行；
    - 总页数 <= 60 页时全部提交；
    - 超过 60 页时取前 30 页 + 后 30 页，最后一页必须是程序结束页（取尾部保证）。
    """
    all_lines: List[str] = []
    file_marks: List[Dict[str, Any]] = []
    cursor = 0
    for f in files:
        cleaned, n = clean_code(f.get("content", ""))
        if n == 0:
            continue
        all_lines.append(f"/* ===== 文件：{f.get('filename', 'code.txt')} ===== */")
        cursor += 1
        all_lines.extend(cleaned.split("\n"))
        file_marks.append({"filename": f.get("filename"), "lines": n})
        cursor += n
    total_lines = len(all_lines)
    total_pages_full = (total_lines + config.CODE_LINES_PER_PAGE - 1) // config.CODE_LINES_PER_PAGE
    if total_pages_full <= config.CODE_MAX_PAGES:
        pages = [all_lines[i:i + config.CODE_LINES_PER_PAGE]
                 for i in range(0, total_lines, config.CODE_LINES_PER_PAGE)]
        mode = "all"
    else:
        head_count = config.CODE_HEAD_PAGES * config.CODE_LINES_PER_PAGE
        tail_count = config.CODE_TAIL_PAGES * config.CODE_LINES_PER_PAGE
        head = all_lines[:head_count]
        tail = all_lines[-tail_count:]
        pages = [head[i:i + config.CODE_LINES_PER_PAGE] for i in range(0, head_count, config.CODE_LINES_PER_PAGE)]
        pages += [tail[i:i + config.CODE_LINES_PER_PAGE] for i in range(0, tail_count, config.CODE_LINES_PER_PAGE)]
        mode = "head_tail"
    # 保证每页都凑满（不足的页是末页属正常）
    return {
        "pages": pages,
        "total_lines": total_lines,
        "total_pages_full": total_pages_full,
        "pages_submitted": len(pages),
        "mode": mode,
        "files": file_marks,
    }


END_CHARS = ("}", ")", "]", ";", "end", "endif", "fi", "done", ">>", "*/", "-->")


def last_page_ends_ok(pages: List[List[str]]) -> Tuple[bool, str]:
    """检查最后一页最后一行是否是程序结束符（审查高频补正项）。"""
    if not pages or not pages[-1]:
        return False, "源代码为空"
    last = pages[-1][-1].strip()
    if not last:
        return False, "末页最后一行为空"
    for ch in END_CHARS:
        if last.endswith(ch):
            return True, last[-20:]
    return False, last[-20:]


IDENT_PATTERNS = [
    re.compile(r"^\s*def\s+([A-Za-z_]\w*)", re.M),
    re.compile(r"^\s*class\s+([A-Za-z_]\w*)", re.M),
    re.compile(r"function\s+([A-Za-z_$][\w$]*)"),
    re.compile(r"(?:const|let|var)\s+([A-Za-z_$][\w$]*)\s*=\s*(?:async\s*)?(?:\([^)]*\)|\w+)\s*=>"),
    re.compile(r"(?:public|private|protected)\s+[\w<>\[\]]+\s+([A-Za-z_]\w*)\s*\("),
    re.compile(r"func\s+(?:\([^)]*\)\s*)?([A-Za-z_]\w*)\s*\("),
    re.compile(r"fn\s+([A-Za-z_]\w*)"),
]

_COMMENT_NOISE = re.compile(
    r"^(?://+\s*(?:TODO|FIXME|generated|auto[- ]?generated|created by AI).*)$",
    re.I,
)


def analyze_files(files: List[Dict[str, Any]]) -> Dict[str, Any]:
    """统计各文件并抽取函数/类名等结构信息（供 LLM 分析与说明书生成用）。"""
    result: List[Dict[str, Any]] = []
    total = 0
    for f in files:
        cleaned, n = clean_code(f.get("content", ""))
        idents: List[str] = []
        for pat in IDENT_PATTERNS:
            idents.extend(pat.findall(cleaned)[:200])
        noise = sum(1 for ln in cleaned.split("\n") if _COMMENT_NOISE.match(ln.strip() or ""))
        result.append({
            "filename": f.get("filename"),
            "lines": n,
            "identifiers": idents[:60],
            "suspicious_comments": noise,
        })
        total += n
    return {"total_lines": total, "files": result}


def snippet(content: str, max_lines: int, head_ratio: float = 0.5) -> str:
    lines = [ln for ln in content.split("\n") if ln.strip()]
    if len(lines) <= max_lines:
        return "\n".join(lines)
    head = int(max_lines * head_ratio)
    tail = max_lines - head
    return "\n".join(lines[:head]) + "\n... (省略) ...\n" + "\n".join(lines[-tail:])
