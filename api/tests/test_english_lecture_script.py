"""
영어 강의 대본 파싱 테스트
수능특강 영어 1강 전체 대본 파싱
"""
import sys
from pathlib import Path

# api 디렉토리를 Python 경로에 추가
api_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(api_dir))

from app.services.lecture_script_parser import LectureScriptParser


def test_english_lecture_script():
    """영어 1강 대본 파싱"""
    
    # 영어 강의 대본 (사용자가 제공한 텍스트)
    script_text = """
안녕하세요. 여러분과 합격의 기쁨을 함께 하겠습니다. 수능특강 영어 강의를 함께할 저는 주혜연입니다. 

작년에는 희한하게도 저한테 입학 축하 영상을 부탁하는 학교들이 정말 많았습니다. 참 감사하고 영광스러운 일입니다. 

일단 문제는 꼭 미리 먼저 풀어보고 오셔야 됩니다. 이거 완전 기본 중에 기본이야. 그다음에 단어만 미리 외우고 와주세요.

일단 짠, 책장을 넘기면 글의 목적 파악이라고 나와 있지. 우리 시험지에는 18번에 배치되는 유형입니다.

우리 목적을 다짜고짜 이야기하는 경우도 물론 있겠지만 대부분은 어때? 이만저만한 배경 설명을 먼저 합니다.

그래서 후반부에 목적이 배치가 된다고. 여기까지 괜찮니? 그래, 그러면 문제를 좀 빨리 풀고 싶으면 어떻게 해야 돼?

일단 문의의 표현입니다. let me know if, 뭐인지 알려주세요. 알고 싶어서 글을 쓴 거니까 문의가 되겠지.

올해 정말 새롭게 도입된 야심찬 코너는 짠, 이다음의 논리 코드입니다. 논리 코드라고 하는 거는 사실은 문제 유형이 아무리 바뀌어도 변하지 않는 거야.

일단은 앞에 뭐라고 뭐라고 배경 설명으로 시작을 하다가 그런데 있잖아, 이렇게 전환하면서 목적이 나오는 경우가 많겠죠.

그래서 전환의 표현 unfortunately, 안타깝게도라든지 however, 하지만 이런 표현들이 있고 그다음에 당연히 결과 부분에 우리가 주목해야 되겠지.

그러면 우리 gateway 문제를 먼저 같이 풀 건데 항상 우리 교재에 있는 gateway 문제는 기출 문제로 이루어져 있어, 평가원 기출 문제.

As a result, 그래서 결과적으로 we have decided to cancel the race. 저희가 이 레이스를 취소하기로 결정을 했습니다.

Unfortunately, 그런데 안타깝게도라고 했으니 뭔가 이제 사건의 전환이 이루어질 겁니다.

however, 하지만, 이제 나왔다. 하지만 안 읽어도 알겠네. 뭐야? 못 할 것 같아, 취소해야 돼.

그래서 이제부터 반전이 시작될 거예요. As a result, 그래서 결과적으로 저희가 취소해야 될 것 같아요가 된 거지.

그래서 우리 아까 정답 너무 잘 골랐다. 일단은 경기 등록해 주셔서 감사하다. 그런데 그 당일날 폭우 예보가 있다.

이제 문제를 어떻게 접근해야 되는지 조금 알겠어? 그래, 그러면 우리 이제 본격적으로 교재에 나와 있는 1번 문제부터 같이 한번 보겠습니다.

we will be providing booth space for rental, 렌탈해 드릴 수 있는, 대여해 드릴 수 있는 어떤 부스 공간을 제공할 예정입니다.

명령문이 나옵니다. 이리로 전화 주세요. do not miss your chance, 기회를 놓치지 마세요.

그래서 지금 대여용 부스 늦기 전에 빨리 예약하세요라고 지금 예약을 권유하고 있는 글입니다.

다음 글에 드러난 Peter의 심경 변화로 가장 적절한 것은? 얘가 gateway의 문제였어요.

Peter was certain, Peter가 아주 확신을 하고 있었다. 자신의 부인인 에이미가 자기의 서프라이즈 선물을 굉장히 좋아할 거라고 확신하고 있었다.

Unfortunately, 안타깝게도, 그러면 이 문장을 기점으로 해서 반전이 이루어지겠네.

he was told, was told니까 이야기를 한 게 아니라 얘기를 들은 겁니다. that the restaurant was fully reserved, 레스토랑이 예약이 꽉 찼다는 이야기를 듣고 말이에요.

이렇게 해서 우리 교재의 첫 단원을 무사히 돌파했습니다.
"""
    
    parser = LectureScriptParser(subject="english")
    result = parser.parse(script_text)
    
    print("=" * 80)
    print("영어 1강 강의 대본 파싱 결과")
    print("=" * 80)
    print(f"과목: {result['subject']}")
    print(f"강 번호: {result['lesson_number']}")
    print(f"전체 길이: {result['statistics']['total_length']:,} 문자")
    print(f"문단 수: {result['statistics']['total_paragraphs']}")
    print(f"섹션 수: {result['statistics']['total_sections']}")
    print()
    
    print("섹션 타입별 통계:")
    for section_type, count in result['statistics']['section_types'].items():
        print(f"  {section_type:15s}: {count:3d}개")
    print()
    
    print("구조 분석:")
    structure = result['structure']
    print(f"  OT 포함: {structure.get('has_ot', False)}")
    print(f"  Overview 포함: {structure.get('has_overview', False)}")
    print(f"  개념 포함: {structure.get('has_concept', False)}")
    print(f"  예제 포함: {structure.get('has_example', False)}")
    print()
    
    print("파싱된 섹션 상세:")
    for i, section in enumerate(result['sections'], 1):
        print(f"\n{'='*80}")
        print(f"[{i}] {section['type'].upper()} 섹션")
        print(f"{'='*80}")
        print(f"문단 수: {len(section['paragraphs'])}")
        print(f"내용 길이: {len(section['content']):,} 문자")
        
        if section['key_points']:
            print(f"\n핵심 포인트 ({len(section['key_points'])}개):")
            for j, point in enumerate(section['key_points'][:5], 1):
                print(f"  {j}. {point[:150]}")
        
        if section['math_expressions']:
            print(f"\n수학 표현식 ({len(section['math_expressions'])}개):")
            for j, expr in enumerate(section['math_expressions'][:5], 1):
                print(f"  {j}. {expr[:150]}")
        
        print(f"\n내용 미리보기:")
        preview = section['content'][:300].replace('\n', ' ')
        print(f"  {preview}...")
    
    print("\n" + "=" * 80)
    print("파싱 완료!")
    print("=" * 80)
    
    return result


if __name__ == "__main__":
    test_english_lecture_script()
