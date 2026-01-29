"""
교재 PDF 파이프라인 실행 스크립트 (개발/테스트용)

⚠️ 주의: 이 스크립트는 개발 및 디버깅용입니다.
실제 운영 환경에서는 API 엔드포인트를 사용하세요:
  POST /api/books/upload

용도:
  - 파이프라인 로직 테스트
  - 디버깅 및 성능 측정
  - 로컬 개발 환경에서 빠른 테스트

실제 사용:
  프론트엔드 → POST /api/books/upload → 백그라운드 처리 → DB 저장
"""
import sys
from pathlib import Path

# 프로젝트 루트를 경로에 추가
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))  # backend/ 디렉토리를 경로에 추가

from app.infrastructure.pdf.pipeline import UnifiedPipeline
from app.core.config import settings

def main():
    """교재 PDF 파이프라인 실행 (개발/테스트용)"""
    
    print("=" * 60)
    print("교재 PDF 기반 AI 학습 콘텐츠 자동 생성 시스템")
    print("=" * 60)
    print("⚠️  개발/테스트용 스크립트입니다.")
    print("    실제 운영: POST /api/books/upload 사용")
    print("=" * 60)
    
    # 과목 선택
    subject = input("과목을 선택하세요 (literature/math1/english): ").strip().lower()
    if subject not in ['literature', 'math1', 'english']:
        print(f"[ERROR] 지원하지 않는 과목입니다: {subject}")
        return
    
    # PDF 파일 찾기
    pdf_dir = project_root / "data" / subject / "pdf"
    if not pdf_dir.exists():
        pdf_dir.mkdir(parents=True, exist_ok=True)
    
    pdf_files = list(pdf_dir.glob("*.pdf"))
    
    if not pdf_files:
        print(f"[ERROR] PDF 파일을 찾을 수 없습니다.")
        print(f"  경로: {pdf_dir}")
        print(f"  PDF 파일을 해당 경로에 넣어주세요.")
        return
    
    pdf_path = pdf_files[0]
    print(f"[INFO] PDF 파일: {pdf_path}")
    print(f"[INFO] 과목: {subject}")
    
    # 최적화 옵션 선택
    print(f"\n[최적화 옵션]")
    print(f"    💡 pdfplumber: 텍스트 레이어가 있는 PDF에 권장 (OCR보다 정확하고 빠름)")
    use_pdfplumber = input("pdfplumber 사용? (Y/n): ").strip().lower() != 'n'
    use_parallel = input("병렬 처리 사용? (Y/n): ").strip().lower() != 'n'
    print(f"    ⚠️ AI 후처리는 각 페이지마다 LLM API 호출로 매우 느립니다 (13페이지 ≈ 30초+).")
    print(f"    💡 빠른 처리를 원하면 'n'을 입력하세요.")
    use_ai = input("AI 후처리 사용? (y/N): ").strip().lower() == 'y'
    dpi_input = input("DPI 설정 (기본값 200, Enter로 기본값 사용): ").strip()
    if dpi_input and dpi_input.isdigit():
        dpi = int(dpi_input)
    else:
        dpi = 200
        if dpi_input:
            print(f"    잘못된 입력입니다. 기본값 200 사용")
    
    # 페이지 제한 옵션 (1강만 처리)
    max_pages_input = input("처리할 최대 페이지 수 (1강만: 20, 전체: Enter): ").strip()
    max_pages = None
    if max_pages_input and max_pages_input.isdigit():
        max_pages = int(max_pages_input)
        print(f"    ⚠️ 첫 {max_pages}페이지만 처리합니다")
    else:
        print(f"    전체 페이지 처리")
    
    # 캐시 및 생성된 파일 삭제 옵션
    clear_cache = input("OCR 캐시 및 생성된 파일 삭제? (빈 결과가 나올 때: y/N): ").strip().lower() == 'y'
    if clear_cache:
        import shutil
        # backend/data 경로만 확인
        base_dirs = [
            project_root / "data" / subject
        ]
        
        deleted_count = 0
        for base_dir in base_dirs:
            if not base_dir.exists():
                continue
            
            # 삭제할 디렉토리 목록
            dirs_to_delete = [
                "cache",
                "concepts_images",
                "content_images",
                "problems_images",
                "lectures",
                "problems",
                "visualizations",
                "pages"  # 페이지 이미지도 삭제
            ]
            
            for dir_name in dirs_to_delete:
                target_dir = base_dir / dir_name
                if target_dir.exists():
                    shutil.rmtree(target_dir)
                    print(f"    ✓ 삭제 완료: {target_dir}")
                    deleted_count += 1
            
            # config.json도 삭제 (선택사항)
            config_file = base_dir / "config.json"
            if config_file.exists():
                config_file.unlink()
                print(f"    ✓ 삭제 완료: {config_file}")
                deleted_count += 1
        
        if deleted_count == 0:
            print(f"    삭제할 파일/폴더가 없습니다 (이미 삭제되었거나 없음)")
        else:
            print(f"    총 {deleted_count}개 파일/폴더 삭제 완료")
    
    print(f"    설정: pdfplumber={use_pdfplumber}, 병렬={use_parallel}, AI={use_ai}, DPI={dpi}, 최대페이지={max_pages or '전체'}")
    
    # 파이프라인 실행 (UnifiedPipeline 직접 사용)
    config_path = settings.API_DIR / "data" / subject / "config.json"
    
    pipeline = UnifiedPipeline(
        subject=subject,
        use_ocr=not use_pdfplumber,  # pdfplumber 사용 시 OCR=False
        use_ml_postprocess=False,  # ML 후처리는 아직 비활성화
        config_path=config_path,
        save_results=True,  # JSON 저장 활성화
        dpi=dpi,
        lang='kor+eng',
        use_parallel=use_parallel,  # 병렬 처리
        max_workers=None,  # CPU 코어 수 자동
        max_pages=max_pages,  # 페이지 제한
    )
    result = pipeline.process(pdf_path)
    
    print(f"\n[결과]")
    lectures = result.get('lectures', [])
    problems = result.get('problems', [])
    lecture_contents = result.get('lecture_contents', [])
    print(f"  생성된 강의: {len(lectures)}개")
    print(f"  생성된 문제: {len(problems)}개")
    print(f"  강의 콘텐츠: {len(lecture_contents)}개")
    
    # 성능 통계 출력 (metadata에서)
    metadata = result.get('metadata', {})
    if metadata:
        print(f"\n[성능 통계]")
        print(f"  총 강의 수: {metadata.get('total_lectures', 0)}개")
        print(f"  총 문제 수: {metadata.get('total_problems', 0)}개")
        print(f"  상태: {metadata.get('status', 'unknown')}")
    
    print(f"\n[생성된 파일]")
    print(f"  강의 목록: data/{subject}/lectures/lectures.json")
    print(f"  강의 콘텐츠: data/{subject}/lectures/lecture_*.json")
    print(f"  문제: data/{subject}/problems/problem_*.json")
    print(f"  페이지 이미지: data/{subject}/pages/page_*.png")
    print(f"  설정 파일: data/{subject}/config.json")
    print("=" * 60)

if __name__ == "__main__":
    main()
