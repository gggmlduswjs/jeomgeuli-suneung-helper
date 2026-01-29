"""
파싱 상태 확인 스크립트
현재 파싱 중인 교재와 상태 확인
"""
import sys
from pathlib import Path
from datetime import datetime

# 프로젝트 루트를 경로에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.infrastructure.database.session import SessionLocal
from app.infrastructure.database.models import Book, ParseStatus


def check_parsing_status(book_id: str = None):
    """파싱 상태 확인"""
    db = SessionLocal()
    
    try:
        if book_id:
            book = db.query(Book).filter(Book.book_id == book_id).first()
            if not book:
                print(f"교재를 찾을 수 없습니다: {book_id}")
                return
            books = [book]
        else:
            books = db.query(Book).order_by(Book.created_at.desc()).limit(10).all()
        
        print("=" * 60)
        print("파싱 상태 확인")
        print("=" * 60)
        print(f"확인 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        for book in books:
            status_icon = {
                ParseStatus.PROCESSING: "[진행중]",
                ParseStatus.DONE: "[완료]",
                ParseStatus.FAILED: "[실패]",
                ParseStatus.PENDING: "[대기]"
            }.get(book.parse_status, "[알수없음]")
            
            progress = book.parse_progress or 0
            current_page = book.current_page or 0
            total_pages = book.total_pages or 0
            
            print(f"{status_icon} {book.title}")
            print(f"  ID: {book.book_id}")
            print(f"  상태: {book.parse_status.value if hasattr(book.parse_status, 'value') else book.parse_status}")
            print(f"  진행률: {progress}%")
            if total_pages > 0:
                print(f"  페이지: {current_page}/{total_pages}")
            # 강의 수는 관계를 통해 가져오기
            lesson_count = len(book.lessons) if hasattr(book, 'lessons') and book.lessons else 0
            print(f"  강의 수: {lesson_count}개")
            print(f"  생성 시간: {book.created_at}")
            print()
        
    finally:
        db.close()


def main():
    """메인 함수"""
    import sys
    
    book_id = sys.argv[1] if len(sys.argv) > 1 else None
    check_parsing_status(book_id)


if __name__ == "__main__":
    main()
