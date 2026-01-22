"""
YOLO 데이터셋 확인 스크립트

데이터셋이 올바르게 준비되었는지 확인
"""
import sys
from pathlib import Path
from collections import Counter

# API 경로 추가
sys.path.insert(0, str(Path(__file__).parent.parent))

PROJECT_ROOT = Path(__file__).parent.parent.parent
YOLO_DATASET_ROOT = PROJECT_ROOT / "data" / "yolo_dataset"
DATASET_YAML = YOLO_DATASET_ROOT / "dataset.yaml"


def check_dataset():
    """데이터셋 상태 확인"""
    print("=" * 60)
    print("[check_dataset] YOLO 데이터셋 확인")
    print("=" * 60)
    
    # 1. 디렉토리 구조 확인
    print("\n[1] 디렉토리 구조 확인...")
    required_dirs = [
        "images/train",
        "images/val",
        "images/test",
        "labels/train",
        "labels/val",
        "labels/test"
    ]
    
    missing_dirs = []
    for dir_path in required_dirs:
        full_path = YOLO_DATASET_ROOT / dir_path
        if not full_path.exists():
            missing_dirs.append(dir_path)
            print(f"  [X] 없음: {dir_path}")
        else:
            print(f"  [O] 있음: {dir_path}")
    
    if missing_dirs:
        print(f"\n[W] 누락된 디렉토리: {missing_dirs}")
        print("   해결: python api/scripts/yolo/prepare_dataset.py 실행")
        return False
    
    # 2. 이미지 및 라벨 파일 확인
    print("\n[2] 이미지 및 라벨 파일 확인...")
    
    splits = ["train", "val", "test"]
    total_images = 0
    total_labels = 0
    missing_labels = []
    
    for split in splits:
        images_dir = YOLO_DATASET_ROOT / "images" / split
        labels_dir = YOLO_DATASET_ROOT / "labels" / split
        
        if not images_dir.exists():
            print(f"  [W] {split}: images 디렉토리 없음")
            continue
        
        # 이미지 파일 목록
        image_files = list(images_dir.glob("*.png")) + list(images_dir.glob("*.jpg"))
        label_files = list(labels_dir.glob("*.txt"))
        
        # 이미지 이름으로 라벨 파일 찾기
        image_names = {img.stem for img in image_files}
        label_names = {label.stem for label in label_files}
        
        missing = image_names - label_names
        if missing:
            missing_labels.extend([f"{split}/{name}" for name in missing])
        
        print(f"  {split}:")
        print(f"    이미지: {len(image_files)}개")
        print(f"    라벨: {len(label_files)}개")
        print(f"    라벨 누락: {len(missing)}개")
        
        total_images += len(image_files)
        total_labels += len(label_files)
    
    if missing_labels:
        print(f"\n[W] 라벨 파일이 없는 이미지: {len(missing_labels)}개")
        print("   예시:", missing_labels[:5])
        print("   해결: LabelImg로 라벨링 필요")
    
    # 3. 라벨 파일 형식 확인
    print("\n[3] 라벨 파일 형식 확인...")
    
    sample_labels_checked = 0
    invalid_labels = []
    class_counts = Counter()
    
    for split in splits:
        labels_dir = YOLO_DATASET_ROOT / "labels" / split
        if not labels_dir.exists():
            continue
        
        label_files = list(labels_dir.glob("*.txt"))[:10]  # 샘플 10개만 확인
        
        for label_file in label_files:
            try:
                with open(label_file, "r", encoding="utf-8") as f:
                    lines = f.readlines()
                    
                    for line in lines:
                        line = line.strip()
                        if not line:
                            continue
                        
                        parts = line.split()
                        if len(parts) != 5:
                            invalid_labels.append(f"{split}/{label_file.name}: 형식 오류 (5개 값 필요)")
                            continue
                        
                        class_id = int(parts[0])
                        if class_id < 0 or class_id > 5:
                            invalid_labels.append(f"{split}/{label_file.name}: 잘못된 클래스 ID {class_id}")
                            continue
                        
                        class_counts[class_id] += 1
                        
                        # 좌표 값 확인 (0-1 범위)
                        try:
                            center_x, center_y, width, height = map(float, parts[1:5])
                            if not (0 <= center_x <= 1 and 0 <= center_y <= 1 and 
                                   0 <= width <= 1 and 0 <= height <= 1):
                                invalid_labels.append(f"{split}/{label_file.name}: 좌표 범위 오류")
                        except ValueError:
                            invalid_labels.append(f"{split}/{label_file.name}: 좌표 파싱 오류")
                
                sample_labels_checked += 1
            except Exception as e:
                invalid_labels.append(f"{split}/{label_file.name}: 읽기 오류 - {e}")
    
    if invalid_labels:
        print(f"  [W] 잘못된 라벨 파일: {len(invalid_labels)}개")
        for error in invalid_labels[:5]:
            print(f"    - {error}")
    else:
        print(f"  [O] 샘플 {sample_labels_checked}개 라벨 파일 형식 정상")
    
    # 클래스 분포
    if class_counts:
        print(f"\n  클래스 분포 (샘플):")
        class_names = {
            0: "header",
            1: "section",
            2: "passage",
            3: "question",
            4: "concept_box",
            5: "sidebar"
        }
        for class_id in sorted(class_counts.keys()):
            print(f"    {class_id} ({class_names.get(class_id, 'unknown')}): {class_counts[class_id]}개")
    
    # 4. dataset.yaml 확인
    print("\n[4] dataset.yaml 확인...")
    if DATASET_YAML.exists():
        print(f"  [O] 있음: {DATASET_YAML}")
        
        # YAML 내용 확인
        try:
            import yaml
            with open(DATASET_YAML, "r", encoding="utf-8") as f:
                config = yaml.safe_load(f)
            
            print(f"    클래스 개수: {config.get('nc', 'N/A')}")
            print(f"    클래스 이름: {list(config.get('names', {}).values())}")
        except Exception as e:
            print(f"  [W] YAML 파싱 오류: {e}")
    else:
        print(f"  [X] 없음: {DATASET_YAML}")
        print("   해결: python api/scripts/yolo/prepare_dataset.py 실행")
    
    # 5. 요약
    print("\n" + "=" * 60)
    print("[check_dataset] 요약")
    print("=" * 60)
    print(f"총 이미지: {total_images}개")
    print(f"총 라벨: {total_labels}개")
    print(f"라벨 누락: {len(missing_labels)}개")
    print(f"잘못된 라벨: {len(invalid_labels)}개")
    
    if total_images > 0 and total_labels == total_images and len(invalid_labels) == 0:
        print("\n[O] 데이터셋 준비 완료! 학습을 시작할 수 있습니다.")
        print("   다음 단계: python api/scripts/yolo/train_yolo.py")
        return True
    else:
        print("\n[W] 데이터셋 준비가 완료되지 않았습니다.")
        if missing_labels:
            print("   - 라벨 파일 추가 필요")
        if invalid_labels:
            print("   - 라벨 파일 형식 수정 필요")
        return False


if __name__ == "__main__":
    check_dataset()
