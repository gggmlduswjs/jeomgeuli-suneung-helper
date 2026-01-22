"""
YOLO 기반 문학 파싱 파이프라인 통합 테스트

LiteratureStrategy의 extract_with_yolo() 메서드를 사용하여 전체 파이프라인을 테스트합니다.

사용법:
    # Roboflow API로 테스트
    python scripts/yolo/test_literature_pipeline.py --start-page 8 --end-page 12

    # 로컬 모델로 테스트 (학습 후)
    python scripts/yolo/test_literature_pipeline.py --mode local --model models/yolo_literature.pt --start-page 8 --end-page 12
"""
import argparse
import json
import os
from pathlib import Path
import sys

# 프로젝트 루트를 sys.path에 추가
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from app.parsing.strategies.literature_strategy import LiteratureParsingStrategy


def create_mock_ocr_data(start_page: int, end_page: int, pages_dir: Path) -> list:
    """
    테스트용 Mock OCR 데이터 생성

    Args:
        start_page: 시작 페이지
        end_page: 종료 페이지
        pages_dir: 페이지 이미지 디렉토리

    Returns:
        OCR 데이터 리스트
    """
    ocr_data_list = []

    for page_num in range(start_page, end_page + 1):
        page_path = pages_dir / f"page_{page_num:03d}.png"

        if not page_path.exists():
            print(f"⚠️  페이지 이미지가 없습니다: {page_path.name}")
            continue

        ocr_data_list.append({
            'page_num': page_num,
            'page_path': str(page_path),
            'text': [],  # OCR 텍스트 (YOLO 사용 시 불필요)
            'top': [],
            'left': [],
            'width': [],
            'height': []
        })

    return ocr_data_list


def test_yolo_pipeline(
    mode: str = "roboflow",
    start_page: int = 8,
    end_page: int = 12,
    model_path: str = "models/yolo_literature.pt",
    output_file: str = "output/yolo_parsing_result.json"
):
    """
    YOLO 기반 문학 파싱 파이프라인 테스트

    Args:
        mode: "roboflow" 또는 "local"
        start_page: 시작 페이지
        end_page: 종료 페이지
        model_path: 로컬 모델 경로 (local 모드)
        output_file: 결과 저장 파일
    """
    print("=" * 80)
    print("YOLO 기반 문학 파싱 파이프라인 테스트")
    print("=" * 80)
    print()

    # 설정
    pages_dir = PROJECT_ROOT / "data" / "literature" / "pages"
    config = {
        'data_dir': str(PROJECT_ROOT / "data" / "literature"),
        'start_content_page': 8
    }

    print(f"📂 페이지 디렉토리: {pages_dir}")
    print(f"📄 테스트 범위: 페이지 {start_page} ~ {end_page}")
    print(f"🤖 모드: {mode}")
    print()

    # Mock OCR 데이터 생성
    print("📋 OCR 데이터 생성 중...")
    ocr_data = create_mock_ocr_data(start_page, end_page, pages_dir)
    print(f"✅ {len(ocr_data)}개 페이지 데이터 생성 완료")
    print()

    # LiteratureParsingStrategy 생성
    strategy = LiteratureParsingStrategy()

    # API 키 확인 (Roboflow 모드)
    api_key = None
    if mode == "roboflow":
        api_key = os.getenv("ROBOFLOW_API_KEY")
        if not api_key:
            print("⚠️  경고: ROBOFLOW_API_KEY 환경변수가 설정되지 않았습니다.")
            api_key = "ohDbNa6uGc3Aozm81aci"
            print(f"   테스트용 키 사용: {api_key[:10]}...")
        print()

    # YOLO 파싱 실행
    print("🔍 YOLO 파싱 수행 중...")
    print()

    try:
        if mode == "roboflow":
            result = strategy.extract_with_yolo(
                all_ocr_data=ocr_data,
                config=config,
                use_roboflow=True,
                roboflow_api_key=api_key
            )
        else:
            full_model_path = PROJECT_ROOT / model_path
            if not full_model_path.exists():
                print(f"❌ 모델 파일을 찾을 수 없습니다: {full_model_path}")
                print()
                print("먼저 모델을 학습하세요:")
                print("   python scripts/yolo/train_yolo.py")
                return

            result = strategy.extract_with_yolo(
                all_ocr_data=ocr_data,
                config=config,
                use_roboflow=False,
                local_model_path=str(full_model_path)
            )

        print("✅ YOLO 파싱 완료")
        print()

    except Exception as e:
        print(f"❌ 파싱 실패: {e}")
        import traceback
        traceback.print_exc()
        return

    # 결과 출력
    print("=" * 80)
    print("📊 파싱 결과 요약")
    print("=" * 80)
    print()

    print(f"📚 강의 (헤더): {len(result['lectures'])}개")
    if result['lectures']:
        for lec in result['lectures'][:5]:
            print(f"   - 페이지 {lec['page']}: {lec['title']} (conf: {lec['confidence']:.3f})")
        if len(result['lectures']) > 5:
            print(f"   ... 외 {len(result['lectures']) - 5}개")
    print()

    print(f"❓ 문제 (질문): {len(result['problems'])}개")
    if result['problems']:
        for prob in result['problems'][:5]:
            print(f"   - 페이지 {prob['page']}: 문제 {prob['problem_id']} (conf: {prob['confidence']:.3f})")
        if len(result['problems']) > 5:
            print(f"   ... 외 {len(result['problems']) - 5}개")
    print()

    print(f"📖 지문 (본문): {len(result['passages'])}개")
    if result['passages']:
        for pass_item in result['passages'][:5]:
            print(f"   - 페이지 {pass_item['page']}: 지문 {pass_item['passage_id']} (conf: {pass_item['confidence']:.3f})")
        if len(result['passages']) > 5:
            print(f"   ... 외 {len(result['passages']) - 5}개")
    print()

    print(f"🗂️  섹션: {len(result['sections'])}개")
    print(f"💡 개념박스: {len(result['concept_boxes'])}개")
    print(f"📝 사이드바: {len(result['sidebars'])}개")
    print()

    # 결과 저장
    output_path = PROJECT_ROOT / output_file
    output_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        print(f"💾 결과 저장 완료: {output_path}")
    except Exception as e:
        print(f"⚠️  결과 저장 실패: {e}")

    print()
    print("=" * 80)
    print("✅ 테스트 완료")
    print("=" * 80)


def main():
    parser = argparse.ArgumentParser(description="YOLO 기반 문학 파싱 파이프라인 테스트")
    parser.add_argument(
        "--mode",
        type=str,
        default="roboflow",
        choices=["roboflow", "local"],
        help="테스트 모드 (roboflow: Roboflow API, local: 로컬 모델)"
    )
    parser.add_argument(
        "--start-page",
        type=int,
        default=8,
        help="시작 페이지 번호"
    )
    parser.add_argument(
        "--end-page",
        type=int,
        default=12,
        help="종료 페이지 번호"
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
        default="output/yolo_parsing_result.json",
        help="결과 저장 파일"
    )

    args = parser.parse_args()

    test_yolo_pipeline(
        mode=args.mode,
        start_page=args.start_page,
        end_page=args.end_page,
        model_path=args.model,
        output_file=args.output
    )


if __name__ == "__main__":
    main()
