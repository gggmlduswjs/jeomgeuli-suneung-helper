"""
교재 데이터 정리 스크립트
- file_path가 None인 교재 삭제
- 파일이 없는 교재 삭제
- FAILED 상태의 오래된 교재 삭제 (선택적)
"""
import sys
from pathlib import Path
from datetime import datetime, timedelta

# api 디렉토리를 Python 경로에 추가
api_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(api_dir))

from app.db.session import SessionLocal
from app.db.models import Book, Lesson, ParseStatus

def cleanup_books(
    delete_no_file: bool = True,
    delete_failed_old: bool = True,
    failed_days: int = 7
):
    """교재 데이터 정리"""
    db = SessionLocal()
    try:
        books = db.query(Book).all()
        print(f"총 {len(books)}개 교재 확인 중...\n")
        
        deleted_count = 0
        kept_count = 0
        
        for book in books:
            should_delete = False
            reason = []
            
            # 1. file_path가 None인 경우
            if delete_no_file and not book.file_path:
                should_delete = True
                reason.append("file_path가 None")
            
            # 2. 파일이 실제로 없는 경우
            if book.file_path:
                file_path = Path(book.file_path)
                if not file_path.exists():
                    should_delete = True
                    reason.append(f"파일 없음: {book.file_path}")
            
            # 3. FAILED 상태이고 오래된 경우
            if delete_failed_old and book.parse_status == ParseStatus.FAILED:
                if book.created_at:
                    days_old = (datetime.utcnow() - book.created_at.replace(tzinfo=None)).days
                    if days_old >= failed_days:
                        should_delete = True
                        reason.append(f"FAILED 상태 {days_old}일 경과")
            
            if should_delete:
                print(f"[삭제] {book.book_id}")
                print(f"   제목: {book.title}")
                print(f"   이유: {', '.join(reason)}")
                
                # 관련 레슨도 삭제 (cascade)
                lesson_count = len(book.lessons) if book.lessons else 0
                if lesson_count > 0:
                    print(f"   관련 레슨 {lesson_count}개도 함께 삭제됨")
                
                db.delete(book)
                deleted_count += 1
            else:
                kept_count += 1
                print(f"[유지] {book.book_id} - {book.title} ({book.parse_status})")
        
        if deleted_count > 0:
            db.commit()
            print(f"\n[완료] {deleted_count}개 교재 삭제 완료")
        else:
            print(f"\n[완료] 삭제할 교재가 없습니다")
        
        print(f"[결과] 삭제 {deleted_count}개, 유지 {kept_count}개")
        
    except Exception as e:
        print(f"[오류] 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="교재 데이터 정리")
    parser.add_argument("--no-file", action="store_true", help="file_path가 None인 교재 삭제")
    parser.add_argument("--failed-old", action="store_true", help="FAILED 상태의 오래된 교재 삭제")
    parser.add_argument("--failed-days", type=int, default=7, help="FAILED 상태 유지 기간 (일, 기본값: 7)")
    parser.add_argument("--yes", action="store_true", help="확인 없이 실행")
    
    args = parser.parse_args()
    
    delete_no_file = args.no_file if args.no_file else True
    delete_failed_old = args.failed_old if args.failed_old else True
    
    if not args.yes:
        print("[경고] 다음 조건의 교재가 삭제됩니다:")
        if delete_no_file:
            print("  - file_path가 None인 교재")
            print("  - 파일이 실제로 없는 교재")
        if delete_failed_old:
            print(f"  - FAILED 상태이고 {args.failed_days}일 이상 경과한 교재")
        print()
        confirm = input("계속하시겠습니까? (y/N): ").strip().lower()
        if confirm != 'y':
            print("취소되었습니다.")
            sys.exit(0)
    
    cleanup_books(
        delete_no_file=delete_no_file,
        delete_failed_old=delete_failed_old,
        failed_days=args.failed_days
    )
