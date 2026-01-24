"""
Lessons API 테스트
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

from app.main import app
from app.infrastructure.database.models import Book, Lesson, Unit, Subject, UnitType

client = TestClient(app)


class TestLessonsAPI:
    """Lessons API 엔드포인트 테스트"""

    def test_create_lesson_success(self):
        """레슨 생성 - 성공"""
        with patch('app.routers.lessons.get_db') as mock_db:
            mock_session = Mock(spec=Session)

            # Mock Book
            mock_book = Mock(spec=Book)
            mock_book.book_id = "test_book_123"
            mock_book.subject = Subject.KOREAN

            # Mock query for Book
            mock_book_query = Mock()
            mock_book_query.filter.return_value.first.return_value = mock_book

            # Mock Lesson after creation
            mock_lesson = Mock(spec=Lesson)
            mock_lesson.lesson_id = "korean_001"
            mock_lesson.book_id = "test_book_123"
            mock_lesson.index = 1
            mock_lesson.title = "1강. 문학의 이해"
            mock_lesson.lecture_script_text = None
            mock_lesson.estimated_time = None
            mock_lesson.key_points = None
            mock_lesson.has_question = False
            mock_lesson.has_analysis = False
            mock_lesson.created_at = datetime.now()

            # Mock session methods
            mock_session.query.return_value = mock_book_query
            mock_session.add = Mock()
            mock_session.commit = Mock()
            mock_session.refresh = Mock()
            mock_db.return_value = mock_session

            with patch('app.routers.lessons.generate_lesson_id', return_value="korean_001"):
                response = client.post("/api/v1/lessons", json={
                    "book_id": "test_book_123",
                    "index": 1,
                    "title": "1강. 문학의 이해"
                })

            assert response.status_code == 201
            data = response.json()
            assert data["book_id"] == "test_book_123"
            assert data["title"] == "1강. 문학의 이해"

    def test_create_lesson_book_not_found(self):
        """레슨 생성 - 교재 없음 (404)"""
        with patch('app.routers.lessons.get_db') as mock_db:
            mock_session = Mock(spec=Session)
            mock_query = Mock()
            mock_query.filter.return_value.first.return_value = None
            mock_session.query.return_value = mock_query
            mock_db.return_value = mock_session

            response = client.post("/api/v1/lessons", json={
                "book_id": "nonexistent_book",
                "index": 1,
                "title": "테스트 레슨"
            })

            assert response.status_code == 404
            assert "교재를 찾을 수 없습니다" in response.json()["detail"]

    def test_list_lessons_success(self):
        """레슨 목록 조회 - 성공"""
        with patch('app.routers.lessons.get_db') as mock_db:
            mock_session = Mock(spec=Session)

            # Mock Book
            mock_book = Mock(spec=Book)
            mock_book.book_id = "test_book_123"

            # Mock Lessons
            mock_lesson1 = Mock(spec=Lesson)
            mock_lesson1.lesson_id = "korean_001"
            mock_lesson1.book_id = "test_book_123"
            mock_lesson1.index = 1
            mock_lesson1.title = "1강. 문학의 이해"
            mock_lesson1.lecture_script_text = "강의 대본..."
            mock_lesson1.estimated_time = 30
            mock_lesson1.key_points = '["핵심1", "핵심2"]'
            mock_lesson1.has_question = True
            mock_lesson1.has_analysis = False
            mock_lesson1.created_at = datetime.now()

            # Mock units for counting
            mock_unit1 = Mock(spec=Unit)
            mock_unit1.type = UnitType.CONCEPT
            mock_unit2 = Mock(spec=Unit)
            mock_unit2.type = UnitType.QUESTION
            mock_lesson1.units = [mock_unit1, mock_unit2]

            mock_lesson2 = Mock(spec=Lesson)
            mock_lesson2.lesson_id = "korean_002"
            mock_lesson2.book_id = "test_book_123"
            mock_lesson2.index = 2
            mock_lesson2.title = "2강. 시의 이해"
            mock_lesson2.lecture_script_text = None
            mock_lesson2.estimated_time = None
            mock_lesson2.key_points = None
            mock_lesson2.has_question = False
            mock_lesson2.has_analysis = False
            mock_lesson2.created_at = datetime.now()
            mock_lesson2.units = []

            # Setup query mocks
            def query_side_effect(model):
                if model == Book:
                    mock_book_query = Mock()
                    mock_book_query.filter.return_value.first.return_value = mock_book
                    return mock_book_query
                elif model == Lesson:
                    mock_lesson_query = Mock()
                    mock_lesson_query.filter.return_value.order_by.return_value.all.return_value = [
                        mock_lesson1, mock_lesson2
                    ]
                    return mock_lesson_query

            mock_session.query.side_effect = query_side_effect
            mock_db.return_value = mock_session

            response = client.get("/api/v1/books/test_book_123/lessons")

            assert response.status_code == 200
            data = response.json()
            assert len(data) == 2
            assert data[0]["title"] == "1강. 문학의 이해"
            assert data[0]["unit_count"] == 2
            assert data[0]["question_count"] == 1
            assert data[1]["title"] == "2강. 시의 이해"
            assert data[1]["unit_count"] == 0

    def test_list_lessons_book_not_found(self):
        """레슨 목록 조회 - 교재 없음 (404)"""
        with patch('app.routers.lessons.get_db') as mock_db:
            mock_session = Mock(spec=Session)
            mock_query = Mock()
            mock_query.filter.return_value.first.return_value = None
            mock_session.query.return_value = mock_query
            mock_db.return_value = mock_session

            response = client.get("/api/v1/books/nonexistent_book/lessons")

            assert response.status_code == 404
            assert "교재를 찾을 수 없습니다" in response.json()["detail"]

    def test_get_lesson_success(self):
        """레슨 상세 조회 - 성공"""
        with patch('app.routers.lessons.get_db') as mock_db:
            mock_session = Mock(spec=Session)

            # Mock Lesson with units
            mock_lesson = Mock(spec=Lesson)
            mock_lesson.lesson_id = "korean_001"
            mock_lesson.book_id = "test_book_123"
            mock_lesson.index = 1
            mock_lesson.title = "1강. 문학의 이해"
            mock_lesson.lecture_script_text = "강의 대본입니다..."
            mock_lesson.estimated_time = 30
            mock_lesson.key_points = '["핵심1", "핵심2", "핵심3"]'
            mock_lesson.has_question = True
            mock_lesson.has_analysis = True
            mock_lesson.created_at = datetime.now()

            # Mock units
            mock_unit1 = Mock(spec=Unit)
            mock_unit1.type = UnitType.CONCEPT
            mock_unit2 = Mock(spec=Unit)
            mock_unit2.type = UnitType.QUESTION
            mock_unit3 = Mock(spec=Unit)
            mock_unit3.type = UnitType.QUESTION
            mock_lesson.units = [mock_unit1, mock_unit2, mock_unit3]

            mock_query = Mock()
            mock_query.filter.return_value.first.return_value = mock_lesson
            mock_session.query.return_value = mock_query
            mock_db.return_value = mock_session

            response = client.get("/api/v1/lessons/korean_001")

            assert response.status_code == 200
            data = response.json()
            assert data["lesson_id"] == "korean_001"
            assert data["title"] == "1강. 문학의 이해"
            assert data["estimated_time"] == 30
            assert data["unit_count"] == 3
            assert data["question_count"] == 2
            assert len(data["key_points"]) == 3

    def test_get_lesson_not_found(self):
        """레슨 상세 조회 - 레슨 없음 (404)"""
        with patch('app.routers.lessons.get_db') as mock_db:
            mock_session = Mock(spec=Session)
            mock_query = Mock()
            mock_query.filter.return_value.first.return_value = None
            mock_session.query.return_value = mock_query
            mock_db.return_value = mock_session

            response = client.get("/api/v1/lessons/nonexistent_lesson")

            assert response.status_code == 404
            assert "레슨을 찾을 수 없습니다" in response.json()["detail"]

    def test_split_lesson_script_no_script(self):
        """레슨 분할 - 강의 대본 없음 (400)"""
        with patch('app.routers.lessons.get_db') as mock_db:
            mock_session = Mock(spec=Session)

            # Mock Lesson without script
            mock_lesson = Mock(spec=Lesson)
            mock_lesson.lesson_id = "korean_001"
            mock_lesson.lecture_script_text = None

            mock_query = Mock()
            mock_query.filter.return_value.first.return_value = mock_lesson
            mock_session.query.return_value = mock_query
            mock_db.return_value = mock_session

            response = client.post("/api/v1/lessons/korean_001/split", json={})

            assert response.status_code == 400
            assert "강의 대본이 없습니다" in response.json()["detail"]

    def test_get_lesson_script_success(self):
        """레슨 강의 대본 조회 - 성공"""
        with patch('app.routers.lessons.get_db') as mock_db:
            mock_session = Mock(spec=Session)

            mock_lesson = Mock(spec=Lesson)
            mock_lesson.lesson_id = "korean_001"
            mock_lesson.title = "1강. 문학의 이해"
            mock_lesson.lecture_script_text = "강의 대본입니다..."
            mock_lesson.estimated_time = 30
            mock_lesson.key_points = '["핵심1", "핵심2"]'

            mock_query = Mock()
            mock_query.filter.return_value.first.return_value = mock_lesson
            mock_session.query.return_value = mock_query
            mock_db.return_value = mock_session

            response = client.get("/api/v1/lessons/korean_001/script")

            assert response.status_code == 200
            data = response.json()
            assert data["lesson_id"] == "korean_001"
            assert data["title"] == "1강. 문학의 이해"
            assert data["script_text"] == "강의 대본입니다..."
            assert data["estimated_time"] == 30
            assert len(data["key_points"]) == 2

    def test_get_lesson_script_not_found(self):
        """레슨 강의 대본 조회 - 레슨 없음 (404)"""
        with patch('app.routers.lessons.get_db') as mock_db:
            mock_session = Mock(spec=Session)
            mock_query = Mock()
            mock_query.filter.return_value.first.return_value = None
            mock_session.query.return_value = mock_query
            mock_db.return_value = mock_session

            response = client.get("/api/v1/lessons/nonexistent_lesson/script")

            assert response.status_code == 404
            assert "레슨을 찾을 수 없습니다" in response.json()["detail"]

    def test_get_lesson_summary_no_content(self):
        """레슨 요약 - 요약할 내용 없음 (400)"""
        with patch('app.routers.lessons.get_db') as mock_db:
            mock_session = Mock(spec=Session)

            # Mock Lesson with no content
            mock_lesson = Mock(spec=Lesson)
            mock_lesson.lesson_id = "korean_001"
            mock_lesson.title = None
            mock_lesson.lecture_script_text = None
            mock_lesson.key_points = None
            mock_lesson.book = None

            mock_query = Mock()
            mock_query.filter.return_value.first.return_value = mock_lesson
            mock_session.query.return_value = mock_query
            mock_db.return_value = mock_session

            response = client.get("/api/v1/lessons/korean_001/summary")

            assert response.status_code == 400
            assert "요약할 내용이 없습니다" in response.json()["detail"]
