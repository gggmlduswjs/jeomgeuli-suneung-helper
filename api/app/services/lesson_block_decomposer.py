"""
강의대본 → 레슨 블록 자동 분해 시스템

프롬프트 기반 AI 분해 + 규칙 기반 분해 하이브리드
"""
import re
from typing import List, Dict, Any, Optional
from enum import Enum
from pathlib import Path


class BlockType(str, Enum):
    """레슨 블록 타입"""
    ORIENTATION = "orientation"
    LEARNING_GOAL = "learning_goal"
    EXAM_STRUCTURE = "exam_structure"
    CONCEPT_FRAME = "concept_frame"
    WORK_ANALYSIS = "work_analysis"
    PROBLEM_APPLICATION = "problem_application"
    EXPLANATION = "explanation"
    SUMMARY = "summary"
    CLOSING_MESSAGE = "closing_message"


class Subject(str, Enum):
    """과목"""
    KOREAN = "korean"
    MATH = "math"
    ENGLISH = "english"


class LessonBlockDecomposer:
    """
    강의대본을 레슨 블록으로 자동 분해
    
    설계 철학:
    - 점자는 신호등 (내용 전달 X, 상태 인지 O)
    - 블록 분해 기준: 학습자가 인지적으로 위치를 바꿔야 하는 지점
    - 과목별 특화 분해 규칙 적용
    """
    
    # 과목별 점자 신호 매핑
    BRAILLE_SIGNALS = {
        Subject.KOREAN: {
            BlockType.ORIENTATION: "●○○",      # 강의 시작
            BlockType.CONCEPT_FRAME: "○●○",    # 감상 공식
            BlockType.WORK_ANALYSIS: "○●●",    # 작품 시작
            BlockType.PROBLEM_APPLICATION: "○○●",  # 문제
            BlockType.EXPLANATION: "●●○",      # 해설
            BlockType.SUMMARY: "●○●",          # 정리
        },
        Subject.MATH: {
            BlockType.ORIENTATION: "●○○",      # 문제
            BlockType.LEARNING_GOAL: "●●○",    # 조건
            BlockType.CONCEPT_FRAME: "○●○",    # 정의
            BlockType.EXAM_STRUCTURE: "●●●",    # 핵심
            BlockType.PROBLEM_APPLICATION: "○○●",  # 전환
            BlockType.SUMMARY: "●○●",          # 결론
        },
        Subject.ENGLISH: {
            BlockType.ORIENTATION: "●○○",      # 강의 시작
            BlockType.CONCEPT_FRAME: "○●○",    # 구조
            BlockType.EXAM_STRUCTURE: "●●●",    # 표현
            BlockType.LEARNING_GOAL: "●●○",    # 논리 코드
            BlockType.PROBLEM_APPLICATION: "○○●",  # 문제 접근
            BlockType.EXPLANATION: "●●○",      # 해설
            BlockType.SUMMARY: "●○●",          # 출제 포인트
        }
    }
    
    # 과목별 상태 의미 메시지
    STATE_MEANINGS = {
        Subject.KOREAN: {
            BlockType.ORIENTATION: "강의가 시작되었습니다",
            BlockType.CONCEPT_FRAME: "감상 프레임을 학습합니다",
            BlockType.WORK_ANALYSIS: "작품 분석을 시작합니다",
            BlockType.PROBLEM_APPLICATION: "문제 풀이를 시작합니다",
            BlockType.EXPLANATION: "문제 해설을 확인합니다",
            BlockType.SUMMARY: "강의 요약을 확인합니다",
        },
        Subject.MATH: {
            BlockType.ORIENTATION: "문제를 확인합니다",
            BlockType.LEARNING_GOAL: "조건을 파악합니다",
            BlockType.CONCEPT_FRAME: "개념을 정의합니다",
            BlockType.EXAM_STRUCTURE: "핵심 포인트를 확인합니다",
            BlockType.PROBLEM_APPLICATION: "풀이 방법을 적용합니다",
            BlockType.SUMMARY: "결론을 정리합니다",
        },
        Subject.ENGLISH: {
            BlockType.ORIENTATION: "강의가 시작되었습니다",
            BlockType.CONCEPT_FRAME: "독해 구조를 파악합니다",
            BlockType.EXAM_STRUCTURE: "표현 기법을 학습합니다",
            BlockType.LEARNING_GOAL: "논리 코드를 확인합니다",
            BlockType.PROBLEM_APPLICATION: "문제 접근 방법을 학습합니다",
            BlockType.EXPLANATION: "해설을 확인합니다",
            BlockType.SUMMARY: "출제 포인트를 정리합니다",
        }
    }
    
    def __init__(self, subject: Subject):
        """
        Args:
            subject: 과목 (korean, math, english)
        """
        self.subject = subject
    
    def decompose(self, script_text: str, lesson_number: Optional[int] = None) -> Dict[str, Any]:
        """
        강의대본을 레슨 블록으로 분해
        
        Args:
            script_text: 강의 대본 텍스트
            lesson_number: 강의 번호
            
        Returns:
            레슨 블록 JSON 구조
        """
        # 1. 강의 메타 정보 추출
        lesson_title = self._extract_lesson_title(script_text, lesson_number)
        
        # 2. 블록 분해 지점 찾기
        break_points = self._find_break_points(script_text)
        
        # 3. 블록 생성
        blocks = []
        for i, (start_idx, end_idx, block_type, context) in enumerate(break_points, 1):
            block_text = script_text[start_idx:end_idx].strip()
            
            if not block_text or len(block_text) < 20:
                continue
            
            block = self._create_block(
                block_id=f"B{i}",
                block_type=block_type,
                block_text=block_text,
                start_idx=start_idx,
                end_idx=end_idx,
                context=context
            )
            blocks.append(block)
        
        return {
            "lesson_title": lesson_title,
            "subject": self.subject.value,
            "lesson_number": lesson_number or self._extract_lesson_number(script_text) or 1,
            "blocks": blocks
        }
    
    def _extract_lesson_title(self, script_text: str, lesson_number: Optional[int] = None) -> str:
        """레슨 제목 추출"""
        # "1강", "수능특강 문학 1강" 패턴
        patterns = [
            r'(\d+)\s*강\s*([가-힣\s]+)',
            r'수능특강\s*([가-힣]+)\s*(\d+)\s*강',
            r'(\d+)\s*강',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, script_text[:500])
            if match:
                if lesson_number:
                    return f"{lesson_number}강 {match.group(2) if len(match.groups()) > 1 else ''}".strip()
                return match.group(0)
        
        return f"{lesson_number or 1}강" if lesson_number else "1강"
    
    def _extract_lesson_number(self, script_text: str) -> Optional[int]:
        """강의 번호 추출"""
        match = re.search(r'(\d+)\s*강', script_text[:500])
        return int(match.group(1)) if match else None
    
    def _find_break_points(self, script_text: str) -> List[tuple]:
        """
        블록 분해 지점 찾기
        
        Returns:
            [(start_idx, end_idx, block_type, context), ...]
        """
        break_points = []
        current_pos = 0
        
        # 과목별 분해 규칙 적용
        if self.subject == Subject.KOREAN:
            break_points = self._find_korean_break_points(script_text)
        elif self.subject == Subject.MATH:
            break_points = self._find_math_break_points(script_text)
        elif self.subject == Subject.ENGLISH:
            break_points = self._find_english_break_points(script_text)
        
        return break_points
    
    def _find_korean_break_points(self, script_text: str) -> List[tuple]:
        """국어 과목 블록 분해 지점"""
        break_points = []
        
        # 패턴 기반 분해
        patterns = [
            # 오리엔테이션
            (r'여러분.*안녕|안녕하세요|반갑습니다|시작됐습니다', BlockType.ORIENTATION),
            # 감상 프레임
            (r'화자가\s*무엇을\s*어떻게|감상\s*프레임|사고\s*틀|분석\s*방법', BlockType.CONCEPT_FRAME),
            # 작품 분석
            (r'작품|지문|본문|고전|현대|시조|소설', BlockType.WORK_ANALYSIS),
            # 문제
            (r'\d+\s*번\s*문제|문제\s*\d+|마지막\s*문제', BlockType.PROBLEM_APPLICATION),
            # 해설
            (r'해설|정답|선택지|보기', BlockType.EXPLANATION),
            # 정리
            (r'정리|요약|한\s*판에\s*담판|마무리', BlockType.SUMMARY),
        ]
        
        # 문단 단위로 분할
        paragraphs = re.split(r'\n\s*\n+', script_text)
        
        current_block_type = None
        current_block_start = 0
        current_block_text = []
        
        for para_idx, para in enumerate(paragraphs):
            para = para.strip()
            if not para or len(para) < 20:
                continue
            
            # 블록 타입 감지
            detected_type = None
            for pattern, block_type in patterns:
                if re.search(pattern, para, re.IGNORECASE):
                    detected_type = block_type
                    break
            
            # 블록 전환 감지
            if detected_type and detected_type != current_block_type:
                # 이전 블록 저장
                if current_block_type and current_block_text:
                    block_text = '\n\n'.join(current_block_text)
                    start_idx = script_text.find(current_block_text[0])
                    end_idx = start_idx + len(block_text)
                    break_points.append((
                        start_idx,
                        end_idx,
                        current_block_type,
                        {'paragraph_index': para_idx - len(current_block_text)}
                    ))
                
                # 새 블록 시작
                current_block_type = detected_type
                current_block_text = [para]
            else:
                # 같은 블록 계속
                if not current_block_type:
                    current_block_type = BlockType.ORIENTATION  # 기본값
                current_block_text.append(para)
        
        # 마지막 블록 저장
        if current_block_type and current_block_text:
            block_text = '\n\n'.join(current_block_text)
            start_idx = script_text.find(current_block_text[0])
            end_idx = start_idx + len(block_text)
            break_points.append((
                start_idx,
                end_idx,
                current_block_type,
                {'paragraph_index': len(paragraphs) - len(current_block_text)}
            ))
        
        return break_points
    
    def _find_math_break_points(self, script_text: str) -> List[tuple]:
        """수학 과목 블록 분해 지점"""
        break_points = []
        
        patterns = [
            (r'문제\s*\d+|예제\s*\d+|유제\s*\d+', BlockType.ORIENTATION),
            (r'조건|전제|가정', BlockType.LEARNING_GOAL),
            (r'정의|개념|약속', BlockType.CONCEPT_FRAME),
            (r'핵심|중요|포인트', BlockType.EXAM_STRUCTURE),
            (r'풀이|해결|접근', BlockType.PROBLEM_APPLICATION),
            (r'정리|결론|마무리', BlockType.SUMMARY),
        ]
        
        # 수학은 문장 단위로도 분해 가능
        sentences = re.split(r'[.!?]\s+', script_text)
        
        current_block_type = None
        current_block_sentences = []
        current_start = 0
        
        for sent in sentences:
            sent = sent.strip()
            if not sent:
                continue
            
            detected_type = None
            for pattern, block_type in patterns:
                if re.search(pattern, sent, re.IGNORECASE):
                    detected_type = block_type
                    break
            
            if detected_type and detected_type != current_block_type:
                if current_block_type and current_block_sentences:
                    block_text = '. '.join(current_block_sentences) + '.'
                    start_idx = script_text.find(current_block_sentences[0])
                    end_idx = start_idx + len(block_text)
                    break_points.append((
                        start_idx, end_idx, current_block_type,
                        {'sentence_count': len(current_block_sentences)}
                    ))
                
                current_block_type = detected_type
                current_block_sentences = [sent]
            else:
                if not current_block_type:
                    current_block_type = BlockType.ORIENTATION
                current_block_sentences.append(sent)
        
        if current_block_type and current_block_sentences:
            block_text = '. '.join(current_block_sentences) + '.'
            start_idx = script_text.find(current_block_sentences[0])
            end_idx = start_idx + len(block_text)
            break_points.append((
                start_idx, end_idx, current_block_type,
                {'sentence_count': len(current_block_sentences)}
            ))
        
        return break_points
    
    def _find_english_break_points(self, script_text: str) -> List[tuple]:
        """영어 과목 블록 분해 지점"""
        # 국어와 유사하지만 영어 특화 패턴
        break_points = []
        
        patterns = [
            (r'여러분.*안녕|시작', BlockType.ORIENTATION),
            (r'독해\s*구조|문장\s*기능|글의\s*목적', BlockType.CONCEPT_FRAME),
            (r'표현|기법|어법', BlockType.EXAM_STRUCTURE),
            (r'논리\s*코드|전환어|연결어', BlockType.LEARNING_GOAL),
            (r'문제|접근', BlockType.PROBLEM_APPLICATION),
            (r'해설|설명', BlockType.EXPLANATION),
            (r'출제\s*포인트|정리', BlockType.SUMMARY),
        ]
        
        paragraphs = re.split(r'\n\s*\n+', script_text)
        
        current_block_type = None
        current_block_text = []
        
        for para_idx, para in enumerate(paragraphs):
            para = para.strip()
            if not para or len(para) < 20:
                continue
            
            detected_type = None
            for pattern, block_type in patterns:
                if re.search(pattern, para, re.IGNORECASE):
                    detected_type = block_type
                    break
            
            if detected_type and detected_type != current_block_type:
                if current_block_type and current_block_text:
                    block_text = '\n\n'.join(current_block_text)
                    start_idx = script_text.find(current_block_text[0])
                    end_idx = start_idx + len(block_text)
                    break_points.append((
                        start_idx, end_idx, current_block_type,
                        {'paragraph_index': para_idx - len(current_block_text)}
                    ))
                
                current_block_type = detected_type
                current_block_text = [para]
            else:
                if not current_block_type:
                    current_block_type = BlockType.ORIENTATION
                current_block_text.append(para)
        
        if current_block_type and current_block_text:
            block_text = '\n\n'.join(current_block_text)
            start_idx = script_text.find(current_block_text[0])
            end_idx = start_idx + len(block_text)
            break_points.append((
                start_idx, end_idx, current_block_type,
                {'paragraph_index': len(paragraphs) - len(current_block_text)}
            ))
        
        return break_points
    
    def _create_block(
        self,
        block_id: str,
        block_type: BlockType,
        block_text: str,
        start_idx: int,
        end_idx: int,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """블록 생성"""
        # 점자 신호
        braille_signal = self.BRAILLE_SIGNALS.get(self.subject, {}).get(
            block_type, "●○○"
        )
        
        # 상태 의미
        state_meaning = self.STATE_MEANINGS.get(self.subject, {}).get(
            block_type, "학습을 계속합니다"
        )
        
        # 오디오 포커스 (강의자가 무엇을 설명 중인지)
        audio_focus = self._extract_audio_focus(block_type, block_text)
        
        # 소스 범위 설명
        source_range = self._describe_source_range(start_idx, end_idx, context)
        
        return {
            "block_id": block_id,
            "block_type": block_type.value,
            "braille_signal": braille_signal,
            "audio_focus": audio_focus,
            "state_meaning": state_meaning,
            "source_range": source_range
        }
    
    def _extract_audio_focus(self, block_type: BlockType, block_text: str) -> str:
        """오디오 포커스 추출 (강의자가 무엇을 설명 중인지)"""
        # 블록 타입에 따른 기본 포커스
        focus_map = {
            BlockType.ORIENTATION: "강의 소개 및 목표",
            BlockType.LEARNING_GOAL: "학습 목표 및 조건",
            BlockType.CONCEPT_FRAME: "감상 프레임 및 분석 방법",
            BlockType.WORK_ANALYSIS: "작품 분석 및 해석",
            BlockType.PROBLEM_APPLICATION: "문제 풀이 및 적용",
            BlockType.EXPLANATION: "문제 해설 및 정답 설명",
            BlockType.SUMMARY: "핵심 내용 정리",
        }
        
        base_focus = focus_map.get(block_type, "학습 내용")
        
        # 텍스트에서 구체적 주제 추출 시도
        if block_type == BlockType.WORK_ANALYSIS:
            work_match = re.search(r'<([^>]+)>|([가-힣]+의\s*[가-힣]+)', block_text[:200])
            if work_match:
                return f"작품 분석: {work_match.group(1) or work_match.group(2)}"
        
        elif block_type == BlockType.PROBLEM_APPLICATION:
            problem_match = re.search(r'(\d+)\s*번\s*문제', block_text[:200])
            if problem_match:
                return f"문제 {problem_match.group(1)} 풀이"
        
        return base_focus
    
    def _describe_source_range(self, start_idx: int, end_idx: int, context: Dict[str, Any]) -> str:
        """소스 범위 설명"""
        if 'paragraph_index' in context:
            return f"문단 {context['paragraph_index'] + 1}부터"
        elif 'sentence_count' in context:
            return f"{context['sentence_count']}개 문장"
        else:
            return f"위치 {start_idx}~{end_idx}"


def decompose_lecture_script(
    script_text: str,
    subject: str,
    lesson_number: Optional[int] = None
) -> Dict[str, Any]:
    """
    강의대본을 레슨 블록으로 분해 (편의 함수)
    
    Args:
        script_text: 강의 대본 텍스트
        subject: 과목 ('korean', 'math', 'english')
        lesson_number: 강의 번호
        
    Returns:
        레슨 블록 JSON
    """
    subject_enum = Subject(subject)
    decomposer = LessonBlockDecomposer(subject=subject_enum)
    return decomposer.decompose(script_text, lesson_number)
