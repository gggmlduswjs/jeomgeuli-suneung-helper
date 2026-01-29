"""
문학 이미지 재생성 스크립트
기존 JSON 데이터의 bbox를 사용하여 이미지를 다시 크롭
"""
import json
import sys
from pathlib import Path
from PIL import Image
from typing import List, Dict, Any

# 프로젝트 루트를 경로에 추가
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.config import settings
from app.infrastructure.pdf.image_cache import ImageCache

def get_page_image_path(page_num: int, pages_dir: Path) -> Path:
    """페이지 이미지 경로 찾기"""
    # pages 디렉토리에서 페이지 이미지 찾기
    page_files = list(pages_dir.glob(f"page_{page_num:03d}.png"))
    if not page_files:
        # 다른 형식 시도
        page_files = list(pages_dir.glob(f"page_{page_num}.png"))
    if page_files:
        return page_files[0]
    return None

def get_ocr_size_from_image(image_size: tuple) -> tuple:
    """이미지 크기로부터 OCR 크기 추정
    일반적으로 PDF는 A4 (595x842 포인트)이고, 
    이미지는 72 DPI 또는 150 DPI로 렌더링됨
    """
    img_width, img_height = image_size
    
    # 일반적인 비율로 OCR 크기 추정
    # A4 비율: 595/842 ≈ 0.706
    # 이미지 비율에 맞춰 OCR 크기 추정
    if img_height > 0:
        aspect_ratio = img_width / img_height
        # A4 비율과 비교
        if abs(aspect_ratio - 0.706) < 0.1:  # A4 비율
            # 72 DPI 기준: 595x842 포인트 = 595x842 픽셀
            # 150 DPI 기준: 595x842 포인트 = 1237x1750 픽셀 (대략)
            # 실제 이미지 크기에 맞춰 추정
            if img_width > 1000:
                # 고해상도 (150 DPI)
                ocr_width = 595
                ocr_height = 842
            else:
                # 저해상도 (72 DPI)
                ocr_width = 595
                ocr_height = 842
        else:
            # 비율이 다르면 이미지 크기를 그대로 사용 (이미 이미지 좌표계일 수 있음)
            ocr_width = img_width
            ocr_height = img_height
    else:
        ocr_width = 595
        ocr_height = 842
    
    return (ocr_width, ocr_height)

def normalize_bbox_ocr_to_image(
    bbox: List[float],
    image_size: tuple,
    ocr_size: tuple = None
) -> tuple:
    """OCR 좌표계를 이미지 좌표계로 변환
    
    bbox가 이미 이미지 좌표계인 경우와 OCR 좌표계인 경우를 자동 감지
    """
    if len(bbox) < 4:
        raise ValueError(f"bbox는 4개 요소가 필요합니다: {bbox}")
    
    x_min, y_min, x_max, y_max = bbox[:4]
    img_width, img_height = image_size
    
    # bbox가 이미 이미지 좌표계인지 확인
    # 일반적으로 OCR 좌표는 1000 이하, 이미지 좌표는 1000 이상
    # 또는 bbox가 이미지 크기 범위 내에 있으면 이미지 좌표계로 간주
    is_image_coords = (
        x_max > 500 or y_max > 500 or  # 큰 값이면 이미지 좌표계
        (x_max <= img_width and y_max <= img_height)  # 이미지 크기 내에 있으면 이미지 좌표계
    )
    
    if is_image_coords:
        # 이미 이미지 좌표계
        left = max(0, min(int(x_min), img_width - 1))
        top = max(0, min(int(y_min), img_height - 1))
        right = max(left + 1, min(int(x_max), img_width))
        bottom = max(top + 1, min(int(y_max), img_height))
    else:
        # OCR 좌표계 → 이미지 좌표계 변환
        if ocr_size is None:
            ocr_size = get_ocr_size_from_image(image_size)
        
        ocr_width, ocr_height = ocr_size
        
        scale_x = img_width / ocr_width
        scale_y = img_height / ocr_height
        
        # 좌표 변환
        left = int(x_min * scale_x)
        top = int(y_min * scale_y)
        right = int(x_max * scale_x)
        bottom = int(y_max * scale_y)
        
        # 이미지 크기 제한
        left = max(0, min(left, img_width - 1))
        top = max(0, min(top, img_height - 1))
        right = max(left + 1, min(int(right), img_width))
        bottom = max(top + 1, min(int(bottom), img_height))
    
    return (left, top, right, bottom)

def regenerate_content_images():
    """본문 이미지 재생성"""
    data_dir = settings.API_DIR / "data" / "literature"
    content_dir = data_dir / "content"
    content_images_dir = data_dir / "content_images"
    pages_dir = data_dir / "pages"
    
    if not content_dir.exists():
        print("본문 디렉토리가 없습니다.")
        return
    
    if not pages_dir.exists():
        print("페이지 디렉토리가 없습니다.")
        return
    
    content_images_dir.mkdir(parents=True, exist_ok=True)
    
    # content JSON 파일 읽기
    content_files = sorted(content_dir.glob("content_*.json"))
    print(f"본문 파일 {len(content_files)}개 발견")
    
    regenerated = 0
    for content_file in content_files:
        try:
            with open(content_file, 'r', encoding='utf-8') as f:
                content_data = json.load(f)
            
            page = content_data.get('page', 0)
            bbox = content_data.get('bbox', [])
            
            if not page or not bbox or len(bbox) < 4:
                print(f"  건너뜀: {content_file.name} (페이지 또는 bbox 없음)")
                continue
            
            # 페이지 이미지 로드
            page_image_path = get_page_image_path(page, pages_dir)
            if not page_image_path or not page_image_path.exists():
                print(f"  건너뜀: {content_file.name} (페이지 {page} 이미지 없음)")
                continue
            
            page_image = Image.open(page_image_path)
            
            # bbox를 이미지 좌표계로 변환 (OCR 크기 자동 추정)
            left, top, right, bottom = normalize_bbox_ocr_to_image(
                bbox,
                page_image.size
            )
            
            # 이미지 크롭
            cropped = page_image.crop((left, top, right, bottom))
            
            # 파일명 생성
            content_id = content_data.get('content_id', content_file.stem.replace('content_', ''))
            filename = f"content_p{page:02d}_{content_id.split('_')[-1] if '_' in content_id else '01'}.png"
            output_path = content_images_dir / filename
            
            # 저장
            cropped.save(output_path, 'PNG')
            print(f"  재생성: {filename} (bbox: [{left}, {top}, {right}, {bottom}])")
            regenerated += 1
            
        except Exception as e:
            print(f"  오류: {content_file.name} - {e}")
    
    print(f"\n본문 이미지 {regenerated}개 재생성 완료")

def regenerate_problem_images():
    """문제 이미지 재생성"""
    data_dir = settings.API_DIR / "data" / "literature"
    problems_dir = data_dir / "problems"
    problems_images_dir = data_dir / "problems_images"
    pages_dir = data_dir / "pages"
    
    if not problems_dir.exists():
        print("문제 디렉토리가 없습니다.")
        return
    
    if not pages_dir.exists():
        print("페이지 디렉토리가 없습니다.")
        return
    
    problems_images_dir.mkdir(parents=True, exist_ok=True)
    
    # problem JSON 파일 읽기
    problem_files = sorted(problems_dir.glob("problem_*.json"))
    print(f"문제 파일 {len(problem_files)}개 발견")
    
    regenerated = 0
    for problem_file in problem_files:
        try:
            with open(problem_file, 'r', encoding='utf-8') as f:
                problem_data = json.load(f)
            
            page = problem_data.get('page', 0)
            bbox = problem_data.get('bbox', [])
            problem_id = problem_data.get('problem_id', '')
            
            if not page or not bbox or len(bbox) < 4:
                print(f"  건너뜀: {problem_file.name} (페이지 또는 bbox 없음)")
                continue
            
            # 페이지 이미지 로드
            page_image_path = get_page_image_path(page, pages_dir)
            if not page_image_path or not page_image_path.exists():
                print(f"  건너뜀: {problem_file.name} (페이지 {page} 이미지 없음)")
                continue
            
            page_image = Image.open(page_image_path)
            
            # bbox를 이미지 좌표계로 변환 (OCR 크기 자동 추정)
            left, top, right, bottom = normalize_bbox_ocr_to_image(
                bbox,
                page_image.size
            )
            
            # 이미지 크롭
            cropped = page_image.crop((left, top, right, bottom))
            
            # 파일명 생성
            filename = f"problem_p{page:02d}_{problem_id}.png"
            output_path = problems_images_dir / filename
            
            # 저장
            cropped.save(output_path, 'PNG')
            print(f"  재생성: {filename} (bbox: [{left}, {top}, {right}, {bottom}])")
            regenerated += 1
            
        except Exception as e:
            print(f"  오류: {problem_file.name} - {e}")
    
    print(f"\n문제 이미지 {regenerated}개 재생성 완료")

if __name__ == "__main__":
    print("=" * 60)
    print("문학 이미지 재생성 스크립트")
    print("=" * 60)
    
    print("\n1. 본문 이미지 재생성")
    print("-" * 60)
    regenerate_content_images()
    
    print("\n2. 문제 이미지 재생성")
    print("-" * 60)
    regenerate_problem_images()
    
    print("\n" + "=" * 60)
    print("완료!")
    print("=" * 60)
