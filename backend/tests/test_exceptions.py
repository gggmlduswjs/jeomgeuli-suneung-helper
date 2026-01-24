"""
커스텀 Exception 테스트
"""
import pytest
from fastapi import status

from app.core.exceptions import (
    BookNotFoundException,
    LessonNotFoundException,
    UnitNotFoundException,
    CurriculumNotFoundException,
    TemplateNotFoundException,
    InvalidFileFormatException,
    FileTooLargeException,
    ParsingFailedException,
    InvalidSubjectException,
    DuplicateResourceException,
    DatabaseOperationException,
    ExternalServiceException
)


class TestCustomExceptions:
    """커스텀 Exception 테스트"""

    def test_book_not_found_exception(self):
        """BookNotFoundException 테스트"""
        exc = BookNotFoundException("book_123")
        assert exc.status_code == status.HTTP_404_NOT_FOUND
        assert "book_123" in exc.detail

    def test_lesson_not_found_exception(self):
        """LessonNotFoundException 테스트"""
        exc = LessonNotFoundException("lesson_456")
        assert exc.status_code == status.HTTP_404_NOT_FOUND
        assert "lesson_456" in exc.detail

    def test_unit_not_found_exception(self):
        """UnitNotFoundException 테스트"""
        exc = UnitNotFoundException("unit_789")
        assert exc.status_code == status.HTTP_404_NOT_FOUND
        assert "unit_789" in exc.detail

    def test_curriculum_not_found_exception(self):
        """CurriculumNotFoundException 테스트"""
        exc = CurriculumNotFoundException("curriculum_001")
        assert exc.status_code == status.HTTP_404_NOT_FOUND
        assert "curriculum_001" in exc.detail

    def test_template_not_found_exception(self):
        """TemplateNotFoundException 테스트"""
        exc = TemplateNotFoundException("math", "template_v1")
        assert exc.status_code == status.HTTP_404_NOT_FOUND
        assert "math" in exc.detail
        assert "template_v1" in exc.detail

    def test_invalid_file_format_exception(self):
        """InvalidFileFormatException 테스트"""
        exc = InvalidFileFormatException("PDF", "test.docx")
        assert exc.status_code == status.HTTP_400_BAD_REQUEST
        assert "PDF" in exc.detail
        assert "test.docx" in exc.detail

    def test_file_too_large_exception(self):
        """FileTooLargeException 테스트"""
        exc = FileTooLargeException(50)
        assert exc.status_code == status.HTTP_413_REQUEST_ENTITY_TOO_LARGE
        assert "50MB" in exc.detail

    def test_parsing_failed_exception(self):
        """ParsingFailedException 테스트"""
        exc = ParsingFailedException("Invalid PDF format")
        assert exc.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert "Invalid PDF format" in exc.detail

    def test_invalid_subject_exception(self):
        """InvalidSubjectException 테스트"""
        exc = InvalidSubjectException("science")
        assert exc.status_code == status.HTTP_400_BAD_REQUEST
        assert "science" in exc.detail

    def test_duplicate_resource_exception(self):
        """DuplicateResourceException 테스트"""
        exc = DuplicateResourceException("교재", "book_123")
        assert exc.status_code == status.HTTP_409_CONFLICT
        assert "교재" in exc.detail
        assert "book_123" in exc.detail

    def test_database_operation_exception(self):
        """DatabaseOperationException 테스트"""
        exc = DatabaseOperationException("저장", "Connection timeout")
        assert exc.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert "저장" in exc.detail
        assert "Connection timeout" in exc.detail

    def test_external_service_exception(self):
        """ExternalServiceException 테스트"""
        exc = ExternalServiceException("OpenAI", "API key invalid")
        assert exc.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
        assert "OpenAI" in exc.detail
        assert "API key invalid" in exc.detail
