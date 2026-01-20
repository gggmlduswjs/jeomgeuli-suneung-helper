"""
파싱 진행 상황 모니터링 스크립트
"""
import time
import sys
sys.path.insert(0, 'api')

from app.db.session import get_db
from app.db.models import Book, Lesson

def monitor_parsing():
    """파싱 진행 상황을 모니터링"""
    print("=" * 60)
    print("교재 파싱 진행 상황 모니터링")
    print("=" * 60)

    literature_id = 'book_korean_2026_수능특강_문학_3de620'
    english_id = 'book_english_2026_수능특강_영어_ef786c'

    prev_lit_status = None
    prev_eng_status = None

    try:
        while True:
            db = next(get_db())

            # 문학 교재
            lit_book = db.query(Book).filter(Book.book_id == literature_id).first()
            lit_lessons = db.query(Lesson).filter(Lesson.book_id == literature_id).count()

            # 영어 교재
            eng_book = db.query(Book).filter(Book.book_id == english_id).first()
            eng_lessons = db.query(Lesson).filter(Lesson.book_id == english_id).count()

            # 상태 변경 시에만 출력
            lit_status = f"{lit_book.parse_status.value}|{lit_lessons}"
            eng_status = f"{eng_book.parse_status.value}|{eng_lessons}"

            if lit_status != prev_lit_status or eng_status != prev_eng_status:
                timestamp = time.strftime("%H:%M:%S")
                print(f"\n[{timestamp}]")
                print(f"  문학: {lit_book.parse_status.value:12s} - {lit_lessons:2d} 강의")
                print(f"  영어: {eng_book.parse_status.value:12s} - {eng_lessons:2d} 강의")

                prev_lit_status = lit_status
                prev_eng_status = eng_status

                # 둘 다 완료되면 종료
                if lit_book.parse_status.value == 'DONE' and eng_book.parse_status.value == 'DONE':
                    print("\n" + "=" * 60)
                    print("파싱 완료!")
                    print("=" * 60)
                    print(f"문학: {lit_lessons}개 강의")
                    print(f"영어: {eng_lessons}개 강의")
                    break

            time.sleep(10)  # 10초마다 체크

    except KeyboardInterrupt:
        print("\n\n모니터링 중지")

if __name__ == '__main__':
    monitor_parsing()
