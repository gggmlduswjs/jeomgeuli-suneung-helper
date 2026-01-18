"""
레슨 블록 생성 API 테스트
"""
import requests
import json
from pathlib import Path

# API 기본 URL
BASE_URL = "http://localhost:8000/api/v1"

# 테스트용 강의 대본
test_script = """여러분, 안녕하세요? 국어 영역 최선의 선택 최서희입니다. 2026 수능특강 최서희의 문학 1강이 시작됐습니다. 

오늘 1강에서는 시의 표현과 형식, 그리고 시의 내용에 대해서 배울 거거든. 

시적 표현 했을 때 형상화라는 말이 날개에 나와 있죠? 형상화했다라는 말이 나오면 정서나 교훈, 삶의 이치 등과 같이 분명한 형체로 나타나 있지 않은 것을 구체적이고 실감나게 그려내는 거고, 시에서는 그걸 언어, 표현을 가지고 그려내는 거야라고 하면 되겠네요. 

이 형상화를 위해서는. 이미지도 다양하게 활용할 수 있고요. 여러 가지 표현상의 특징들, 표현 방식들을 활용할 수도 있습니다. 

이런 표현 방식은 교재에 나와 있어. 비유, 상징, 역설, 대구, 반복, 설의, 쭉 있잖아. 

이제 구체적인 작품을 해 봅시다. 박두진의 '해', 이 작품은요. 정말 우리가 배운 시에 나올 만한 표현 형식상의 특징들을 참 잘 녹여내고 있는 작품이야. 

해야 솟아라. 화자가 말했어. 해야 솟아라. 말갛게 씻은 얼굴 고운 해야 솟아라. 

화자가 무엇을 어떻게 얘기하고 있니? 화자가요. 해에 대해서 얘기하면서 아주 강렬하게 솟아라라고 얘기를 하죠. 그러면 화자는 해가 솟기를 바라고 있네요라는 거 알 수 있습니다. 

해는 해인데 고운 해야. 말갛게 씻은 얼굴이래. 그러니까 긍정적이야, 지금 해가. 산 넘어, 산 넘어서 어둠을 살라 먹는다라는 것은 불태워 없애버린다라는 것이거든요. 

달밤이 싫어. 서술어 봐 봐. 대놓고 얘기하고 있어요. 나 싫어. 뭐가요? 달밤이 싫어. 해는 좋아. 솟기를 바라니까. 그런데 달밤은 싫어. 

이 작품의 중요한 표현 형식상의 특징 한번 체크를 해 볼까요? 첫 번째, 해라는 상징적인 시어를 활용하고 있어. 밝음과 어둠의 이미지의 대립도 확인할 수 있죠? 

1번 문제 한번 보도록 하겠습니다. 시구의 반복과 변주를 통해서 정서의 고조를 드러내고 있다. 

해야 솟아라. 해야 솟아라. 말갛게 씻은 얼굴 고운 해야 솟아라. 결국은 해가 솟기를 바라는 그 간절한 마음이 명령형으로 드러나고 있다라고 볼 수 있으니까 오케이. 

이제 마무리 지어야 되겠죠? 우리 강의의 제일 끝부분에는요. 매 작품을 한 판에 담판으로 또 한 번 정리를 해 줍니다."""

print("=" * 70)
print("레슨 블록 생성 API 테스트")
print("=" * 70)

# 1. 규칙 기반 생성 테스트
print("\n[1] 규칙 기반 생성 테스트")
payload = {
    "script_text": test_script,
    "subject": "korean",
    "lesson_number": 1,
    "use_ai": False
}

try:
    response = requests.post(
        f"{BASE_URL}/lesson-blocks/generate",
        json=payload,
        timeout=30
    )
    
    if response.status_code == 200:
        result = response.json()
        print(f"  성공!")
        print(f"  레슨 제목: {result['lesson_title']}")
        print(f"  블록 수: {result['block_count']}")
        print(f"  생성 방식: {result['generated_by']}")
        
        # 처음 3개 블록 출력
        print(f"\n  [블록 샘플]")
        for i, block in enumerate(result['blocks'][:3], 1):
            print(f"    블록 {i}: {block['block_id']}")
            print(f"      타입: {block['block_type']}")
            print(f"      점자: {block['braille_signal']}")
            print(f"      상태: {block['state_meaning']}")
    else:
        print(f"  실패: {response.status_code}")
        print(f"  응답: {response.text}")
        
except requests.exceptions.ConnectionError:
    print("  [오류] API 서버에 연결할 수 없습니다.")
    print("  [힌트] uvicorn으로 서버를 실행하세요:")
    print("    cd api && python -m uvicorn app.main:app --reload")
except Exception as e:
    print(f"  [오류] {e}")

# 2. AI 기반 생성 테스트 (API 키가 있는 경우)
print("\n[2] AI 기반 생성 테스트 (선택적)")
payload_ai = {
    "script_text": test_script,
    "subject": "korean",
    "lesson_number": 1,
    "use_ai": True,
    "llm_model": "gpt-4o-mini",
    "temperature": 0
}

try:
    response = requests.post(
        f"{BASE_URL}/lesson-blocks/generate",
        json=payload_ai,
        timeout=60
    )
    
    if response.status_code == 200:
        result = response.json()
        print(f"  성공!")
        print(f"  레슨 제목: {result['lesson_title']}")
        print(f"  블록 수: {result['block_count']}")
        print(f"  생성 방식: {result['generated_by']}")
        if result.get('saved'):
            print(f"  MongoDB 저장: {result.get('mongodb_id')}")
    else:
        print(f"  실패: {response.status_code}")
        if response.status_code == 500:
            print(f"  [힌트] OpenAI API 키가 설정되지 않았거나 LLM 호출 실패")
            print(f"  [해결] 규칙 기반으로 자동 폴백됨")
        
except requests.exceptions.ConnectionError:
    print("  [오류] API 서버에 연결할 수 없습니다.")
except Exception as e:
    print(f"  [오류] {e}")

print("\n" + "=" * 70)
print("테스트 완료")
print("=" * 70)
