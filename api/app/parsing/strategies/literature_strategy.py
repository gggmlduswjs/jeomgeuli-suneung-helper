"""
문학 과목 파싱 전략
"""
import re
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

from .base_strategy import BaseParsingStrategy
from ..utils import group_texts_by_line, matches_patterns

logger = logging.getLogger(__name__)

# YOLO 감지기 import (선택적)
try:
    from app.dl.yolo_detector import RoboflowDetector, YOLODetector, PageDetection
    YOLO_AVAILABLE = True
except ImportError:
    YOLO_AVAILABLE = False
    logger.warning("[LiteratureStrategy] YOLO 감지기를 사용할 수 없습니다. OCR 기반 파싱만 사용됩니다.")


class LiteratureParsingStrategy(BaseParsingStrategy):
    """문학 과목 파싱 전략"""

    def _load_lecture_mapping(self) -> Optional[Dict[str, Any]]:
        """강의 매핑 파일 로드 (수능특강 문학 2026)"""
        mapping_path = Path(__file__).parent.parent / "lecture_maps" / "suneung_literature_2026.json"

        if not mapping_path.exists():
            logger.warning(f"[LiteratureStrategy] 매핑 파일 없음: {mapping_path}")
            return None

        try:
            with open(mapping_path, 'r', encoding='utf-8') as f:
                mapping = json.load(f)
            logger.info(f"[LiteratureStrategy] 매핑 파일 로드 성공: {mapping.get('total_lectures', 0)}개 강의")
            return mapping
        except Exception as e:
            logger.error(f"[LiteratureStrategy] 매핑 파일 로드 실패: {e}")
            return None

    def extract_lectures(self, all_ocr_data: List[Dict[str, Any]], config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        문학 강의 목록 추출

        매핑 파일이 있으면 우선 사용, 없으면 OCR 패턴 매칭

        Args:
            all_ocr_data: OCR 데이터 리스트
            config: 과목별 설정

        Returns:
            강의 리스트
        """
        # 1. 매핑 파일 우선 시도
        mapping = self._load_lecture_mapping()
        if mapping:
            return self._extract_lectures_from_mapping(mapping, all_ocr_data)

        # 2. 매핑 없으면 기존 방식 (OCR 패턴 매칭)
        logger.info("[LiteratureStrategy] 매핑 파일 없음. OCR 패턴 매칭 사용")
        lectures = []
        lecture_id = 1
        patterns = config.get('lecture_title_patterns', [])
        START_CONTENT_PAGE = config.get('start_content_page', 8)
        
        # 각 페이지에서 강의 제목 찾기
        for ocr_data in all_ocr_data:
            page_num = ocr_data['page_num']
            texts = ocr_data.get('text', [])
            tops = ocr_data.get('top', [])
            lefts = ocr_data.get('left', [])
            widths = ocr_data.get('width', [])
            heights = ocr_data.get('height', [])
            
            if not texts or len([t for t in texts if t.strip()]) == 0:
                continue
            
            # y좌표 기준으로 같은 줄의 단어들을 그룹화
            lines = group_texts_by_line(texts, tops, lefts, widths, heights)
            
            # 페이지 상단 영역 체크
            page_top_threshold = None
            if lines and len(lines) > 0 and len(lines[0]) > 0:
                first_line_y = lines[0][0]['top']
                if lines and len(lines[-1]) > 0:
                    last_line = lines[-1]
                    estimated_page_height = last_line[-1]['top'] + last_line[-1]['height']
                    page_top_threshold = first_line_y + (estimated_page_height * 0.4)
            
            # 평균 폰트 크기 계산
            min_title_height = 0
            if lines:
                total_height = sum(word['height'] for line in lines[:10] for word in line[:3])
                total_words = sum(len(line[:3]) for line in lines[:10])
                if total_words > 0:
                    avg_height = total_height / min(30, total_words)
                    min_title_height = avg_height * 1.0
            
            for line in lines:
                line_text = " ".join([word['text'] for word in line]).strip()
                
                if not line_text or len(line_text) < 5:
                    continue
                
                # 목차 형식 제외
                if re.search(r'\d{3,}', line_text) and len(line_text) < 50:
                    continue
                
                # 작품 제목 형식 제외
                if re.search(r'\([가-힣]+\)', line_text) and len(line_text) < 40:
                    continue
                
                # 문제 번호/지문 제외 (더 관대하게 수정)
                # 2자리 숫자로 시작하지만 "N강" 형식이 아니고, 텍스트가 매우 긴 경우만 제외
                if re.match(r'^\d{2,}\s+[가-힣]', line_text) and not re.search(r'^\d+강', line_text):
                    # 텍스트가 매우 긴 경우만 문제 지문으로 간주 (50자 이상)
                    if len(line_text) > 50:
                        continue
                
                # 매우 긴 텍스트는 문제 지문일 가능성이 높음
                if len(line_text) > 80 and re.match(r'^\d{2,}\s+[가-힣]{10,}', line_text) and not re.search(r'^\d+강', line_text):
                    continue
                
                # 페이지 상단 영역 체크
                line_y = line[0]['top']
                if page_top_threshold and line_y > page_top_threshold * 0.8:
                    continue
                
                # 큰 폰트 체크
                line_height = max(word['height'] for word in line)
                if min_title_height > 0 and line_height < min_title_height * 0.9:
                    continue
                
                # 패턴 매칭
                if matches_patterns(line_text, patterns):
                    # 강의 제목 검증: "N강" 또는 "작품으로 이해하기 N" 또는 "NN 장르명" 형식
                    # 검증을 완화하여 다양한 형식 허용 (OCR 오인식 대응)
                    is_valid_lecture = (
                        re.search(r'^\d+강', line_text) or  # "1강 |", "2강" 등
                        re.search(r'작품으로\s*이해하기\s*\d+', line_text) or  # "작품으로 이해하기 4"
                        re.search(r'^\d{2}\s+[가-힣]+', line_text) or  # "01 고전 시가", "02 현대시" 등 (공백 필수)
                        re.search(r'^\d{2}[가-힣]+', line_text) or  # "01고전시가" (공백 없이도 허용)
                        # 추가 패턴: 숫자로 시작하고 한글이 포함된 경우 (더 관대하게)
                        (re.match(r'^\d+', line_text) and re.search(r'[가-힣]', line_text) and len(line_text) >= 3 and len(line_text) <= 50)
                    )
                    if not is_valid_lecture:
                        # 디버깅: 왜 필터링되었는지 로그 (패턴 매칭은 되었지만 검증 실패)
                        if len(line_text) < 50 and re.match(r'^\d+', line_text):
                            print(f"    [필터링] 강의 제목 검증 실패: '{line_text[:40]}' (페이지 {page_num})")
                        continue
                    
                    # 문제/해설 페이지 제외
                    if page_num > 200:
                        if any(keyword in line_text for keyword in ["정답", "해설", "답", "문제", "보기"]):
                            continue
                        if not re.search(r'^\d+강\s*[|]', line_text) and len(line_text) < 20:
                            continue
                    
                    # bbox 계산
                    first_word = line[0]
                    last_word = line[-1]
                    
                    left = first_word['left']
                    top = first_word['top']
                    right = last_word['left'] + last_word['width']
                    bottom = max(w['top'] + w['height'] for w in line)
                    
                    lectures.append({
                        "lecture_id": lecture_id,
                        "title": line_text,
                        "page": page_num,
                        "bbox": [left, top, right, bottom]
                    })
                    lecture_id += 1
                    logger.info(f"강의 발견: {line_text[:50]} (페이지 {page_num})")

        return lectures

    def _extract_lectures_from_mapping(self, mapping: Dict[str, Any], all_ocr_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        매핑 파일로부터 강의 목록 생성

        Args:
            mapping: 강의 매핑 정보
            all_ocr_data: OCR 데이터 (페이지 수 확인용)

        Returns:
            강의 리스트
        """
        lectures = []
        all_lectures_flat = []

        # 모든 섹션의 강의를 평탄화
        for section in mapping.get('sections', []):
            for lec in section.get('lectures', []):
                all_lectures_flat.append({
                    'num': lec['num'],
                    'title': lec['title'],
                    'page': lec['page'],
                    'section': section.get('section_name', '')
                })

        # 강의 번호 순으로 정렬
        all_lectures_flat.sort(key=lambda x: x['num'])

        logger.info(f"[LiteratureStrategy] 매핑에서 {len(all_lectures_flat)}개 강의 로드")

        # 강의 목록 생성 (OCR 데이터 호환 형식)
        for i, lec in enumerate(all_lectures_flat):
            lecture_entry = {
                "lecture_id": lec['num'],
                "title": lec['title'],
                "page": lec['page'],
                "bbox": [0, 0, 0, 0]  # 매핑 기반이므로 bbox 불필요
            }
            lectures.append(lecture_entry)

        logger.info(f"[LiteratureStrategy] {len(lectures)}개 강의 생성 완료")

        return lectures

    def extract_problems(self, all_ocr_data: List[Dict[str, Any]], config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        문학 문제 목록 추출
        
        Args:
            all_ocr_data: OCR 데이터 리스트
            config: 과목별 설정
            
        Returns:
            문제 리스트
        """
        problems = []
        problem_pattern = config.get('problem_number_pattern', r'^\d{2}$')
        START_CONTENT_PAGE = config.get('start_content_page', 8)
        
        for ocr_data in all_ocr_data:
            page_num = ocr_data['page_num']
            
            if page_num < START_CONTENT_PAGE:
                continue
            
            texts = ocr_data.get('text', [])
            tops = ocr_data.get('top', [])
            lefts = ocr_data.get('left', [])
            widths = ocr_data.get('width', [])
            heights = ocr_data.get('height', [])
            
            if not texts:
                continue
            
            lines = group_texts_by_line(texts, tops, lefts, widths, heights)
            
            for line in lines:
                line_text = " ".join([word['text'] for word in line]).strip()
                
                # 문제 번호 패턴 매칭
                if re.match(problem_pattern, line_text):
                    # bbox 계산
                    first_word = line[0]
                    last_word = line[-1]
                    
                    left = first_word['left']
                    top = first_word['top']
                    right = last_word['left'] + last_word['width']
                    bottom = max(w['top'] + w['height'] for w in line)
                    
                    problem_id = line_text.strip()
                    problems.append({
                        "problem_id": problem_id,
                        "page": page_num,
                        "bbox": [left, top, right, bottom]
                    })
                    logger.debug(f"문제 발견: {problem_id} (페이지 {page_num})")

        return problems

    # ============================================================================
    # YOLO 기반 파싱 메서드 (Level 2.2 - AI 강화)
    # ============================================================================

    def extract_with_yolo(
        self,
        all_ocr_data: List[Dict[str, Any]],
        config: Dict[str, Any],
        use_roboflow: bool = True,
        roboflow_api_key: Optional[str] = None,
        local_model_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        YOLO 모델을 사용하여 문학 콘텐츠 추출

        Args:
            all_ocr_data: OCR 데이터 리스트 (페이지 경로 정보 포함)
            config: 과목별 설정
            use_roboflow: Roboflow API 사용 여부
            roboflow_api_key: Roboflow API 키
            local_model_path: 로컬 YOLO 모델 경로

        Returns:
            {
                'lectures': [...],
                'problems': [...],
                'passages': [...],
                'sections': [...],
                'concept_boxes': [...],
                'sidebars': [...]
            }
        """
        if not YOLO_AVAILABLE:
            logger.error("[LiteratureStrategy] YOLO 감지기를 사용할 수 없습니다.")
            return {
                'lectures': [],
                'problems': [],
                'passages': [],
                'sections': [],
                'concept_boxes': [],
                'sidebars': []
            }

        logger.info("[LiteratureStrategy] YOLO 기반 파싱 시작")

        # YOLO 감지기 초기화
        if use_roboflow:
            try:
                detector = RoboflowDetector(
                    workspace_id="-wshlq",
                    project_id="2",
                    api_key=roboflow_api_key,
                    confidence_threshold=0.15,  # 낮춰서 더 많은 header 감지 (0.25 -> 0.15)
                    overlap_threshold=30.0
                )
                logger.info("[LiteratureStrategy] Roboflow 감지기 초기화 완료")
            except Exception as e:
                logger.error(f"[LiteratureStrategy] Roboflow 감지기 초기화 실패: {e}")
                return self._empty_yolo_result()
        else:
            if not local_model_path:
                logger.error("[LiteratureStrategy] 로컬 모델 경로가 제공되지 않았습니다.")
                return self._empty_yolo_result()

            try:
                detector = YOLODetector(
                    model_path=local_model_path,
                    confidence_threshold=0.15,  # 낮춰서 더 많은 header 감지 (0.25 -> 0.15)
                    iou_threshold=0.45
                )
                logger.info("[LiteratureStrategy] 로컬 YOLO 감지기 초기화 완료")
            except Exception as e:
                logger.error(f"[LiteratureStrategy] 로컬 YOLO 감지기 초기화 실패: {e}")
                return self._empty_yolo_result()

        # 페이지별로 감지 수행
        all_detections = []
        page_paths = self._extract_page_paths(all_ocr_data, config)

        logger.info(f"[LiteratureStrategy] {len(page_paths)}개 페이지 감지 시작")

        for page_num, page_path in page_paths.items():
            try:
                page_detection = detector.detect_page(page_path)
                all_detections.append({
                    'page_num': page_num,
                    'page_path': page_path,
                    'detections': page_detection.detections,
                    'image_width': page_detection.image_width,
                    'image_height': page_detection.image_height
                })
                logger.debug(f"[LiteratureStrategy] 페이지 {page_num}: {len(page_detection.detections)}개 영역 감지")
            except Exception as e:
                logger.error(f"[LiteratureStrategy] 페이지 {page_num} 감지 실패: {e}")
                continue

        logger.info(f"[LiteratureStrategy] 감지 완료: {len(all_detections)}개 페이지")

        # 클래스별로 분류
        result = self._classify_detections(all_detections)

        logger.info(f"[LiteratureStrategy] YOLO 파싱 완료:")
        logger.info(f"  - 헤더(강의): {len(result['lectures'])}개")
        logger.info(f"  - 문제: {len(result['problems'])}개")
        logger.info(f"  - 지문: {len(result['passages'])}개")
        logger.info(f"  - 섹션: {len(result['sections'])}개")
        logger.info(f"  - 개념박스: {len(result['concept_boxes'])}개")
        logger.info(f"  - 사이드바: {len(result['sidebars'])}개")

        return result

    def _extract_page_paths(self, all_ocr_data: List[Dict[str, Any]], config: Dict[str, Any]) -> Dict[int, str]:
        """
        OCR 데이터에서 페이지 경로 추출

        Args:
            all_ocr_data: OCR 데이터 리스트
            config: 과목별 설정

        Returns:
            {page_num: page_path}
        """
        page_paths = {}

        # config에서 기본 경로 가져오기
        data_dir = Path(config.get('data_dir', 'data/literature'))
        pages_dir = data_dir / 'pages'

        for ocr_data in all_ocr_data:
            page_num = ocr_data.get('page_num')

            # OCR 데이터에 page_path가 있으면 사용
            if 'page_path' in ocr_data:
                page_paths[page_num] = ocr_data['page_path']
            else:
                # 없으면 규칙 기반으로 생성
                page_path = pages_dir / f"page_{page_num:03d}.png"
                if page_path.exists():
                    page_paths[page_num] = str(page_path)
                else:
                    logger.warning(f"[LiteratureStrategy] 페이지 이미지를 찾을 수 없습니다: {page_path}")

        return page_paths

    def _classify_detections(self, all_detections: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        감지된 영역을 클래스별로 분류

        Args:
            all_detections: 페이지별 감지 결과

        Returns:
            클래스별로 분류된 결과
        """
        lectures = []
        problems = []
        passages = []
        sections = []
        concept_boxes = []
        sidebars = []

        lecture_id = 1
        problem_id = 1
        passage_id = 1
        section_id = 1

        for page_data in all_detections:
            page_num = page_data['page_num']

            for det in page_data['detections']:
                # bbox를 픽셀 좌표로 변환
                x1 = int(det.bbox[0] * page_data['image_width'])
                y1 = int(det.bbox[1] * page_data['image_height'])
                x2 = int(det.bbox[2] * page_data['image_width'])
                y2 = int(det.bbox[3] * page_data['image_height'])

                bbox = [x1, y1, x2, y2]

                if det.class_name == "header":
                    lectures.append({
                        "lecture_id": lecture_id,
                        "title": f"강의 {lecture_id}",  # OCR로 텍스트 추출 필요
                        "page": page_num,
                        "bbox": bbox,
                        "confidence": det.confidence
                    })
                    lecture_id += 1

                elif det.class_name == "question":
                    problems.append({
                        "problem_id": f"{problem_id:02d}",
                        "page": page_num,
                        "bbox": bbox,
                        "confidence": det.confidence
                    })
                    problem_id += 1

                elif det.class_name == "passage":
                    passages.append({
                        "passage_id": passage_id,
                        "page": page_num,
                        "bbox": bbox,
                        "confidence": det.confidence
                    })
                    passage_id += 1

                elif det.class_name == "section":
                    sections.append({
                        "section_id": section_id,
                        "page": page_num,
                        "bbox": bbox,
                        "confidence": det.confidence
                    })
                    section_id += 1

                elif det.class_name == "concept_box":
                    concept_boxes.append({
                        "page": page_num,
                        "bbox": bbox,
                        "confidence": det.confidence
                    })

                elif det.class_name == "sidebar":
                    sidebars.append({
                        "page": page_num,
                        "bbox": bbox,
                        "confidence": det.confidence
                    })

        return {
            'lectures': lectures,
            'problems': problems,
            'passages': passages,
            'sections': sections,
            'concept_boxes': concept_boxes,
            'sidebars': sidebars
        }

    def _empty_yolo_result(self) -> Dict[str, Any]:
        """빈 YOLO 결과 반환"""
        return {
            'lectures': [],
            'problems': [],
            'passages': [],
            'sections': [],
            'concept_boxes': [],
            'sidebars': []
        }
