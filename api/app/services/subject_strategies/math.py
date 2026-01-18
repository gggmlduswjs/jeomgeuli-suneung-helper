"""
수능 수학 PDF 파싱 전략
"""
import re
from typing import List, Dict, Any, Optional, Tuple
from app.services.pdf_parse.base_parser import BaseParser


class MathParser(BaseParser):
    """
    수학 과목 PDF 파서
    
    특징:
    - 수식은 대부분 이미지 또는 벡터 기반
    - 문제는 번호 또는 "다음 중"으로 시작
    - 보기는 ①②③④⑤ 형태
    - 개념 설명 → 예제 → 유제 구성
    """
    
    # 문제 시작 패턴
    QUESTION_PATTERNS = [
        r'^(\d+)[\.\)]\s*',  # "1.", "1)"
        r'^문제\s*(\d+)\s*번',
        r'^(\d+)\s*번',
        r'^다음\s*중',
        r'^다음\s*[가-힣]*\s*의\s*값',
    ]
    
    # 보기 패턴
    CHOICE_PATTERNS = [
        r'[①-⑤]',  # 원숫자
        r'\([1-5]\)',  # (1), (2)
        r'[1-5][\.\)]\s*',  # 1., 1)
    ]
    
    # 수식 관련 키워드
    FORMULA_KEYWORDS = [
        r'[가-힣]*수[가-힣]*',  # 함수, 수식
        r'[가-힣]*식[가-힣]*',  # 방정식, 부등식
        r'[가-힣]*근[가-힣]*',  # 근의 공식
        r'[가-힣]*값[가-힣]*',  # 값
    ]
    
    def parse(self, blocks: List[Dict[str, Any]], metadata: Optional[Dict] = None) -> Dict[str, Any]:
        """
        수학 PDF 블록을 구조화
        """
        pages = {}
        units = []
        current_unit = None
        formula_images = []
        
        for block in blocks:
            page_num = block.get("page", 1)
            block_type = block.get("type", "text")
            content = block.get("content", "")
            
            # 페이지 초기화
            if str(page_num) not in pages:
                pages[str(page_num)] = {
                    "page": page_num,
                    "units": [],
                    "formulas": [],
                }
            
            # 이미지 블록 처리 (수식 가능성)
            if block_type == "image":
                formula_info = {
                    "type": "formula_image",
                    "page": page_num,
                    "bbox": block.get("bbox", []),
                    "image_path": content if isinstance(content, str) else None,
                    "metadata": block.get("metadata", {}),
                }
                formula_images.append(formula_info)
                pages[str(page_num)]["formulas"].append(formula_info)
                continue
            
            # 텍스트 블록 처리
            if block_type != "text" or not content:
                continue
            
            content_type = self.detect_content_type(block)
            
            # 문제 시작 감지
            if content_type == "question":
                # 이전 단위 저장
                if current_unit:
                    units.append(current_unit)
                    pages[str(current_unit["page"])]["units"].append(current_unit)
                
                # 새 문제 단위 생성
                question_num = self._extract_question_number(content)
                current_unit = {
                    "type": "question",
                    "question_number": question_num,
                    "question_stem": content,
                    "choices": [],
                    "formula_images": [],
                    "page": page_num,
                    "metadata": {},
                }
            
            # 보기 감지
            elif content_type == "choice":
                if current_unit and current_unit["type"] == "question":
                    choice_data = self._parse_choice(content)
                    current_unit["choices"].append(choice_data)
            
            # 개념/설명 감지
            elif content_type == "concept":
                # 개념은 별도 단위로
                concept_unit = {
                    "type": "concept",
                    "title": self._extract_concept_title(content),
                    "content": content,
                    "page": page_num,
                    "metadata": {},
                }
                units.append(concept_unit)
                pages[str(page_num)]["units"].append(concept_unit)
            
            # 수식 감지 (텍스트 내 수식 표기)
            elif content_type == "formula":
                if current_unit:
                    current_unit["formula_images"].append({
                        "type": "text_formula",
                        "content": content,
                        "bbox": block.get("bbox", []),
                    })
        
        # 마지막 단위 저장
        if current_unit:
            units.append(current_unit)
            pages[str(current_unit["page"])]["units"].append(current_unit)
        
        return {
            "subject": "math",
            "parser": self.__class__.__name__,
            "pages": pages,
            "units": units,
            "formula_images": formula_images,
            "metadata": metadata or {},
            "statistics": {
                "total_units": len(units),
                "questions": len([u for u in units if u["type"] == "question"]),
                "concepts": len([u for u in units if u["type"] == "concept"]),
                "formula_images": len(formula_images),
            }
        }
    
    def detect_content_type(self, block: Dict[str, Any]) -> str:
        """
        블록의 콘텐츠 타입 감지
        """
        content = block.get("content", "")
        
        if not content:
            return "other"
        
        # 문제 감지
        for pattern in self.QUESTION_PATTERNS:
            if re.search(pattern, content, re.MULTILINE):
                return "question"
        
        # 보기 감지
        for pattern in self.CHOICE_PATTERNS:
            if re.search(pattern, content):
                return "choice"
        
        # 수식 감지 (키워드 기반)
        if any(re.search(keyword, content) for keyword in self.FORMULA_KEYWORDS):
            # 숫자와 연산자 패턴도 확인
            if re.search(r'[0-9+\-*/=<>≤≥≠≈±∞∑∏∫√]', content):
                return "formula"
        
        # 기본적으로 개념으로 처리
        return "concept"
    
    def _extract_question_number(self, text: str) -> Optional[int]:
        """문제 번호 추출"""
        # "1.", "1)", "문제 1번" 등에서 번호 추출
        patterns = [
            r'^(\d+)[\.\)]',
            r'문제\s*(\d+)\s*번',
            r'^(\d+)\s*번',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return int(match.group(1))
        
        return None
    
    def _parse_choice(self, text: str) -> Dict[str, Any]:
        """보기 파싱"""
        # ①②③④⑤ 패턴
        choice_match = re.search(r'([①-⑤])\s*(.+)', text)
        if choice_match:
            choice_num = choice_match.group(1)
            choice_text = choice_match.group(2).strip()
            return {
                "number": choice_num,
                "text": choice_text,
                "index": ord(choice_num) - ord('①'),  # 0-based index
            }
        
        # (1), (2) 패턴
        paren_match = re.search(r'\(([1-5])\)\s*(.+)', text)
        if paren_match:
            choice_num = int(paren_match.group(1))
            choice_text = paren_match.group(2).strip()
            return {
                "number": str(choice_num),
                "text": choice_text,
                "index": choice_num - 1,
            }
        
        # 기본 처리
        return {
            "number": None,
            "text": text.strip(),
            "index": 0,
        }
    
    def _extract_concept_title(self, text: str) -> str:
        """개념 제목 추출 (첫 줄 또는 첫 문장)"""
        lines = text.split('\n')
        first_line = lines[0].strip() if lines else ""
        
        # 제목처럼 보이는 줄 찾기
        if len(first_line) < 100 and not first_line.endswith('.'):
            return first_line
        
        # 첫 문장 추출
        sentences = re.split(r'[.!?。！？]', text)
        if sentences:
            return sentences[0].strip()[:50]
        
        return text[:50]
    
    def is_formula_like(self, text: str) -> bool:
        """텍스트가 수식인지 판단"""
        # 수학 기호 포함 여부
        math_symbols = r'[+\-*/=<>≤≥≠≈±∞∑∏∫√αβγδεθλμπσφω]'
        if re.search(math_symbols, text):
            return True
        
        # 변수 패턴 (x, y, z, f(x) 등)
        variable_pattern = r'\b[a-z]\([a-z0-9]+\)|\b[a-z]\s*[=<>]'
        if re.search(variable_pattern, text, re.IGNORECASE):
            return True
        
        return False
    
    def detect_question_start(self, text: str) -> bool:
        """문제 시작 여부 감지"""
        for pattern in self.QUESTION_PATTERNS:
            if re.search(pattern, text, re.MULTILINE):
                return True
        return False
    
    def group_choices(self, blocks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """보기 블록들을 그룹화"""
        choices = []
        for block in blocks:
            if self.detect_content_type(block) == "choice":
                choice_data = self._parse_choice(block.get("content", ""))
                choices.append({
                    **choice_data,
                    "bbox": block.get("bbox", []),
                    "page": block.get("page", 1),
                })
        
        # 번호 순으로 정렬
        choices.sort(key=lambda c: c.get("index", 0))
        return choices
