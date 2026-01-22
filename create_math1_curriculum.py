"""
수학Ⅰ 교재 목차 기반 커리큘럼 생성
45개 강의 + 각 강의당 더미 문제 1개
"""
import sys
import json
sys.path.insert(0, 'api')

from app.db.session import SessionLocal
from app.db.models import Book, Lesson, Unit, UnitType, Subject, ParseStatus
import uuid
from datetime import datetime

# 45개 강의 목차
LECTURES = [
    # Part I. 지수함수와 로그함수 – 개념·유제
    {"num": 1, "title": "지수와 로그 개념·예제·유제 (1)"},
    {"num": 2, "title": "지수와 로그 개념·예제·유제 (2)"},
    {"num": 3, "title": "지수와 로그 개념·예제·유제 (3)"},
    {"num": 4, "title": "지수와 로그 개념·예제·유제 (4)"},

    # Part II. 지수함수와 로그함수 – 기본 문제(Level 1~3)
    {"num": 5, "title": "지수와 로그 Level 1 (고3 기본)"},
    {"num": 6, "title": "지수와 로그 Level 2 (1)"},
    {"num": 7, "title": "지수와 로그 Level 2 (2)"},
    {"num": 8, "title": "지수와 로그 Level 3"},

    # Part III. 지수함수·로그함수 개념 정리
    {"num": 9, "title": "지수함수와 로그함수 개념·예제 (1)"},
    {"num": 10, "title": "지수함수와 로그함수 개념·예제 (2)"},
    {"num": 11, "title": "지수함수와 로그함수 개념·예제 (3)"},
    {"num": 12, "title": "지수함수와 로그함수 개념·예제 (4)"},

    # Part IV. 지수함수·로그함수 심화(Level)
    {"num": 13, "title": "지수함수와 로그함수 Level 1"},
    {"num": 14, "title": "지수함수와 로그함수 Level 2 (1)"},
    {"num": 15, "title": "지수함수와 로그함수 Level 2 (2)"},
    {"num": 16, "title": "지수함수와 로그함수 Level 2 (3)"},

    # Part V. 삼각함수 – 개념·예제·유제
    {"num": 17, "title": "삼각함수 개념·예제·유제 (1)"},
    {"num": 18, "title": "삼각함수 개념·예제·유제 (2)"},
    {"num": 19, "title": "삼각함수 개념·예제·유제 (3)"},
    {"num": 20, "title": "삼각함수 개념·예제·유제 (4)"},

    # Part VI. 삼각함수 – 기본 문제(Level)
    {"num": 21, "title": "삼각함수 Level 1"},
    {"num": 22, "title": "삼각함수 Level 2 (1)"},
    {"num": 23, "title": "삼각함수 Level 2 (2)"},
    {"num": 24, "title": "삼각함수 Level 3 (1)"},
    {"num": 25, "title": "삼각함수 Level 3 (2) – 사인법칙·코사인법칙"},

    # Part VII. 사인법칙·코사인법칙
    {"num": 26, "title": "사인법칙·코사인법칙 개념·예제 (1)"},
    {"num": 27, "title": "사인법칙·코사인법칙 개념·예제 (2)"},
    {"num": 28, "title": "사인법칙·코사인법칙 개념·예제 (3)"},
    {"num": 29, "title": "사인법칙·코사인법칙 Level 1"},
    {"num": 30, "title": "사인법칙·코사인법칙 Level 2"},
    {"num": 31, "title": "사인법칙·코사인법칙 Level 3"},

    # Part VIII. 등차·등비수열
    {"num": 32, "title": "등차수열·등비수열 개념·예제 (1)"},
    {"num": 33, "title": "등차수열·등비수열 개념·예제 (2)"},
    {"num": 34, "title": "등차수열·등비수열 Level 1"},
    {"num": 35, "title": "등차수열·등비수열 Level 2 (1)"},
    {"num": 36, "title": "등차수열·등비수열 Level 2 (2)"},

    # Part IX. 수열의 합과 수학적 귀납법
    {"num": 37, "title": "수열의 합과 수학적 귀납법 개념 (1)"},
    {"num": 38, "title": "수열의 합과 수학적 귀납법 개념 (2)"},
    {"num": 39, "title": "수열의 합과 수학적 귀납법 개념 (3)"},
    {"num": 40, "title": "수열의 합과 수학적 귀납법 개념 (4)"},
    {"num": 41, "title": "수열의 합과 수학적 귀납법 Level 1"},
    {"num": 42, "title": "수열의 합과 수학적 귀납법 Level 2"},
    {"num": 43, "title": "수열의 합과 수학적 귀납법 Level 3"},

    # Part X. 실전·종합
    {"num": 44, "title": "수열의 합과 수학적 귀납법 종합 문제"},
    {"num": 45, "title": "2025학년도 대비 – 대수능 분석"},
]

BOOK_ID = f'book_math1_2026_수능특강_수학1_{uuid.uuid4().hex[:6]}'

def create_curriculum():
    """강의와 문제 생성"""
    db = SessionLocal()

    try:
        # Book이 있는지 확인, 없으면 생성
        book = db.query(Book).filter(
            Book.title.like('%수학%'),
            Book.subject == Subject.MATH
        ).first()

        if not book:
            print("수학1 교재 생성 중...")
            book = Book(
                book_id=BOOK_ID,
                title="2026 수능특강 수학Ⅰ",
                subject=Subject.MATH,
                year=2026,
                file_path=f"uploads/{BOOK_ID}.pdf",
                parse_status=ParseStatus.DONE,
            )
            db.add(book)
            db.commit()
            print(f"교재 생성 완료: {BOOK_ID}")
        else:
            print(f"기존 교재 사용: {book.book_id}")

        book_id = book.book_id

        # 기존 Lesson, Unit 삭제
        print("기존 데이터 삭제 중...")
        db.query(Unit).filter(Unit.lesson_id.like('lesson_math1_%')).delete(synchronize_session=False)
        db.query(Lesson).filter(Lesson.book_id == book_id).delete(synchronize_session=False)
        db.commit()

        print(f"\n{len(LECTURES)}개 강의 생성 중...\n")

        for lec in LECTURES:
            lesson_num = lec['num']
            lesson_id = f"lesson_math1_{lesson_num:02d}"

            # Lesson 생성
            lesson = Lesson(
                lesson_id=lesson_id,
                book_id=book_id,
                index=lesson_num,
                title=f"{lesson_num}강 {lec['title']}",
            )
            db.add(lesson)
            db.flush()

            # 개념 Unit 1개 (더미)
            concept_unit = Unit(
                unit_id=f"u_{uuid.uuid4().hex[:12]}",
                lesson_id=lesson_id,
                type=UnitType.CONCEPT_CORE,
                order=0,
                title=f"{lesson_num}강 핵심 개념",
                content_text=f"[{lesson_num}강] {lec['title']}\n\n이 강의의 핵심 내용을 학습합니다.",
            )
            db.add(concept_unit)

            # 문제 Unit 1개 (더미)
            question_unit = Unit(
                unit_id=f"u_{uuid.uuid4().hex[:12]}",
                lesson_id=lesson_id,
                type=UnitType.QUESTION,
                order=1,
                title=f"{lesson_num}강 연습 문제",
                content_text=f"다음 문제를 풀어보세요.",
                question_stem=f"[{lesson_num}강 연습 문제]\n\n다음 중 옳은 것은?",
                question_choices=json.dumps({
                    "1": "log₂8 = 3",
                    "2": "2³ = 6",
                    "3": "sin 0° = 1",
                    "4": "cos 90° = 1",
                    "5": "등차수열의 공차는 항상 양수이다."
                }),
                question_answer=1,
            )
            db.add(question_unit)

            if lesson_num % 10 == 0:
                print(f"  진행: {lesson_num}/45 강의 완료...")

        db.commit()

        print(f"\n완료!")
        print(f"  - 생성된 강의: 45개")
        print(f"  - 생성된 개념: 45개")
        print(f"  - 생성된 문제: 45개")

        # lectures.json 생성
        import os
        lectures_dir = 'api/data/math1/lectures'
        os.makedirs(lectures_dir, exist_ok=True)

        lectures_json = [
            {
                "lecture_id": lec['num'],
                "title": f"{lec['num']}강 {lec['title']}"
            }
            for lec in LECTURES
        ]

        with open(f'{lectures_dir}/lectures.json', 'w', encoding='utf-8') as f:
            json.dump(lectures_json, f, ensure_ascii=False, indent=2)

        print(f"\nlectures.json 저장 완료")

        # Book 상태 업데이트
        book.parse_status = ParseStatus.DONE
        db.commit()
        print(f"교재 상태 DONE으로 업데이트")

    except Exception as e:
        db.rollback()
        print(f"\n에러: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == '__main__':
    create_curriculum()
