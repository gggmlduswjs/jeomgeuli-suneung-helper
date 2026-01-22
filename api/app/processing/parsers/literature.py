"""
문학 파서
실제 파싱 로직 구현 (textbook_pipeline에서 이동)
"""
import json
import re
import logging
from pathlib import Path
from typing import List, Dict, Any

from .base import BaseParser

logger = logging.getLogger(__name__)


class LiteratureParser(BaseParser):
    """
    문학 과목 파서
    
    강의, 문제, 섹션 추출 로직 구현
    """

    def __init__(self, config_path: Path = None):
        """
        Args:
            config_path: config.json 경로 (None이면 기본 경로 사용)
        """
        self.config_path = config_path
        self.config = self._load_config() if config_path else {}
        self._setup_default_config()

    def _load_config(self) -> Dict[str, Any]:
        """config.json 로드"""
        if not self.config_path or not self.config_path.exists():
            logger.warning(f"config.json을 찾을 수 없음: {self.config_path}")
            return {}

        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            logger.info(f"config.json 로드 완료: {self.config_path}")
            return config
        except Exception as e:
            logger.error(f"config.json 로드 실패: {e}")
            return {}

    def _setup_default_config(self):
        """기본 설정 (config가 없을 때)"""
        if not self.config:
            self.config = {
                "lecture_title_patterns": [
                    r'^\d+강\s+[가-힣]+',  # "1강 시의 표현과 형식"
                    r'^\d+\s+[가-힣]+',  # "1 시의 표현과 형식"
                ],
                "concept_title_patterns": [
                    r'^\d+\s*[\.]\s+[가-힣]{2,}',  # "1. 시적 표현"
                    r'^\d+\s+[가-힣]{2,}',  # "1 시적 표현"
                ],
                "content_header_patterns": [
                    r'작품으로\s*이해하기',
                    r'작품\s*이해',
                ],
                "problem_number_pattern": r'^\d{2}$',  # "01", "02"
                "start_content_page": 8
            }

    def parse(self, ocr_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        OCR 데이터를 파싱하여 문학 콘텐츠 추출

        Args:
            ocr_data: 페이지별 OCR 결과 리스트

        Returns:
            {
                'lectures': [...],
                'problems': [...],
                'metadata': {...}
            }
        """
        # 강의 추출
        lectures = self.extract_lectures(ocr_data)
        
        # 문제 추출
        problems = self.extract_problems(ocr_data)

        logger.info(f"문학 파싱 완료: {len(lectures)}개 강의, {len(problems)}개 문제")

        return {
            'lectures': lectures,
            'problems': problems,
            'metadata': {
                'total_lectures': len(lectures),
                'total_problems': len(problems),
                'status': 'implemented'
            }
        }

    def _merge_adjacent_texts(self, ocr_page: Dict[str, Any], y_threshold: int = 10, x_threshold: int = 50) -> List[str]:
        """
        인접한 텍스트를 합쳐서 단어/문장 만들기

        Args:
            ocr_page: OCR 페이지 데이터
            y_threshold: 같은 줄로 판단할 y 좌표 차이
            x_threshold: 같은 단어로 판단할 x 좌표 차이

        Returns:
            합쳐진 텍스트 리스트
        """
        texts = ocr_page.get('text', [])
        lefts = ocr_page.get('left', [])
        tops = ocr_page.get('top', [])

        if not texts or len(texts) != len(lefts) or len(texts) != len(tops):
            return texts

        # 텍스트를 좌표와 함께 저장
        items = [(texts[i], lefts[i], tops[i]) for i in range(len(texts))]

        # y 좌표(top)로 그룹화 (같은 줄)
        lines = {}
        for text, left, top in items:
            # 비슷한 y 좌표를 찾음
            found_line = False
            for line_y in lines.keys():
                if abs(top - line_y) <= y_threshold:
                    lines[line_y].append((text, left, top))
                    found_line = True
                    break
            if not found_line:
                lines[top] = [(text, left, top)]

        # 각 줄별로 x 좌표로 정렬하고 인접한 텍스트 합치기
        merged_texts = []
        for line_y in sorted(lines.keys()):
            line_items = sorted(lines[line_y], key=lambda x: x[1])  # x 좌표로 정렬

            if not line_items:
                continue

            current_text = line_items[0][0]
            prev_right = line_items[0][1] + len(line_items[0][0]) * 10  # 대략적인 문자 너비

            for i in range(1, len(line_items)):
                text, left, top = line_items[i]

                # 인접한 텍스트인지 확인
                if left - prev_right <= x_threshold:
                    # 공백 없이 합치기
                    current_text += text
                else:
                    # 새로운 단어 시작
                    if current_text.strip():
                        merged_texts.append(current_text.strip())
                    current_text = text

                prev_right = left + len(text) * 10

            # 마지막 텍스트 추가
            if current_text.strip():
                merged_texts.append(current_text.strip())

        return merged_texts

    def extract_lectures(self, ocr_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """강의 목록 추출"""
        lectures = []
        START_PAGE = self.config.get('start_content_page', 8)
        patterns = self.config.get('lecture_title_patterns', [])

        for ocr_page in ocr_data:
            page_num = ocr_page.get('page_num', 0)
            if page_num < START_PAGE:
                continue

            # 인접한 텍스트 합치기
            merged_texts = self._merge_adjacent_texts(ocr_page)

            if not merged_texts:
                continue

            # 디버깅: 페이지 8, 9, 10의 합쳐진 텍스트 출력
            if page_num in [8, 9, 10]:
                print(f"\n=== Page {page_num} 합쳐진 상위 20개 텍스트 ===")
                for i, text in enumerate(merged_texts[:20]):
                    print(f"  [{i}] {text}")

            # 상위 50개 텍스트 확인 (페이지 상단)
            for text in merged_texts[:50]:
                cleaned = text.strip()
                if not cleaned:
                    continue

                # 강의 제목 패턴 매칭
                for pattern in patterns:
                    match = re.search(pattern, cleaned)
                    if match:
                        # 강의 번호 추출
                        lecture_num_match = re.search(r'^(\d+)', cleaned)
                        if lecture_num_match:
                            lecture_id = int(lecture_num_match.group(1))
                            # 중복 체크
                            if not any(l['lecture_id'] == lecture_id for l in lectures):
                                lectures.append({
                                    'lecture_id': lecture_id,
                                    'title': cleaned,
                                    'page': page_num
                                })
                                print(f"✅ 강의 감지: {cleaned} (페이지 {page_num})")
                                break

        # lecture_id 순서대로 정렬
        lectures.sort(key=lambda x: x['lecture_id'])
        return lectures

    def extract_problems(self, ocr_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """문제 추출"""
        problems = []
        START_PAGE = self.config.get('start_content_page', 8)
        problem_pattern = self.config.get('problem_number_pattern', r'^\d{2}$')
        
        for ocr_page in ocr_data:
            page_num = ocr_page.get('page_num', 0)
            if page_num < START_PAGE:
                continue
            
            texts = ocr_page.get('text', [])
            if not texts:
                continue
            
            for text in texts:
                cleaned = text.strip()
                if re.match(problem_pattern, cleaned):
                    problem_id = cleaned
                    # 중복 체크
                    if not any(p['problem_id'] == problem_id and p['page'] == page_num for p in problems):
                        problems.append({
                            'problem_id': problem_id,
                            'page': page_num
                        })
        
        return problems

    def extract_sections(
        self,
        lecture_ocr_data: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        섹션 추출 (메인 개념 + 본문)
        
        추출 대상:
        1. 메인 개념 섹션: "1. 시적 표현", "2. 시의 형식" (type: "concept")
        2. 본문 섹션: "작품으로 이해하기 - 박두진 [해]" (type: "content")
        """
        sections = []
        concept_patterns = self.config.get('concept_title_patterns', [])
        content_patterns = self.config.get('content_header_patterns', [])
        START_PAGE = self.config.get('start_content_page', 8)
        
        # 강의의 실제 시작 페이지 찾기
        if lecture_ocr_data:
            actual_start_page = min(ocr_data.get('page_num', 0) for ocr_data in lecture_ocr_data)
            search_start_page = min(START_PAGE, actual_start_page)
        else:
            search_start_page = START_PAGE
        
        for ocr_data in lecture_ocr_data:
            page_num = ocr_data.get('page_num', 0)
            
            if page_num < search_start_page:
                continue
            
            texts = ocr_data.get('text', [])
            tops = ocr_data.get('top', [])
            lefts = ocr_data.get('left', [])
            widths = ocr_data.get('width', [])
            heights = ocr_data.get('height', [])
            
            if not texts:
                continue
            
            # y좌표 기준으로 같은 줄의 단어들을 그룹화
            lines = self.group_lines(ocr_data, y_threshold=10)
            
            # 각 줄을 문장으로 결합하고 패턴 매칭
            for line_idx, line in enumerate(lines):
                line_text = self.join_line_text(line)
                line_text = line_text.strip()
                
                if not line_text:
                    continue
                
                # 특수 문자 제거
                cleaned_line = re.sub(r'\(cid:\d+\)', '', line_text).strip()
                
                # 목차 형식 제외
                if re.search(r'\d{3}', cleaned_line) and len(cleaned_line) < 30:
                    continue
                
                section_type = None
                section_title = None
                
                # 1. 메인 개념 섹션 확인 ("1. 시적 표현", "2. 시의 형식")
                main_concept_match = re.match(r'^(\d+)\s*[\.]\s*([가-힣\s]{2,20})$', cleaned_line)
                if main_concept_match:
                    section_type = "concept"
                    section_title = cleaned_line
                # 대체 패턴: "1 시적 표현" (점 없음)
                elif re.match(r'^\d+\s+[가-힣]{2,}\s*[가-힣]*$', cleaned_line) and len(cleaned_line.split()) <= 3:
                    section_type = "concept"
                    section_title = cleaned_line
                # 2. 본문 섹션 확인 ("작품으로 이해하기")
                elif self.matches_patterns(cleaned_line, content_patterns):
                    section_type = "content"
                    section_title = cleaned_line
                    # 다음 줄에서 작품 제목 찾기
                    if line_idx + 1 < len(lines):
                        next_line = lines[line_idx + 1]
                        next_text = self.join_line_text(next_line).strip()
                        next_cleaned = re.sub(r'\(cid:\d+\)', '', next_text).strip()
                        # 작품 제목 패턴 확인
                        if re.search(r'[가-힣]+\s*\[[가-힣]+\]', next_cleaned) or re.search(r'[가-힣]+\s*「[가-힣]+」', next_cleaned):
                            section_title = f"{cleaned_line} - {next_cleaned}"
                
                if section_type and section_title:
                    # bbox 계산
                    bbox = self.get_line_bbox(line)
                    
                    sections.append({
                        "title": section_title,
                        "type": section_type,
                        "page": page_num,
                        "bbox": bbox
                    })
        
        return sections

    def extract_content_paragraphs(
        self,
        lecture_ocr_data: List[Dict[str, Any]],
        sections: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        섹션별 문단 추출
        
        각 섹션에 해당하는 문단들을 추출하여 섹션별로 그룹화
        """
        all_paragraphs = []
        threshold = self.config.get('paragraph_y_threshold', 25)
        
        for ocr_data in lecture_ocr_data:
            page_num = ocr_data.get('page_num', 0)
            texts = ocr_data.get('text', [])
            tops = ocr_data.get('top', [])
            lefts = ocr_data.get('left', [])
            widths = ocr_data.get('width', [])
            heights = ocr_data.get('height', [])
            
            if not texts:
                continue
            
            # y좌표 기준으로 줄 그룹화
            lines = self.group_lines(ocr_data, y_threshold=threshold)
            
            # 줄들을 문단으로 결합
            paragraphs = []
            current_paragraph = {
                "text": "",
                "y_start": None,
                "y_end": None,
                "page": page_num,
                "bbox": None
            }
            
            prev_line_y = None
            
            for line in lines:
                line_text = self.join_line_text(line)
                line_text = line_text.strip()
                
                if not line_text:
                    continue
                
                # 섹션 제목이면 스킵
                cleaned_line = re.sub(r'\(cid:\d+\)', '', line_text).strip()
                
                # 섹션 제목 패턴 제외
                section_patterns = self.config.get('section_title_patterns', [])
                if self.matches_patterns(cleaned_line, section_patterns):
                    continue
                
                # 개념 제목 패턴도 제외
                concept_patterns = self.config.get('concept_title_patterns', [])
                if self.matches_patterns(cleaned_line, concept_patterns):
                    continue
                
                # 본문 헤더 패턴도 제외
                content_patterns = self.config.get('content_header_patterns', [])
                if self.matches_patterns(cleaned_line, content_patterns):
                    continue
                
                # 문제 번호 패턴도 제외
                problem_pattern = self.config.get('problem_number_pattern', r'^\d{2}$')
                if re.match(problem_pattern, cleaned_line):
                    continue
                
                # 제외 패턴들
                exclude_patterns = [
                    r'정답과 해설',
                    r'다음 글을 읽고',
                    r'물음에 답하시오',
                ]
                if any(re.search(p, cleaned_line) for p in exclude_patterns):
                    continue
                
                line_y = line[0]['top']
                
                # 같은 문단인지 확인 (y좌표 차이)
                if prev_line_y is not None and abs(line_y - prev_line_y) < threshold:
                    # 같은 문단에 추가
                    if current_paragraph['text']:
                        current_paragraph['text'] += " " + line_text
                    else:
                        current_paragraph['text'] = line_text
                        current_paragraph['y_start'] = line_y
                        current_paragraph['bbox'] = self.get_line_bbox(line)
                    
                    # bbox 확장
                    if current_paragraph['bbox']:
                        line_bbox = self.get_line_bbox(line)
                        current_paragraph['bbox'][0] = min(current_paragraph['bbox'][0], line_bbox[0])
                        current_paragraph['bbox'][1] = min(current_paragraph['bbox'][1], line_bbox[1])
                        current_paragraph['bbox'][2] = max(current_paragraph['bbox'][2], line_bbox[2])
                        current_paragraph['bbox'][3] = max(current_paragraph['bbox'][3], line_bbox[3])
                    
                    current_paragraph['y_end'] = line_y
                else:
                    # 새 문단 시작
                    if current_paragraph['text']:
                        paragraphs.append(current_paragraph.copy())
                    
                    # 새 문단 초기화
                    current_paragraph = {
                        "text": line_text,
                        "y_start": line_y,
                        "y_end": line_y,
                        "page": page_num,
                        "bbox": self.get_line_bbox(line)
                    }
                
                prev_line_y = line_y
            
            # 마지막 문단 추가
            if current_paragraph['text']:
                paragraphs.append(current_paragraph)
            
            all_paragraphs.extend(paragraphs)
        
        return all_paragraphs
