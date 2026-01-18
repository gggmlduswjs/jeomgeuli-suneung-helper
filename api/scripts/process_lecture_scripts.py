"""
강의 대본 일괄 처리 스크립트

사용법:
    python scripts/process_lecture_scripts.py --subject literature --input data/lecture_scripts/수능특강_문학_2026 --output data/parsed/literature
    python scripts/process_lecture_scripts.py --subject math1 --input data/lecture_scripts/수능특강_수1_2026 --output data/parsed/math1
"""
import argparse
import sys
from pathlib import Path

# 프로젝트 루트를 경로에 추가
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.lecture_to_json_pipeline import process_lecture_scripts_directory


def main():
    parser = argparse.ArgumentParser(description='강의 대본을 구조화된 JSON으로 변환')
    parser.add_argument('--subject', required=True, choices=['literature', 'math1', 'english'],
                       help='과목명')
    parser.add_argument('--input', required=True, type=Path,
                       help='강의 대본 디렉토리 경로')
    parser.add_argument('--output', required=True, type=Path,
                       help='출력 디렉토리 경로')
    parser.add_argument('--pattern', default='*.hwp',
                       help='파일 패턴 (기본값: *.hwp)')
    
    args = parser.parse_args()
    
    # 입력 디렉토리 확인
    if not args.input.exists():
        print(f"[오류] 입력 디렉토리를 찾을 수 없습니다: {args.input}")
        return 1
    
    # 처리 시작
    print(f"[시작] 과목: {args.subject}")
    print(f"[시작] 입력: {args.input}")
    print(f"[시작] 출력: {args.output}")
    print("-" * 70)
    
    results = process_lecture_scripts_directory(
        scripts_dir=args.input,
        output_dir=args.output,
        subject=args.subject,
        file_pattern=args.pattern
    )
    
    # 결과 요약
    print("-" * 70)
    print(f"[완료] 총 {len(results)}개 파일 처리")
    print(f"[완료] 총 {sum(r['sections'] for r in results)}개 섹션 생성")
    print(f"[완료] 총 {sum(r['units'] for r in results)}개 학습 단위 생성")
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
