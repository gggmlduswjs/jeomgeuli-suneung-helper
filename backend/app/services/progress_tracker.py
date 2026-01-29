"""
진행률 추적 서비스
PDF 파싱 작업의 진행률을 데이터베이스에 업데이트하고 로깅합니다.
"""
import logging
from typing import Optional
from sqlalchemy.orm import Session

from app.infrastructure.database.models import Book


logger = logging.getLogger(__name__)


class ProgressTracker:
    """PDF 파싱 작업의 진행률을 추적하고 업데이트하는 클래스

    데이터베이스의 Book 레코드를 업데이트하고 로그를 남깁니다.
    중복된 진행률 업데이트 코드를 제거하고 일관성을 보장합니다.
    """

    def __init__(self, db: Session, book_id: str):
        """
        Args:
            db: 데이터베이스 세션
            book_id: 추적할 Book의 ID
        """
        self.db = db
        self.book_id = book_id

    def update(
        self,
        progress: int,
        message: str = "",
        current_page: Optional[int] = None
    ) -> bool:
        """진행률을 업데이트하고 로그를 남깁니다

        Args:
            progress: 진행률 퍼센트 (0-100)
            message: 로그 메시지 (선택)
            current_page: 현재 처리 중인 페이지 번호 (선택)

        Returns:
            업데이트 성공 여부
        """
        try:
            book = self.db.query(Book).filter(Book.book_id == self.book_id).first()
            if not book:
                logger.warning(f"[ProgressTracker] Book not found: {self.book_id}")
                return False

            # 진행률 업데이트
            book.parse_progress = progress

            # 현재 페이지 업데이트 (제공된 경우)
            if current_page is not None:
                book.current_page = current_page

            self.db.commit()

            # 로그 출력
            log_msg = f"[ProgressTracker] 진행률: {progress}%"
            if message:
                log_msg += f" - {message}"
            if current_page is not None:
                log_msg += f" (페이지: {current_page})"

            logger.info(log_msg)
            return True

        except Exception as e:
            logger.error(f"[ProgressTracker] 진행률 업데이트 실패: {e}")
            return False

    def update_with_page_range(
        self,
        progress: int,
        message: str = "",
        start_page: Optional[int] = None,
        end_page: Optional[int] = None
    ) -> bool:
        """페이지 범위 정보와 함께 진행률을 업데이트합니다

        Args:
            progress: 진행률 퍼센트 (0-100)
            message: 로그 메시지 (선택)
            start_page: 시작 페이지 번호 (선택)
            end_page: 종료 페이지 번호 (선택)

        Returns:
            업데이트 성공 여부
        """
        try:
            book = self.db.query(Book).filter(Book.book_id == self.book_id).first()
            if not book:
                logger.warning(f"[ProgressTracker] Book not found: {self.book_id}")
                return False

            # 진행률 업데이트
            book.parse_progress = progress

            # 현재 페이지 업데이트 (시작 페이지로 설정)
            if start_page is not None:
                book.current_page = start_page

            self.db.commit()

            # 로그 출력
            log_msg = f"[ProgressTracker] 진행률: {progress}%"
            if message:
                log_msg += f" - {message}"
            if start_page is not None and end_page is not None:
                log_msg += f" (페이지 {start_page}-{end_page} 처리 중)"
            elif start_page is not None:
                log_msg += f" (페이지 {start_page}부터 처리 중)"

            logger.info(log_msg)
            return True

        except Exception as e:
            logger.error(f"[ProgressTracker] 진행률 업데이트 실패: {e}")
            return False

    def get_current_progress(self) -> Optional[int]:
        """현재 진행률을 조회합니다

        Returns:
            현재 진행률 (0-100), 실패 시 None
        """
        try:
            book = self.db.query(Book).filter(Book.book_id == self.book_id).first()
            if book:
                return book.parse_progress
            return None
        except Exception as e:
            logger.error(f"[ProgressTracker] 진행률 조회 실패: {e}")
            return None
