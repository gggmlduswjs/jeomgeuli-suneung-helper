"""
파싱 진행 상황 모니터링 스크립트
실시간으로 파싱 상태와 로그를 확인
"""
import sys
import time
from pathlib import Path
from datetime import datetime

# 프로젝트 루트를 경로에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.core.config import settings
from app.infrastructure.database.session import SessionLocal
from app.infrastructure.database.models import Book, ParseStatus


def monitor_book_parsing(book_id: str = None, interval: int = 5):
    """
    교재 파싱 상태 모니터링
    
    Args:
        book_id: 모니터링할 교재 ID (None이면 모든 PROCESSING 교재)
        interval: 확인 간격 (초)
    """
    db = SessionLocal()
    
    try:
        print("=" * 60)
        print("파싱 진행 상황 모니터링")
        print("=" * 60)
        print(f"확인 간격: {interval}초")
        print()
        
        while True:
            try:
                # 교재 조회
                if book_id:
                    books = [db.query(Book).filter(Book.book_id == book_id).first()]
                    books = [b for b in books if b]
                else:
                    books = db.query(Book).filter(
                        Book.parse_status == ParseStatus.PROCESSING
                    ).all()
                
                if not books:
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] 파싱 중인 교재가 없습니다.")
                    time.sleep(interval)
                    continue
                
                # 각 교재 상태 출력
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
                    
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] {status_icon} {book.title}")
                    print(f"  상태: {book.parse_status.value if hasattr(book.parse_status, 'value') else book.parse_status}")
                    print(f"  진행률: {progress}%")
                    if total_pages > 0:
                        print(f"  페이지: {current_page}/{total_pages}")
                    print()
                
                # 완료된 교재가 있으면 종료
                if any(b.parse_status in [ParseStatus.DONE, ParseStatus.FAILED] for b in books):
                    print("파싱이 완료되었습니다!")
                    break
                
                time.sleep(interval)
                
            except KeyboardInterrupt:
                print("\n모니터링을 중단합니다.")
                break
            except Exception as e:
                print(f"[ERROR] 오류 발생: {e}")
                time.sleep(interval)
                
    finally:
        db.close()


def list_parsing_books():
    """파싱 중인 교재 목록"""
    db = SessionLocal()
    
    try:
        books = db.query(Book).filter(
            Book.parse_status == ParseStatus.PROCESSING
        ).all()
        
        if not books:
            print("파싱 중인 교재가 없습니다.")
            return
        
        print("=" * 60)
        print("파싱 중인 교재 목록")
        print("=" * 60)
        
        for book in books:
            progress = book.parse_progress or 0
            print(f"  - {book.book_id}: {book.title} ({progress}%)")
        
        print()
        print("모니터링 시작:")
        print(f"  python scripts/monitor_parsing.py {books[0].book_id}")
        
    finally:
        db.close()


def main():
    """메인 함수"""
    import sys
    
    if len(sys.argv) > 1:
        book_id = sys.argv[1]
        interval = int(sys.argv[2]) if len(sys.argv) > 2 else 5
        monitor_book_parsing(book_id, interval)
    else:
        list_parsing_books()


if __name__ == "__main__":
    main()
