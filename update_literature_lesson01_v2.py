"""
문학 1강 실제 데이터 연동 v2
이미지 개수대로 유닛 구성
"""
import sys
import json
sys.path.insert(0, 'api')

from app.db.session import SessionLocal
from app.db.models import Lesson, Unit, UnitType
import uuid

LESSON_ID = "lesson_literature_01"

# 유닛 데이터 (이미지 개수대로 분리)
UNITS = [
    # 1. 개념 섹션 1
    {
        "type": UnitType.CONCEPT_CORE,
        "order": 0,
        "title": "시적 표현의 개념",
        "content_text": """형상화 • 시의 주제나 화자의 정서를 형상화하는 데 기여하는 일체의 언어적 표현을 가리킴.
• 비유, 상징, 역설, 반어, 대구, 반복, 설의, 영탄, 도치, 열거, 점층, 우의, 풍자, 병렬 등의 표현 기법이 있음.

정서나 교훈, 삶의 이치 등과 같이 분명한 형체로 나타나 있지 않은 것을 다양한 방법이나 매체를 통해 구체적이고 실감 나게 그려 내는 것을 뜻한다.""",
        "content_image_paths": ["data/literature/concepts_images/concept_p08_01.png"]
    },

    # 2. 개념 섹션 2
    {
        "type": UnitType.CONCEPT_CORE,
        "order": 1,
        "title": "시적 표현의 여러 가지 효과",
        "content_text": """• 음악적인 리듬이 느껴지게 함.
• 시어의 함축성을 높여 의미를 풍부하게 함.
• 어떤 대상을 감각적으로 연상하게 함.
• 상식적인 생각을 뒤집거나 깨뜨림으로써 지적 충격을 줌.
• 재미를 느끼고 웃게 하거나 반대로 슬픈 감정을 환기하게 함.
• 일상적인 표현에 변화를 가하여 말의 묘미를 느끼게 함.
• 화자의 사고나 감정, 상황 등을 강조하거나 부각함.""",
        "content_image_paths": ["data/literature/concepts_images/concept_p08_02.png"]
    },

    # 3. 본문 - 박두진 「해」
    {
        "type": UnitType.PASSAGE,
        "order": 2,
        "title": "박두진, 「해」",
        "content_text": """해야 솟아라. 해야 솟아라. 말갛게 씻은 얼굴 고운 해야 솟아라.
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
        "content_image_paths": ["data/literature/content_images/content_p09_01.png"]
    },

    # 4. 문제 1
    {
        "type": UnitType.QUESTION,
        "order": 3,
        "title": "문제 1",
        "content_text": """해야 솟아라. 해야 솟아라. 말갛게 씻은 얼굴 고운 해야 솟아라.
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
        "question_stem": "윗글을 이해한 내용으로 적절하지 않은 것은?",
        "question_choices": {
            "1": "화자는 '해'가 뜨기를 간절히 바라고 있다.",
            "2": "화자는 '달밤'보다 햇빛이 가득한 낮을 더 선호한다.",
            "3": "화자는 '청산'에서 자유롭고 평화로운 삶을 누리고 싶어 한다.",
            "4": "화자는 '해'가 뜨면 모든 생명체와 조화롭게 지낼 수 있다고 생각한다.",
            "5": "화자는 '사슴'과 '칡범'을 두려워하며 피하려고 한다."
        },
        "question_answer": 5,
        "ai_explanation": "화자는 '사슴을 만나면 사슴과 놀고, 칡범을 만나면 칡범과 놀고'라고 하여 이들과 함께 노는 모습을 그리고 있습니다. 따라서 이들을 두려워하거나 피하려는 것이 아닙니다.",
        "content_image_paths": ["data/literature/problems_images/problem_p09_01.png"]
    },

    # 5. 문제 2
    {
        "type": UnitType.QUESTION,
        "order": 4,
        "title": "문제 2",
        "content_text": """해야 솟아라. 해야 솟아라. 말갛게 씻은 얼굴 고운 해야 솟아라.
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
        "question_stem": "이 시의 표현상 특징으로 가장 적절한 것은?",
        "question_choices": {
            "1": "의성어와 의태어를 활용하여 생동감을 부여하고 있다.",
            "2": "대조적인 시어를 활용하여 주제를 부각하고 있다.",
            "3": "과거와 현재를 넘나들며 시상을 전개하고 있다.",
            "4": "계절의 변화를 통해 시간의 흐름을 드러내고 있다.",
            "5": "특정 시어를 반복하여 강조하고 있다."
        },
        "question_answer": 5,
        "ai_explanation": "'해야 솟아라', '해야, 고운 해야' 등 '해'와 관련된 시어를 반복적으로 사용하여 화자의 염원을 강조하고 있습니다.",
        "content_image_paths": ["data/literature/problems_images/problem_p10_02.png"]
    },

    # 6. 문제 3
    {
        "type": UnitType.QUESTION,
        "order": 5,
        "title": "문제 3",
        "content_text": """해야 솟아라. 해야 솟아라. 말갛게 씻은 얼굴 고운 해야 솟아라.
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
        "question_stem": """<보기>를 참고하여 윗글을 감상한 내용으로 적절하지 않은 것은?

<보기>
이 시는 광복 직전인 일제 강점기 말에 쓰인 작품으로, 암울한 시대 상황 속에서 밝은 미래에 대한 희망을 노래하고 있다. 화자가 간절히 바라는 '해'는 광복을 상징하며, '달밤'은 일제의 억압을 의미한다고 볼 수 있다.""",
        "question_choices": {
            "1": "'해'는 광복이라는 밝은 미래를 상징하는군.",
            "2": "'달밤'은 일제 강점기의 암울한 현실을 의미하는군.",
            "3": "'청산'은 광복 이후 누릴 자유로운 삶의 공간을 뜻하는군.",
            "4": "'어둠을 살라 먹고'는 일제의 억압을 물리치는 모습을 표현한 것이군.",
            "5": "'앳되고 고운 날'은 일제 강점기 이전의 과거 시절을 그리워하는 것이군."
        },
        "question_answer": 5,
        "ai_explanation": "'앳되고 고운 날'은 과거를 그리워하는 것이 아니라, 광복 이후 누릴 밝고 아름다운 미래를 의미합니다.",
        "content_image_paths": ["data/literature/problems_images/problem_p10_03.png"]
    },

    # 7. 단원 요약
    {
        "type": UnitType.CONCEPT_SUMMARY,
        "order": 6,
        "title": "1강 핵심 요약",
        "content_text": """이 강의에서는 시의 표현과 형식에 대해 학습했습니다.

주요 학습 내용:
• 시적 표현의 개념과 효과
• 시의 형식과 구조
• 실제 작품(박두진 「해」) 분석

작품 「해」는 광복 직전 일제 강점기 말에 쓰인 작품으로, 암울한 시대 상황 속에서 밝은 미래(광복)에 대한 간절한 염원을 노래하고 있습니다.""",
        "braille_keywords": ["시적표현", "형상화기법", "광복염원"]
    }
]

def update_lesson_01():
    """1강 실제 데이터로 업데이트"""
    db = SessionLocal()

    try:
        # 기존 1강 유닛 삭제
        print("기존 1강 유닛 삭제 중...")
        db.query(Unit).filter(Unit.lesson_id == LESSON_ID).delete(synchronize_session=False)
        db.commit()

        print(f"\n1강 실제 데이터 생성 중 (총 {len(UNITS)}개 유닛)...\n")

        for unit_data in UNITS:
            # 기본 필드
            unit = Unit(
                unit_id=f"u_{uuid.uuid4().hex[:12]}",
                lesson_id=LESSON_ID,
                type=unit_data["type"],
                order=unit_data["order"],
                title=unit_data["title"],
                content_text=unit_data.get("content_text")
            )

            # 이미지 경로 (JSON 배열)
            if "content_image_paths" in unit_data:
                unit.content_image_paths = json.dumps(unit_data["content_image_paths"])

            # 문제 관련 필드
            if unit_data["type"] == UnitType.QUESTION:
                unit.question_stem = unit_data["question_stem"]
                unit.question_choices = json.dumps(unit_data["question_choices"])
                unit.question_answer = unit_data["question_answer"]
                unit.ai_explanation = unit_data["ai_explanation"]

            # 점자 키워드
            if "braille_keywords" in unit_data:
                unit.braille_keywords = json.dumps(unit_data["braille_keywords"], ensure_ascii=False)

            db.add(unit)
            print(f"  [OK] [{unit_data['type'].value}] {unit_data['title']}")

        db.commit()

        print(f"\n완료!")
        print(f"  총 {len(UNITS)}개 유닛 생성")

        # 검증
        units = db.query(Unit).filter(Unit.lesson_id == LESSON_ID).order_by(Unit.order).all()
        print(f"\n[검증] 1강 유닛 {len(units)}개:")
        for u in units:
            print(f"  {u.order}. [{u.type.value}] {u.title}")
            if u.content_image_paths:
                images = json.loads(u.content_image_paths)
                print(f"     이미지: {len(images)}개")

    except Exception as e:
        db.rollback()
        print(f"\n에러: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == '__main__':
    update_lesson_01()
