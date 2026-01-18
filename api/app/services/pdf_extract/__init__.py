"""
PDF 추출 모듈
PDF에서 원본 블록을 좌표 기반으로 추출 (구조 해석 없음)
"""
from .base_extractor import BaseExtractor
from .pdfplumber_extractor import PDFPlumberExtractor
from .image_extractor import ImageExtractor
from .literature_extractor import LiteraturePDFExtractor
from .exceptions import (
    PDFExtractionError,
    PDFNotFoundError,
    PDFCorruptedError,
    UnsupportedPDFFormatError,
    PDFExtractionTimeoutError
)

# 상위 디렉토리의 pdf_extract.py 모듈에서 함수들 import
import importlib.util
from pathlib import Path

# pdf_extract.py 모듈 직접 import
services_dir = Path(__file__).parent.parent
pdf_extract_module_path = services_dir / "pdf_extract.py"

if pdf_extract_module_path.exists():
    spec = importlib.util.spec_from_file_location("pdf_extract_module", pdf_extract_module_path)
    pdf_extract_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(pdf_extract_module)
    
    # 함수들을 현재 네임스페이스로 가져오기
    extract_text_from_pdf = pdf_extract_module.extract_text_from_pdf
    get_extracted_text = pdf_extract_module.get_extracted_text
else:
    # pdf_extract.py가 없는 경우를 위한 fallback
    extract_text_from_pdf = None
    get_extracted_text = None

__all__ = [
    "BaseExtractor",
    "PDFPlumberExtractor", 
    "ImageExtractor",
    "LiteraturePDFExtractor",
    "PDFExtractionError",
    "PDFNotFoundError",
    "PDFCorruptedError",
    "UnsupportedPDFFormatError",
    "PDFExtractionTimeoutError",
    "extract_text_from_pdf",
    "get_extracted_text",
]
