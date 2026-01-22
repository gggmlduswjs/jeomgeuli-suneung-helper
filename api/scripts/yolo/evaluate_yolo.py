"""
YOLO 모델 평가 스크립트

사용법:
    python scripts/yolo/evaluate_yolo.py
"""
import sys
from pathlib import Path

# API 경로 추가
sys.path.insert(0, str(Path(__file__).parent.parent))

from ultralytics import YOLO

PROJECT_ROOT = Path(__file__).parent.parent.parent
MODEL_PATH = PROJECT_ROOT / "models" / "yolo_literature.pt"
DATASET_YAML = PROJECT_ROOT / "data" / "yolo_dataset" / "dataset.yaml"


def evaluate_model():
    """모델 성능 평가"""
    print(f"[evaluate_yolo] 모델 평가 시작...")
    
    # 모델 파일 확인
    if not MODEL_PATH.exists():
        print(f"[evaluate_yolo] ❌ 모델 파일을 찾을 수 없습니다: {MODEL_PATH}")
        print(f"[evaluate_yolo] 먼저 학습을 실행하세요: python scripts/yolo/train_yolo.py")
        return
    
    # 데이터셋 파일 확인
    if not DATASET_YAML.exists():
        print(f"[evaluate_yolo] ❌ 데이터셋 설정 파일을 찾을 수 없습니다: {DATASET_YAML}")
        print(f"[evaluate_yolo] 먼저 데이터셋을 준비하세요: python scripts/yolo/prepare_dataset.py")
        return
    
    try:
        # 모델 로드
        print(f"[evaluate_yolo] 모델 로드: {MODEL_PATH}")
        model = YOLO(str(MODEL_PATH))
        
        # 검증 데이터셋으로 평가
        print(f"[evaluate_yolo] 평가 실행 중...")
        results = model.val(
            data=str(DATASET_YAML),
            imgsz=640,
            conf=0.25,
            iou=0.45,
            verbose=True
        )
        
        # 결과 출력
        print("\n" + "=" * 60)
        print("[evaluate_yolo] 평가 결과")
        print("=" * 60)
        print(f"mAP50: {results.box.map50:.4f}")
        print(f"mAP50-95: {results.box.map:.4f}")
        print(f"\n클래스별 성능:")
        
        # 클래스별 mAP 출력
        if hasattr(results.box, 'maps'):
            class_names = [
                "header", "section", "passage", 
                "question", "concept_box", "sidebar"
            ]
            for i, (class_name, map_value) in enumerate(zip(class_names, results.box.maps)):
                print(f"  {class_name}: {map_value:.4f}")
        
        print("\n" + "=" * 60)
        print(f"[evaluate_yolo] ✅ 평가 완료!")
        print("=" * 60)
        
    except Exception as e:
        print(f"[evaluate_yolo] ❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    evaluate_model()
