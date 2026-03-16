"""PDF 文件服务"""

import os
from pathlib import Path
from typing import List, Dict
from app.config import BASE_DIR


def get_pdf_files() -> List[Dict]:
    """获取 pdfs 目录下的所有 PDF 文件列表

    Returns:
        文件列表，包含文件名、大小等信息
    """
    pdfs_dir = BASE_DIR / "data" / "pdfs"

    if not pdfs_dir.exists():
        return []

    pdf_files = []
    for file_path in sorted(pdfs_dir.glob("*.pdf")):
        size = file_path.stat().st_size
        pdf_files.append({
            "filename": file_path.name,
            "size": size,
            "size_human": _format_size(size),
            "path": str(file_path.relative_to(BASE_DIR))
        })

    return pdf_files


def get_pdf_path(filename: str) -> Path | None:
    """获取 PDF 文件的完整路径

    Args:
        filename: PDF 文件名

    Returns:
        文件路径，如果文件不存在返回 None
    """
    # 安全检查：防止目录遍历攻击
    if ".." in filename or "/" in filename or "\\" in filename:
        return None

    pdf_path = BASE_DIR / "data" / "pdfs" / filename

    if not pdf_path.exists() or not pdf_path.is_file():
        return None

    return pdf_path


def _format_size(size: int) -> str:
    """将字节大小转换为人类可读格式"""
    for unit in ["B", "KB", "MB", "GB"]:
        if size < 1024:
            return f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} TB"
