"""
LangChain Flow 테스트

실제 LLM을 사용한 레슨 블록 자동 생성 테스트
"""
import sys
import os
from pathlib import Path
import json

# 프로젝트 루트를 경로에 추가
sys.path.insert(0, str(Path(__file__).parent))

from app.services.langchain_lesson_flow import (
    generate_lesson_blocks,
    LessonBlockGenerationFlow
)

# 테스트용 강의 대본 (짧은 버전)
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
print("LangChain Flow 테스트")
print("=" * 70)

# OpenAI API 키 확인
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    print("[경고] OPENAI_API_KEY 환경변수가 설정되지 않았습니다.")
    print("[경고] 규칙 기반 분해로 폴백합니다.")
    
    # 규칙 기반으로 폴백
    from app.services.lesson_block_decomposer import decompose_lecture_script
    result = decompose_lecture_script(
        script_text=test_script,
        subject="korean",
        lesson_number=1
    )
    
    print(f"\n[규칙 기반 결과]")
    print(f"  레슨 제목: {result['lesson_title']}")
    print(f"  블록 수: {len(result['blocks'])}")
    
else:
    print(f"[LLM 사용] 모델: gpt-4o-mini")
    
    try:
        # LangChain Flow 실행
        flow = LessonBlockGenerationFlow(
            subject="korean",
            llm_model="gpt-4o-mini",
            temperature=0,
            openai_api_key=api_key
        )
        
        result = flow.generate(
            script_text=test_script,
            lesson_number=1
        )
        
        print(f"\n[LLM 생성 결과]")
        print(f"  레슨 제목: {result.lesson_title}")
        print(f"  과목: {result.subject}")
        print(f"  강의 번호: {result.lesson_number}")
        print(f"  블록 수: {len(result.blocks)}")
        
        print(f"\n[블록 상세]")
        for i, block in enumerate(result.blocks[:5], 1):  # 처음 5개만
            print(f"\n  블록 {i}: {block.block_id}")
            print(f"    타입: {block.block_type}")
            print(f"    점자 신호: {block.braille_signal}")
            print(f"    오디오 포커스: {block.audio_focus}")
            print(f"    상태 의미: {block.state_meaning}")
        
        if len(result.blocks) > 5:
            print(f"\n  ... 외 {len(result.blocks) - 5}개 블록")
        
        # JSON 파일로 저장
        output_dir = Path(__file__).parent.parent.parent / "data" / "parsed" / "literature"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        output_file = output_dir / f"{result.subject}_{result.lesson_number:02d}_langchain.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result.model_dump(), f, ensure_ascii=False, indent=2)
        
        print(f"\n[저장] {output_file}")
        
    except Exception as e:
        print(f"[오류] {e}")
        import traceback
        traceback.print_exc()
        
        # 폴백
        print("\n[폴백] 규칙 기반 분해로 전환")
        from app.services.lesson_block_decomposer import decompose_lecture_script
        result = decompose_lecture_script(
            script_text=test_script,
            subject="korean",
            lesson_number=1
        )
        print(f"  블록 수: {len(result['blocks'])}")

print("\n" + "=" * 70)
print("테스트 완료")
print("=" * 70)
