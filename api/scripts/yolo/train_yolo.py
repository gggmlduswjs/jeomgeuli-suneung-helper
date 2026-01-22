"""
YOLO 모델 학습 스크립트

사용법:
    python scripts/yolo/train_yolo.py
"""
import shutil
from pathlib import Path
from ultralytics import YOLO

PROJECT_ROOT = Path(__file__).parent.parent.parent
# 프로젝트 루트의 dataset 폴더 우선 사용, 없으면 api/data/yolo_dataset 사용
DATASET_YAML_ROOT = PROJECT_ROOT.parent / "dataset" / "data.yaml"
DATASET_YAML_FALLBACK = PROJECT_ROOT / "data" / "yolo_dataset" / "dataset.yaml"

if DATASET_YAML_ROOT.exists():
    DATASET_YAML = DATASET_YAML_ROOT
    print(f"[train_yolo] 프로젝트 루트의 dataset 사용: {DATASET_YAML}")
else:
    DATASET_YAML = DATASET_YAML_FALLBACK
    print(f"[train_yolo] api/data/yolo_dataset 사용: {DATASET_YAML}")

MODEL_OUTPUT = PROJECT_ROOT / "models" / "yolo_literature.pt"


def train_yolo_model(
    model_size: str = "n",  # "n", "s", "m", "l", "x"
    epochs: int = 100,
    batch_size: int = 16,
    image_size: int = 640,
    device: str = "cpu"  # "cpu" or "cuda"
):
    """
    YOLOv8 모델 학습
    
    Args:
        model_size: 모델 크기 ("n"=nano, "s"=small, "m"=medium, "l"=large, "x"=xlarge)
        epochs: 학습 에포크 수
        batch_size: 배치 크기
        image_size: 입력 이미지 크기
        device: 사용할 디바이스
    """
    print(f"[train_yolo] YOLO 모델 학습 시작")
    print(f"  모델 크기: YOLOv8{model_size}")
    print(f"  에포크: {epochs}")
    print(f"  배치 크기: {batch_size}")
    print(f"  이미지 크기: {image_size}")
    print(f"  디바이스: {device}")
    
    # 데이터셋 파일 확인
    if not DATASET_YAML.exists():
        raise FileNotFoundError(
            f"데이터셋 설정 파일을 찾을 수 없습니다: {DATASET_YAML}\n"
            "먼저 scripts/yolo/prepare_dataset.py를 실행하세요."
        )
    
    # 사전 학습된 모델 로드
    model_name = f"yolov8{model_size}.pt"
    print(f"[train_yolo] 모델 로드: {model_name}")
    model = YOLO(model_name)
    
    # 학습 시작
    print(f"[train_yolo] 학습 시작...")
    results = model.train(
        data=str(DATASET_YAML),
        epochs=epochs,
        imgsz=image_size,
        batch=batch_size,
        name="literature_detector",
        device=device,
        patience=20,  # Early stopping
        save=True,
        plots=True,
        verbose=True,
    )
    
    # 최고 성능 모델 저장
    best_model_path = Path("runs/detect/literature_detector/weights/best.pt")
    if best_model_path.exists():
        MODEL_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(best_model_path, MODEL_OUTPUT)
        print(f"[train_yolo] ✅ 모델 저장 완료: {MODEL_OUTPUT}")
    else:
        print(f"[train_yolo] ⚠️  최고 모델을 찾을 수 없습니다: {best_model_path}")
    
    # 학습 결과 요약
    print("\n[train_yolo] 학습 완료!")
    print(f"  최고 모델: {best_model_path}")
    print(f"  저장 위치: {MODEL_OUTPUT}")
    print(f"  결과 디렉토리: runs/detect/literature_detector/")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="YOLO 모델 학습")
    parser.add_argument("--model-size", type=str, default="s", choices=["n", "s", "m", "l", "x"],
                        help="모델 크기 (n=nano, s=small, m=medium, l=large, x=xlarge)")
    parser.add_argument("--epochs", type=int, default=100, help="학습 에포크 수")
    parser.add_argument("--batch-size", type=int, default=16, help="배치 크기")
    parser.add_argument("--image-size", type=int, default=640, help="이미지 크기")
    parser.add_argument("--device", type=str, default="cpu", choices=["cpu", "cuda"],
                        help="사용할 디바이스")
    
    args = parser.parse_args()
    
    train_yolo_model(
        model_size=args.model_size,
        epochs=args.epochs,
        batch_size=args.batch_size,
        image_size=args.image_size,
        device=args.device
    )
