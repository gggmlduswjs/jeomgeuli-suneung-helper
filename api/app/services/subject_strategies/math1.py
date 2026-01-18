"""
수능특강 수학Ⅰ PDF 파싱 전략 (수학Ⅰ 전용)

수학Ⅰ 고정 구조:
- 개념 / 예제 / 유제로 구성
- 수식은 이미지 또는 벡터
- 문제 번호, 보기 기호(①②③④⑤), 수식은 반드시 분리
- 결과는 점자 변환 및 음성 시험 모드에 사용
"""
import re
from typing import List, Dict, Any, Optional
from app.services.pdf_parse.base_parser import BaseParser


class Math1Parser(BaseParser):
    """
    수능특강 수학Ⅰ 전용 파서
    
    섹션 타입:
    - concept: 개념 설명
    - example: 예제
    - exercise: 유제
    """
    
    # 섹션 시작 패턴
    SECTION_PATTERNS = {
        "concept": [
            r'^개념',
            r'^\d+\s*개념',
            r'^[가-힣]+\s*개념',
        ],
        "example": [
            r'^예제',
            r'^예제\s*\d+',
            r'^\d+\s*예제',
        ],
        "exercise": [
            r'^유제',
            r'^유제\s*\d+',
            r'^\d+\s*유제',
        ],
    }
    
    # 문제 시작 패턴
    QUESTION_PATTERNS = [
        r'^\d+\.',  # "1."
        r'^예제\s*\d+',
        r'^유제\s*\d+',
        r'^다음\s*중',
        r'^다음\s*[가-힣]*\s*의\s*값',
    ]
    
    # 보기 패턴
    CHOICE_PATTERNS = [
        r'[①-⑤]',  # 원숫자
        r'\([1-5]\)',  # (1), (2)
    ]
    
    def __init__(self):
        self.current_section = None
        self.current_chapter = None
    
    def parse(self, blocks: List[Dict[str, Any]], metadata: Optional[Dict] = None) -> Dict[str, Any]:
        """
        수학Ⅰ PDF 블록을 구조화
        """
        pages = {}
        items = []
        current_question = None
        formula_images = []
        
        for block in blocks:
            page_num = block.get("page", 1)
            block_type = block.get("type", "text")
            content = block.get("content", "")
            bbox = block.get("bbox", [])
            
            # 페이지 초기화
            if str(page_num) not in pages:
                pages[str(page_num)] = {
                    "page": page_num,
                    "sections": [],
                    "questions": [],
                    "formulas": [],
                }
            
            # 이미지 블록 처리 (수식 가능성)
            if block_type == "image":
                # 수식 이미지 감지 (중앙 정렬 + 특정 크기 비율)
                if self._is_formula_image(bbox, block):
                    formula_info = {
                        "formula_id": f"formula_{len(formula_images) + 1}",
                        "image_path": content if isinstance(content, str) else None,
                        "bbox": bbox,
                        "page": page_num,
                        "metadata": block.get("metadata", {}),
                    }
                    formula_images.append(formula_info)
                    pages[str(page_num)]["formulas"].append(formula_info)
                    
                    # 현재 문제에 수식 추가
                    if current_question:
                        current_question["formula_images"].append(formula_info)
                continue
            
            # 텍스트 블록 처리
            if block_type != "text" or not content:
                continue
            
            # 섹션 감지
            section_type = self._detect_section(content)
            if section_type:
                # 이전 섹션/문제 저장
                if current_question:
                    items.append(current_question)
                    pages[str(current_question["page"])]["questions"].append(current_question)
                
                self.current_section = section_type
                current_question = None
                pages[str(page_num)]["sections"].append(section_type)
                continue
            
            # 문제 시작 감지
            if self.is_math1_question_start(content):
                # 이전 문제 저장
                if current_question:
                    items.append(current_question)
                    pages[str(current_question["page"])]["questions"].append(current_question)
                
                # 새 문제 생성
                question_num = self._extract_question_number(content)
                question_id = self._generate_question_id(question_num)
                
                current_question = {
                    "type": "question",
                    "question_id": question_id,
                    "question_number": question_num,
                    "section": self.current_section or "unknown",
                    "chapter": self.current_chapter or "unknown",
                    "body": content,
                    "choices": [],
                    "formula_images": [],
                    "page": page_num,
                    "metadata": {
                        "difficulty": None,
                    }
                }
            
            # 보기 처리
            elif self._is_choice(content):
                if current_question:
                    choice_data = self._parse_choice(content)
                    current_question["choices"].append(choice_data)
                # 문제가 없으면 개념의 성질로 처리
                elif self.current_section == "concept":
                    # 개념의 성질 항목 (●, ▶, (1)(2) 등)
                    pass
            
            # 개념 내용 처리
            elif self.current_section == "concept" and not current_question:
                # 개념 설명 블록
                concept_item = {
                    "type": "concept",
                    "section": "concept",
                    "text": content,
                    "formulas": [],
                    "page": page_num,
                }
                items.append(concept_item)
        
        # 마지막 문제 저장
        if current_question:
            items.append(current_question)
            pages[str(current_question["page"])]["questions"].append(current_question)
        
        return {
            "subject": "math1",
            "parser": self.__class__.__name__,
            "chapter": self.current_chapter,
            "pages": pages,
            "items": items,  # concepts + questions
            "formula_images": formula_images,
            "metadata": metadata or {},
            "statistics": {
                "total_items": len(items),
                "concepts": len([i for i in items if i["type"] == "concept"]),
                "questions": len([i for i in items if i["type"] == "question"]),
                "formula_images": len(formula_images),
                "sections": {
                    "concept": len([i for i in items if i.get("section") == "concept"]),
                    "example": len([i for i in items if i.get("section") == "example"]),
                    "exercise": len([i for i in items if i.get("section") == "exercise"]),
                }
            }
        }
    
    def detect_content_type(self, block: Dict[str, Any]) -> str:
        """블록의 콘텐츠 타입 감지"""
        content = block.get("content", "")
        
        if not content:
            return "other"
        
        # 문제 감지
        if self.is_math1_question_start(content):
            return "question"
        
        # 보기 감지
        if self._is_choice(content):
            return "choice"
        
        # 섹션 감지
        if self._detect_section(content):
            return "section"
        
        # 개념 감지
        if self.current_section == "concept":
            return "concept"
        
        return "other"
    
    def is_math1_question_start(self, text: str) -> bool:
        """
        수학Ⅰ 문제 시작 감지
        
        패턴:
        - ^\d+\. (예: "1.")
        - ^예제\s*\d+
        - ^유제\s*\d+
        - ^다음\s*중
        """
        # 줄 시작부터 확인
        first_line = text.split('\n')[0].strip() if text else ""
        
        patterns = [
            r'^\d+\.',  # "1."
            r'^예제\s*\d+',
            r'^유제\s*\d+',
            r'^다음\s*중',
        ]
        
        for pattern in patterns:
            if re.search(pattern, first_line):
                return True
        
        return False
    
    def _detect_section(self, text: str) -> Optional[str]:
        """섹션 타입 감지 (concept/example/exercise)"""
        first_line = text.split('\n')[0].strip() if text else ""
        
        for section_type, patterns in self.SECTION_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, first_line):
                    return section_type
        
        return None
    
    def _extract_question_number(self, text: str) -> Optional[int]:
        """문제 번호 추출"""
        patterns = [
            r'^(\d+)\.',  # "1."
            r'예제\s*(\d+)',
            r'유제\s*(\d+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return int(match.group(1))
        
        return None
    
    def _generate_question_id(self, question_num: Optional[int]) -> str:
        """문제 ID 생성 (예: M1-01-03)"""
        chapter = self.current_chapter or "XX"
        section_abbr = {
            "example": "EX",
            "exercise": "UJ",
        }.get(self.current_section, "XX")
        
        num_str = f"{question_num:02d}" if question_num else "XX"
        
        return f"M1-{chapter}-{section_abbr}-{num_str}"
    
    def _is_choice(self, text: str) -> bool:
        """보기인지 감지"""
        for pattern in self.CHOICE_PATTERNS:
            if re.search(pattern, text):
                return True
        return False
    
    def _parse_choice(self, text: str) -> Dict[str, Any]:
        """보기 파싱"""
        # ①②③④⑤ 패턴
        choice_match = re.search(r'([①-⑤])\s*(.+)', text, re.DOTALL)
        if choice_match:
            choice_num = choice_match.group(1)
            choice_text = choice_match.group(2).strip()
            return {
                "number": choice_num,
                "text": choice_text,
                "index": ord(choice_num) - ord('①'),
            }
        
        # (1), (2) 패턴
        paren_match = re.search(r'\(([1-5])\)\s*(.+)', text, re.DOTALL)
        if paren_match:
            choice_num = int(paren_match.group(1))
            choice_text = paren_match.group(2).strip()
            return {
                "number": str(choice_num),
                "text": choice_text,
                "index": choice_num - 1,
            }
        
        return {
            "number": None,
            "text": text.strip(),
            "index": 0,
        }
    
    def _is_formula_image(self, bbox: List[float], block: Dict[str, Any]) -> bool:
        """
        수식 이미지인지 판단
        
        기준:
        - 중앙 정렬 (가로 중앙 근처)
        - 특정 크기 비율 (세로가 긴 직사각형)
        - 메타데이터에 수식 관련 키워드
        """
        if not bbox or len(bbox) < 4:
            return False
        
        width = bbox[2] - bbox[0]
        height = bbox[3] - bbox[1]
        
        if width == 0 or height == 0:
            return False
        
        # 가로세로 비율 (수식은 보통 세로가 길거나 정사각형)
        aspect_ratio = height / width
        
        # 중앙 정렬 여부 (페이지 중앙 ± 20% 이내)
        # 실제로는 페이지 너비를 알아야 하지만, 간단히 높이 비율로 판단
        center_threshold = 0.3  # 페이지 중앙 ±30%
        
        # 간단한 휴리스틱: 높이가 너비의 1.2배 이상이거나, 너비가 너무 작으면 수식 가능성
        if aspect_ratio > 1.2 or (width < 100 and height < 100):
            return True
        
        # 메타데이터 확인
        metadata = block.get("metadata", {})
        if "formula" in str(metadata).lower() or "math" in str(metadata).lower():
            return True
        
        return False
    
    def group_math1_choices(self, blocks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        수학Ⅰ 문제에서 보기(①②③④⑤)를 하나의 choices 배열로 묶기
        
        조건:
        - 보기 기호는 반드시 유지
        - y좌표 기준으로 정렬
        - 다른 문제의 보기와 섞이지 않도록
        """
        choices = []
        
        # 보기 블록만 필터링
        choice_blocks = [
            block for block in blocks
            if block.get("type") == "text" and self._is_choice(block.get("content", ""))
        ]
        
        # y좌표 기준 정렬
        choice_blocks.sort(key=lambda b: b.get("bbox", [0, 0, 0, 0])[1])
        
        # 파싱
        for block in choice_blocks:
            choice_data = self._parse_choice(block.get("content", ""))
            choice_data["bbox"] = block.get("bbox", [])
            choice_data["page"] = block.get("page", 1)
            choices.append(choice_data)
        
        # 인덱스 순으로 재정렬 (보기 번호 순서)
        choices.sort(key=lambda c: c.get("index", 0))
        
        return choices
