"""
PDF 구조화 추출 서비스
문제, 본문, 선택지 등을 구조화하여 추출
"""
import pdfplumber
import re
from typing import List, Dict, Optional
from pathlib import Path


class PDFStructureExtractor:
    def __init__(self):
        # 문제 패턴 (다양한 형식 지원)
        self.question_patterns = [
            r'문제\s*(\d+)\s*번',  # "문제 1번"
            r'(\d+)\s*번\s*문제',  # "1번 문제"
            r'(\d+)[\.\)]\s*',     # "1.", "1)"
            r'[①-⑤]',              # 원숫자
        ]
        
        # 선택지 패턴
        self.choice_patterns = [
            r'[①-⑤]\s*(.+?)(?=[①-⑤]|$)',  # 원숫자 선택지
            r'\(\d+\)\s*(.+?)(?=\(\d+\)|$)',  # (1), (2) 형식
            r'\d+[\.\)]\s*(.+?)(?=\d+[\.\)]|$)',  # 1., 2) 형식
        ]
        
        # 본문 패턴
        self.passage_patterns = [
            r'\[([^\]]+)\]',  # [작품명]
            r'작품\s*[:：]',
            r'지문\s*[:：]',
        ]
    
    def extract_structured_content(self, pdf_path: Path) -> Dict:
        """PDF에서 구조화된 콘텐츠 추출"""
        structured_content = {
            "lessons": [],
            "passages": [],
            "questions": []
        }
        
        try:
            with pdfplumber.open(pdf_path) as pdf:
                for page_num, page in enumerate(pdf.pages, 1):
                    # 텍스트 추출
                    text = page.extract_text()
                    if not text:
                        continue
                    
                    # 테이블 추출 (문제/선택지가 표 형식인 경우)
                    tables = page.extract_tables()
                    
                    # 페이지별 구조 분석
                    page_structure = self._analyze_page_structure(
                        text, tables, page_num
                    )
                    
                    structured_content["lessons"].extend(
                        page_structure.get("lessons", [])
                    )
                    structured_content["passages"].extend(
                        page_structure.get("passages", [])
                    )
                    structured_content["questions"].extend(
                        page_structure.get("questions", [])
                    )
        except Exception as e:
            print(f"[pdf_structure_extract] Error extracting structured content: {e}")
        
        return structured_content
    
    def _analyze_page_structure(
        self, 
        text: str, 
        tables: List, 
        page_num: int
    ) -> Dict:
        """페이지 구조 분석"""
        structure = {
            "lessons": [],
            "passages": [],
            "questions": []
        }
        
        # 1. 문제 추출
        questions = self._extract_questions(text, page_num)
        structure["questions"].extend(questions)
        
        # 2. 본문 추출
        passages = self._extract_passages(text, page_num)
        structure["passages"].extend(passages)
        
        # 3. 테이블에서 문제/선택지 추출
        if tables:
            table_questions = self._extract_from_tables(tables, page_num)
            structure["questions"].extend(table_questions)
        
        return structure
    
    def _extract_questions(self, text: str, page_num: int) -> List[Dict]:
        """문제 추출"""
        questions = []
        
        # 문제 번호 찾기
        for pattern in self.question_patterns:
            matches = re.finditer(pattern, text)
            for match in matches:
                question_num = match.group(1) if match.groups() else None
                start_pos = match.end()
                
                # 다음 문제까지 또는 선택지까지 추출
                next_question = re.search(
                    r'문제\s*\d+\s*번|(\d+)[\.\)]\s*', 
                    text[start_pos:]
                )
                end_pos = start_pos + (next_question.start() if next_question else len(text))
                
                question_text = text[start_pos:end_pos].strip()
                
                # 선택지 추출
                choices = self._extract_choices(question_text)
                
                questions.append({
                    "number": question_num,
                    "stem": question_text,
                    "choices": choices,
                    "page": page_num,
                    "position": match.start()
                })
        
        return questions
    
    def _extract_choices(self, text: str) -> List[Dict]:
        """선택지 추출"""
        choices = []
        
        # 원숫자 선택지
        choice_pattern = r'([①-⑤])\s*(.+?)(?=[①-⑤]|정답|해설|$)'
        matches = re.finditer(choice_pattern, text, re.DOTALL)
        
        for match in matches:
            choice_num = match.group(1)
            choice_text = match.group(2).strip()
            choices.append({
                "number": choice_num,
                "text": choice_text
            })
        
        # 원숫자가 없으면 괄호 형식 시도
        if not choices:
            paren_pattern = r'\((\d+)\)\s*(.+?)(?=\(\d+\)|정답|해설|$)'
            paren_matches = re.finditer(paren_pattern, text, re.DOTALL)
            for match in paren_matches:
                choice_num = match.group(1)
                choice_text = match.group(2).strip()
                choices.append({
                    "number": f"({choice_num})",
                    "text": choice_text
                })
        
        return choices
    
    def _extract_passages(self, text: str, page_num: int) -> List[Dict]:
        """본문 추출"""
        passages = []
        
        for pattern in self.passage_patterns:
            matches = re.finditer(pattern, text)
            for match in matches:
                passage_title = match.group(1) if match.groups() else None
                start_pos = match.end()
                
                # 다음 섹션까지 추출
                next_section = re.search(
                    r'\[|작품|지문|문제', 
                    text[start_pos:]
                )
                end_pos = start_pos + (next_section.start() if next_section else len(text))
                
                passage_text = text[start_pos:end_pos].strip()
                
                if passage_text:  # 빈 본문은 제외
                    passages.append({
                        "title": passage_title,
                        "content": passage_text,
                        "page": page_num,
                        "position": match.start()
                    })
        
        return passages
    
    def _extract_from_tables(self, tables: List, page_num: int) -> List[Dict]:
        """테이블에서 문제/선택지 추출"""
        questions = []
        
        for table in tables:
            # 테이블 구조 분석
            # 첫 번째 행이 헤더인지 확인
            if not table or len(table) < 2:
                continue
            
            # 문제 번호가 있는 행 찾기
            for row_idx, row in enumerate(table):
                if not row:
                    continue
                
                # 첫 번째 셀에 문제 번호가 있는지 확인
                first_cell = str(row[0]) if row[0] else ""
                question_match = re.search(r'(\d+)[\.\)]', first_cell)
                
                if question_match:
                    question_num = question_match.group(1)
                    question_stem = " ".join([str(cell) for cell in row[1:] if cell])
                    
                    # 다음 행들이 선택지일 수 있음
                    choices = []
                    for next_row in table[row_idx + 1:row_idx + 6]:  # 최대 5개 선택지
                        if not next_row:
                            break
                        choice_cell = str(next_row[0]) if next_row[0] else ""
                        if re.match(r'[①-⑤]|\(\d+\)', choice_cell):
                            choice_text = " ".join([str(cell) for cell in next_row[1:] if cell])
                            choices.append({
                                "number": choice_cell.strip(),
                                "text": choice_text
                            })
                        else:
                            break
                    
                    questions.append({
                        "number": question_num,
                        "stem": question_stem,
                        "choices": choices,
                        "page": page_num,
                        "position": 0  # 테이블 위치는 정확하지 않음
                    })
        
        return questions
