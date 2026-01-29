"""
템플릿 매칭 실패 디버깅 스크립트
"""
import sys
import re
from pathlib import Path

# backend 디렉토리를 Python 경로에 추가
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from app.infrastructure.pdf.parsers.template_manager import TemplateManager
from app.infrastructure.pdf.parsers.template import ParsingTemplate

def debug_template_matching():
    """템플릿 매칭 디버깅"""

    # 1. 템플릿 로드
    print("=" * 80)
    print("1. 템플릿 로드")
    print("=" * 80)

    manager = TemplateManager()
    print(f"로드된 템플릿 수: {len(manager.templates)}")

    for key, template in manager.templates.items():
        print(f"\n템플릿: {key}")
        print(f"  - 이름: {template.name}")
        print(f"  - 과목: {template.subject}")
        print(f"  - 신뢰도: {template.confidence}")
        print(f"  - 패턴 수:")
        print(f"    - lecture_title_patterns: {len(template.patterns.get('lecture_title_patterns', []))}")
        print(f"    - toc_lecture_patterns: {len(template.patterns.get('toc_lecture_patterns', []))}")
        print(f"    - concept_title_patterns: {len(template.patterns.get('concept_title_patterns', []))}")
        print(f"    - problem_number_pattern: {template.patterns.get('problem_number_pattern', 'N/A')}")

    # 2. 문학 템플릿 상세 분석
    print("\n" + "=" * 80)
    print("2. 문학 템플릿 패턴 분석")
    print("=" * 80)

    lit_templates = manager.get_templates_by_subject("literature")
    if not lit_templates:
        print("[ERROR] 문학 템플릿이 없습니다!")
        return

    template = lit_templates[0]
    print(f"\n템플릿: {template.name}")
    print(f"신뢰도: {template.confidence}")

    # 패턴 테스트
    print("\n강의 제목 패턴:")
    lecture_patterns = template.patterns.get("lecture_title_patterns", [])
    for i, pattern in enumerate(lecture_patterns):
        print(f"  [{i}] {pattern}")

    # 샘플 텍스트로 패턴 테스트
    sample_texts = [
        "1강 | 시의 표현과 형식",
        "1강 시의 표현과 형식",
        "2강 | 시의 내용",
        "3강: 소설의 서술상 특징",
        "10강 극의 특성과 극 문학의 구성 요소",
        "본문 텍스트",
        "문제 1번",
        "개념 설명",
    ]

    print("\n패턴 매칭 테스트:")
    for text in sample_texts:
        matched = False
        for pattern in lecture_patterns:
            if re.search(pattern, text.strip()):
                print(f"  [OK] '{text}' -> 패턴 '{pattern}' 매칭")
                matched = True
                break
        if not matched:
            print(f"  [FAIL] '{text}' -> 매칭 실패")

    # 3. 신뢰도 계산 시뮬레이션
    print("\n" + "=" * 80)
    print("3. 신뢰도 계산 시뮬레이션")
    print("=" * 80)

    # 목차 페이지 시뮬레이션 (7페이지, 강의 79개)
    print("\n시나리오 1: 목차 페이지 (첫 5페이지)")
    toc_lines = [
        "수능특강 문학",
        "목차",
        "1강 | 시의 표현과 형식",
        "2강 | 시의 내용",
        "3강 | 소설의 서술상 특징",
        "4강 | 소설의 내용 구성 요소",
        "5강 | 극의 특성과 극 문학의 구성 요소",
    ] * 10  # 70줄 정도

    simulate_confidence(manager, template, toc_lines, "목차 페이지")

    # 콘텐츠 페이지 시뮬레이션
    print("\n시나리오 2: 콘텐츠 페이지 (8페이지~)")
    content_lines = [
        "1강 시의 표현과 형식",
        "개념 학습",
        "시의 표현과 형식이란?",
        "율격, 시행, 연 등의 요소가 시의 주제나 화자의 정서를",
        "비유, 상징, 역설, 반어, 대구, 반복, 설의, 영탄, 도치,",
        "문제 1",
        "다음 작품을 읽고 물음에 답하시오.",
        "(가) 김소월 - 진달래꽃",
    ] * 20  # 160줄 정도

    simulate_confidence(manager, template, content_lines, "콘텐츠 페이지")

    # 표지 페이지 시뮬레이션
    print("\n시나리오 3: 표지 페이지")
    cover_lines = [
        "2026 수능특강",
        "문학",
        "EBS 한국교육방송공사",
        "국어영역",
    ] * 10

    simulate_confidence(manager, template, cover_lines, "표지 페이지")


def simulate_confidence(manager, template, lines, scenario_name):
    """신뢰도 계산 시뮬레이션"""
    pdf_text = '\n'.join(lines)

    # 패턴 매칭 카운트
    lecture_patterns = template.patterns.get("lecture_title_patterns", [])
    toc_patterns = template.patterns.get("toc_lecture_patterns", [])
    concept_patterns = template.patterns.get("concept_title_patterns", [])
    problem_pattern = template.patterns.get("problem_number_pattern", "")

    lecture_matches = 0
    concept_matches = 0
    problem_matches = 0

    for line in lines:
        line_stripped = line.strip()

        # 강의 제목 매칭
        for pattern in lecture_patterns + toc_patterns:
            if re.search(pattern, line_stripped):
                lecture_matches += 1
                break

        # 개념 매칭
        for pattern in concept_patterns:
            if re.search(pattern, line_stripped):
                concept_matches += 1
                break

        # 문제 번호 매칭
        if problem_pattern and re.search(problem_pattern, line_stripped):
            problem_matches += 1

    # 매칭률 계산
    total_lines = len(lines)
    lecture_score = min(lecture_matches / max(total_lines, 1), 1.0)
    concept_score = min(concept_matches / max(total_lines, 1), 1.0)
    problem_score = min(problem_matches / 10.0, 1.0)

    # 매칭 수가 5개 미만이면 패널티
    if lecture_matches < 5:
        lecture_score *= 0.5
    if concept_matches < 5:
        concept_score *= 0.5

    base_confidence = template.confidence

    # 신호 매칭이 없으면 0
    signal_matches = lecture_matches + concept_matches + problem_matches
    if signal_matches == 0:
        total_confidence = 0.0
    else:
        # 가중 평균 (영역 마킹 없는 경우)
        total_confidence = (
            lecture_score * 0.4 +
            problem_score * 0.3 +
            concept_score * 0.2 +
            base_confidence * 0.1
        )
        total_confidence = min(total_confidence, 1.0)

    print(f"\n{scenario_name} 분석:")
    print(f"  총 라인 수: {total_lines}")
    print(f"  강의 제목 매칭: {lecture_matches}개 → 점수 {lecture_score:.3f} (40%)")
    print(f"  개념 매칭: {concept_matches}개 → 점수 {concept_score:.3f} (20%)")
    print(f"  문제 번호 매칭: {problem_matches}개 → 점수 {problem_score:.3f} (30%)")
    print(f"  기본 신뢰도: {base_confidence:.3f} (10%)")
    print(f"  -> 총 신뢰도: {total_confidence:.3f}")
    print(f"  -> 임계값 0.85 {'[OK]' if total_confidence >= 0.85 else '[FAIL]'}")

    if signal_matches == 0:
        print(f"  [WARN] 패턴 매칭이 전혀 없음 -> 신뢰도 강제 0")
    elif lecture_matches < 5:
        print(f"  [WARN] 강의 제목 매칭 < 5개 -> 패널티 적용 (0.5배)")


if __name__ == "__main__":
    debug_template_matching()
