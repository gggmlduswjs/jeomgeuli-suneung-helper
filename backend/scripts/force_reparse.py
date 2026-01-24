"""
강제 재파싱 스크립트
멈춘 파싱을 강제로 재시작
"""
import sys
from pathlib import Path

# 프로젝트 루트를 sys.path에 추가
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from app.infrastructure.database.session import get_db
from app.infrastructure.database.models import Book, ParseStatus
from app.routers.books import _process_pdf_background
from app.core.config import settings
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def force_reparse_all_processing():
    """PROCESSING 상태인 모든 책을 FAILED로 변경 후 재파싱"""
    db = next(get_db())
    
    try:
        processing_books = db.query(Book).filter(Book.parse_status == ParseStatus.PROCESSING).all()
        
        if not processing_books:
            print("[force_reparse] PROCESSING 상태인 책이 없습니다.")
            return
        
        print(f"[force_reparse] {len(processing_books)}개 책 발견")
        
        for book in processing_books:
            print(f"\n[force_reparse] ========================================")
            print(f"[force_reparse] 책: {book.title} ({book.book_id})")
            print(f"[force_reparse] 상태: {book.parse_status}")
            print(f"[force_reparse] 진행률: {book.parse_progress}%")
            print(f"[force_reparse] ========================================")
            
            # 파일 경로 확인
            if not book.file_path:
                print(f"[force_reparse] ⚠️ 파일 경로가 없습니다. 건너뜁니다.")
                book.parse_status = ParseStatus.FAILED
                db.commit()
                continue
            
            file_path = Path(book.file_path)
            if not file_path.exists():
                print(f"[force_reparse] ⚠️ 파일이 없습니다: {file_path}")
                book.parse_status = ParseStatus.FAILED
                db.commit()
                continue
            
            # 상태를 PENDING으로 변경 (재파싱 준비)
            book.parse_status = ParseStatus.PENDING
            book.parse_progress = 0
            book.current_page = None
            db.commit()
            
            print(f"[force_reparse] ✅ 상태를 PENDING으로 변경했습니다.")
            print(f"[force_reparse] 관리자 페이지에서 '재파싱' 버튼을 클릭하세요.")
            print(f"[force_reparse] 또는 API 호출: POST /api/v1/books/{book.book_id}/reparse")
        
        db.commit()
        print(f"\n[force_reparse] 완료: {len(processing_books)}개 책 준비됨")
        
    except Exception as e:
        logger.error(f"[force_reparse] 오류: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    force_reparse_all_processing()
