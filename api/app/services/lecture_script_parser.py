"""
강의 대본 파싱 서비스
수능특강 강의 대본(텍스트)을 구조화하여 파싱

주요 섹션:
- OT (Overview): 강의 소개 및 전체 맵
- 개념 설명: 각 개념에 대한 상세 설명
- 예제/유제: 문제 풀이
- 정리: 핵심 요약
"""
import re
from typing import List, Dict, Any, Optional
from pathlib import Path


class LectureScriptParser:
    """
    강의 대본 파서
    
    구조:
    - 강 번호 추출
    - 섹션별 분류 (OT, 개념, 예제, 정리)
    - 핵심 키워드 추출
    - 수식/기호 인식
    """
    
    # 강 번호 패턴
    LESSON_PATTERN = re.compile(r'(\d+)\s*강', re.IGNORECASE)
    
    # 섹션 패턴 (과목별로 확장 가능)
    SECTION_PATTERNS = {
        "ot": [
            r'OT\s*[:\-]?',
            r'오티',
            r'overview',
            r'여러분.*안녕',
            r'안녕하세요',
            r'반갑습니다',
            r'합격의\s*기쁨',
            r'수능특강.*강의를\s*함께',
            r'시작입니다',
            r'출발',
        ],
        "overview": [
            r'전체.*맵',
            r'수학[Ⅰ1I].*구성',
            r'과목.*구성',
            r'순서',
            r'흐름',
            r'올해.*바꿔보',
            r'올해.*전면',
            r'방법론.*전달',
        ],
        "concept": [
            r'개념',
            r'정의',
            r'약속',
            r'글의\s*목적',
            r'논리\s*코드',
            r'심경.*변화',
            r'심경.*파악',
            r'분위기\s*파악',
            r'핵심\s*표현',
            r'전환의\s*표현',
            r'결과의\s*표현',
            r'문의의\s*표현',
            r'요청의\s*표현',
            r'^[가-힣]+의\s*[가-힣]+$',  # "a의 n제곱근" 같은 형태
        ],
        "example": [
            r'예제',
            r'예시',
            r'문제\s*\d+',
            r'gateway\s*문제',
            r'기출\s*문제',
            r'평가원\s*기출',
            r'1번\s*문제',
            r'2번\s*문제',
            r'3번\s*문제',
            r'4번\s*문제',
            r'문제를\s*풀',
            r'문제.*접근',
            r'정답',
            r'선택지',
        ],
        "exercise": [
            r'유제',
            r'연습',
            r'변형\s*문제',
            r'복습',
        ],
        "summary": [
            r'정리',
            r'요약',
            r'핵심',
            r'중요',
            r'마무리',
            r'돌파',
            r'다음\s*시간',
            r'숙제',
        ],
        "next_lesson": [
            r'다음\s*강',
            r'2강',
            r'다음\s*시간',
            r'두\s*번째\s*유형',
        ],
    }
    
    # 수학 키워드 패턴
    MATH_KEYWORDS = [
        r'[a-z]\s*[의의]?\s*[가-힣]*제곱근',
        r'[a-z]\s*[의의]?\s*n제곱근',
        r'지수',
        r'로그',
        r'함수',
        r'방정식',
        r'그래프',
        r'실수',
        r'허수',
        r'복소수',
        r'짝수',
        r'홀수',
    ]
    
    def __init__(self, subject: str = "math1"):
        """
        Args:
            subject: 과목명 (math1, literature, english 등)
        """
        self.subject = subject
        self.lesson_number = None
        self.sections = []
        
    def parse(self, script_text: str) -> Dict[str, Any]:
        """
        강의 대본 파싱
        
        Args:
            script_text: 강의 대본 텍스트
            
        Returns:
            파싱된 구조화 데이터
        """
        if not script_text:
            return self._empty_result()
        
        # 강 번호 추출
        self.lesson_number = self._extract_lesson_number(script_text)
        
        # 문단 단위로 분할
        paragraphs = self._split_into_paragraphs(script_text)
        
        # 섹션별로 분류
        sections = []
        current_section = None
        
        for para in paragraphs:
            if not para.strip():
                continue
            
            # 섹션 타입 감지
            section_type = self._detect_section_type(para)
            
            # 새로운 섹션이 시작되면
            if section_type and section_type != current_section:
                # 이전 섹션 저장
                if current_section:
                    sections.append({
                        "type": current_section,
                        "content": "\n".join(current_content),
                        "paragraphs": current_content,
                        "key_points": self._extract_key_points("\n".join(current_content)),
                        "math_expressions": self._extract_math_expressions("\n".join(current_content)),
                    })
                
                current_section = section_type
                current_content = [para]
            else:
                # 같은 섹션 계속
                if not current_section:
                    current_section = "general"
                    current_content = []
                
                current_content.append(para)
        
        # 마지막 섹션 저장
        if current_section and current_content:
            sections.append({
                "type": current_section,
                "content": "\n".join(current_content),
                "paragraphs": current_content,
                "key_points": self._extract_key_points("\n".join(current_content)),
                "math_expressions": self._extract_math_expressions("\n".join(current_content)),
            })
        
        # 전체 구조 분석
        structure = self._analyze_structure(script_text, sections)
        
        return {
            "subject": self.subject,
            "lesson_number": self.lesson_number,
            "sections": sections,
            "structure": structure,
            "statistics": {
                "total_paragraphs": len(paragraphs),
                "total_sections": len(sections),
                "section_types": {
                    section["type"]: sum(1 for s in sections if s["type"] == section["type"])
                    for section in sections
                },
                "total_length": len(script_text),
            },
            "metadata": {
                "parser": self.__class__.__name__,
                "subject": self.subject,
            }
        }
    
    def _extract_lesson_number(self, text: str) -> Optional[int]:
        """강 번호 추출"""
        match = self.LESSON_PATTERN.search(text)
        if match:
            return int(match.group(1))
        return None
    
    def _split_into_paragraphs(self, text: str) -> List[str]:
        """
        문단 단위로 분할
        
        기준:
        - 빈 줄로 구분
        - 문장 단위로도 분할 (마침표 기준)
        """
        # 먼저 빈 줄로 문단 분할
        paragraphs = re.split(r'\n\s*\n+', text)
        
        # 각 문단을 문장 단위로도 분할 (너무 긴 문단은 나눔)
        result = []
        for para in paragraphs:
            para = para.strip()
            if not para:
                continue
            
            # 너무 긴 문단은 문장 단위로 분할
            if len(para) > 500:
                sentences = re.split(r'([.!?]\s+)', para)
                # 문장 재결합 (짝수 인덱스가 문장, 홀수 인덱스가 구분자)
                current_sentence = ""
                for i, part in enumerate(sentences):
                    current_sentence += part
                    if i % 2 == 1:  # 구분자 다음
                        if len(current_sentence.strip()) > 50:
                            result.append(current_sentence.strip())
                            current_sentence = ""
                
                if current_sentence.strip():
                    result.append(current_sentence.strip())
            else:
                result.append(para)
        
        return result
    
    def _detect_section_type(self, text: str) -> Optional[str]:
        """섹션 타입 감지"""
        text_lower = text.lower()
        
        # 각 섹션 타입 확인
        for section_type, patterns in self.SECTION_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, text_lower):
                    return section_type
        
        return None
    
    def _extract_key_points(self, text: str) -> List[str]:
        """
        핵심 키워드/포인트 추출
        
        패턴:
        - "중요한 것은", "핵심은", "제일 중요한 건"
        - 번호가 있는 항목 (1., 2., ①, ②)
        - 강조 표현 ("반드시", "무조건", "꼭")
        """
        key_points = []
        
        # 강조 표현이 있는 문장
        emphasis_patterns = [
            r'[가-힣]*중요[가-힣]*\s*[것건는은]\s*[가-힣]*[는은다]',
            r'핵심[은는]\s*[가-힣]+',
            r'제일\s*중요[가-힣]*',
            r'반드시\s+[가-힣]+',
            r'무조건\s+[가-힣]+',
            r'꼭\s+[가-힣]+',
        ]
        
        sentences = re.split(r'[.!?]\s+', text)
        for sentence in sentences:
            for pattern in emphasis_patterns:
                if re.search(pattern, sentence):
                    # 앞뒤 문맥 포함
                    key_points.append(sentence.strip())
                    break
        
        # 번호가 있는 항목
        numbered_items = re.findall(r'[①-⑤\d]\s*[\.\)]\s*([^①-⑤\d\n]+)', text)
        key_points.extend([item.strip() for item in numbered_items])
        
        return list(set(key_points))  # 중복 제거
    
    def _extract_math_expressions(self, text: str) -> List[str]:
        """수학 표현식 추출"""
        expressions = []
        
        # 수학 키워드가 포함된 문장
        for keyword in self.MATH_KEYWORDS:
            pattern = rf'[^.!?]*{keyword}[^.!?]*'
            matches = re.findall(pattern, text, re.IGNORECASE)
            expressions.extend([m.strip() for m in matches])
        
        # 기호 패턴 (예: a의 n제곱근, x의 n제곱 등)
        symbol_patterns = [
            r'[a-z]\s*[의의]?\s*\d*제곱근',
            r'[a-z]\s*[의의]?\s*n제곱근',
            r'[a-z]\s*[의의]?\s*\d*제곱',
            r'x\s*[의의]?\s*n제곱\s*=\s*[a-z0-9]',
        ]
        
        for pattern in symbol_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            expressions.extend([m.strip() for m in matches])
        
        return list(set(expressions))
    
    def _analyze_structure(self, text: str, sections: List[Dict]) -> Dict[str, Any]:
        """전체 구조 분석"""
        structure = {
            "has_ot": any(s["type"] == "ot" for s in sections),
            "has_overview": any(s["type"] == "overview" for s in sections),
            "has_concept": any(s["type"] == "concept" for s in sections),
            "has_example": any(s["type"] == "example" for s in sections),
            "has_summary": any(s["type"] == "summary" for s in sections),
            "concepts": [],
            "examples": [],
        }
        
        # 개념 추출
        concept_sections = [s for s in sections if s["type"] == "concept"]
        for section in concept_sections:
            # 개념 정의 찾기 (예: "a의 n제곱근은...")
            definition_patterns = [
                r'([가-힣]+의\s*[가-힣]+제곱근)[은는]\s*([^.]+)',
                r'([가-힣]+)[은는]\s*([^.]+이라고?\s*[한다약속한다])',
            ]
            
            for pattern in definition_patterns:
                matches = re.findall(pattern, section["content"])
                for match in matches:
                    structure["concepts"].append({
                        "term": match[0],
                        "definition": match[1].strip() if len(match) > 1 else "",
                    })
        
        # 예제 추출
        example_sections = [s for s in sections if s["type"] == "example"]
        for section in example_sections:
            # 예제 번호 추출
            example_matches = re.findall(r'예제\s*(\d+)', section["content"])
            structure["examples"].extend([int(m) for m in example_matches])
        
        return structure
    
    def _empty_result(self) -> Dict[str, Any]:
        """빈 결과 반환"""
        return {
            "subject": self.subject,
            "lesson_number": None,
            "sections": [],
            "structure": {},
            "statistics": {
                "total_paragraphs": 0,
                "total_sections": 0,
                "section_types": {},
                "total_length": 0,
            },
            "metadata": {
                "parser": self.__class__.__name__,
                "subject": self.subject,
            }
        }


def parse_lecture_script_file(file_path: Path, subject: str = "math1") -> Dict[str, Any]:
    """
    강의 대본 파일 파싱
    
    Args:
        file_path: 대본 파일 경로 (.txt, .hwp 등)
        subject: 과목명
        
    Returns:
        파싱된 데이터
    """
    parser = LectureScriptParser(subject=subject)
    
    # 파일 읽기
    if not file_path.exists():
        raise FileNotFoundError(f"파일을 찾을 수 없습니다: {file_path}")
    
    if file_path.suffix.lower() == '.txt':
        with open(file_path, 'r', encoding='utf-8') as f:
            script_text = f.read()
    elif file_path.suffix.lower() in ['.hwp', '.hwpx']:
        from app.services.hwp_extract import extract_text_from_hwp
        script_text = extract_text_from_hwp(file_path)
        if not script_text:
            raise ValueError(f"HWP 파일에서 텍스트를 추출할 수 없습니다: {file_path}")
    else:
        raise ValueError(f"지원하지 않는 파일 형식: {file_path.suffix}")
    
    return parser.parse(script_text)


def parse_lecture_script_text(script_text: str, subject: str = "math1") -> Dict[str, Any]:
    """
    강의 대본 텍스트 파싱
    
    Args:
        script_text: 강의 대본 텍스트
        subject: 과목명
        
    Returns:
        파싱된 데이터
    """
    parser = LectureScriptParser(subject=subject)
    return parser.parse(script_text)
