"""
교재 목록 API 확인 스크립트
"""
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "api"))

from app.db.session import SessionLocal
from app.db.models import Book, Subject

def main():
    db = SessionLocal()
    
    try:
        print("=" * 80)
        print("교재 목록 확인")
        print("=" * 80)
        print()
        
        # 전체 교재
        all_books = db.query(Book).order_by(Book.created_at.desc()).all()
        print(f"[전체 교재] {len(all_books)}개")
        print()
        
        for book in all_books:
            lesson_count = len(book.lessons) if book.lessons else 0
            print(f"  - {book.title} ({book.subject.value if hasattr(book.subject, 'value') else book.subject})")
            print(f"    Book ID: {book.book_id}")
            print(f"    Lesson 수: {lesson_count}")
            print()
        
        # 국어(KOREAN) 교재만
        korean_books = db.query(Book).filter(Book.subject == Subject.KOREAN).all()
        print(f"[국어 교재] {len(korean_books)}개")
        print()
        
        for book in korean_books:
            lesson_count = len(book.lessons) if book.lessons else 0
            print(f"  - {book.title}")
            print(f"    Book ID: {book.book_id}")
            print(f"    Lesson 수: {lesson_count}")
            print()
        
        print("=" * 80)
        print()
        print("✅ 교재가 DB에 있으면 프론트엔드 교재 선택 화면에 표시됩니다.")
        print()
        
    except Exception as e:
        print(f"[ERROR] {e}")
        import traceback
        traceback.print_exc()
        return 1
    finally:
        db.close()
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
