"""
YOLO 감지 결과를 Unit으로 변환하는 유틸리티

YOLO 클래스 매핑:
- header -> 강의 제목 (Lesson)
- section -> 개념 제목 (Unit: concept, subtype: title)
- concept_box -> 개념 내용 (Unit: concept, subtype: content)
- sidebar -> 세부 개념 (Unit: concept_detail)
- passage -> 본문 (Unit: passage)
- question -> 문제 (Unit: question)

Lesson 구성 규칙:
- Lesson 제목은 header 목록으로 구성
- 각 Lesson 안의 Unit은 페이지 단위로 구성
- 페이지 내 순서: 개념(section, concept_box, sidebar) → 본문(passage) → 문제(question)
- y좌표 기준으로 위에서 아래로 정렬
"""
import logging
from typing import List, Dict, Any, Tuple
from PIL import Image

logger = logging.getLogger(__name__)


def convert_yolo_detections_to_units(
    yolo_detection_results: Dict[str, Any],
    all_ocr_data: List[Dict[str, Any]],
    pages_dir: Any  # Path 객체
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    YOLO 감지 결과를 lectures와 problems로 변환
    
    Args:
        yolo_detection_results: YOLO 감지 결과 (extract_with_yolo 반환 형식)
        all_ocr_data: OCR 데이터 (텍스트 추출용)
        pages_dir: 페이지 이미지 디렉토리
        
    Returns:
        (lectures, problems) 튜플
    """
    lectures = []
    problems = []
    
    # extract_with_yolo의 반환 형식: {'lectures': [...], 'problems': [...], ...}
    if isinstance(yolo_detection_results, dict):
        # 이미 분류된 결과인 경우
        yolo_lectures = yolo_detection_results.get('lectures', [])
        yolo_problems = yolo_detection_results.get('problems', [])
        yolo_passages = yolo_detection_results.get('passages', [])
        yolo_sections = yolo_detection_results.get('sections', [])
        yolo_concept_boxes = yolo_detection_results.get('concept_boxes', [])
        yolo_sidebars = yolo_detection_results.get('sidebars', [])
        
        # 페이지별 OCR 데이터 매핑
        ocr_by_page = {ocr['page_num']: ocr for ocr in all_ocr_data}
        
        # header를 강의로 변환
        for header_data in yolo_lectures:
            page_num = header_data.get('page')
            ocr_data = ocr_by_page.get(page_num)
            
            # header 텍스트 추출
            header_text = header_data.get('title', '')
            if not header_text and ocr_data:
                bbox = header_data.get('bbox', [])
                if len(bbox) == 4:
                    # bbox를 정규화된 좌표로 변환 (이미 픽셀 좌표일 수 있음)
                    # OCR 데이터에서 이미지 크기 추정
                    if 'image_width' in header_data and 'image_height' in header_data:
                        img_w = header_data['image_width']
                        img_h = header_data['image_height']
                    else:
                        # 기본값 사용
                        img_w = 1000
                        img_h = 1400
                    
                    # bbox가 픽셀 좌표인지 확인 (큰 값이면 픽셀 좌표)
                    if bbox[2] > 1:
                        # 픽셀 좌표를 정규화
                        norm_bbox = [bbox[0]/img_w, bbox[1]/img_h, bbox[2]/img_w, bbox[3]/img_h]
                    else:
                        norm_bbox = bbox
                    
                    header_text = _extract_text_from_bbox(ocr_data, norm_bbox, img_w, img_h)
            
            if not header_text:
                header_text = f"{header_data.get('lecture_id', len(lectures) + 1)}강"
            
            # 해당 페이지의 다른 영역들을 찾아 unit으로 구성
            # 페이지 단위로 구성하고, 순서: 개념 → 본문 → 문제
            page_units = []
            
            # 같은 페이지의 모든 영역 수집
            page_detections = []
            
            # 개념 영역들 (section, concept_box, sidebar)
            for section in yolo_sections:
                if section.get('page') == page_num:
                    bbox = section.get('bbox', [])
                    page_detections.append({
                        "type": "concept",
                        "subtype": "title",
                        "page": page_num,
                        "bbox": bbox,
                        "text": "",
                        "confidence": section.get('confidence', 0.0),
                        "class_name": "section",
                        "y1": bbox[1] if len(bbox) >= 2 else 0,  # y좌표 (정렬용)
                        "priority": 1  # 개념 우선순위
                    })
            
            for concept_box in yolo_concept_boxes:
                if concept_box.get('page') == page_num:
                    bbox = concept_box.get('bbox', [])
                    page_detections.append({
                        "type": "concept",
                        "subtype": "content",
                        "page": page_num,
                        "bbox": bbox,
                        "text": "",
                        "confidence": concept_box.get('confidence', 0.0),
                        "class_name": "concept_box",
                        "y1": bbox[1] if len(bbox) >= 2 else 0,
                        "priority": 1  # 개념 우선순위
                    })
            
            for sidebar in yolo_sidebars:
                if sidebar.get('page') == page_num:
                    bbox = sidebar.get('bbox', [])
                    page_detections.append({
                        "type": "concept_detail",
                        "subtype": None,
                        "page": page_num,
                        "bbox": bbox,
                        "text": "",
                        "confidence": sidebar.get('confidence', 0.0),
                        "class_name": "sidebar",
                        "y1": bbox[1] if len(bbox) >= 2 else 0,
                        "priority": 1  # 개념 우선순위
                    })
            
            # 본문 영역 (passage)
            for passage in yolo_passages:
                if passage.get('page') == page_num:
                    bbox = passage.get('bbox', [])
                    page_detections.append({
                        "type": "passage",
                        "subtype": None,
                        "page": page_num,
                        "bbox": bbox,
                        "text": "",
                        "confidence": passage.get('confidence', 0.0),
                        "class_name": "passage",
                        "y1": bbox[1] if len(bbox) >= 2 else 0,
                        "priority": 2  # 본문 우선순위
                    })
            
            # 문제 영역 (question) - 같은 페이지의 문제도 포함
            for question in yolo_problems:
                if question.get('page') == page_num:
                    bbox = question.get('bbox', [])
                    page_detections.append({
                        "type": "question",
                        "subtype": None,
                        "page": page_num,
                        "bbox": bbox,
                        "text": "",
                        "confidence": question.get('confidence', 0.0),
                        "class_name": "question",
                        "y1": bbox[1] if len(bbox) >= 2 else 0,
                        "priority": 3  # 문제 우선순위
                    })
            
            # 정렬: 우선순위(개념→본문→문제) → y좌표(위→아래)
            page_detections.sort(key=lambda x: (x.get('priority', 999), x.get('y1', 0)))
            
            # priority, y1 필드 제거하고 units에 추가
            for det in page_detections:
                unit = {k: v for k, v in det.items() if k not in ['priority', 'y1']}
                page_units.append(unit)
            
            lecture = {
                "lecture_id": header_data.get('lecture_id', len(lectures) + 1),
                "title": header_text,
                "page": page_num,
                "bbox": header_data.get('bbox', []),
                "units": page_units
            }
            lectures.append(lecture)
        
        # question을 문제로 변환 (lecture에 포함되지 않은 독립적인 문제들)
        # 이미 lecture의 units에 포함된 문제는 제외
        lecture_pages = {lec.get('page') for lec in lectures}
        
        for question_data in yolo_problems:
            question_page = question_data.get('page')
            # lecture가 있는 페이지의 문제는 이미 units에 포함되었으므로 제외
            if question_page not in lecture_pages:
                problem = {
                    "problem_id": question_data.get('problem_id', f"{len(problems) + 1:02d}"),
                    "page": question_page,
                    "bbox": question_data.get('bbox', []),
                    "text": "",
                    "confidence": question_data.get('confidence', 0.0)
                }
                problems.append(problem)
    
    return lectures, problems


def _detection_to_unit(
    detection: Any,
    page_num: int,
    ocr_data: Dict[str, Any],
    image_width: int,
    image_height: int
) -> Dict[str, Any]:
    """
    YOLO 감지 결과를 unit으로 변환
    
    클래스 매핑:
    - section -> concept (개념 제목)
    - concept_box -> concept (개념 내용)
    - sidebar -> concept_detail (세부 개념)
    - passage -> passage (본문)
    """
    class_name = detection.class_name
    
    # unit 타입 결정
    if class_name == "section":
        unit_type = "concept"
        unit_subtype = "title"
    elif class_name == "concept_box":
        unit_type = "concept"
        unit_subtype = "content"
    elif class_name == "sidebar":
        unit_type = "concept_detail"
        unit_subtype = None
    elif class_name == "passage":
        unit_type = "passage"
        unit_subtype = None
    else:
        # question은 별도 처리
        return None
    
    # 텍스트 추출
    text = _extract_text_from_bbox(ocr_data, detection.bbox, image_width, image_height)
    
    # bbox 변환
    bbox = [
        int(detection.bbox[0] * image_width),
        int(detection.bbox[1] * image_height),
        int(detection.bbox[2] * image_width),
        int(detection.bbox[3] * image_height)
    ]
    
    unit = {
        "type": unit_type,
        "subtype": unit_subtype,
        "page": page_num,
        "bbox": bbox,
        "text": text or "",
        "confidence": detection.confidence,
        "class_name": class_name
    }
    
    return unit


def _extract_text_from_bbox(
    ocr_data: Dict[str, Any],
    bbox: List[float],  # [x1, y1, x2, y2] 정규화된 좌표
    image_width: int,
    image_height: int
) -> str:
    """
    OCR 데이터에서 bbox 영역의 텍스트 추출
    
    Args:
        ocr_data: OCR 데이터 (text, left, top, width, height 리스트)
        bbox: 정규화된 bbox [x1, y1, x2, y2]
        image_width: 이미지 너비
        image_height: 이미지 높이
        
    Returns:
        추출된 텍스트
    """
    if not ocr_data:
        return ""
    
    # bbox를 픽셀 좌표로 변환
    x1 = int(bbox[0] * image_width)
    y1 = int(bbox[1] * image_height)
    x2 = int(bbox[2] * image_width)
    y2 = int(bbox[3] * image_height)
    
    texts = ocr_data.get('text', [])
    lefts = ocr_data.get('left', [])
    tops = ocr_data.get('top', [])
    widths = ocr_data.get('width', [])
    heights = ocr_data.get('height', [])
    
    if not texts or len(texts) != len(lefts):
        return ""
    
    # bbox 내에 있는 단어들 추출
    words_in_bbox = []
    for i, text in enumerate(texts):
        if i >= len(lefts) or i >= len(tops):
            continue
        
        word_left = lefts[i]
        word_top = tops[i]
        word_width = widths[i] if i < len(widths) else 0
        word_height = heights[i] if i < len(heights) else 0
        
        word_right = word_left + word_width
        word_bottom = word_top + word_height
        
        # 단어가 bbox와 겹치는지 확인 (50% 이상 겹치면 포함)
        overlap_x = max(0, min(x2, word_right) - max(x1, word_left))
        overlap_y = max(0, min(y2, word_bottom) - max(y1, word_top))
        overlap_area = overlap_x * overlap_y
        word_area = word_width * word_height
        
        if word_area > 0 and overlap_area / word_area > 0.5:
            words_in_bbox.append((word_top, word_left, text))
    
    # y좌표 기준으로 정렬 (위에서 아래로)
    words_in_bbox.sort(key=lambda x: (x[0], x[1]))
    
    # 텍스트 조합
    result_text = " ".join([word[2] for word in words_in_bbox])
    
    return result_text.strip()
