"""
PDF 추출 관련 예외 클래스
"""
from pathlib import Path
from typing import Optional


class PDFExtractionError(Exception):
    """PDF 추출 기본 예외"""
    def __init__(self, message: str, pdf_path: Optional[Path] = None):
        self.message = message
        self.pdf_path = pdf_path
        super().__init__(self.message)
    
    def __str__(self):
        if self.pdf_path:
            return f"{self.message} (파일: {self.pdf_path})"
        return self.message


class PDFNotFoundError(PDFExtractionError):
    """PDF 파일을 찾을 수 없음"""
    pass


class PDFCorruptedError(PDFExtractionError):
    """PDF 파일이 손상됨"""
    pass


class UnsupportedPDFFormatError(PDFExtractionError):
    """지원하지 않는 PDF 형식"""
    pass


class PDFExtractionTimeoutError(PDFExtractionError):
    """PDF 추출 시간 초과"""
    pass
