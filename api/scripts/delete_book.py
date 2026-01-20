"""
특정 교재 삭제 스크립트
"""
import sys
from pathlib import Path

# api 디렉토리를 Python 경로에 추가
api_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(api_dir))

from app.db.session import SessionLocal
from app.db.models import Book, Lesson, Curriculum, LearningUnit

def delete_book(book_id: str = None, book_id_pattern: str = None):
    """특정 교재 삭제 (파일 + DB)"""
    db = SessionLocal()
    try:
        if book_id:
            book = db.query(Book).filter(Book.book_id == book_id).first()
        elif book_id_pattern:
            # 패턴으로 검색 (인코딩 문제 대비)
            book = db.query(Book).filter(Book.book_id.like(f'%{book_id_pattern}%')).first()
        else:
            print("[오류] book_id 또는 book_id_pattern이 필요합니다.")
            return False
        
        if not book:
            print(f"[오류] 교재를 찾을 수 없습니다: {book_id}")
            return False
        
        print(f"[확인] 교재 정보:")
        print(f"  ID: {book.book_id}")
        print(f"  제목: {book.title}")
        print(f"  과목: {book.subject}")
        print(f"  상태: {book.parse_status}")
        print(f"  파일 경로: {book.file_path}")
        
        # 파일 삭제
        if book.file_path:
            file_path = Path(book.file_path)
            if file_path.exists():
                try:
                    file_path.unlink()
                    print(f"[삭제] 파일 삭제 완료: {file_path}")
                except Exception as e:
                    print(f"[경고] 파일 삭제 실패: {e}")
            else:
                print(f"[정보] 파일이 이미 없습니다: {file_path}")
        
        # 관련 데이터 삭제
        # 1. LearningUnit (커리큘럼과 연결된 학습 단위)
        curricula = db.query(Curriculum).filter(Curriculum.book_id == book.book_id).all()
        for curriculum in curricula:
            learning_units = db.query(LearningUnit).filter(LearningUnit.curriculum_id == curriculum.curriculum_id).all()
            for unit in learning_units:
                db.delete(unit)
            db.delete(curriculum)
            print(f"[삭제] 커리큘럼 삭제: {curriculum.curriculum_id}")
        
        # 2. Lesson (cascade로 자동 삭제되지만 명시적으로)
        lessons = db.query(Lesson).filter(Lesson.book_id == book.book_id).all()
        for lesson in lessons:
            db.delete(lesson)
        if lessons:
            print(f"[삭제] 레슨 {len(lessons)}개 삭제")
        
        # 3. Book 삭제
        deleted_book_id = book.book_id
        db.delete(book)
        db.commit()
        
        print(f"[완료] 교재 삭제 완료: {deleted_book_id}")
        return True
        
    except Exception as e:
        print(f"[오류] 삭제 중 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
        return False
    finally:
        db.close()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="특정 교재 삭제")
    parser.add_argument("--book-id", help="삭제할 교재 ID (전체)")
    parser.add_argument("--pattern", help="삭제할 교재 ID 패턴 (부분 일치)")
    parser.add_argument("--yes", action="store_true", help="확인 없이 실행")
    
    args = parser.parse_args()
    
    if not args.book_id and not args.pattern:
        print("[오류] --book-id 또는 --pattern이 필요합니다.")
        sys.exit(1)
    
    target = args.book_id or args.pattern
    if not args.yes:
        print(f"[경고] 다음 교재를 삭제합니다: {target}")
        confirm = input("계속하시겠습니까? (y/N): ").strip().lower()
        if confirm != 'y':
            print("취소되었습니다.")
            sys.exit(0)
    
    success = delete_book(book_id=args.book_id, book_id_pattern=args.pattern)
    sys.exit(0 if success else 1)
