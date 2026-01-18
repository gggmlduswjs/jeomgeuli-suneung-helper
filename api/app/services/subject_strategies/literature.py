"""
수능특강 국어 문학 PDF 파싱 전략

문학 과목의 특징:
- 텍스트가 전부 (이미지는 거의 없음)
- 지문(passage)과 문제(question)가 명확히 분리됨
- 지문이 여러 페이지에 걸쳐 있을 수 있음
- 문제는 지문 이후에 나옴
"""
import re
from typing import List, Dict, Any, Optional
from app.services.pdf_parse.base_parser import BaseParser


class LiteratureParser(BaseParser):
    """
    문학 과목 PDF 파서
    
    핵심 구조:
    - 지문(passage): 문제 번호가 나오기 전까지의 텍스트
    - 문제(question): 숫자로 시작하는 질문
    - 보기(choice): ①②③④⑤ 패턴
    """
    
    # 지문 시작 패턴
    PASSAGE_START_PATTERNS = [
        r'\[([^\]]+)\]',  # [갈래/작가/작품명]
        r'<보기>',
        r'보기',
    ]
    
    # 문제 시작 패턴
    QUESTION_START_PATTERNS = [
        r'^\d+\.',  # "1."
        r'^다음\s*중',
        r'^윗글을',
        r'^이\s*작품',
        r'^다음\s*[가-힣]*\s*으로\s*가장',
    ]
    
    # 보기 패턴
    CHOICE_PATTERNS = [
        r'[①-⑤]',  # 원숫자
        r'\([1-5]\)',  # (1), (2)
    ]
    
    def __init__(self):
        self.current_passage_id = None
        self.passage_lines = []
        self.in_passage = False
    
    def parse(self, blocks: List[Dict[str, Any]], metadata: Optional[Dict] = None) -> Dict[str, Any]:
        """
        문학 PDF 블록을 구조화
        
        핵심: 지문과 문제를 절대 섞지 않음
        """
        pages = {}
        passages = []
        questions = []
        current_question = None
        
        # 블록이 "lines" 형식인지 "blocks" 형식인지 확인
        is_line_format = blocks and "line_number" in blocks[0] if blocks else False
        
        if is_line_format:
            # 줄 단위 형식 (LiteraturePDFExtractor 결과)
            return self._parse_lines(blocks, metadata)
        else:
            # 블록 단위 형식 (일반 추출기 결과)
            return self._parse_blocks(blocks, metadata)
    
    def _parse_lines(self, lines: List[Dict[str, Any]], metadata: Optional[Dict] = None) -> Dict[str, Any]:
        """줄 단위 파싱 (문학 전용)"""
        passages = []
        questions = []
        current_passage = None
        current_question = None
        
        for line in lines:
            page_num = line.get("page", 1)
            text = line.get("text", "").strip()
            
            if not text:
                continue
            
            # 문제 시작 감지
            if self.is_literature_question_start(text):
                # 이전 문제 저장
                if current_question:
                    questions.append(current_question)
                
                # 이전 지문 저장 (문제가 시작되면 지문 종료)
                if current_passage:
                    current_passage["text"] = "\n".join(current_passage["lines"])
                    passages.append(current_passage)
                    current_passage = None
                    self.in_passage = False
                
                # 새 문제 시작
                question_num = self._extract_question_number(text)
                question_id = self._generate_question_id(question_num, len(questions) + 1)
                
                current_question = {
                    "type": "question",
                    "question_id": question_id,
                    "question_number": question_num,
                    "passage_id": None,  # 나중에 연결
                    "question_text": text,
                    "choices": [],
                    "page": page_num,
                    "metadata": {},
                }
                
                # 가장 가까운 지문과 연결
                if passages:
                    current_question["passage_id"] = passages[-1]["passage_id"]
            
            # 보기 처리
            elif self._is_choice(text):
                if current_question:
                    choice_data = self._parse_choice(text)
                    current_question["choices"].append(choice_data)
            
            # 지문 시작 감지
            elif self.is_literature_passage_line(text):
                # 이전 지문 저장
                if current_passage:
                    current_passage["text"] = "\n".join(current_passage["lines"])
                    passages.append(current_passage)
                
                # 새 지문 시작
                passage_id = self._generate_passage_id(len(passages) + 1)
                current_passage = {
                    "type": "passage",
                    "passage_id": passage_id,
                    "title": self._extract_passage_title(text),
                    "lines": [text],
                    "text": "",  # 나중에 합침
                    "page_start": page_num,
                    "page_end": page_num,
                    "metadata": {},
                }
                self.in_passage = True
                self.current_passage_id = passage_id
            
            # 지문 내용 추가
            elif self.in_passage and current_passage:
                current_passage["lines"].append(text)
                current_passage["page_end"] = page_num
            
            # 문제 본문 추가
            elif current_question and not self._is_choice(text):
                if current_question["question_text"] != text:
                    current_question["question_text"] += "\n" + text
        
        # 마지막 단위 저장
        if current_passage:
            current_passage["text"] = "\n".join(current_passage["lines"])
            passages.append(current_passage)
        
        if current_question:
            questions.append(current_question)
        
        # 지문과 문제 연결
        for question in questions:
            if not question["passage_id"] and passages:
                # 가장 가까운 지문 연결
                question["passage_id"] = passages[-1]["passage_id"]
        
        return {
            "subject": "literature",
            "parser": self.__class__.__name__,
            "passages": passages,
            "questions": questions,
            "metadata": metadata or {},
            "statistics": {
                "total_passages": len(passages),
                "total_questions": len(questions),
                "passages_with_questions": len(set(q["passage_id"] for q in questions if q["passage_id"])),
            }
        }
    
    def _parse_blocks(self, blocks: List[Dict[str, Any]], metadata: Optional[Dict] = None) -> Dict[str, Any]:
        """블록 단위 파싱 (일반 추출기 결과)"""
        # 블록을 텍스트로 합치고 줄 단위로 분리
        lines = []
        for block in blocks:
            if block.get("type") == "text":
                content = block.get("content", "")
                # 줄 단위로 분리
                for line_text in content.split('\n'):
                    if line_text.strip():
                        lines.append({
                            "type": "text",
                            "text": line_text.strip(),
                            "page": block.get("page", 1),
                            "bbox": block.get("bbox", []),
                            "line_number": len(lines) + 1,
                        })
        
        return self._parse_lines(lines, metadata)
    
    def detect_content_type(self, block: Dict[str, Any]) -> str:
        """블록의 콘텐츠 타입 감지"""
        text = block.get("text") or block.get("content", "")
        
        if not text:
            return "other"
        
        # 문제 감지
        if self.is_literature_question_start(text):
            return "question"
        
        # 보기 감지
        if self._is_choice(text):
            return "choice"
        
        # 지문 감지
        if self.is_literature_passage_line(text):
            return "passage"
        
        return "other"
    
    def is_literature_passage_line(self, text: str) -> bool:
        """
        문학 지문 시작 감지
        
        지문 시작 신호:
        - [갈래/작가/작품명] 패턴
        - <보기> 또는 "보기" 패턴
        - 작품명 + 작가명 형식
        """
        # [작품명] 패턴
        if re.search(r'\[([^\]]+)\]', text):
            return True
        
        # <보기> 패턴
        if re.search(r'<보기>|보기', text):
            return True
        
        # 작품명 + 작가명 패턴 (예: "황조가(신라)")
        if re.search(r'[가-힣]+\([가-힣]+\)', text):
            return True
        
        # 작가명이 포함된 패턴 (예: "작가: 김동인")
        if re.search(r'작가\s*[:：]|저자\s*[:：]', text):
            return True
        
        return False
    
    def is_literature_question_start(self, text: str) -> bool:
        """
        문학 문제 시작 감지
        
        문제 시작 패턴:
        - ^\d+\. (예: "1.")
        - ^다음\s*중
        - ^윗글을
        - ^이\s*작품
        """
        # 첫 줄만 확인
        first_line = text.split('\n')[0].strip() if text else ""
        
        for pattern in self.QUESTION_START_PATTERNS:
            if re.search(pattern, first_line):
                return True
        
        return False
    
    def _extract_passage_title(self, text: str) -> Optional[str]:
        """지문 제목/작품명 추출"""
        # [작품명] 패턴
        bracket_match = re.search(r'\[([^\]]+)\]', text)
        if bracket_match:
            return bracket_match.group(1)
        
        # 작품명(작가) 패턴
        work_match = re.search(r'([가-힣]+)\([가-힣]+\)', text)
        if work_match:
            return work_match.group(1)
        
        # 첫 줄 (짧은 경우)
        first_line = text.split('\n')[0].strip()
        if len(first_line) < 50:
            return first_line
        
        return None
    
    def _extract_question_number(self, text: str) -> Optional[int]:
        """문제 번호 추출"""
        patterns = [
            r'^(\d+)\.',  # "1."
            r'문제\s*(\d+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return int(match.group(1))
        
        return None
    
    def _generate_passage_id(self, index: int) -> str:
        """지문 ID 생성 (예: LIT-01-P01)"""
        return f"LIT-01-P{index:02d}"
    
    def _generate_question_id(self, question_num: Optional[int], index: int) -> str:
        """문제 ID 생성 (예: LIT-01-Q01)"""
        num_str = f"{question_num:02d}" if question_num else f"{index:02d}"
        return f"LIT-01-Q{num_str}"
    
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
