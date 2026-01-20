import sys
sys.path.insert(0, 'api')

from app.db.session import get_db
from app.db.models import Book, Lesson

db = next(get_db())

lit = db.query(Book).filter(Book.book_id == 'book_korean_2026_수능특강_문학_3de620').first()
eng = db.query(Book).filter(Book.book_id == 'book_english_2026_수능특강_영어_ef786c').first()

lit_lessons = db.query(Lesson).filter(Lesson.book_id == lit.book_id).count()
eng_lessons = db.query(Lesson).filter(Lesson.book_id == eng.book_id).count()

print(f'문학: {lit.parse_status.value:12s} - {lit_lessons:2d} 강의')
print(f'영어: {eng.parse_status.value:12s} - {eng_lessons:2d} 강의')
