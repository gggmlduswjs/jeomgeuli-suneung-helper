"""
전체 강의 대본 파싱 테스트
사용자가 제공한 수학Ⅰ 1강 전체 대본 파싱
"""
import sys
from pathlib import Path

# api 디렉토리를 Python 경로에 추가
api_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(api_dir))

from app.services.lecture_script_parser import LectureScriptParser


def test_full_math1_script():
    """전체 수학Ⅰ 1강 대본 파싱"""
    
    # 전체 대본 (사용자가 제공한 텍스트)
    script_text = """
반갑습니다. 여러분들과 수학을 함께 하는 정상모입니다. 드디어 우리 2026 수능특강 수학Ⅰ 전문항 개념 및 문제풀이 강좌의 시작입니다.

1강이고요. 이제 1과 지수와 로그 편부터 시작입니다. 수학Ⅰ, 여러분 항상 공부 시작할 때 처음으로 하는, 또 수능의 직접적인 출제 과목이고요. 

굉장히 중요한 많은 내용들이 있는 그런 과목입니다. 그 시작을 여러분들, 저하고 함께 할 수 있어서 무한한 영광이고요, 

여러분들도 저 만나서 많은 실력 향상을 이끌어 갔으면 좋겠습니다. 

1강에서는 지수와 로그를 좀 다루는데요. 우리가 항상 그런 것 같아요. 어떤 공부를 하고 어떤 과목을 공부한다면 그 맵을 한번 잡아보는 건 좋거든요. 

그래서 전체적으로 여러분들 좀 이 수학Ⅰ이라고 하는 이 과목을 좀 보시면, 큰 맵을 한번 잡아보자. 

첫 번째 뭐가 있죠? 지수와 로그가 있습니다. 지수와 로그. 이게 이제 첫 번째 단원이고요. 두 번째로는 지수함수와 로그함수가 있습니다. 

자, 그래서 우리는 실수 a에 대해서 n이 2 이상의 자연수, 설명 다 됐죠? n제곱해서 a가 되는 수, 즉 여기 나오네요.

a의 n제곱근이에요. a의 n제곱근입니다. 

어떤 방정식을 떠올려야 되냐면 x의 n제곱이 a가 된다 라고 하는 이 방정식을 떠올려야 됩니다.

예시를 하나 더 보겠습니다. 16의 4제곱근이다. 16의 4제곱근이다 라고 하면 그냥 떠올리시는 거야.

4제곱을 그린 다음에, y=x의 4제곱을 그린 다음에 그다음에 16을 이렇게 치는 거야.

그럼 여기, 여기가 생기잖아. 실수 값이잖아. 그니까 어떤 거 4제곱이 16 돼? 2잖아. 그럼 여기는 대칭이잖아. -2잖아.

이렇게 되는 거야.
"""
    
    parser = LectureScriptParser(subject="math1")
    result = parser.parse(script_text)
    
    print("=" * 80)
    print("수학Ⅰ 1강 전체 대본 파싱 결과")
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
    print(f"  정리 포함: {structure.get('has_summary', False)}")
    print()
    
    if structure.get('concepts'):
        print(f"추출된 개념 ({len(structure['concepts'])}개):")
        for concept in structure['concepts'][:5]:
            print(f"  - {concept.get('term', 'N/A')}: {concept.get('definition', '')[:100]}")
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
    test_full_math1_script()
