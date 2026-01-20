"""
과목별 학습 단위 타입 정의
공통 구조를 유지하면서 과목별 특성을 반영
"""
from enum import Enum
from typing import Dict, List


class KoreanSectionType(str, Enum):
    """국어 학습 단위 타입"""
    ORIENTATION = "orientation"  # 강의 오리엔테이션
    CONCEPT_EXPRESSION = "concept_expression"  # 시의 표현 개념
    CONCEPT_FORM = "concept_form"  # 시의 형식 개념
    CONCEPT_CONTENT = "concept_content"  # 시의 내용 개념
    WORK_ANALYSIS = "work_analysis"  # 작품 분석
    PROBLEM_SOLVING = "problem_solving"  # 문제 풀이
    SUMMARY = "summary"  # 정리


class MathSectionType(str, Enum):
    """수학 학습 단위 타입"""
    ORIENTATION = "orientation"  # 강의 오리엔테이션
    CONCEPT_DEFINITION = "concept_definition"  # 개념 정의
    CONCEPT_APPLICATION = "concept_application"  # 개념 적용
    GRAPH_INTERPRETATION = "graph_interpretation"  # 그래프 해석
    EQUATION_SOLVING = "equation_solving"  # 방정식 풀이
    EXAMPLE = "example"  # 예제
    PROBLEM = "problem"  # 문제
    SUMMARY = "summary"  # 정리


class EnglishSectionType(str, Enum):
    """영어 학습 단위 타입"""
    ORIENTATION = "orientation"  # 강의 오리엔테이션
    STRATEGY = "strategy"  # 전략 설명
    SIGNAL_EXPRESSION = "signal_expression"  # 핵심 표현(시그널)
    LOGIC_CODE = "logic_code"  # 논리 코드
    GATEWAY_PROBLEM = "gateway_problem"  # Gateway 문제
    PRACTICE_PROBLEM = "practice_problem"  # 실전 문제
    VARIATION = "variation"  # 변형 출제
    SUMMARY = "summary"  # 정리


# 과목별 타입 매핑
SUBJECT_SECTION_TYPES: Dict[str, type] = {
    "KOREAN": KoreanSectionType,
    "MATH": MathSectionType,
    "ENGLISH": EnglishSectionType,
}


def get_section_type_for_subject(subject: str) -> type:
    """과목에 맞는 section_type enum 반환"""
    return SUBJECT_SECTION_TYPES.get(subject.upper(), KoreanSectionType)


# 공통 학습 단위 구조 (모든 과목 공통)
COMMON_UNIT_STRUCTURE = {
    "title": "학습 단위 제목",
    "learning_objective": "학습 목표",
    "key_content": "핵심 내용",
    "learning_point": "학습 포인트",
    "content": "전체 내용",
    "braille_pattern": "점자 3셀 패턴 (상태 전환 신호)",
    "tts_text": "TTS용 요약 텍스트",
}
