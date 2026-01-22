"""
영어 교재 목차 기반 커리큘럼 생성
33개 강의 + 각 강의당 더미 문제 1개
"""
import sys
import json
sys.path.insert(0, 'api')

from app.db.session import SessionLocal
from app.db.models import Book, Lesson, Unit, UnitType, Subject, ParseStatus
import uuid

# 33개 강의 목차 (사용자 제공)
LECTURES = [
    # Part I. 유형편
    {"num": 1, "title": "글의 목적 파악", "page": 10},
    {"num": 2, "title": "심경·분위기 파악", "page": 16},
    {"num": 3, "title": "요지 파악", "page": 20},
    {"num": 4, "title": "주장 파악", "page": 26},
    {"num": 5, "title": "함축적 의미 파악", "page": 32},
    {"num": 6, "title": "주제 파악", "page": 38},
    {"num": 7, "title": "제목 파악", "page": 44},
    {"num": 8, "title": "도표 정보 파악", "page": 50},
    {"num": 9, "title": "내용 일치·불일치 (설명문)", "page": 56},
    {"num": 10, "title": "내용 일치·불일치 (실용문)", "page": 60},
    {"num": 11, "title": "어법 정확성 파악", "page": 66},
    {"num": 12, "title": "어휘 적절성 파악", "page": 70},
    {"num": 13, "title": "빈칸 내용 추론 (1)", "page": 74},
    {"num": 14, "title": "빈칸 내용 추론 (2)", "page": 80},
    {"num": 15, "title": "흐름에 무관한 문장 찾기", "page": 86},
    {"num": 16, "title": "문단 내 글의 순서 파악하기", "page": 90},
    {"num": 17, "title": "주어진 문장의 적합한 위치 찾기", "page": 98},
    {"num": 18, "title": "문단 요약하기", "page": 104},
    {"num": 19, "title": "장문 독해 (1)", "page": 110},
    {"num": 20, "title": "장문 독해 (2)", "page": 116},

    # Part II. 주제·소재편
    {"num": 21, "title": "철학·종교·역사·풍습·지리", "page": 128},
    {"num": 22, "title": "환경·자원·재활용", "page": 132},
    {"num": 23, "title": "물리·화학·생명과학·지구과학", "page": 136},
    {"num": 24, "title": "스포츠·레저·취미·여행", "page": 140},
    {"num": 25, "title": "교육·학교·진로", "page": 144},
    {"num": 26, "title": "언어·문학·예술", "page": 148},
    {"num": 27, "title": "컴퓨터·인터넷·정보·미디어·교통", "page": 152},
    {"num": 28, "title": "심리·대인 관계", "page": 156},
    {"num": 29, "title": "정치·경제·사회·법", "page": 160},
    {"num": 30, "title": "의학·건강·영양·식품", "page": 164},

    # Part III. 테스트편
    {"num": 31, "title": "Test 1", "page": 170},
    {"num": 32, "title": "Test 2", "page": 192},
    {"num": 33, "title": "Test 3", "page": 214},
]

BOOK_ID = 'book_english_2026_수능특강_영어_ef786c'

def create_curriculum():
    """강의와 문제 생성"""
    db = SessionLocal()

    try:
        # Book 생성 또는 가져오기
        book = db.query(Book).filter(Book.book_id == BOOK_ID).first()
        if not book:
            print("영어 교재 생성 중...")
            book = Book(
                book_id=BOOK_ID,
                title="2026 수능특강 영어",
                subject=Subject.ENGLISH,
                year=2026,
                file_path=f"uploads/{BOOK_ID}.pdf",
                parse_status=ParseStatus.DONE,
            )
            db.add(book)
            db.commit()
            print(f"교재 생성 완료: {BOOK_ID}")
        else:
            print(f"기존 교재 사용: {BOOK_ID}")

        # 기존 Lesson, Unit 삭제
        print("기존 데이터 삭제 중...")
        db.query(Unit).filter(Unit.lesson_id.like('lesson_english_%')).delete(synchronize_session=False)
        db.query(Lesson).filter(Lesson.book_id == BOOK_ID).delete(synchronize_session=False)
        db.commit()

        print(f"\n{len(LECTURES)}개 강의 생성 중...\n")

        for lec in LECTURES:
            lesson_num = lec['num']
            lesson_id = f"lesson_english_{lesson_num:02d}"

            # Lesson 생성
            lesson = Lesson(
                lesson_id=lesson_id,
                book_id=BOOK_ID,
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
                content_text=f"[{lesson_num}강] {lec['title']}\n\nThis lesson covers key concepts and strategies.",
            )
            db.add(concept_unit)

            # 문제 Unit 1개 (더미)
            question_unit = Unit(
                unit_id=f"u_{uuid.uuid4().hex[:12]}",
                lesson_id=lesson_id,
                type=UnitType.QUESTION,
                order=1,
                title=f"{lesson_num}강 연습 문제",
                content_text=f"Read the following passage and answer the question.",
                question_stem=f"[{lesson_num}강 Practice Question]\n\nWhat is the main idea of this passage?",
                question_choices=json.dumps({
                    "1": "The importance of education",
                    "2": "The role of technology",
                    "3": "Environmental concerns",
                    "4": "Social relationships",
                    "5": "Economic development"
                }),
                question_answer=1,
            )
            db.add(question_unit)

            if lesson_num % 10 == 0:
                print(f"  진행: {lesson_num}/33 강의 완료...")

        db.commit()

        print(f"\n완료!")
        print(f"  - 생성된 강의: 33개")
        print(f"  - 생성된 개념: 33개")
        print(f"  - 생성된 문제: 33개")

        # lectures.json 생성
        lectures_json = [
            {
                "lecture_id": lec['num'],
                "title": f"{lec['num']}강 {lec['title']}",
                "page": lec['page']
            }
            for lec in LECTURES
        ]

        with open('api/data/english/lectures/lectures.json', 'w', encoding='utf-8') as f:
            json.dump(lectures_json, f, ensure_ascii=False, indent=2)

        print(f"\nlectures.json 저장 완료")

        # Book 상태 업데이트
        book = db.query(Book).filter(Book.book_id == BOOK_ID).first()
        if book:
            book.parse_status = ParseStatus.DONE
            db.commit()
            print(f"[OK] 교재 상태 DONE으로 업데이트")

    except Exception as e:
        db.rollback()
        print(f"\n에러: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == '__main__':
    create_curriculum()
