"""
교재 PDF 파이프라인 실행 스크립트
"""
import sys
from pathlib import Path

# 프로젝트 루트를 경로에 추가
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "api"))

from app.services.textbook_pipeline import TextbookPipeline

def main():
    """교재 PDF 파이프라인 실행"""
    
    print("=" * 60)
    print("교재 PDF 기반 AI 학습 콘텐츠 자동 생성 시스템")
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
        # 두 가지 경로 모두 확인 (api/data와 data)
        base_dirs = [
            project_root / "api" / "data" / subject,
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
    
    # 파이프라인 실행 (최적화 옵션 적용)
    pipeline = TextbookPipeline(
        subject=subject,
        dpi=dpi,  # 최적화: 300 → 200
        use_parallel=use_parallel,  # 병렬 처리
        use_ai_postprocess=use_ai,  # AI 후처리
        use_cache=True,  # 캐싱 활성화
        max_pages=max_pages,  # 페이지 제한
        use_pdfplumber=use_pdfplumber  # pdfplumber 사용 (텍스트 레이어 추출)
    )
    result = pipeline.process_pdf(pdf_path)
    
    print(f"\n[결과]")
    print(f"  처리된 페이지: {result['pages_processed']}개")
    print(f"  생성된 강의: {len(result['lectures'])}개")
    print(f"  생성된 문제: {len(result['problems'])}개")
    
    # 성능 통계 출력
    if 'stats' in result:
        stats = result['stats']
        print(f"\n[성능 통계]")
        print(f"  총 처리 시간: {stats.get('total_time', 0):.1f}초")
        print(f"  OCR 시간: {stats.get('ocr_time', 0):.1f}초")
        if stats.get('ai_postprocess_time', 0) > 0:
            print(f"  AI 후처리 시간: {stats.get('ai_postprocess_time', 0):.1f}초")
        print(f"  캐시 히트: {stats.get('cache_hits', 0)}개")
        print(f"  캐시 미스: {stats.get('cache_misses', 0)}개")
    
    print(f"\n[생성된 파일]")
    print(f"  강의 목록: data/{subject}/lectures/lectures.json")
    print(f"  강의 콘텐츠: data/{subject}/lectures/lecture_*.json")
    print(f"  문제: data/{subject}/problems/problem_*.json")
    print(f"  페이지 이미지: data/{subject}/pages/page_*.png")
    print(f"  설정 파일: data/{subject}/config.json")
    print("=" * 60)

if __name__ == "__main__":
    main()
