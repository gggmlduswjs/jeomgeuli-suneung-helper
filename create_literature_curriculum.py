"""
문학 교재 목차 기반 커리큘럼 생성
80개 강의 + 각 강의당 더미 문제 1개
"""
import sys
import json
sys.path.insert(0, 'api')

from app.db.session import SessionLocal
from app.db.models import Book, Lesson, Unit, UnitType, Subject, ParseStatus
import uuid

# 80개 강의 목차 (사용자 제공)
LECTURES = [
    # Part I. 교과서 개념 학습
    {"num": 1, "title": "시의 표현과 형식 - 해(박도진)", "page": 9},
    {"num": 2, "title": "시의 내용 - 마흔 여덟에~ / 노인이 전하는 말~", "page": 12},
    {"num": 3, "title": "소설의 서술상 특징 - 운수 좋은 날", "page": 15},
    {"num": 4, "title": "소설의 내용 구성 요소 - 전우치전", "page": 19},
    {"num": 5, "title": "극의 특성과 극문학의 구성 요소 - 고등학생", "page": 24},
    {"num": 6, "title": "고전 문학의 특징과 구성 요소 - 차마설", "page": 29},
    {"num": 7, "title": "작품의 작가 및 독자 맥락 - 사랑손님과 어머니", "page": 32},
    {"num": 8, "title": "작품의 문맥적 상호 텍스트적 맥락 - 불편한 편의점", "page": 36},
    {"num": 9, "title": "작품의 사회문화적 역사적 맥락 - 당신을 보았습니다", "page": 41},

    # Part II. 적용 학습 - 고전 시가
    {"num": 10, "title": "모죽지랑가(득오) / 화왕가", "page": 44},
    {"num": 11, "title": "정과정곡 / 사모곡 중 <서경전사전>", "page": 46},
    {"num": 12, "title": "가시리 / 거문고 노래 / 공무도하가", "page": 49},
    {"num": 13, "title": "사미인곡 / 속미인곡", "page": 51},
    {"num": 14, "title": "오우가 / 선상탄", "page": 53},
    {"num": 15, "title": "복수자", "page": 56},
    {"num": 16, "title": "용부가", "page": 60},
    {"num": 17, "title": "동아 / 동명왕편", "page": 64},
    {"num": 18, "title": "나물 캐는 노래 / 사동사리 / 사랑을 찾는 해성", "page": 67},
    {"num": 19, "title": "호산가 / 장자부사", "page": 70},
    {"num": 20, "title": "잠령민요 / 우국가", "page": 74},

    # Part III. 적용 학습 - 현대시
    {"num": 21, "title": "그날이 오면 / 산상의 노래", "page": 77},
    {"num": 22, "title": "황혼 / 서시", "page": 80},
    {"num": 23, "title": "봉산탈춤 / 꽃", "page": 83},
    {"num": 24, "title": "달 / 포도 / 잎새 / 아침", "page": 86},
    {"num": 25, "title": "희망의 거처", "page": 89},
    {"num": 26, "title": "역사(신작시) / 지리와 파국", "page": 92},
    {"num": 27, "title": "전라도 가시내", "page": 95},
    {"num": 28, "title": "병원", "page": 98},
    {"num": 29, "title": "눈물", "page": 100},
    {"num": 30, "title": "파랑 가에서", "page": 103},
    {"num": 31, "title": "춤", "page": 106},

    # Part IV. 적용 학습 - 고전 산문
    {"num": 32, "title": "나혜석이 선생부곡 답답박사", "page": 109},
    {"num": 33, "title": "채생기우", "page": 113},
    {"num": 34, "title": "김진옥전", "page": 117},
    {"num": 35, "title": "숙향전", "page": 121},
    {"num": 36, "title": "정진사전", "page": 125},
    {"num": 37, "title": "강도몽유록", "page": 129},
    {"num": 38, "title": "옥소전", "page": 133},
    {"num": 39, "title": "춘향전", "page": 137},
    {"num": 40, "title": "수궁가", "page": 141},
    {"num": 41, "title": "심청전", "page": 146},
    {"num": 42, "title": "지봉전", "page": 151},

    # Part V. 적용 학습 - 현대 소설
    {"num": 43, "title": "무정", "page": 155},
    {"num": 44, "title": "날개", "page": 159},
    {"num": 45, "title": "태평천하", "page": 163},
    {"num": 46, "title": "사수", "page": 167},
    {"num": 47, "title": "편편이 춤춘다", "page": 171},
    {"num": 48, "title": "하산", "page": 175},
    {"num": 49, "title": "활화산 심층", "page": 179},
    {"num": 50, "title": "탐욕", "page": 184},
    {"num": 51, "title": "벌목사무처", "page": 188},
    {"num": 52, "title": "서울 사는 뜬금", "page": 192},
    {"num": 53, "title": "세월 사는 뜬금", "page": 196},

    # Part VI. 적용 학습 - 극·수필
    {"num": 54, "title": "강 건너 동네 / 강물 탐승", "page": 200},
    {"num": 55, "title": "겨울일기", "page": 204},
    {"num": 56, "title": "해무 / 소나기", "page": 207},
    {"num": 57, "title": "아사달이 아리랑 / 아비", "page": 211},
    {"num": 58, "title": "산문 / 서설", "page": 214},
    {"num": 59, "title": "추억의 사물들", "page": 219},
    {"num": 60, "title": "동주", "page": 223},
    {"num": 61, "title": "우리들의 블루스", "page": 227},

    # Part VII. 갈래 복합
    {"num": 62, "title": "한계사의 노스탤지어 / 소학지", "page": 232},
    {"num": 63, "title": "일제강점기 미상 / 침바람", "page": 237},
    {"num": 64, "title": "새벽 속의 희미함 / 오오랑과 설악의 재회", "page": 243},
    {"num": 65, "title": "동전 / 금오신화", "page": 249},
    {"num": 66, "title": "화전가 / 역옹록담화록 / 병에 걸린 무사", "page": 255},
    {"num": 67, "title": "남신의 죽음 / 내 영혼의 봄날", "page": 262},
    {"num": 68, "title": "경서재목록 / 거울과 물의 대화", "page": 267},
    {"num": 69, "title": "감나무 그늘 아래 / 수묵 풍경 / 창밖의 소수 여행", "page": 272},
    {"num": 70, "title": "광화문, 겨울, 물빛, 나무 / 화이트", "page": 277},
    {"num": 71, "title": "현대 소설에서 서술자의 특성과 효과", "page": 283},
    {"num": 72, "title": "내 그물로 오는 가시고기", "page": 289},

    # Part VIII. 실전 학습
    {"num": 73, "title": "1회 [01-04] 정복력", "page": 296},
    {"num": 74, "title": "1회 [05-10] 출제 구조 / 문항 유형", "page": 300},
    {"num": 75, "title": "1회 [11-14] 독해를 가르는 기준", "page": 306},
    {"num": 76, "title": "1회 [15-17] 그 특성 하나로 길을 찾다", "page": 310},
    {"num": 77, "title": "2회 [01-04] 조율", "page": 312},
    {"num": 78, "title": "2회 [05-10] 상상력의 확장", "page": 317},
    {"num": 79, "title": "2회 [11-14] 상대성 인식", "page": 321},
    {"num": 80, "title": "2회 [15-17] 공감과 거리 두기", "page": 326},
]

BOOK_ID = 'book_korean_2026_수능특강_문학_3de620'

def create_curriculum():
    """강의와 문제 생성"""
    db = SessionLocal()

    try:
        # Book 생성 또는 가져오기
        book = db.query(Book).filter(Book.book_id == BOOK_ID).first()
        if not book:
            print("문학 교재 생성 중...")
            book = Book(
                book_id=BOOK_ID,
                title="2026 수능특강 문학",
                subject=Subject.KOREAN,
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
        db.query(Unit).filter(Unit.lesson_id.like('lesson_literature_%')).delete(synchronize_session=False)
        db.query(Lesson).filter(Lesson.book_id == BOOK_ID).delete(synchronize_session=False)
        db.commit()

        print(f"\n{len(LECTURES)}개 강의 생성 중...\n")

        for lec in LECTURES:
            lesson_num = lec['num']
            lesson_id = f"lesson_literature_{lesson_num:02d}"

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
                content_text=f"다음 작품을 읽고 물음에 답하시오.",
                question_stem=f"[{lesson_num}강 연습 문제]\n\n다음 중 이 작품의 특징으로 적절한 것은?",
                question_choices=json.dumps({
                    "1": "화자의 정서가 드러난다.",
                    "2": "비유적 표현이 사용되었다.",
                    "3": "시대적 배경이 나타난다.",
                    "4": "인물의 심리가 묘사된다.",
                    "5": "갈등 구조가 드러난다."
                }),
                question_answer=1,
            )
            db.add(question_unit)

            if lesson_num % 10 == 0:
                print(f"  진행: {lesson_num}/80 강의 완료...")

        db.commit()

        print(f"\n✓ 완료!")
        print(f"  - 생성된 강의: 80개")
        print(f"  - 생성된 개념: 80개")
        print(f"  - 생성된 문제: 80개")

        # lectures.json 생성
        lectures_json = [
            {
                "lecture_id": lec['num'],
                "title": f"{lec['num']}강 {lec['title']}",
                "page": lec['page']
            }
            for lec in LECTURES
        ]

        with open('api/data/literature/lectures/lectures.json', 'w', encoding='utf-8') as f:
            json.dump(lectures_json, f, ensure_ascii=False, indent=2)

        print(f"\n✓ lectures.json 저장 완료")

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
