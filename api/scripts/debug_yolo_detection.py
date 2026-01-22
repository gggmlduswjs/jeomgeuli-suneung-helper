"""
YOLO header 감지 디버깅 스크립트

실제로 몇 개의 header가 감지되는지 확인
"""
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "api"))

from app.parsing.strategies.literature_strategy import LiteratureParsingStrategy
import os

def main():
    # 설정
    pages_dir = PROJECT_ROOT / "api" / "data" / "literature" / "pages"
    config = {
        'data_dir': str(PROJECT_ROOT / "api" / "data" / "literature"),
        'start_content_page': 8
    }
    
    # 페이지 이미지 찾기
    page_files = sorted(pages_dir.glob("page_*.png"))
    print(f"총 {len(page_files)}개 페이지 이미지 발견")
    
    if not page_files:
        print("페이지 이미지가 없습니다. 먼저 PDF를 처리하세요.")
        return
    
    # OCR 데이터 형식으로 생성
    ocr_data = []
    for page_file in page_files:
        page_num = int(page_file.stem.split('_')[1])
        ocr_data.append({
            'page_num': page_num,
            'page_path': str(page_file),
            'text': [],
            'left': [],
            'top': [],
            'width': [],
            'height': []
        })
    
    print(f"\n처리할 페이지: {len(ocr_data)}개")
    print(f"페이지 범위: {ocr_data[0]['page_num']} ~ {ocr_data[-1]['page_num']}")
    
    # LiteratureStrategy 생성
    strategy = LiteratureParsingStrategy()
    
    # Roboflow API 키
    api_key = os.getenv("ROBOFLOW_API_KEY", "ohDbNa6uGc3Aozm81aci")
    
    print(f"\nYOLO 감지 시작...")
    print(f"Confidence threshold: 0.25")
    
    # YOLO 파싱 실행
    result = strategy.extract_with_yolo(
        all_ocr_data=ocr_data,
        config=config,
        use_roboflow=True,
        roboflow_api_key=api_key
    )
    
    # 결과 분석
    print(f"\n{'='*80}")
    print(f"YOLO 감지 결과")
    print(f"{'='*80}")
    print(f"헤더(강의): {len(result['lectures'])}개")
    print(f"문제: {len(result['problems'])}개")
    print(f"지문: {len(result['passages'])}개")
    print(f"섹션: {len(result['sections'])}개")
    print(f"개념박스: {len(result['concept_boxes'])}개")
    print(f"사이드바: {len(result['sidebars'])}개")
    
    # 페이지별 header 분포
    print(f"\n{'='*80}")
    print(f"페이지별 Header 감지 현황")
    print(f"{'='*80}")
    
    page_header_count = {}
    for lecture in result['lectures']:
        page = lecture.get('page', 0)
        page_header_count[page] = page_header_count.get(page, 0) + 1
    
    # 페이지별로 정렬
    for page in sorted(page_header_count.keys()):
        count = page_header_count[page]
        confidence = [l.get('confidence', 0) for l in result['lectures'] if l.get('page') == page]
        avg_conf = sum(confidence) / len(confidence) if confidence else 0
        print(f"페이지 {page:3d}: {count}개 header (평균 confidence: {avg_conf:.3f})")
    
    # Header 상세 정보
    print(f"\n{'='*80}")
    print(f"Header 상세 정보 (최대 20개)")
    print(f"{'='*80}")
    for i, lecture in enumerate(result['lectures'][:20], 1):
        print(f"{i:2d}. 페이지 {lecture.get('page', 0):3d} | "
              f"confidence: {lecture.get('confidence', 0):.3f} | "
              f"bbox: {lecture.get('bbox', [])}")
    
    if len(result['lectures']) > 20:
        print(f"... 외 {len(result['lectures']) - 20}개")
    
    # Confidence 분포
    confidences = [l.get('confidence', 0) for l in result['lectures']]
    if confidences:
        print(f"\n{'='*80}")
        print(f"Confidence 분포")
        print(f"{'='*80}")
        print(f"최소: {min(confidences):.3f}")
        print(f"최대: {max(confidences):.3f}")
        print(f"평균: {sum(confidences)/len(confidences):.3f}")
        print(f"0.25 미만: {sum(1 for c in confidences if c < 0.25)}개")
        print(f"0.25 이상: {sum(1 for c in confidences if c >= 0.25)}개")
        print(f"0.5 이상: {sum(1 for c in confidences if c >= 0.5)}개")
        print(f"0.7 이상: {sum(1 for c in confidences if c >= 0.7)}개")

if __name__ == "__main__":
    main()
