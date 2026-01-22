import sys
import json
sys.path.insert(0, 'api')

from app.db.session import SessionLocal
from app.db.models import Unit

db = SessionLocal()

units = db.query(Unit).filter(Unit.lesson_id == 'lesson_literature_01').order_by(Unit.order).all()

print(f"1강 유닛 수: {len(units)}\n")

for u in units:
    print(f"{u.order}. [{u.type.value}] {u.title}")
    print(f"   content_text 길이: {len(u.content_text) if u.content_text else 0}자")

    if u.question_stem:
        print(f"   question_stem 길이: {len(u.question_stem)}자")
        print(f"   question_answer: {u.question_answer}")

    if u.ai_explanation:
        print(f"   ai_explanation: {u.ai_explanation[:50]}...")

    if u.content_image_paths:
        images = json.loads(u.content_image_paths)
        print(f"   이미지: {images}")

    print()

db.close()
