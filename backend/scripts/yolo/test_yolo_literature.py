"""
YOLO 문학 모델 테스트 스크립트

새로운 6개 클래스 모델 테스트:
- header: 단원/유형/번호/코너 이름
- section: 하나의 문제 묶음 또는 학습 단위
- passage: 문제를 풀기 위해 읽어야 하는 본문 영역
- question: 질문 + 선지
- concept_box: 풀이 전략/개념 설명
- sidebar: 부가 정보 (단어 뜻, 주석 등)

사용법:
    # Roboflow API 테스트
    python scripts/yolo/test_yolo_literature.py --mode roboflow --page 8

    # 로컬 모델 테스트 (학습 후)
    python scripts/yolo/test_yolo_literature.py --mode local --page 8 --model models/yolo_literature.pt
"""
import argparse
import os
from pathlib import Path
import sys

# 프로젝트 루트를 sys.path에 추가
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from app.dl.yolo_detector import YOLODetector, RoboflowDetector


def test_roboflow_detector(page_num: int = 8, output_dir: str = "output"):
    """
    Roboflow API를 사용하여 문학 페이지 테스트

    Args:
        page_num: 테스트할 페이지 번호
        output_dir: 결과 저장 디렉토리
    """
    print("=" * 80)
    print("Roboflow YOLO Detector 테스트")
    print("=" * 80)

    # 페이지 경로
    page_path = PROJECT_ROOT / "data" / "literature" / "pages" / f"page_{page_num:03d}.png"

    if not page_path.exists():
        print(f"❌ 페이지를 찾을 수 없습니다: {page_path}")
        print(f"   다른 페이지를 시도하거나 data/literature/pages/ 디렉토리를 확인하세요.")
        return

    print(f"📄 테스트 페이지: {page_path.name}")
    print()

    # API 키 확인
    api_key = os.getenv("ROBOFLOW_API_KEY")
    if not api_key:
        print("⚠️  경고: ROBOFLOW_API_KEY 환경변수가 설정되지 않았습니다.")
        print("   다음 명령으로 설정하세요:")
        print("   export ROBOFLOW_API_KEY=your_api_key_here")
        print()
        # 하드코딩된 키 사용 (테스트용)
        api_key = "ohDbNa6uGc3Aozm81aci"
        print(f"   테스트용 키 사용: {api_key[:10]}...")
        print()

    # Roboflow Detector 생성
    try:
        detector = RoboflowDetector(
            workspace_id="-wshlq",
            project_id="2",
            api_key=api_key,
            confidence_threshold=0.25,
            overlap_threshold=30.0
        )
        print("✅ Roboflow Detector 초기화 완료")
        print()
    except Exception as e:
        print(f"❌ Detector 초기화 실패: {e}")
        return

    # 감지 수행
    print("🔍 감지 수행 중...")
    try:
        result = detector.detect_page(str(page_path))
        print(f"✅ 감지 완료: {len(result.detections)}개 영역 발견")
        print()
    except Exception as e:
        print(f"❌ 감지 실패: {e}")
        return

    # 결과 출력
    print("📊 감지 결과:")
    print("-" * 80)
    if result.detections:
        for i, det in enumerate(result.detections, 1):
            print(f"{i:2d}. {det.class_name:12s} (conf: {det.confidence:.3f})")
            print(f"    bbox: [{det.bbox[0]:.3f}, {det.bbox[1]:.3f}, {det.bbox[2]:.3f}, {det.bbox[3]:.3f}]")
            print()
    else:
        print("   감지된 영역이 없습니다.")
        print("   - confidence_threshold를 낮춰보세요 (현재: 0.25)")
        print("   - 다른 페이지를 시도해보세요")

    print("-" * 80)

    # 클래스별 통계
    class_counts = {}
    for det in result.detections:
        class_counts[det.class_name] = class_counts.get(det.class_name, 0) + 1

    if class_counts:
        print()
        print("📈 클래스별 통계:")
        for class_name, count in sorted(class_counts.items()):
            print(f"   {class_name:12s}: {count:2d}개")

    print()
    print("=" * 80)


def test_local_detector(page_num: int = 8, model_path: str = "models/yolo_literature.pt", output_dir: str = "output"):
    """
    로컬 YOLO 모델을 사용하여 문학 페이지 테스트

    Args:
        page_num: 테스트할 페이지 번호
        model_path: 모델 파일 경로
        output_dir: 결과 저장 디렉토리
    """
    print("=" * 80)
    print("로컬 YOLO Detector 테스트")
    print("=" * 80)

    # 페이지 경로
    page_path = PROJECT_ROOT / "data" / "literature" / "pages" / f"page_{page_num:03d}.png"

    if not page_path.exists():
        print(f"❌ 페이지를 찾을 수 없습니다: {page_path}")
        print(f"   다른 페이지를 시도하거나 data/literature/pages/ 디렉토리를 확인하세요.")
        return

    print(f"📄 테스트 페이지: {page_path.name}")

    # 모델 경로 확인
    full_model_path = PROJECT_ROOT / model_path
    if not full_model_path.exists():
        print(f"❌ 모델 파일을 찾을 수 없습니다: {full_model_path}")
        print()
        print("먼저 모델을 학습하세요:")
        print("   python scripts/yolo/train_yolo.py")
        print()
        print("또는 Roboflow API를 사용하세요:")
        print("   python scripts/yolo/test_yolo_literature.py --mode roboflow")
        return

    print(f"🤖 모델 파일: {full_model_path.name}")
    print()

    # YOLO Detector 생성
    try:
        detector = YOLODetector(
            model_path=str(full_model_path),
            confidence_threshold=0.25,
            iou_threshold=0.45,
            device="cpu"
        )
        print("✅ YOLO Detector 초기화 완료")
        print()
    except Exception as e:
        print(f"❌ Detector 초기화 실패: {e}")
        return

    # 감지 수행
    print("🔍 감지 수행 중...")
    try:
        result = detector.detect_page(str(page_path))
        print(f"✅ 감지 완료: {len(result.detections)}개 영역 발견")
        print()
    except Exception as e:
        print(f"❌ 감지 실패: {e}")
        return

    # 결과 출력
    print("📊 감지 결과:")
    print("-" * 80)
    if result.detections:
        for i, det in enumerate(result.detections, 1):
            print(f"{i:2d}. {det.class_name:12s} (conf: {det.confidence:.3f})")
            print(f"    bbox: [{det.bbox[0]:.3f}, {det.bbox[1]:.3f}, {det.bbox[2]:.3f}, {det.bbox[3]:.3f}]")
            print()
    else:
        print("   감지된 영역이 없습니다.")
        print("   - confidence_threshold를 낮춰보세요 (현재: 0.25)")
        print("   - 모델 재학습이 필요할 수 있습니다")

    print("-" * 80)

    # 클래스별 통계
    class_counts = {}
    for det in result.detections:
        class_counts[det.class_name] = class_counts.get(det.class_name, 0) + 1

    if class_counts:
        print()
        print("📈 클래스별 통계:")
        for class_name, count in sorted(class_counts.items()):
            print(f"   {class_name:12s}: {count:2d}개")

    # 시각화 (선택적)
    output_path = PROJECT_ROOT / output_dir / f"page_{page_num:03d}_detected.png"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        print()
        print(f"🎨 시각화 저장 중: {output_path.name}")
        detector.visualize_detections(str(page_path), str(output_path))
        print(f"✅ 시각화 완료: {output_path}")
    except Exception as e:
        print(f"⚠️  시각화 실패: {e}")

    print()
    print("=" * 80)


def main():
    parser = argparse.ArgumentParser(description="YOLO 문학 모델 테스트")
    parser.add_argument(
        "--mode",
        type=str,
        default="roboflow",
        choices=["roboflow", "local"],
        help="테스트 모드 (roboflow: Roboflow API, local: 로컬 모델)"
    )
    parser.add_argument(
        "--page",
        type=int,
        default=8,
        help="테스트할 페이지 번호 (기본값: 8)"
    )
    parser.add_argument(
        "--model",
        type=str,
        default="models/yolo_literature.pt",
        help="로컬 모델 경로 (local 모드에서만 사용)"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="output",
        help="결과 저장 디렉토리"
    )

    args = parser.parse_args()

    if args.mode == "roboflow":
        test_roboflow_detector(page_num=args.page, output_dir=args.output)
    else:
        test_local_detector(page_num=args.page, model_path=args.model, output_dir=args.output)


if __name__ == "__main__":
    main()
