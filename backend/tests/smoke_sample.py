# -*- coding: utf-8 -*-
"""CI 冒烟用例样例源码:供 build-windows.yml 打包后的 exe 做端到端验证。"""
import json
import os
from pathlib import Path


def count_lines(content: str) -> dict:
    """统计代码/空行/注释行数。"""
    total = code = blank = comment = 0
    for raw in content.splitlines():
        total += 1
        line = raw.strip()
        if not line:
            blank += 1
        elif line.startswith("#") or line.startswith("//"):
            comment += 1
        else:
            code += 1
    return {"total": total, "code": code, "blank": blank, "comment": comment}


def scan_dir(root: str) -> dict:
    """递归统计目录下所有源码文件。"""
    result = {"files": [], "summary": {"total": 0, "code": 0}}
    for dirpath, _, filenames in os.walk(root):
        if ".git" in dirpath or "node_modules" in dirpath:
            continue
        for name in filenames:
            path = Path(dirpath) / name
            if path.suffix.lower() not in (".py", ".js", ".ts", ".java", ".go"):
                continue
            text = path.read_text(encoding="utf-8", errors="replace")
            stat = count_lines(text)
            stat["file"] = str(path)
            result["files"].append(stat)
            result["summary"]["total"] += stat["total"]
            result["summary"]["code"] += stat["code"]
    return result


def format_report(data: dict) -> str:
    """输出 JSON 报告。"""
    return json.dumps(data, ensure_ascii=False, indent=2)


def main() -> None:
    """入口:扫描当前目录并打印统计报告。"""
    report = scan_dir(".")
    print(format_report(report))


if __name__ == "__main__":
    main()
