import sys
import json
sys.path.insert(0, 'api')

from app.db.session import SessionLocal
from app.db.models import Lesson, Unit

db = SessionLocal()

# Check literature lesson 1
lesson = db.query(Lesson).filter(Lesson.lesson_id == 'lesson_literature_01').first()
units = db.query(Unit).filter(Unit.lesson_id == 'lesson_literature_01').all()

print(f"Lesson: {lesson.title}")
print(f"Units: {len(units)}")
for u in units:
    print(f"  - [{u.type.value}] {u.title}")
    if u.type.value == 'QUESTION':
        choices = json.loads(u.question_choices) if u.question_choices else {}
        print(f"    Question: {u.question_stem[:50]}...")
        print(f"    Answer: {u.question_answer}, Choices: {len(choices)}")

# Check English lesson 1
print("\n" + "="*50 + "\n")
lesson = db.query(Lesson).filter(Lesson.lesson_id == 'lesson_english_01').first()
units = db.query(Unit).filter(Unit.lesson_id == 'lesson_english_01').all()

print(f"Lesson: {lesson.title}")
print(f"Units: {len(units)}")
for u in units:
    print(f"  - [{u.type.value}] {u.title}")
    if u.type.value == 'QUESTION':
        choices = json.loads(u.question_choices) if u.question_choices else {}
        print(f"    Question: {u.question_stem[:50]}...")
        print(f"    Answer: {u.question_answer}, Choices: {len(choices)}")

db.close()
print("\nVerification complete!")
