"""
Roboflow API 테스트 스크립트

사용법:
    python scripts/test_roboflow.py
"""
import sys
from pathlib import Path

# API 경로 추가
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.dl.yolo_detector import RoboflowDetector

def test_roboflow():
    """Roboflow API 테스트"""
    print("[test_roboflow] Roboflow API 테스트 시작...")
    
    # 테스트 이미지 경로
    test_image = Path(__file__).parent.parent / "data" / "literature" / "pages" / "page_001.png"
    
    if not test_image.exists():
        print(f"[test_roboflow] 테스트 이미지를 찾을 수 없습니다: {test_image}")
        return
    
    try:
        # 감지기 생성
        detector = RoboflowDetector(
            workspace_id="-wshlq",
            project_id="2",
            api_key="ohDbNa6uGc3Aozm81aci",
            confidence_threshold=0.25
        )
        
        print(f"[test_roboflow] 이미지 감지 중: {test_image}")
        
        # 감지 실행
        results = detector.detect_page(str(test_image))
        
        print(f"[test_roboflow] 감지 완료: {len(results.detections)}개 영역 발견")
        
        # 결과 출력
        for i, det in enumerate(results.detections, 1):
            print(f"\n  [{i}] {det.class_name}")
            print(f"      신뢰도: {det.confidence:.2%}")
            print(f"      위치: {det.bbox}")
            print(f"      픽셀 좌표: [")
            print(f"        x1={int(det.bbox[0] * results.image_width)}, "
                  f"y1={int(det.bbox[1] * results.image_height)}")
            print(f"        x2={int(det.bbox[2] * results.image_width)}, "
                  f"y2={int(det.bbox[3] * results.image_height)}")
            print(f"      ]")
        
        print(f"\n[test_roboflow] ✅ 테스트 완료!")
        
    except Exception as e:
        print(f"[test_roboflow] ❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_roboflow()
