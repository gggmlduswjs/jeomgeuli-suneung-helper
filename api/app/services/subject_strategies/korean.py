"""
수능 국어 PDF 파싱 전략 (문학/비문학)
"""
import re
from typing import List, Dict, Any, Optional
from app.services.pdf_parse.base_parser import BaseParser


class KoreanParser(BaseParser):
    """
    국어 과목 PDF 파서
    
    특징:
    - 지문이 매우 길다
    - 문단 단위 구조가 중요
    - 문제는 지문 이후에 묶여 나옴
    - 보기는 문장 길이가 길다
    """
    
    # 지문 시작 패턴
    PASSAGE_PATTERNS = [
        r'\[([^\]]+)\]',  # [작품명]
        r'작품\s*[:：]',
        r'지문\s*[:：]',
        r'다음\s*[가-힣]*\s*을\s*읽고',
        r'다음\s*[가-힣]*\s*를\s*읽고',
    ]
    
    # 문제 시작 패턴
    QUESTION_PATTERNS = [
        r'^(\d+)[\.\)]\s*',
        r'^문제\s*(\d+)\s*번',
        r'^(\d+)\s*번',
    ]
    
    # 보기 패턴
    CHOICE_PATTERNS = [
        r'[①-⑤]',
        r'\([1-5]\)',
    ]
    
    def parse(self, blocks: List[Dict[str, Any]], metadata: Optional[Dict] = None) -> Dict[str, Any]:
        """
        국어 PDF 블록을 구조화
        """
        pages = {}
        units = []
        current_passage = None
        current_question = None
        
        for block in blocks:
            page_num = block.get("page", 1)
            block_type = block.get("type", "text")
            content = block.get("content", "")
            
            if block_type != "text" or not content:
                continue
            
            # 페이지 초기화
            if str(page_num) not in pages:
                pages[str(page_num)] = {
                    "page": page_num,
                    "passages": [],
                    "questions": [],
                }
            
            content_type = self.detect_content_type(block)
            
            # 지문 시작 감지
            if content_type == "passage":
                # 이전 지문 저장
                if current_passage:
                    units.append(current_passage)
                    pages[str(current_passage["page"])]["passages"].append(current_passage)
                
                # 새 지문 생성
                passage_title = self._extract_passage_title(content)
                paragraphs = self._split_into_paragraphs(content)
                
                current_passage = {
                    "type": "passage",
                    "passage_id": f"passage_{len(units) + 1}",
                    "title": passage_title,
                    "paragraphs": paragraphs,  # 문단 배열
                    "full_text": content,
                    "page": page_num,
                    "metadata": {
                        "paragraph_count": len(paragraphs),
                        "char_count": len(content),
                    }
                }
            
            # 문제 시작 감지
            elif content_type == "question":
                # 이전 문제 저장
                if current_question:
                    units.append(current_question)
                    pages[str(current_question["page"])]["questions"].append(current_question)
                
                question_num = self._extract_question_number(content)
                
                # 현재 지문 참조
                passage_id = current_passage["passage_id"] if current_passage else None
                
                current_question = {
                    "type": "question",
                    "question_number": question_num,
                    "passage_id": passage_id,  # 지문 참조
                    "question_stem": content,
                    "choices": [],
                    "page": page_num,
                    "metadata": {},
                }
            
            # 보기 처리
            elif content_type == "choice":
                if current_question:
                    choice_data = self._parse_choice(content)
                    current_question["choices"].append(choice_data)
            
            # 지문 내용 추가 (연속된 텍스트 블록)
            elif content_type == "other" and current_passage:
                # 현재 블록을 문단으로 추가
                paragraphs = self._split_into_paragraphs(content)
                current_passage["paragraphs"].extend(paragraphs)
                current_passage["full_text"] += "\n\n" + content
                current_passage["metadata"]["paragraph_count"] += len(paragraphs)
        
        # 마지막 단위 저장
        if current_passage:
            units.append(current_passage)
            pages[str(current_passage["page"])]["passages"].append(current_passage)
        
        if current_question:
            units.append(current_question)
            pages[str(current_question["page"])]["questions"].append(current_question)
        
        return {
            "subject": "korean",
            "parser": self.__class__.__name__,
            "pages": pages,
            "units": units,
            "metadata": metadata or {},
            "statistics": {
                "total_units": len(units),
                "passages": len([u for u in units if u["type"] == "passage"]),
                "questions": len([u for u in units if u["type"] == "question"]),
                "total_paragraphs": sum(
                    u.get("metadata", {}).get("paragraph_count", 0)
                    for u in units if u["type"] == "passage"
                ),
            }
        }
    
    def detect_content_type(self, block: Dict[str, Any]) -> str:
        """블록의 콘텐츠 타입 감지"""
        content = block.get("content", "")
        
        if not content:
            return "other"
        
        # 지문 감지
        for pattern in self.PASSAGE_PATTERNS:
            if re.search(pattern, content):
                return "passage"
        
        # 문제 감지
        for pattern in self.QUESTION_PATTERNS:
            if re.search(pattern, content, re.MULTILINE):
                return "question"
        
        # 보기 감지
        for pattern in self.CHOICE_PATTERNS:
            if re.search(pattern, content):
                return "choice"
        
        return "other"
    
    def _extract_passage_title(self, text: str) -> Optional[str]:
        """지문 제목 추출 (작품명 등)"""
        # [작품명] 패턴
        bracket_match = re.search(r'\[([^\]]+)\]', text)
        if bracket_match:
            return bracket_match.group(1)
        
        # "작품:" 패턴
        work_match = re.search(r'작품\s*[:：]\s*([^\n]+)', text)
        if work_match:
            return work_match.group(1).strip()
        
        # 첫 줄 (짧은 경우)
        first_line = text.split('\n')[0].strip()
        if len(first_line) < 50 and not first_line.endswith('.'):
            return first_line
        
        return None
    
    def _split_into_paragraphs(self, text: str) -> List[Dict[str, Any]]:
        """
        텍스트를 문단으로 분리
        
        Returns:
            List[Dict]: 문단 리스트
                - index: 문단 번호 (0-based)
                - text: 문단 텍스트
                - char_count: 문자 수
                - sentence_count: 문장 수
        """
        # 빈 줄 기준으로 문단 분리
        paragraphs_text = [p.strip() for p in re.split(r'\n\s*\n', text) if p.strip()]
        
        paragraphs = []
        for idx, para_text in enumerate(paragraphs_text):
            # 문장 수 계산
            sentences = re.split(r'[.!?。！？]', para_text)
            sentence_count = len([s for s in sentences if s.strip()])
            
            paragraphs.append({
                "index": idx,
                "text": para_text,
                "char_count": len(para_text),
                "sentence_count": sentence_count,
            })
        
        return paragraphs
    
    def _extract_question_number(self, text: str) -> Optional[int]:
        """문제 번호 추출"""
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
        choice_match = re.search(r'([①-⑤])\s*(.+)', text, re.DOTALL)
        if choice_match:
            choice_num = choice_match.group(1)
            choice_text = choice_match.group(2).strip()
            return {
                "number": choice_num,
                "text": choice_text,
                "index": ord(choice_num) - ord('①'),
                "char_count": len(choice_text),
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
                "char_count": len(choice_text),
            }
        
        return {
            "number": None,
            "text": text.strip(),
            "index": 0,
            "char_count": len(text),
        }
