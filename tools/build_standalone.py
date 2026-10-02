#!/usr/bin/env python3
"""把前端打包为单文件 standalone/index.html。

用途：不启动后端时也能双击打开预览界面骨架（app.js 检测 file:// 协议
会展示预览模式横幅）；发后端时仍是 frontend/ 目录为准。
重新构建：python3 tools/build_standalone.py
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FRONT = ROOT / "frontend"
OUT = ROOT / "standalone" / "index.html"

html = (FRONT / "index.html").read_text(encoding="utf-8")
css = (FRONT / "style.css").read_text(encoding="utf-8")
js = (FRONT / "app.js").read_text(encoding="utf-8")

for token in ("</script>", "<!--"):
    if token in js or token in css:
        raise SystemExit(f"前端资源包含内联不安全的序列：{token}")

html = html.replace(
    '<link rel="stylesheet" href="/static/style.css">',
    "<style>\n" + css + "\n</style>")
html = html.replace(
    '<script src="/static/app.js"></script>',
    "<script>\n" + js + "\n</script>")

OUT.parent.mkdir(exist_ok=True)
OUT.write_text(html, encoding="utf-8")
print(f"已生成 {OUT}（{OUT.stat().st_size // 1024} KB）")
