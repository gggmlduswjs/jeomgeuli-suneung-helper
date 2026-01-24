"""
Books API 테스트
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from unittest.mock import Mock, patch, MagicMock
from io import BytesIO

from app.main import app
from app.infrastructure.database.models import Book, ParseStatus, Subject


client = TestClient(app)


class TestBooksAPI:
    """Books API 엔드포인트 테스트"""

    def test_list_books_empty(self):
        """교재 목록 조회 - 빈 결과"""
        with patch('app.routers.books.get_db') as mock_db:
            mock_session = Mock(spec=Session)
            mock_query = Mock()
            mock_query.order_by.return_value.all.return_value = []
            mock_session.query.return_value = mock_query
            mock_db.return_value = mock_session

            response = client.get("/api/v1/books")
            assert response.status_code == 200
            assert response.json() == []

    def test_list_books_with_subject_filter(self):
        """교재 목록 조회 - 과목 필터"""
        with patch('app.routers.books.get_db') as mock_db:
            mock_session = Mock(spec=Session)
            mock_book = Mock(spec=Book)
            mock_book.book_id = "korean_test_2024"
            mock_book.title = "수능특강 문학"
            mock_book.subject = Subject.KOREAN
            mock_book.year = 2024
            mock_book.parse_status = ParseStatus.DONE
            mock_book.lessons = []
            mock_book.created_at = "2024-01-01"

            mock_query = Mock()
            mock_filter = Mock()
            mock_filter.order_by.return_value.all.return_value = [mock_book]
            mock_query.filter.return_value = mock_filter
            mock_session.query.return_value = mock_query
            mock_db.return_value = mock_session

            response = client.get("/api/v1/books?subject=KOREAN")
            assert response.status_code == 200
            data = response.json()
            assert len(data) == 1
            assert data[0]["title"] == "수능특강 문학"

    def test_get_book_success(self):
        """교재 상세 조회 - 성공"""
        with patch('app.routers.books.get_db') as mock_db:
            mock_session = Mock(spec=Session)
            mock_book = Mock(spec=Book)
            mock_book.book_id = "test_book_123"
            mock_book.title = "테스트 교재"
            mock_book.subject = Subject.MATH
            mock_book.year = 2024
            mock_book.parse_status = ParseStatus.DONE
            mock_book.lessons = []

            mock_query = Mock()
            mock_query.filter.return_value.first.return_value = mock_book
            mock_session.query.return_value = mock_query
            mock_db.return_value = mock_session

            response = client.get("/api/v1/books/test_book_123")
            assert response.status_code == 200
            data = response.json()
            assert data["book_id"] == "test_book_123"
            assert data["title"] == "테스트 교재"
            assert data["subject"] == "MATH"

    def test_get_book_not_found(self):
        """교재 상세 조회 - 404"""
        with patch('app.routers.books.get_db') as mock_db:
            mock_session = Mock(spec=Session)
            mock_query = Mock()
            mock_query.filter.return_value.first.return_value = None
            mock_session.query.return_value = mock_query
            mock_db.return_value = mock_session

            response = client.get("/api/v1/books/nonexistent_book")
            assert response.status_code == 404
            assert "찾을 수 없습니다" in response.json()["detail"]

    def test_get_parse_status_processing(self):
        """파싱 상태 조회 - 진행 중"""
        with patch('app.routers.books.get_db') as mock_db:
            mock_session = Mock(spec=Session)
            mock_book = Mock(spec=Book)
            mock_book.book_id = "test_book_123"
            mock_book.parse_status = ParseStatus.PROCESSING
            mock_book.parse_progress = 50
            mock_book.current_page = 25
            mock_book.total_pages = 50

            mock_query = Mock()
            mock_query.filter.return_value.first.return_value = mock_book
            mock_session.query.return_value = mock_query
            mock_db.return_value = mock_session

            response = client.get("/api/v1/books/test_book_123/parse-status")
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "PROCESSING"
            assert data["progress"] == 50
            assert data["current_page"] == 25
            assert data["total_pages"] == 50

    def test_get_parse_status_done(self):
        """파싱 상태 조회 - 완료"""
        with patch('app.routers.books.get_db') as mock_db:
            mock_session = Mock(spec=Session)
            mock_book = Mock(spec=Book)
            mock_book.book_id = "test_book_123"
            mock_book.parse_status = ParseStatus.DONE
            mock_book.parse_progress = None
            mock_book.current_page = None
            mock_book.total_pages = None

            mock_query = Mock()
            mock_query.filter.return_value.first.return_value = mock_book
            mock_session.query.return_value = mock_query
            mock_db.return_value = mock_session

            response = client.get("/api/v1/books/test_book_123/parse-status")
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "DONE"
            assert data["progress"] == 100
            assert data["message"] == "파싱 완료"

    def test_upload_book_invalid_file_format(self):
        """교재 업로드 - 잘못된 파일 형식"""
        files = {"file": ("test.txt", BytesIO(b"test content"), "text/plain")}
        data = {
            "title": "테스트 교재",
            "subject": "KOREAN",
            "year": 2024
        }

        response = client.post("/api/v1/books/upload", files=files, data=data)
        assert response.status_code == 400
        assert "PDF" in response.json()["detail"]

    def test_delete_book_success(self):
        """교재 삭제 - 성공"""
        with patch('app.routers.books.get_db') as mock_db:
            mock_session = Mock(spec=Session)
            mock_book = Mock(spec=Book)
            mock_book.book_id = "test_book_123"
            mock_book.file_path = "/tmp/test.pdf"
            mock_book.lessons = []

            mock_query = Mock()
            mock_query.filter.return_value.first.return_value = mock_book
            mock_session.query.return_value = mock_query
            mock_db.return_value = mock_session

            with patch('pathlib.Path.exists', return_value=True), \
                 patch('pathlib.Path.unlink'):
                response = client.delete("/api/v1/books/test_book_123")
                assert response.status_code == 200
                assert "삭제되었습니다" in response.json()["message"]
