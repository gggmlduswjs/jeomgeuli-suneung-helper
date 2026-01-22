"""
문학 1강 실제 데이터 연동
- 개념 (이미지 포함)
- 본문 - 박두진 「해」 (이미지 포함)
- 문제 3개 (이미지 포함)
- 단원요약 (점자키워드 3개)
"""
import sys
import json
sys.path.insert(0, 'api')

from app.db.session import SessionLocal
from app.db.models import Lesson, Unit, UnitType
import uuid

# 1강 데이터
LESSON_ID = "lesson_literature_01"

# 개념 섹션 데이터
CONCEPT_DATA = {
    "title": "시의 표현과 형식",
    "sections": [
        {
            "subtitle": "(1) 시적 표현의 개념",
            "content": """형상화 • 시의 주제나 화자의 정서를 형상화하는 데 기여하는 일체의 언어적 표현을 가리킴.
• 비유, 상징, 역설, 반어, 대구, 반복, 설의, 영탄, 도치, 열거, 점층, 우의, 풍자, 병렬 등의 표현 기법이 있음.

정서나 교훈, 삶의 이치 등과 같이 분명한 형체로 나타나 있지 않은 것을 다양한 방법이나 매체를 통해 구체적이고 실감 나게 그려 내는 것을 뜻한다.""",
            "image_path": "data/literature/concepts_images/concept_p08_01.png"
        },
        {
            "subtitle": "(2) 시적 표현의 여러 가지 효과",
            "content": """• 음악적인 리듬이 느껴지게 함.
• 시어의 함축성을 높여 의미를 풍부하게 함.
• 어떤 대상을 감각적으로 연상하게 함.
• 상식적인 생각을 뒤집거나 깨뜨림으로써 지적 충격을 줌.
• 재미를 느끼고 웃게 하거나 반대로 슬픈 감정을 환기하게 함.
• 일상적인 표현에 변화를 가하여 말의 묘미를 느끼게 함.
• 화자의 사고나 감정, 상황 등을 강조하거나 부각함.""",
            "image_path": "data/literature/concepts_images/concept_p08_02.png"
        }
    ]
}

# 본문 - 박두진 「해」
PASSAGE_DATA = {
    "title": "박두진, 「해」",
    "content": """해야 솟아라. 해야 솟아라. 말갛게 씻은 얼굴 고운 해야 솟아라.
산 넘어 산 넘어서 어둠을 살라 먹고,
산 넘어서 밤새도록 어둠을 살라 먹고,
이글이글 앳된 얼굴 고운 해야 솟아라.

달밤이 싫어, 달밤이 싫어, 눈물 같은 골짜기에 달밤이 싫어,
아무도 없는 뜰에 달밤이 나는 싫어……,
해야, 고운 해야. 늬가 오면 늬가사 오면,
나는 나는 청산이 좋아라. 훨훨훨 깃을 치는 청산이 좋아라.
청산이 있으면 홀로래도 좋아라.

사슴을 따라, 사슴을 따라, 양지로 양지로 사슴을 따라
사슴을 만나면 사슴과 놀고,
칡범을 따라 칡범을 따라
칡범을 만나면 칡범과 놀고, ……

해야, 고운 해야. 해야 솟아라. 꿈이 아니래도 너를 만나면,
꽃도 새도 짐승도 한자리 앉아, 워어이 워어이 모두 불러 한자리 앉아
앳되고 고운 날을 누려 보리라.

- 박두진, 「해」""",
    "image_path": "data/literature/content_images/content_p09_01.png"
}

# 문제 3개
PROBLEMS = [
    {
        "number": 1,
        "stem": "윗글을 이해한 내용으로 적절하지 않은 것은?",
        "choices": {
            "1": "화자는 '해'가 뜨기를 간절히 바라고 있다.",
            "2": "화자는 '달밤'보다 햇빛이 가득한 낮을 더 선호한다.",
            "3": "화자는 '청산'에서 자유롭고 평화로운 삶을 누리고 싶어 한다.",
            "4": "화자는 '해'가 뜨면 모든 생명체와 조화롭게 지낼 수 있다고 생각한다.",
            "5": "화자는 '사슴'과 '칡범'을 두려워하며 피하려고 한다."
        },
        "answer": 5,
        "explanation": "화자는 '사슴을 만나면 사슴과 놀고, 칡범을 만나면 칡범과 놀고'라고 하여 이들과 함께 노는 모습을 그리고 있습니다. 따라서 이들을 두려워하거나 피하려는 것이 아닙니다.",
        "image_path": "data/literature/problems_images/problem_p09_01.png"
    },
    {
        "number": 2,
        "stem": "이 시의 표현상 특징으로 가장 적절한 것은?",
        "choices": {
            "1": "의성어와 의태어를 활용하여 생동감을 부여하고 있다.",
            "2": "대조적인 시어를 활용하여 주제를 부각하고 있다.",
            "3": "과거와 현재를 넘나들며 시상을 전개하고 있다.",
            "4": "계절의 변화를 통해 시간의 흐름을 드러내고 있다.",
            "5": "특정 시어를 반복하여 강조하고 있다."
        },
        "answer": 5,
        "explanation": "'해야 솟아라', '해야, 고운 해야' 등 '해'와 관련된 시어를 반복적으로 사용하여 화자의 염원을 강조하고 있습니다.",
        "image_path": "data/literature/problems_images/problem_p10_02.png"
    },
    {
        "number": 3,
        "stem": "<보기>를 참고하여 윗글을 감상한 내용으로 적절하지 않은 것은?",
        "context": """<보기>
이 시는 광복 직전인 일제 강점기 말에 쓰인 작품으로, 암울한 시대 상황 속에서 밝은 미래에 대한 희망을 노래하고 있다. 화자가 간절히 바라는 '해'는 광복을 상징하며, '달밤'은 일제의 억압을 의미한다고 볼 수 있다.""",
        "choices": {
            "1": "'해'는 광복이라는 밝은 미래를 상징하는군.",
            "2": "'달밤'은 일제 강점기의 암울한 현실을 의미하는군.",
            "3": "'청산'은 광복 이후 누릴 자유로운 삶의 공간을 뜻하는군.",
            "4": "'어둠을 살라 먹고'는 일제의 억압을 물리치는 모습을 표현한 것이군.",
            "5": "'앳되고 고운 날'은 일제 강점기 이전의 과거 시절을 그리워하는 것이군."
        },
        "answer": 5,
        "explanation": "'앳되고 고운 날'은 과거를 그리워하는 것이 아니라, 광복 이후 누릴 밝고 아름다운 미래를 의미합니다.",
        "image_path": "data/literature/problems_images/problem_p10_03.png"
    }
]

# 단원 요약 - 점자키워드 3개
SUMMARY_DATA = {
    "title": "1강 핵심 요약",
    "content": """이 강의에서는 시의 표현과 형식에 대해 학습했습니다.

주요 학습 내용:
• 시적 표현의 개념과 효과
• 시의 형식과 구조
• 실제 작품(박두진 「해」) 분석

작품 「해」는 광복 직전 일제 강점기 말에 쓰인 작품으로, 암울한 시대 상황 속에서 밝은 미래(광복)에 대한 간절한 염원을 노래하고 있습니다.""",
    "braille_keywords": [
        "시적표현",
        "형상화기법",
        "광복염원"
    ]
}

def update_lesson_01():
    """1강 실제 데이터로 업데이트"""
    db = SessionLocal()

    try:
        # 기존 1강 유닛 삭제
        print("기존 1강 유닛 삭제 중...")
        db.query(Unit).filter(Unit.lesson_id == LESSON_ID).delete(synchronize_session=False)
        db.commit()

        print(f"\n1강 실제 데이터 생성 중...\n")

        # 1. 개념 유닛 생성 (2개 섹션 통합)
        concept_content = f"{CONCEPT_DATA['title']}\n\n"
        for i, section in enumerate(CONCEPT_DATA['sections']):
            concept_content += f"{section['subtitle']}\n{section['content']}\n\n"

        concept_unit = Unit(
            unit_id=f"u_{uuid.uuid4().hex[:12]}",
            lesson_id=LESSON_ID,
            type=UnitType.CONCEPT_CORE,
            order=0,
            title="시의 표현과 형식 - 핵심 개념",
            content_text=concept_content.strip(),
            content_image_paths=json.dumps([
                CONCEPT_DATA['sections'][0]['image_path'],
                CONCEPT_DATA['sections'][1]['image_path']
            ])
        )
        db.add(concept_unit)
        print("  [OK] 개념 유닛 생성")

        # 2. 본문 유닛 생성 (PASSAGE)
        passage_unit = Unit(
            unit_id=f"u_{uuid.uuid4().hex[:12]}",
            lesson_id=LESSON_ID,
            type=UnitType.PASSAGE,
            order=1,
            title=PASSAGE_DATA['title'],
            content_text=PASSAGE_DATA['content'],
            content_image_paths=json.dumps([PASSAGE_DATA['image_path']])
        )
        db.add(passage_unit)
        print("  [OK] 본문 유닛 생성 (박두진 「해」)")

        # 3. 문제 유닛 3개 생성
        for i, problem in enumerate(PROBLEMS):
            question_stem = problem['stem']
            if 'context' in problem:
                question_stem = f"{problem['context']}\n\n{problem['stem']}"

            question_unit = Unit(
                unit_id=f"u_{uuid.uuid4().hex[:12]}",
                lesson_id=LESSON_ID,
                type=UnitType.QUESTION,
                order=2 + i,
                title=f"문제 {problem['number']}",
                content_text=PASSAGE_DATA['content'],  # 지문은 본문 재사용
                question_stem=question_stem,
                question_choices=json.dumps(problem['choices']),
                question_answer=problem['answer'],
                ai_explanation=problem['explanation'],
                content_image_paths=json.dumps([problem['image_path']])
            )
            db.add(question_unit)
            print(f"  [OK] 문제 {problem['number']} 유닛 생성")

        # 4. 단원 요약 유닛 생성 (점자키워드 포함)
        summary_unit = Unit(
            unit_id=f"u_{uuid.uuid4().hex[:12]}",
            lesson_id=LESSON_ID,
            type=UnitType.CONCEPT_SUMMARY,
            order=5,
            title=SUMMARY_DATA['title'],
            content_text=SUMMARY_DATA['content'],
            braille_keywords=json.dumps(SUMMARY_DATA['braille_keywords'], ensure_ascii=False)
        )
        db.add(summary_unit)
        print("  [OK] 단원 요약 유닛 생성 (점자키워드 3개)")

        db.commit()

        print(f"\n완료!")
        print(f"  - 개념: 1개")
        print(f"  - 본문: 1개")
        print(f"  - 문제: 3개")
        print(f"  - 요약: 1개")
        print(f"  총 6개 유닛 생성")

        # 검증
        units = db.query(Unit).filter(Unit.lesson_id == LESSON_ID).all()
        print(f"\n[검증] 1강 유닛 {len(units)}개:")
        for u in units:
            print(f"  - [{u.type.value}] {u.title}")
            if u.type == UnitType.CONCEPT_SUMMARY and u.braille_keywords:
                keywords = json.loads(u.braille_keywords)
                print(f"    점자키워드: {', '.join(keywords)}")

    except Exception as e:
        db.rollback()
        print(f"\n에러: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == '__main__':
    update_lesson_01()
