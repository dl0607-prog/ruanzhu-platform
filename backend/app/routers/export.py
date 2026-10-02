"""导出路由：各材料 docx 下载、打包下载与打印视图。"""
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse, HTMLResponse

from ..services import exporter, print_view

router = APIRouter(prefix="/api/projects", tags=["export"])

_MEDIA = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"


@router.get("/{pid}/export/source")
def export_source(pid: int):
    try:
        r = exporter.export_source(pid)
    except ValueError as e:
        raise HTTPException(400, str(e))
    path = exporter.export_file_path(pid, r["path"])
    return FileResponse(str(path), filename=r["path"], media_type=_MEDIA)


@router.get("/{pid}/export/manual")
def export_manual(pid: int):
    try:
        r = exporter.export_manual(pid)
    except ValueError as e:
        raise HTTPException(400, str(e))
    path = exporter.export_file_path(pid, r["path"])
    return FileResponse(str(path), filename=r["path"], media_type=_MEDIA)


@router.get("/{pid}/export/form")
def export_form(pid: int):
    try:
        r = exporter.export_form(pid)
    except ValueError as e:
        raise HTTPException(400, str(e))
    path = exporter.export_file_path(pid, r["path"])
    return FileResponse(str(path), filename=r["path"], media_type=_MEDIA)


@router.get("/{pid}/export/evidence")
def export_evidence(pid: int):
    try:
        r = exporter.export_evidence(pid)
    except ValueError as e:
        raise HTTPException(400, str(e))
    path = exporter.export_file_path(pid, r["path"])
    return FileResponse(str(path), filename=r["path"], media_type=_MEDIA)


@router.get("/{pid}/export/bundle")
def export_bundle(pid: int):
    try:
        r = exporter.export_all(pid)
    except ValueError as e:
        raise HTTPException(400, str(e))
    path = exporter.export_file_path(pid, r["zip"])
    return FileResponse(str(path), filename=r["zip"],
                        media_type="application/zip")


@router.get("/{pid}/print/{doc_type}")
def print_doc(pid: int, doc_type: str):
    """A4 排版打印视图：浏览器打开后"打印 → 另存为 PDF"即为 PDF 版材料。"""
    try:
        html = print_view.render(pid, doc_type)
    except ValueError as e:
        raise HTTPException(400, str(e))
    return HTMLResponse(html)


@router.get("/{pid}/files")
def list_files(pid: int):
    return {"files": exporter.list_export_files(pid)}


@router.get("/{pid}/files/{filename}")
def get_file(pid: int, filename: str):
    try:
        path = exporter.export_file_path(pid, filename)
    except ValueError as e:
        raise HTTPException(404, str(e))
    return FileResponse(str(path), filename=filename)
