"""간단한 DB 확인 (인코딩 문제 없음)"""
import sys
from pathlib import Path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "api"))
from app.db.session import SessionLocal
from app.db.models import Lesson, Unit, Book

db = SessionLocal()
book = db.query(Book).filter(Book.title.like('%수능특강%')).first()
if book:
    lessons = db.query(Lesson).filter(Lesson.book_id == book.book_id).count()
    units = db.query(Unit).join(Lesson).filter(Lesson.book_id == book.book_id).count()
    print(f"Book: {book.book_id}")
    print(f"Lessons: {lessons}")
    print(f"Units: {units}")
db.close()
