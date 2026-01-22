import sys
import json
sys.path.insert(0, 'api')

from app.db.session import SessionLocal
from app.db.models import Book, Lesson, Unit

db = SessionLocal()

# Check math1
math_book = db.query(Book).filter(Book.subject == 'MATH').first()
if math_book:
    lessons = db.query(Lesson).filter(Lesson.book_id == math_book.book_id).count()
    units = db.query(Unit).join(Lesson).filter(Lesson.book_id == math_book.book_id).count()
    print(f"수학1: {math_book.parse_status.value} | 강의 {lessons}개 | 유닛 {units}개")

    # Check a sample lesson
    lesson = db.query(Lesson).filter(Lesson.lesson_id == 'lesson_math1_01').first()
    units_sample = db.query(Unit).filter(Unit.lesson_id == 'lesson_math1_01').all()

    print(f"\n샘플 확인: {lesson.title}")
    print(f"  유닛 수: {len(units_sample)}")
    for u in units_sample:
        print(f"  - [{u.type.value}] {u.title}")
else:
    print("수학1 교재 없음")

db.close()

# Check lectures.json
print("\nlectures.json 확인:")
with open('api/data/math1/lectures/lectures.json', 'r', encoding='utf-8') as f:
    data = json.load(f)
    print(f"  총 강의: {len(data)}개")
    print(f"  첫 강의: {data[0]['title']}")
    print(f"  마지막 강의: {data[-1]['title']}")

print("\n검증 완료!")
