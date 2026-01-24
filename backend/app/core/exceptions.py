"""
커스텀 Exception 클래스

일관된 에러 핸들링을 위한 커스텀 예외 정의
"""
from fastapi import HTTPException, status


class BookNotFoundException(HTTPException):
    """교재를 찾을 수 없을 때"""
    def __init__(self, book_id: str):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"교재를 찾을 수 없습니다: {book_id}"
        )


class LessonNotFoundException(HTTPException):
    """레슨을 찾을 수 없을 때"""
    def __init__(self, lesson_id: str):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"레슨을 찾을 수 없습니다: {lesson_id}"
        )


class UnitNotFoundException(HTTPException):
    """학습 단위를 찾을 수 없을 때"""
    def __init__(self, unit_id: str):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"학습 단위를 찾을 수 없습니다: {unit_id}"
        )


class CurriculumNotFoundException(HTTPException):
    """커리큘럼을 찾을 수 없을 때"""
    def __init__(self, curriculum_id: str):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"커리큘럼을 찾을 수 없습니다: {curriculum_id}"
        )


class TemplateNotFoundException(HTTPException):
    """템플릿을 찾을 수 없을 때"""
    def __init__(self, subject: str, name: str):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"템플릿을 찾을 수 없습니다: {subject}/{name}"
        )


class InvalidFileFormatException(HTTPException):
    """잘못된 파일 형식"""
    def __init__(self, expected: str, actual: str = None):
        detail = f"{expected} 파일만 업로드 가능합니다."
        if actual:
            detail += f" (업로드된 파일: {actual})"
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail
        )


class FileTooLargeException(HTTPException):
    """파일 크기 초과"""
    def __init__(self, max_size_mb: int):
        super().__init__(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"파일 크기는 {max_size_mb}MB를 초과할 수 없습니다."
        )


class ParsingFailedException(HTTPException):
    """파싱 실패"""
    def __init__(self, reason: str = None):
        detail = "파싱에 실패했습니다."
        if reason:
            detail += f" ({reason})"
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=detail
        )


class InvalidSubjectException(HTTPException):
    """유효하지 않은 과목"""
    def __init__(self, subject: str):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"유효하지 않은 과목입니다: {subject}"
        )


class DuplicateResourceException(HTTPException):
    """중복된 리소스"""
    def __init__(self, resource_type: str, identifier: str):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"{resource_type}이(가) 이미 존재합니다: {identifier}"
        )


class DatabaseOperationException(HTTPException):
    """데이터베이스 작업 실패"""
    def __init__(self, operation: str, reason: str = None):
        detail = f"데이터베이스 {operation} 작업에 실패했습니다."
        if reason:
            detail += f" ({reason})"
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=detail
        )


class ExternalServiceException(HTTPException):
    """외부 서비스 호출 실패"""
    def __init__(self, service_name: str, reason: str = None):
        detail = f"{service_name} 서비스 호출에 실패했습니다."
        if reason:
            detail += f" ({reason})"
        super().__init__(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=detail
        )
