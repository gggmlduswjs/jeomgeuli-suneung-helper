"""
커리큘럼 자동 생성 시스템
강의대본(HWP) 분석을 통해 학습 단위를 자동으로 생성
"""
import re
import json
from typing import List, Dict, Any, Optional
from pathlib import Path
import re
from app.services.lecture_script_parser import LectureScriptParser
from app.services.hwp_extract import extract_text_from_hwp


class CurriculumGenerator:
    """커리큘럼 자동 생성기"""
    
    def __init__(self, subject: str):
        """
        Args:
            subject: 과목명 ('literature', 'math1', 'english')
        """
        self.subject = subject
        self.script_parser = LectureScriptParser(subject=subject)
        
    def analyze_lecture_script(self, hwp_path: Path) -> Dict[str, Any]:
        """
        강의대본 분석
        
        Args:
            hwp_path: HWP 파일 경로
            
        Returns:
            {
                'lesson_number': 1,
                'sections': [...],
                'break_points': [...],
                'pdf_references': [...],
                'learning_units': [...]
            }
        """
        # 0. 파일명에서 레슨 번호 및 구조 정보 추출 (우선)
        lesson_number_from_filename = self._extract_lesson_number_from_filename(hwp_path.name)
        file_structure = self._extract_structure_from_filename(hwp_path.name)
        
        # 1. HWP 파일에서 텍스트 추출
        script_text = extract_text_from_hwp(hwp_path)
        
        if not script_text:
            # 텍스트 추출 실패 시 파일명 기반 기본 구조 생성
            return self._create_structure_from_filename(hwp_path.name, lesson_number_from_filename, file_structure)
        
        # 2. 강의대본 파싱
        parsed = self.script_parser.parse(script_text)
        
        # 파일명에서 추출한 레슨 번호가 있으면 우선 사용
        lesson_number = lesson_number_from_filename if lesson_number_from_filename is not None else parsed.get('lesson_number', 0)
        
        # 3. 학습 단위 분할 지점 파악
        break_points = self._identify_break_points(parsed)
        
        # 4. 문학 과목의 경우 문제 번호 추출 및 구조화
        if self.subject == 'literature':
            parsed = self._structure_literature_script(parsed)
        
        # 5. PDF 참조 정보 추출
        pdf_refs = self._extract_pdf_references(parsed)
        
        # 5. 학습 단위 생성
        learning_units = self._create_learning_units(parsed, break_points, pdf_refs)
        
        # 파일명 기반 정보로 보완
        if file_structure and not learning_units:
            # 학습 단위가 없으면 파일명 기반으로 생성
            learning_units = self._create_units_from_filename_structure(file_structure, lesson_number)
        
        return {
            'lesson_number': lesson_number,
            'sections': parsed.get('sections', []) or file_structure.get('sections', []),
            'break_points': break_points,
            'pdf_references': pdf_refs,
            'learning_units': learning_units
        }
    
    def _extract_structure_from_filename(self, filename: str) -> Dict[str, Any]:
        """파일명에서 구조 정보 추출"""
        structure = {
            'category': None,
            'numbers': [],
            'sections': []
        }
        
        # 카테고리 추출 (예: [교과서_개념], [고전_시가])
        category_match = re.search(r'\[([^\]]+)\]', filename)
        if category_match:
            category = category_match.group(1)
            structure['category'] = category.replace('_', ' ')
            
            # 카테고리에 따른 섹션 타입 결정
            if '교과서' in category or '개념' in category:
                structure['sections'].append({'type': 'concept', 'name': category})
            elif '고전' in category or '시가' in category:
                structure['sections'].append({'type': 'textbook_content', 'name': '고전시가'})
            elif '현대' in category and '시' in category:
                structure['sections'].append({'type': 'textbook_content', 'name': '현대시'})
            elif '고전' in category and '산문' in category:
                structure['sections'].append({'type': 'textbook_content', 'name': '고전산문'})
            elif '현대' in category and '소설' in category:
                structure['sections'].append({'type': 'textbook_content', 'name': '현대소설'})
            elif '극' in category or '수필' in category:
                structure['sections'].append({'type': 'textbook_content', 'name': category})
            elif '갈래' in category or '복합' in category:
                structure['sections'].append({'type': 'textbook_content', 'name': '갈래복합'})
            elif '실전' in category:
                structure['sections'].append({'type': 'problem', 'name': category})
        
        # 번호 추출 (예: "1_2", "02_03_04")
        number_match = re.search(r'\]_(\d+(?:_\d+)*)', filename)
        if number_match:
            numbers = number_match.group(1).split('_')
            structure['numbers'] = [int(n) for n in numbers]
        
        return structure
    
    def _create_structure_from_filename(self, filename: str, lesson_number: Optional[int], 
                                       file_structure: Dict[str, Any]) -> Dict[str, Any]:
        """파일명 기반 기본 구조 생성"""
        # 파일명에서 정보 추출
        category = file_structure.get('category', '일반')
        numbers = file_structure.get('numbers', [])
        
        # 기본 섹션 생성
        sections = []
        if file_structure.get('sections'):
            for sec in file_structure['sections']:
                sections.append({
                    'type': sec.get('type', 'general'),
                    'content': f"{sec.get('name', category)} 관련 내용",
                    'paragraphs': []
                })
        else:
            sections.append({
                'type': 'general',
                'content': f"{category} 관련 내용",
                'paragraphs': []
            })
        
        # 기본 학습 단위 생성 (파일명 기반)
        learning_units = self._create_units_from_filename_structure(file_structure, lesson_number or 0)
        
        return {
            'lesson_number': lesson_number or 0,
            'sections': sections,
            'break_points': [],
            'pdf_references': [],
            'learning_units': learning_units
        }
    
    def _create_units_from_filename_structure(self, file_structure: Dict[str, Any], 
                                             lesson_number: int) -> List[Dict]:
        """파일명 구조 기반 학습 단위 생성"""
        learning_units = []
        category = file_structure.get('category', '일반')
        numbers = file_structure.get('numbers', [])
        
        # 번호별로 학습 단위 생성
        if numbers:
            for i, num in enumerate(numbers):
                learning_units.append({
                    'unit_index': i,
                    'section_type': 'textbook_content' if '교과서' not in category else 'concept',
                    'content': f"{category} {num}번 관련 내용",
                    'key_points': [],
                    'pdf_references': [{'type': 'problem', 'number': num}]
                })
        else:
            # 번호가 없으면 카테고리별로 하나의 단위
            learning_units.append({
                'unit_index': 0,
                'section_type': 'general',
                'content': f"{category} 관련 내용",
                'key_points': [],
                'pdf_references': []
            })
        
        return learning_units
    
    def _extract_lesson_number_from_filename(self, filename: str) -> Optional[int]:
        """파일명에서 레슨 번호 추출 (예: "01강_..." -> 1)"""
        import re
        # "01강", "1강", "오리엔테이션" 등 패턴 매칭
        patterns = [
            r'(\d+)강',  # "01강", "1강"
            r'^(\d+)_',  # "01_..."
            r'^(\d+)',   # "01..."
        ]
        
        for pattern in patterns:
            match = re.search(pattern, filename)
            if match:
                return int(match.group(1))
        
        # "오리엔테이션"은 0으로 처리
        if '오리엔테이션' in filename or 'orientation' in filename.lower():
            return 0
        
        return None
    
    def _identify_break_points(self, parsed: Dict) -> List[Dict]:
        """
        말하는 단위 분할 지점 파악
        
        강의대본에서 자연스러운 분할 지점 찾기:
        - 문장 끝
        - "자, 그다음에..." 같은 전환 표현
        - "먼저...", "그리고...", "마지막으로..." 같은 순서 표현
        - 문제 번호 (문제1, 문제2 등)
        """
        break_points = []
        
        for section in parsed.get('sections', []):
            content = section.get('content', '')
            paragraphs = section.get('paragraphs', [])
            
            if not paragraphs:
                # paragraphs가 없으면 content를 문장 단위로 분할
                sentences = re.split(r'[.!?]\s+', content)
                paragraphs = [s for s in sentences if s.strip()]
            
            for i, para in enumerate(paragraphs):
                # 전환 표현 감지
                transition_patterns = [
                    r'자,\s*그다음에',
                    r'자,\s*그다음',
                    r'먼저',
                    r'그리고',
                    r'마지막으로',
                    r'다음\s*페이지',
                    r'이제',
                    r'그럼',
                    r'문제\s*\d+',
                    r'예제\s*\d+',
                    r'유제\s*\d+',
                ]
                
                for pattern in transition_patterns:
                    if re.search(pattern, para, re.IGNORECASE):
                        break_points.append({
                            'section_type': section.get('type', 'general'),
                            'paragraph_index': i,
                            'text': para[:50] + '...' if len(para) > 50 else para,
                            'transition_type': self._classify_transition(para)
                        })
                        break
        
        return break_points
    
    def _classify_transition(self, text: str) -> str:
        """전환 표현 분류"""
        if re.search(r'먼저', text, re.IGNORECASE):
            return 'sequence_start'
        elif re.search(r'그리고|또한', text, re.IGNORECASE):
            return 'sequence_continue'
        elif re.search(r'마지막으로|마지막', text, re.IGNORECASE):
            return 'sequence_end'
        elif re.search(r'문제|예제|유제', text, re.IGNORECASE):
            return 'problem'
        elif re.search(r'자,\s*그다음', text, re.IGNORECASE):
            return 'transition'
        else:
            return 'general'
    
    def _extract_pdf_references(self, parsed: Dict) -> List[Dict]:
        """
        PDF 참조 정보 추출
        
        강의대본에서 언급되는 PDF 내용:
        - "교과서 개념 1번 문제"
        - "고전시가 본문"
        - "수학Ⅰ 15페이지"
        """
        pdf_refs = []
        
        # 문제 번호 패턴
        problem_pattern = r'(문제|예제|유제)\s*(\d+)'
        # 페이지 참조 패턴
        page_pattern = r'(\d+)\s*페이지'
        # 교재 섹션 참조 패턴
        section_pattern = r'(교과서\s*개념|고전시가|현대시|고전\s*산문|현대\s*소설|극\s*수필|갈래\s*복합|실전)'
        
        for section in parsed.get('sections', []):
            content = section.get('content', '')
            
            # 문제 참조 찾기
            for match in re.finditer(problem_pattern, content, re.IGNORECASE):
                pdf_refs.append({
                    'type': 'problem',
                    'number': int(match.group(2)),
                    'section': section.get('type', 'general'),
                    'context': self._extract_context(content, match.start(), match.end())
                })
            
            # 페이지 참조 찾기
            for match in re.finditer(page_pattern, content, re.IGNORECASE):
                pdf_refs.append({
                    'type': 'page',
                    'number': int(match.group(1)),
                    'section': section.get('type', 'general'),
                    'context': self._extract_context(content, match.start(), match.end())
                })
            
            # 섹션 참조 찾기
            for match in re.finditer(section_pattern, content, re.IGNORECASE):
                pdf_refs.append({
                    'type': 'section',
                    'name': match.group(1),
                    'section': section.get('type', 'general'),
                    'context': self._extract_context(content, match.start(), match.end())
                })
        
        return pdf_refs
    
    def _extract_context(self, text: str, start: int, end: int, context_size: int = 50) -> str:
        """참조 주변 텍스트 추출"""
        context_start = max(0, start - context_size)
        context_end = min(len(text), end + context_size)
        return text[context_start:context_end].strip()
    
    def _create_learning_units(self, parsed: Dict, break_points: List[Dict], pdf_refs: List[Dict]) -> List[Dict]:
        """
        학습 단위 생성
        
        말하는 단위로 분할된 학습 콘텐츠 단위
        문학 과목의 경우:
        - 교과서 개념 → 개념 설명 단위
        - 본문/지문 → 작품 분석 단위
        - 문제 → 문제 풀이 단위
        """
        learning_units = []
        unit_index = 0
        
        # 섹션이 없으면 전체를 하나의 단위로
        sections = parsed.get('sections', [])
        if not sections:
            # 전체 텍스트를 의미있는 단위로 분할
            all_content = '\n'.join([s.get('content', '') for s in sections]) if sections else ''
            if not all_content:
                return []
            
            # 문장 단위로 분할
            sentences = re.split(r'([.!?]\s+)', all_content)
            current_unit = []
            current_length = 0
            max_unit_length = 500  # 최대 단위 길이
            
            for i in range(0, len(sentences), 2):  # 짝수 인덱스가 문장
                if i < len(sentences):
                    sentence = sentences[i] + (sentences[i+1] if i+1 < len(sentences) else '')
                    sentence_length = len(sentence)
                    
                    if current_length + sentence_length > max_unit_length and current_unit:
                        # 현재 단위 저장
                        unit_text = ''.join(current_unit)
                        learning_units.append({
                            'unit_index': unit_index,
                            'section_type': 'general',
                            'content': unit_text.strip(),
                            'key_points': self._extract_key_points_from_text(unit_text),
                            'pdf_references': []
                        })
                        unit_index += 1
                        current_unit = []
                        current_length = 0
                    
                    current_unit.append(sentence)
                    current_length += sentence_length
            
            # 마지막 단위
            if current_unit:
                unit_text = ''.join(current_unit)
                learning_units.append({
                    'unit_index': unit_index,
                    'section_type': 'general',
                    'content': unit_text.strip(),
                    'key_points': self._extract_key_points_from_text(unit_text),
                    'pdf_references': []
                })
            
            return learning_units
        
        # 섹션별로 학습 단위 생성
        for section in sections:
            section_type = section.get('type', 'general')
            content = section.get('content', '')
            paragraphs = section.get('paragraphs', [])
            
            if not paragraphs:
                # paragraphs가 없으면 content를 문장 단위로 분할
                sentences = re.split(r'([.!?]\s+)', content)
                # 문장과 구분자를 합쳐서 paragraphs 생성
                paragraphs = []
                for i in range(0, len(sentences), 2):
                    if i < len(sentences):
                        para = sentences[i] + (sentences[i+1] if i+1 < len(sentences) else '')
                        if para.strip():
                            paragraphs.append(para.strip())
            
            # 해당 섹션의 분할 지점 찾기
            section_breaks = [bp for bp in break_points 
                            if bp.get('section_type') == section_type]
            
            # 문학 과목 특화: 의미있는 단위로 분할
            if self.subject == 'literature':
                learning_units.extend(self._create_literature_units(
                    section, paragraphs, section_breaks, pdf_refs, unit_index
                ))
                unit_index += len([u for u in learning_units if u.get('unit_index', 0) >= unit_index])
            else:
                # 기본 분할 로직
                if not section_breaks:
                    # 분할 지점이 없으면 섹션 전체를 하나의 단위로
                    # 단, 너무 길면 여러 단위로 분할
                    if len(content) > 1000:
                        # 여러 단위로 분할
                        units = self._split_long_content(content, section_type, pdf_refs, unit_index)
                        learning_units.extend(units)
                        unit_index += len(units)
                    else:
                        # PDF 참조 매칭
                        unit_pdf_refs = [ref for ref in pdf_refs 
                                       if ref.get('section') == section_type]
                        
                        learning_units.append({
                            'unit_index': unit_index,
                            'section_type': section_type,
                            'content': content,
                            'key_points': section.get('key_points', []),
                            'pdf_references': unit_pdf_refs
                        })
                        unit_index += 1
                else:
                    # 분할 지점 기준으로 여러 단위로 나누기
                    current_unit_content = []
                    
                    for i, para in enumerate(paragraphs):
                        current_unit_content.append(para)
                        
                        # 분할 지점인지 확인
                        if any(bp.get('paragraph_index') == i for bp in section_breaks):
                            # PDF 참조 매칭 (현재 단위 내용 기준)
                            unit_text = '\n'.join(current_unit_content)
                            unit_pdf_refs = [ref for ref in pdf_refs 
                                            if ref.get('section') == section_type and
                                            ref.get('context', '') in unit_text]
                            
                            learning_units.append({
                                'unit_index': unit_index,
                                'section_type': section_type,
                                'content': unit_text,
                                'key_points': self._extract_key_points_from_text(unit_text),
                                'pdf_references': unit_pdf_refs
                            })
                            unit_index += 1
                            current_unit_content = []
                    
                    # 마지막 남은 내용
                    if current_unit_content:
                        unit_text = '\n'.join(current_unit_content)
                        unit_pdf_refs = [ref for ref in pdf_refs 
                                        if ref.get('section') == section_type and
                                        ref.get('context', '') in unit_text]
                        
                        learning_units.append({
                            'unit_index': unit_index,
                            'section_type': section_type,
                            'content': unit_text,
                            'key_points': self._extract_key_points_from_text(unit_text),
                            'pdf_references': unit_pdf_refs
                        })
                        unit_index += 1
        
        return learning_units
    
    def _create_literature_units(self, section: Dict, paragraphs: List[str], 
                                section_breaks: List[Dict], pdf_refs: List[Dict], 
                                start_index: int) -> List[Dict]:
        """문학 과목 특화 학습 단위 생성"""
        learning_units = []
        unit_index = start_index
        section_type = section.get('type', 'general')
        
        # 문학 특화 분할 패턴
        # 1. 문제 번호 기준 분할 (문제1, 문제2 등)
        # 2. 작품/본문 기준 분할
        # 3. 전환 표현 기준 분할
        
        current_unit = []
        current_length = 0
        max_unit_length = 400  # 문학은 조금 더 짧게
        
        for i, para in enumerate(paragraphs):
            # 문제 번호 감지
            problem_match = re.search(r'(?:문제|예제|유제)\s*[①②③④⑤]?\s*(\d+)', para)
            # 작품/본문 시작 감지
            work_match = re.search(r'(?:본문|지문|작품|고전|현대)', para)
            # 전환 표현 감지
            transition_match = re.search(r'(?:자,\s*그다음|먼저|그리고|마지막으로|이제|그럼)', para)
            
            # 분할 지점인지 확인
            should_split = (
                problem_match or 
                work_match or 
                transition_match or
                any(bp.get('paragraph_index') == i for bp in section_breaks) or
                (current_length + len(para) > max_unit_length and current_unit)
            )
            
            if should_split and current_unit:
                # 현재 단위 저장
                unit_text = '\n'.join(current_unit)
                unit_pdf_refs = [ref for ref in pdf_refs 
                               if ref.get('section') == section_type and
                               ref.get('context', '') in unit_text]
                
                learning_units.append({
                    'unit_index': unit_index,
                    'section_type': section_type,
                    'content': unit_text.strip(),
                    'key_points': self._extract_key_points_from_text(unit_text),
                    'pdf_references': unit_pdf_refs
                })
                unit_index += 1
                current_unit = []
                current_length = 0
            
            current_unit.append(para)
            current_length += len(para)
        
        # 마지막 단위
        if current_unit:
            unit_text = '\n'.join(current_unit)
            unit_pdf_refs = [ref for ref in pdf_refs 
                           if ref.get('section') == section_type and
                           ref.get('context', '') in unit_text]
            
            learning_units.append({
                'unit_index': unit_index,
                'section_type': section_type,
                'content': unit_text.strip(),
                'key_points': self._extract_key_points_from_text(unit_text),
                'pdf_references': unit_pdf_refs
            })
        
        return learning_units
    
    def _split_long_content(self, content: str, section_type: str, 
                            pdf_refs: List[Dict], start_index: int) -> List[Dict]:
        """긴 내용을 여러 단위로 분할"""
        units = []
        unit_index = start_index
        
        # 문장 단위로 분할
        sentences = re.split(r'([.!?]\s+)', content)
        current_unit = []
        current_length = 0
        max_length = 500
        
        for i in range(0, len(sentences), 2):
            if i < len(sentences):
                sentence = sentences[i] + (sentences[i+1] if i+1 < len(sentences) else '')
                sentence_length = len(sentence)
                
                if current_length + sentence_length > max_length and current_unit:
                    unit_text = ''.join(current_unit)
                    unit_pdf_refs = [ref for ref in pdf_refs 
                                   if ref.get('context', '') in unit_text]
                    
                    units.append({
                        'unit_index': unit_index,
                        'section_type': section_type,
                        'content': unit_text.strip(),
                        'key_points': self._extract_key_points_from_text(unit_text),
                        'pdf_references': unit_pdf_refs
                    })
                    unit_index += 1
                    current_unit = []
                    current_length = 0
                
                current_unit.append(sentence)
                current_length += sentence_length
        
        # 마지막 단위
        if current_unit:
            unit_text = ''.join(current_unit)
            unit_pdf_refs = [ref for ref in pdf_refs 
                           if ref.get('context', '') in unit_text]
            
            units.append({
                'unit_index': unit_index,
                'section_type': section_type,
                'content': unit_text.strip(),
                'key_points': self._extract_key_points_from_text(unit_text),
                'pdf_references': unit_pdf_refs
            })
        
        return units
    
    def _extract_key_points_from_text(self, text: str) -> List[str]:
        """텍스트에서 핵심 포인트 추출"""
        key_points = []
        
        # 핵심 포인트 패턴
        patterns = [
            r'핵심[은는]?\s*[:：]?\s*([^\.]+)',
            r'중요[한]?\s*[:：]?\s*([^\.]+)',
            r'요점[은는]?\s*[:：]?\s*([^\.]+)',
        ]
        
        for pattern in patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                key_point = match.group(1).strip()
                if key_point and len(key_point) > 3:
                    key_points.append(key_point)
        
        return key_points[:5]  # 최대 5개
    
    def _empty_result(self) -> Dict[str, Any]:
        """빈 결과 반환"""
        return {
            'lesson_number': 0,
            'sections': [],
            'break_points': [],
            'pdf_references': [],
            'learning_units': []
        }
    
    def _structure_literature_script(self, parsed: Dict) -> Dict:
        """
        문학 강의 대본을 인트로, 본문, 문제 1, 문제 2 형식으로 구조화
        
        섹션 구조:
        - intro: 강의 시작 인사 및 소개
        - main_content: 작품 분석 본문
        - problem_1, problem_2, problem_3: 각 문제별 해설
        """
        sections = parsed.get('sections', [])
        structured_sections = []
        current_problem_num = None
        current_problem_content = []
        
        for section in sections:
            section_type = section.get('type', 'general')
            content = section.get('content', '')
            paragraphs = section.get('paragraphs', [])
            
            # 인트로 섹션 감지
            if section_type == 'ot' or any(re.search(r'여러분.*안녕|안녕하세요|반갑습니다|시작됐습니다', para, re.IGNORECASE) 
                                          for para in (paragraphs if paragraphs else [content])):
                if structured_sections and structured_sections[-1].get('type') == 'intro':
                    # 기존 인트로에 추가
                    structured_sections[-1]['content'] += '\n\n' + content
                    structured_sections[-1]['paragraphs'].extend(paragraphs if paragraphs else [content])
                else:
                    structured_sections.append({
                        'type': 'intro',
                        'name': '인트로',
                        'content': content,
                        'paragraphs': paragraphs if paragraphs else [content],
                        'key_points': section.get('key_points', [])
                    })
                continue
            
            # 문제 번호 추출 (예: "1번 문제", "2번 문제", "마지막 문제")
            problem_match = re.search(r'(\d+)\s*번\s*문제|마지막\s*문제|마지막.*(\d+)\s*번', content, re.IGNORECASE)
            if problem_match:
                # 이전 문제 저장
                if current_problem_num is not None:
                    structured_sections.append({
                        'type': f'problem_{current_problem_num}',
                        'name': f'문제 {current_problem_num}',
                        'content': '\n\n'.join(current_problem_content),
                        'paragraphs': current_problem_content,
                        'key_points': []
                    })
                
                # 새 문제 시작
                problem_num = int(problem_match.group(1)) if problem_match.group(1) else (
                    int(problem_match.group(2)) if problem_match.group(2) else 
                    (current_problem_num + 1 if current_problem_num is not None else 1)
                )
                current_problem_num = problem_num
                current_problem_content = [content]
                continue
            
            # 문제 섹션이면 문제 내용에 추가
            if current_problem_num is not None:
                current_problem_content.append(content)
                continue
            
            # 본문 섹션 (작품 분석 등)
            if section_type in ['textbook_content', 'concept', 'summary'] or not structured_sections:
                # 본문 섹션이 없으면 생성
                if not structured_sections or structured_sections[-1].get('type') != 'main_content':
                    structured_sections.append({
                        'type': 'main_content',
                        'name': '본문',
                        'content': content,
                        'paragraphs': paragraphs if paragraphs else [content],
                        'key_points': section.get('key_points', [])
                    })
                else:
                    # 기존 본문에 추가
                    structured_sections[-1]['content'] += '\n\n' + content
                    structured_sections[-1]['paragraphs'].extend(paragraphs if paragraphs else [content])
                continue
            
            # 기타 섹션
            structured_sections.append({
                'type': section_type,
                'name': section.get('name', section_type),
                'content': content,
                'paragraphs': paragraphs if paragraphs else [content],
                'key_points': section.get('key_points', [])
            })
        
        # 마지막 문제 저장
        if current_problem_num is not None:
            structured_sections.append({
                'type': f'problem_{current_problem_num}',
                'name': f'문제 {current_problem_num}',
                'content': '\n\n'.join(current_problem_content),
                'paragraphs': current_problem_content,
                'key_points': []
            })
        
        # 구조화된 섹션으로 교체
        parsed['sections'] = structured_sections
        return parsed
