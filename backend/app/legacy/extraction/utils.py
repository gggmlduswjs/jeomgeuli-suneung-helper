"""
PDF 추출 유틸리티 함수
"""
import logging
from pathlib import Path
from .exceptions import PDFNotFoundError, UnsupportedPDFFormatError

logger = logging.getLogger(__name__)


def validate_pdf_path(pdf_path: Path) -> None:
    """
    PDF 파일 경로 검증
    
    Args:
        pdf_path: PDF 파일 경로
    
    Raises:
        PDFNotFoundError: 파일이 존재하지 않을 때
        UnsupportedPDFFormatError: PDF 파일이 아닐 때
    """
    if not pdf_path.exists():
        raise PDFNotFoundError("PDF 파일을 찾을 수 없습니다", pdf_path=pdf_path)
    
    if not pdf_path.suffix.lower() == '.pdf':
        raise UnsupportedPDFFormatError(
            f"PDF 파일이 아닙니다: {pdf_path.suffix}",
            pdf_path=pdf_path
        )


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
