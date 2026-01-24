"""
문제 번호 패턴 매칭기
템플릿의 problem_patterns를 활용하여 문제 추출 정확도 향상
"""
import re
import logging
from typing import Optional, List, Tuple

from app.infrastructure.pdf.types import JSONDict

logger = logging.getLogger(__name__)


class ProblemPatternMatcher:
    """문제 번호 패턴 매칭기"""
    
    def __init__(self, problem_patterns: Optional[JSONDict] = None):
        """
        Args:
            problem_patterns: 문제 패턴 정보 딕셔너리
                {
                    "number_format": "1.",  // "1)", "(1)", "①" 등
                    "number_position": "start_of_line",  // "start_of_line", "inline", "margin"
                    "answer_format": "①",  // "①", "(1)", "1)" 등
                    "answer_position": "end_of_problem",  // "end_of_problem", "inline", "separate"
                    "problem_separator": "\n\n",  // 문제 간 구분자
                    "example_numbers": ["1.", "2.", "3.", "4.", "5."]
                }
        """
        self.problem_patterns = problem_patterns or {}
        self.enabled = bool(self.problem_patterns)
        
        # 패턴 정보 추출
        self.number_format = self.problem_patterns.get('number_format', r'\d+\.')
        self.number_position = self.problem_patterns.get('number_position', 'start_of_line')
        self.answer_format = self.problem_patterns.get('answer_format', '')
        self.answer_position = self.problem_patterns.get('answer_position', 'end_of_problem')
        self.problem_separator = self.problem_patterns.get('problem_separator', '\n\n')
        self.example_numbers = self.problem_patterns.get('example_numbers', [])
        
        # 정규식 패턴 생성
        self._build_patterns()
        
        if self.enabled:
            logger.info(
                f"[ProblemPatternMatcher] 활성화: "
                f"번호 형식={self.number_format}, 위치={self.number_position}"
            )
    
    def _build_patterns(self):
        """정규식 패턴 생성"""
        # number_format을 정규식으로 변환
        if isinstance(self.number_format, str):
            # 특수 문자 이스케이프
            escaped = re.escape(self.number_format)
            # 숫자 부분을 \d+로 치환
            self.number_regex = re.sub(r'\\d', r'\\d+', escaped)
            # 숫자 패턴이 없으면 추가
            if r'\d+' not in self.number_regex:
                self.number_regex = r'\d+' + self.number_regex
        else:
            self.number_regex = r'\d+\.'
        
        # answer_format 정규식
        if self.answer_format:
            self.answer_regex = re.escape(self.answer_format)
            # 숫자 부분 치환
            self.answer_regex = re.sub(r'\\d', r'\\d+', self.answer_regex)
        else:
            self.answer_regex = None
    
    def match_problem_number(
        self,
        text: str,
        position: Optional[Tuple[float, float, float, float]] = None
    ) -> Optional[JSONDict]:
        """문제 번호 매칭

        Args:
            text: 텍스트
            position: 텍스트 위치 (x, y, width, height) - 선택

        Returns:
            {
                'number': 문제 번호,
                'confidence': 신뢰도,
                'position_match': 위치 매칭 여부
            } 또는 None
        """
        if not self.enabled:
            return None
        
        # 정규식으로 문제 번호 찾기
        match = re.search(self.number_regex, text)
        if not match:
            return None
        
        problem_number = match.group(0)
        
        # 위치 검증
        position_match = True
        if position and self.number_position == 'start_of_line':
            # 줄 시작 부분인지 확인 (x 좌표가 작은 값)
            x, y, width, height = position
            # 왼쪽 여백 내에 있으면 줄 시작으로 간주
            margin_left = 50  # 기본 왼쪽 여백
            position_match = x < margin_left
        
        # 예시 번호와 비교하여 신뢰도 계산
        confidence = 0.7
        if problem_number in self.example_numbers:
            confidence = 1.0
        elif any(problem_number.startswith(ex.replace(r'\d+', '')) for ex in self.example_numbers):
            confidence = 0.9
        
        return {
            'number': problem_number,
            'confidence': confidence,
            'position_match': position_match
        }
    
    def extract_problem_boundary(
        self,
        text: str,
        problem_start: int
    ) -> Optional[Tuple[int, int]]:
        """문제 경계 추출
        
        Args:
            text: 전체 텍스트
            problem_start: 문제 시작 위치
            
        Returns:
            (시작 위치, 종료 위치) 또는 None
        """
        if not self.enabled:
            return None
        
        # problem_separator로 다음 문제 찾기
        if self.problem_separator:
            next_separator = text.find(self.problem_separator, problem_start + 1)
            if next_separator > 0:
                return (problem_start, next_separator)
        
        # 다음 문제 번호 찾기
        next_match = re.search(self.number_regex, text[problem_start + 1:])
        if next_match:
            next_start = problem_start + 1 + next_match.start()
            return (problem_start, next_start)
        
        return None
    
    def match_answer(
        self,
        text: str
    ) -> Optional[JSONDict]:
        """답안 형식 매칭

        Args:
            text: 텍스트

        Returns:
            {
                'answer': 답안,
                'confidence': 신뢰도
            } 또는 None
        """
        if not self.enabled or not self.answer_regex:
            return None
        
        match = re.search(self.answer_regex, text)
        if match:
            return {
                'answer': match.group(0),
                'confidence': 0.8
            }
        
        return None
