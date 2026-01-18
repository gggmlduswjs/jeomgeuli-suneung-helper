"""
테스트 헬퍼 함수
"""
from pathlib import Path
from typing import Optional, Dict, Any, List
from app.core.config import settings


def find_pdf_file(pattern: Optional[str] = None) -> Optional[Path]:
    """
    PDF 파일 찾기 헬퍼
    
    Args:
        pattern: 파일명 패턴 (예: "*문학*.pdf")
    
    Returns:
        찾은 PDF 파일 경로 또는 None
    """
    pdf_dir = settings.PDFS_DIR
    
    if pattern:
        pdf_files = list(pdf_dir.glob(pattern))
    else:
        pdf_files = list(pdf_dir.glob("*.pdf"))
    
    return pdf_files[0] if pdf_files else None


def format_block_preview(block: Dict[str, Any], max_length: int = 50) -> str:
    """
    블록 미리보기 포맷팅
    
    Args:
        block: 블록 딕셔너리
        max_length: 최대 길이
    
    Returns:
        포맷팅된 미리보기 문자열
    """
    content = block.get("content", "")
    
    if isinstance(content, str):
        preview = content[:max_length].replace("\n", " ")
    elif isinstance(content, list):
        preview = str(content)[:max_length].replace("\n", " ")
    else:
        preview = str(content)[:max_length]
    
    return preview if preview else "(내용 없음)"


def count_block_types(blocks: List[Dict[str, Any]]) -> Dict[str, int]:
    """
    블록 타입별 개수 세기
    
    Args:
        blocks: 블록 리스트
    
    Returns:
        타입별 개수 딕셔너리
    """
    block_types = {}
    for block in blocks:
        block_type = block.get("type", "unknown")
        block_types[block_type] = block_types.get(block_type, 0) + 1
    return block_types


def format_file_size(size_bytes: int) -> str:
    """
    파일 크기를 읽기 쉬운 형식으로 변환
    
    Args:
        size_bytes: 바이트 단위 크기
    
    Returns:
        포맷팅된 크기 문자열 (예: "1.5 MB")
    """
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} TB"
