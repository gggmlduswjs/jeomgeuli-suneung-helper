"""
YOLO 데이터셋 준비 스크립트

기존에 추출된 이미지들을 YOLO 학습용 데이터셋으로 변환
"""
import shutil
import json
from pathlib import Path
from typing import List, Tuple
import random
from PIL import Image

# 프로젝트 루트 경로
PROJECT_ROOT = Path(__file__).parent.parent.parent
DATA_ROOT = PROJECT_ROOT / "data" / "literature"
YOLO_DATASET_ROOT = PROJECT_ROOT / "data" / "yolo_dataset"


def create_yolo_label_from_existing_data(
    image_path: Path,
    image_type: str,  # "concept", "problem", "content"
    page_image_path: Path
) -> Tuple[str, List[float]]:
    """
    기존 추출된 이미지로부터 YOLO 라벨 생성
    
    Args:
        image_path: 추출된 이미지 경로 (예: concepts_images/concept_p08_01.png)
        image_type: 이미지 타입 ("concept", "problem", "content")
        page_image_path: 원본 페이지 이미지 경로
        
    Returns:
        (class_name, bbox) 튜플
        bbox는 [center_x, center_y, width, height] 형식 (0-1 정규화)
    """
    # 클래스 매핑
    class_map = {
        "concept": 1,
        "problem": 0,
        "content": 2,
    }
    
    class_id = class_map.get(image_type, 2)
    
    # 원본 페이지 이미지 크기
    page_img = Image.open(page_image_path)
    page_width, page_height = page_img.size
    
    # 추출된 이미지 크기
    crop_img = Image.open(image_path)
    crop_width, crop_height = crop_img.size
    
    # 파일명에서 위치 정보 추출 (예: concept_p08_01.png -> page 8)
    # 실제로는 JSON 메타데이터나 다른 방법으로 bbox를 찾아야 함
    # 여기서는 간단한 예시만 제공
    
    # TODO: 실제 bbox 정보는 lecture JSON이나 다른 메타데이터에서 가져와야 함
    # 임시로 중앙에 배치 (실제로는 정확한 좌표 필요)
    center_x = 0.5
    center_y = 0.5
    width = min(crop_width / page_width, 0.9)
    height = min(crop_height / page_height, 0.9)
    
    bbox = [center_x, center_y, width, height]
    
    return (class_id, bbox)


def prepare_dataset_from_lectures():
    """
    lecture JSON 파일들을 기반으로 데이터셋 준비
    """
    print("[prepare_dataset] 데이터셋 준비 시작...")
    
    # 디렉토리 생성
    for split in ["train", "val", "test"]:
        (YOLO_DATASET_ROOT / "images" / split).mkdir(parents=True, exist_ok=True)
        (YOLO_DATASET_ROOT / "labels" / split).mkdir(parents=True, exist_ok=True)
    
    # lecture JSON 파일 읽기
    lectures_dir = DATA_ROOT / "lectures"
    lecture_files = sorted(lectures_dir.glob("lecture_*.json"))
    
    all_pages = []
    
    for lecture_file in lecture_files:
        print(f"[prepare_dataset] 처리 중: {lecture_file.name}")
        
        with open(lecture_file, "r", encoding="utf-8") as f:
            lecture_data = json.load(f)
        
        # 각 섹션에서 페이지 정보 추출
        sections = lecture_data.get("sections", [])
        for section in sections:
            page = section.get("page")
            if page:
                all_pages.append(page)
    
    # 중복 제거 및 정렬
    unique_pages = sorted(set(all_pages))
    print(f"[prepare_dataset] 총 {len(unique_pages)}개 페이지 발견")
    
    # train/val/test 분할 (70/20/10)
    random.shuffle(unique_pages)
    n = len(unique_pages)
    train_end = int(n * 0.7)
    val_end = train_end + int(n * 0.2)
    
    train_pages = unique_pages[:train_end]
    val_pages = unique_pages[train_end:val_end]
    test_pages = unique_pages[val_end:]
    
    print(f"[prepare_dataset] 분할: train={len(train_pages)}, val={len(val_pages)}, test={len(test_pages)}")
    
    # 각 페이지에 대해 이미지와 라벨 준비
    for split, pages in [("train", train_pages), ("val", val_pages), ("test", test_pages)]:
        for page_num in pages:
            page_image_path = DATA_ROOT / "pages" / f"page_{page_num:03d}.png"
            
            if not page_image_path.exists():
                print(f"[prepare_dataset] 경고: {page_image_path} 없음, 건너뜀")
                continue
            
            # 이미지 복사
            dest_image = YOLO_DATASET_ROOT / "images" / split / f"page_{page_num:03d}.png"
            shutil.copy(page_image_path, dest_image)
            
            # 라벨 파일 생성 (임시 - 실제로는 lecture JSON에서 bbox 정보 가져와야 함)
            label_file = YOLO_DATASET_ROOT / "labels" / split / f"page_{page_num:03d}.txt"
            
            # TODO: lecture JSON에서 해당 페이지의 실제 bbox 정보 추출
            # 여기서는 빈 라벨 파일 생성 (수동 라벨링 필요)
            label_file.write_text("", encoding="utf-8")
    
    print(f"[prepare_dataset] 데이터셋 준비 완료: {YOLO_DATASET_ROOT}")
    print("[prepare_dataset] 다음 단계: LabelImg로 수동 라벨링 필요")


def create_dataset_yaml():
    """YOLO 데이터셋 설정 파일 생성"""
    yaml_content = """# YOLO 데이터셋 설정
path: {path}
train: images/train
val: images/val
test: images/test

# 클래스 정의 (업데이트된 클래스 매핑)
names:
  0: header        # 헤더 영역 (단원/유형/번호/코너 이름)
  1: section       # 섹션 영역 (하나의 문제 묶음/학습 단위)
  2: passage       # 본문 영역 (문제를 풀기 위해 읽어야 하는 지문)
  3: question      # 문제 영역 (질문 + 선지)
  4: concept_box   # 개념박스 영역 (풀이 전략/개념 설명)
  5: sidebar       # 사이드바 영역 (부가 정보: 단어 뜻, 주석 등)

# 클래스 개수
nc: 6
""".format(path=str(YOLO_DATASET_ROOT.absolute()))
    
    yaml_path = YOLO_DATASET_ROOT / "dataset.yaml"
    yaml_path.write_text(yaml_content, encoding="utf-8")
    print(f"[prepare_dataset] dataset.yaml 생성: {yaml_path}")


if __name__ == "__main__":
    prepare_dataset_from_lectures()
    create_dataset_yaml()
