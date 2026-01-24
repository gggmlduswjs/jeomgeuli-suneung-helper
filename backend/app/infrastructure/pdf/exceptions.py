"""
PDF 파싱 관련 커스텀 예외 클래스
"""
from typing import Optional

from app.infrastructure.pdf.types import ErrorDetails


class ParsingError(Exception):
    """파싱 관련 기본 예외

    모든 PDF 파싱 관련 예외의 기본 클래스
    """

    def __init__(
        self,
        message: str,
        details: Optional[ErrorDetails] = None,
        original_error: Optional[Exception] = None
    ):
        """
        Args:
            message: 에러 메시지
            details: 추가 상세 정보 (딕셔너리)
            original_error: 원본 예외 (있는 경우)
        """
        super().__init__(message)
        self.message = message
        self.details = details or {}
        self.original_error = original_error
    
    def __str__(self) -> str:
        base_msg = self.message
        if self.details:
            detail_str = ", ".join(f"{k}={v}" for k, v in self.details.items())
            return f"{base_msg} ({detail_str})"
        return base_msg


class ExtractionError(ParsingError):
    """텍스트 추출 실패 예외
    
    OCR 또는 pdfplumber를 통한 텍스트 추출 실패 시 발생
    """
    pass


class TemplateNotFoundError(ParsingError):
    """템플릿을 찾을 수 없음
    
    템플릿 매칭 실패 또는 템플릿 파일이 없을 때 발생
    """
    pass


class TemplateLoadError(ParsingError):
    """템플릿 로드 실패
    
    템플릿 파일을 읽거나 파싱하는 중 오류 발생
    """
    pass


class ParsingStrategyError(ParsingError):
    """파싱 전략 실행 실패
    
    특정 파싱 전략(템플릿/AI/폴백) 실행 중 오류 발생
    """
    pass


class SectionExtractionError(ParsingError):
    """섹션 추출 실패
    
    섹션 추출 과정에서 오류 발생
    """
    pass


class ImageProcessingError(ParsingError):
    """이미지 처리 실패
    
    이미지 크롭, 저장, 렌더링 중 오류 발생
    """
    pass


class ConfigurationError(ParsingError):
    """설정 오류
    
    config.json 로드 실패 또는 설정 값이 유효하지 않을 때 발생
    """
    pass


class PageRangeError(ParsingError):
    """페이지 범위 오류
    
    페이지 범위 계산 또는 검증 실패 시 발생
    """
    pass


# 예외 처리 헬퍼 함수
def handle_parsing_error(func):
    """파싱 함수의 공통 예외 처리 데코레이터
    
    사용 예:
        @handle_parsing_error
        def parse_document(self, data):
            ...
    """
    from functools import wraps
    import logging
    
    logger = logging.getLogger(__name__)
    
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except ParsingError:
            raise  # 파싱 관련 예외는 그대로 전파
        except Exception as e:
            logger.error(f"{func.__name__} 실행 중 예상치 못한 오류: {e}")
            raise ParsingError(
                f"{func.__name__} 실패: {e}",
                details={"function": func.__name__},
                original_error=e
            ) from e
    return wrapper
