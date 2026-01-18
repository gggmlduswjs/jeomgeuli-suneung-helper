"""
수능 영어 PDF 파싱 전략
"""
import re
from typing import List, Dict, Any, Optional
from app.services.pdf_parse.base_parser import BaseParser


class EnglishParser(BaseParser):
    """
    영어 과목 PDF 파서
    
    특징:
    - 지문 + 문제 구조가 명확
    - 빈칸 추론, 순서 배열, 삽입 문제가 많음
    - 문장 단위 분리가 중요
    """
    
    # 지문 시작 패턴
    PASSAGE_PATTERNS = [
        r'^[A-Z][^.!?]*[.!?]',  # 대문자로 시작하는 문장
        r'Read\s+the\s+following',
        r'다음\s+[가-힣]*\s+을?\s*읽고',
    ]
    
    # 문제 시작 패턴
    QUESTION_PATTERNS = [
        r'^(\d+)[\.\)]\s*',
        r'^Question\s+(\d+)',
        r'^문제\s*(\d+)',
    ]
    
    # 문제 유형 키워드
    QUESTION_TYPE_KEYWORDS = {
        "blank": [r'빈칸', r'blank', r'___', r'다음 중 알맞은 것'],
        "ordering": [r'순서', r'order', r'다음 문장들'],
        "insertion": [r'삽입', r'insert', r'넣을', r'들어갈'],
        "main_idea": [r'주제', r'main idea', r'요지', r'제목'],
        "detail": [r'세부사항', r'detail', r'내용'],
    }
    
    def parse(self, blocks: List[Dict[str, Any]], metadata: Optional[Dict] = None) -> Dict[str, Any]:
        """
        영어 PDF 블록을 구조화
        """
        pages = {}
        units = []
        current_passage = None
        current_question = None
        
        # 디버깅: 처음 50개 블록만 로그
        debug_mode = metadata.get("debug", False) if metadata else False
        debug_count = 0
        debug_limit = 50
        
        for block in blocks:
            page_num = block.get("page", 1)
            block_type = block.get("type", "text")
            # 줄 단위 형식(text) 또는 블록 형식(content) 모두 처리
            content = block.get("content") or block.get("text", "")
            
            # 디버그: 처음 N개 블록의 실제 내용 확인
            if debug_mode and debug_count < debug_limit:
                content_preview = content[:80].replace("\n", "\\n") if content else "(empty)"
                debug_count += 1
            
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
            
            if debug_mode and debug_count <= debug_limit:
                print(f"  [{debug_count:3d}] type={content_type:8s} | len={len(content):4d} | {content_preview}")
            
            # 지문 시작 감지
            if content_type == "passage":
                # 이전 지문 저장
                if current_passage:
                    units.append(current_passage)
                    pages[str(current_passage["page"])]["passages"].append(current_passage)
                
                # 새 지문 생성 (문장 단위로 분리)
                sentences = self._split_into_sentences(content)
                
                passage_id = self._generate_passage_id(len(units) + 1)
                current_passage = {
                    "type": "passage",
                    "passage_id": passage_id,
                    "sentences": [s["text"] for s in sentences],  # 순수 문장 배열
                    "sentences_detail": sentences,  # 상세 정보 (index, has_placeholder 등)
                    "full_text": content,
                    "placeholders": self._find_placeholders(content),  # 빈칸 위치 (___ 유지)
                    "page": page_num,
                    "metadata": {
                        "sentence_count": len(sentences),
                        "char_count": len(content),
                        "word_count": len(content.split()),
                    }
                }
            
            # 문제 시작 감지
            elif content_type == "question":
                # 이전 문제 저장
                if current_question:
                    units.append(current_question)
                    pages[str(current_question["page"])]["questions"].append(current_question)
                
                # 문제가 시작되면 지문 종료 (문학 파서처럼)
                if current_passage:
                    units.append(current_passage)
                    pages[str(current_passage["page"])]["passages"].append(current_passage)
                    # 가장 가까운 지문 참조
                    passage_id = current_passage["passage_id"]
                    current_passage = None
                else:
                    # 이전 지문이 있으면 참조
                    passage_id = units[-1]["passage_id"] if units and units[-1].get("type") == "passage" else None
                
                question_num = self._extract_question_number(content)
                question_type = self.detect_english_question_type(content)
                question_id = self._generate_question_id(question_num, len([u for u in units if u.get("type") == "question"]) + 1)
                
                current_question = {
                    "type": "question",
                    "question_id": question_id,
                    "question_number": question_num,
                    "question_type": question_type,  # blank, ordering, insertion, main_idea 등
                    "passage_id": passage_id,
                    "question": content,  # question_stem 대신 question
                    "choices": [],
                    "page": page_num,
                    "metadata": {},
                }
            
            # 보기 처리
            elif content_type == "choice":
                if current_question:
                    choice_data = self._parse_choice(content)
                    current_question["choices"].append(choice_data)
            
            # 지문 내용 추가 (문제가 아닌 연속된 줄을 지문으로 처리)
            elif (content_type == "other" or content_type == "passage") and not current_question:
                # 지문이 없으면 새 지문 시작
                if not current_passage:
                    sentences = self._split_into_sentences(content)
                    passage_id = self._generate_passage_id(len(units) + 1)
                    current_passage = {
                        "type": "passage",
                        "passage_id": passage_id,
                        "sentences": [s["text"] for s in sentences],
                        "sentences_detail": sentences,
                        "full_text": content,
                        "placeholders": self._find_placeholders(content),
                        "page": page_num,
                        "metadata": {
                            "sentence_count": len(sentences),
                            "char_count": len(content),
                            "word_count": len(content.split()),
                        }
                    }
                else:
                    # 기존 지문에 내용 추가
                    sentences = self._split_into_sentences(content)
                    current_passage["sentences"].extend([s["text"] for s in sentences])
                    current_passage["sentences_detail"].extend(sentences)
                    current_passage["full_text"] += "\n\n" + content
                    current_passage["metadata"]["sentence_count"] += len(sentences)
                    current_passage["metadata"]["char_count"] += len(content)
                    current_passage["metadata"]["word_count"] += len(content.split())
                    
                    # 빈칸 위치 업데이트
                    placeholders = self._find_placeholders(content)
                    if placeholders:
                        offset = len(current_passage["full_text"]) - len(content)
                        for ph in placeholders:
                            ph["position"] += offset
                        current_passage["placeholders"].extend(placeholders)
        
        # 마지막 단위 저장
        if current_passage:
            units.append(current_passage)
            pages[str(current_passage["page"])]["passages"].append(current_passage)
        
        if current_question:
            units.append(current_question)
            pages[str(current_question["page"])]["questions"].append(current_question)
        
        return {
            "subject": "english",
            "parser": self.__class__.__name__,
            "pages": pages,
            "units": units,
            "metadata": metadata or {},
            "statistics": {
                "total_units": len(units),
                "passages": len([u for u in units if u["type"] == "passage"]),
                "questions": len([u for u in units if u["type"] == "question"]),
                "question_types": self._count_question_types(units),
                "total_sentences": sum(
                    u.get("metadata", {}).get("sentence_count", 0)
                    for u in units if u["type"] == "passage"
                ),
            }
        }
    
    def detect_content_type(self, block: Dict[str, Any]) -> str:
        """블록의 콘텐츠 타입 감지"""
        # 줄 단위 형식(text) 또는 블록 형식(content) 모두 처리
        content = block.get("content") or block.get("text", "")
        content = content.strip()
        
        if not content:
            return "other"
        
        # 문제 발문 감지 (우선순위 높음)
        if re.search(r'다음\s+글의\s+목적|다음\s+글에\s+드러난|다음\s+빈칸|다음\s+문장', content):
            return "question"
        
        # 문제 번호 감지 (1., 2. 등으로 시작)
        if re.match(r'^\d+[\.\)]\s*', content):
            return "question"
        
        for pattern in self.QUESTION_PATTERNS:
            if re.search(pattern, content):
                return "question"
        
        # 보기 감지
        if re.search(r'[①-⑤]|\([1-5]\)', content):
            return "choice"
        
        # 지문 감지 - 더 유연한 패턴
        # 1. 영어 문장으로 시작 (대문자로 시작하고 마침표/물음표/느낌표로 끝)
        if re.match(r'^[A-Z][^.?!]*[.!?]\s*$', content):
            return "passage"
        
        # 2. 긴 영어 텍스트 (50자 이상, 영어 단어 포함)
        if len(content) >= 50:
            # 영어 단어 비율 확인
            english_words = re.findall(r'\b[A-Za-z]+\b', content)
            total_words = len(content.split())
            if total_words > 0 and len(english_words) / total_words > 0.5:
                return "passage"
        
        # 3. 짧은 줄이지만 영어 문장 패턴
        if re.match(r'^[A-Z][a-z]+', content) and len(content) >= 20:
            return "passage"
        
        return "other"
    
    def split_english_sentences(self, passage_text: str) -> List[str]:
        """
        영어 지문을 sentence 단위로 분리
        
        조건:
        - 마침표(.), 물음표(?) 기준
        - 약어(Mr., etc.)는 분리하지 않는다
        - 빈칸 ___ 은 문장 내부에 유지한다
        
        Returns:
            List[str]: 문장 리스트 (순수 텍스트)
        """
        # 약어 패턴 (마침표로 끝나지만 문장 종료가 아님)
        abbreviations = [
            r'Mr\.', r'Mrs\.', r'Ms\.', r'Dr\.', r'Prof\.',
            r'etc\.', r'e\.g\.', r'i\.e\.', r'vs\.', r'U\.S\.',
            r'Inc\.', r'Ltd\.', r'Co\.', r'St\.', r'Ave\.',
        ]
        
        # 약어 패턴 통합
        abbrev_pattern = '|'.join(f'({abbrev})' for abbrev in abbreviations)
        
        # 약어가 아닌 마침표/물음표/느낌표로 문장 분리
        # 약어 뒤의 마침표는 무시
        text = passage_text
        sentences = []
        
        # 간단한 구현: . ! ? 기준 분리, 하지만 약어는 보호
        # 약어를 임시 토큰으로 치환
        temp_tokens = {}
        for i, abbrev in enumerate(abbreviations):
            token = f"__ABBREV_{i}__"
            text = re.sub(abbrev, token, text)
            temp_tokens[token] = abbrev
        
        # 문장 구분 (마침표, 물음표, 느낌표 + 공백)
        sentence_pattern = r'([.!?]+)\s+'
        parts = re.split(sentence_pattern, text)
        
        current_sentence = ""
        for i, part in enumerate(parts):
            if re.match(r'^[.!?]+$', part):
                # 문장 종료 기호
                current_sentence += part
                if current_sentence.strip():
                    sentences.append(current_sentence.strip())
                current_sentence = ""
            else:
                current_sentence += part
        
        # 마지막 문장
        if current_sentence.strip():
            sentences.append(current_sentence.strip())
        
        # 약어 토큰 원복
        result = []
        for sent in sentences:
            for token, abbrev in temp_tokens.items():
                sent = sent.replace(token, abbrev)
            result.append(sent)
        
        return result
    
    def _split_into_sentences(self, text: str) -> List[Dict[str, Any]]:
        """
        텍스트를 문장으로 분리 (dict 형식, 내부 사용)
        
        Returns:
            List[Dict]: 문장 리스트
                - index: 문장 번호 (0-based)
                - text: 문장 텍스트
                - char_count: 문자 수
                - word_count: 단어 수
                - has_placeholder: 빈칸 포함 여부
        """
        # split_english_sentences 사용
        sentences_text = self.split_english_sentences(text)
        
        sentences = []
        for idx, sent_text in enumerate(sentences_text):
            # 빈칸 포함 여부
            has_placeholder = bool(re.search(r'___+|\(.+\)', sent_text))
            
            sentences.append({
                "index": idx,
                "text": sent_text,
                "char_count": len(sent_text),
                "word_count": len(sent_text.split()),
                "has_placeholder": has_placeholder,
            })
        
        return sentences
    
    def _find_placeholders(self, text: str) -> List[Dict[str, Any]]:
        """
        빈칸(placeholder) 위치 찾기
        
        Returns:
            List[Dict]: 빈칸 정보
                - position: 텍스트 내 위치
                - length: 길이
                - context: 주변 문맥
        """
        placeholders = []
        
        # ___ 패턴
        for match in re.finditer(r'_{3,}', text):
            placeholders.append({
                "position": match.start(),
                "length": len(match.group()),
                "type": "blank",
                "context": self._get_context(text, match.start(), match.end()),
            })
        
        # ( ) 패턴 (삽입 위치)
        for match in re.finditer(r'\(([^)]+)\)', text):
            placeholders.append({
                "position": match.start(),
                "length": len(match.group()),
                "type": "insertion",
                "context": self._get_context(text, match.start(), match.end()),
            })
        
        return placeholders
    
    def _get_context(self, text: str, start: int, end: int, window: int = 30) -> str:
        """빈칸 주변 문맥 추출"""
        context_start = max(0, start - window)
        context_end = min(len(text), end + window)
        return text[context_start:context_end]
    
    def detect_english_question_type(self, text: str) -> str:
        """
        수능특강 영어 문제 유형을 자동 분류
        
        분류 규칙:
        - 빈칸 추론: 지문 또는 문제에 ___ 포함
        - 순서 배열: (A), (B), (C) 또는 문장 나열 언급
        - 문장 삽입: 삽입 위치 ①②③④⑤ 언급
        - 주제/요지: main idea, topic, title 등
        - 그 외: general
        """
        text_lower = text.lower()
        
        # 빈칸 추론 (가장 명확)
        if re.search(r'___+|_+\s+', text):
            return "blank"
        
        # 순서 배열
        if (re.search(r'\([A-C]\)|\([a-c]\)', text) or
            re.search(r'순서|order|다음 문장들|the following', text_lower)):
            return "ordering"
        
        # 문장 삽입
        if (re.search(r'삽입|insert|넣을|들어갈', text_lower) or
            re.search(r'[①②③④⑤]\s*위치', text)):
            return "insertion"
        
        # 주제/요지
        if re.search(r'주제|main\s+idea|topic|요지|제목|title|subject', text_lower):
            return "main_idea"
        
        # 세부사항
        if re.search(r'세부|detail|내용|what|which|who', text_lower):
            return "detail"
        
        return "general"
    
    def _detect_question_type(self, text: str) -> str:
        """문제 유형 자동 분류 (내부 사용, detect_english_question_type 호출)"""
        return self.detect_english_question_type(text)
    
    def _extract_question_number(self, text: str) -> Optional[int]:
        """문제 번호 추출"""
        patterns = [
            r'^(\d+)[\.\)]',
            r'Question\s+(\d+)',
            r'^(\d+)\s*번',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return int(match.group(1))
        
        return None
    
    def group_english_choices(self, lines: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        수능특강 영어 문제의 보기를 묶기
        
        조건:
        - 보기 기호는 반드시 ①②③④⑤ 유지
        - 보기 순서는 변경하지 않는다
        - 다른 문제의 보기와 섞이지 않게 한다
        
        Args:
            lines: 줄 리스트 (text 필드 포함)
        
        Returns:
            List[Dict]: Choice 리스트
        """
        choices = []
        choice_pattern = re.compile(r'([①-⑤])\s*(.+)', re.DOTALL)
        
        for line in lines:
            text = line.get("text", "") or line.get("content", "")
            if not text:
                continue
            
            # ①②③④⑤ 패턴
            match = choice_pattern.search(text)
            if match:
                choice_num = match.group(1)
                choice_text = match.group(2).strip()
                
                choices.append({
                    "label": choice_num,  # ①, ② 등
                    "number": choice_num,
                    "text": choice_text,
                    "index": ord(choice_num) - ord('①'),
                    "char_count": len(choice_text),
                    "word_count": len(choice_text.split()),
                    "bbox": line.get("bbox"),
                    "page": line.get("page", 1),
                })
        
        # 인덱스 순으로 정렬 (이미 순서대로일 것이지만 확실히)
        choices.sort(key=lambda c: c.get("index", 0))
        
        return choices
    
    def _parse_choice(self, text: str) -> Dict[str, Any]:
        """보기 파싱 (내부 사용)"""
        # ①②③④⑤ 패턴
        choice_match = re.search(r'([①-⑤])\s*(.+)', text, re.DOTALL)
        if choice_match:
            choice_num = choice_match.group(1)
            choice_text = choice_match.group(2).strip()
            return {
                "label": choice_num,
                "number": choice_num,
                "text": choice_text,
                "index": ord(choice_num) - ord('①'),
                "char_count": len(choice_text),
                "word_count": len(choice_text.split()),
            }
        
        # (1), (2) 패턴
        paren_match = re.search(r'\(([1-5])\)\s*(.+)', text, re.DOTALL)
        if paren_match:
            choice_num = int(paren_match.group(1))
            choice_text = paren_match.group(2).strip()
            return {
                "label": str(choice_num),
                "number": str(choice_num),
                "text": choice_text,
                "index": choice_num - 1,
                "char_count": len(choice_text),
                "word_count": len(choice_text.split()),
            }
        
        return {
            "label": None,
            "number": None,
            "text": text.strip(),
            "index": 0,
        }
    
    def _generate_passage_id(self, index: int) -> str:
        """지문 ID 생성 (예: ENG-01-P01)"""
        return f"ENG-01-P{index:02d}"
    
    def _generate_question_id(self, question_num: Optional[int], index: int) -> str:
        """문제 ID 생성 (예: ENG-01-Q01)"""
        num_str = f"{question_num:02d}" if question_num else f"{index:02d}"
        return f"ENG-01-Q{num_str}"
    
    def _count_question_types(self, units: List[Dict[str, Any]]) -> Dict[str, int]:
        """문제 유형별 개수 집계"""
        type_count = {}
        for unit in units:
            if unit.get("type") == "question":
                q_type = unit.get("question_type", "unknown")
                type_count[q_type] = type_count.get(q_type, 0) + 1
        return type_count
