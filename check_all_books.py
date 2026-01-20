import sys
sys.path.insert(0, 'api')

from app.db.session import SessionLocal
from app.db.models import Book, Lesson

db = SessionLocal()

books = db.query(Book).all()
print(f"전체 교재: {len(books)}개\n")

for b in books:
    lessons = db.query(Lesson).filter(Lesson.book_id == b.book_id).count()
    print(f"[{b.subject.value}] {b.title}")
    print(f"  - 강의: {lessons}강")
    print(f"  - 상태: {b.parse_status.value}")
    print()

db.close()
