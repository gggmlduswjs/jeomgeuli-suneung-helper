"""
실제 파싱 파이프라인 테스트 스크립트
PDF 파일 없이도 파이프라인 초기화 및 기본 로직 테스트
"""
import sys
from pathlib import Path

# 프로젝트 루트를 경로에 추가
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app.infrastructure.pdf.pipeline import UnifiedPipeline
from app.core.config import settings


def test_pipeline_initialization():
    """파이프라인 초기화 테스트"""
    print("=" * 60)
    print("파이프라인 초기화 테스트")
    print("=" * 60)
    
    subjects = ['literature', 'math1', 'english']
    
    for subject in subjects:
        try:
            print(f"\n[{subject}] 파이프라인 초기화 중...")
            
            # config.json 경로 확인
            config_path = settings.API_DIR / "data" / subject / "config.json"
            print(f"  Config 경로: {config_path}")
            print(f"  Config 존재: {config_path.exists()}")
            
            # 파이프라인 초기화 (PDF 없이)
            pipeline = UnifiedPipeline(
                subject=subject,
                use_ocr=False,  # pdfplumber 사용
                config_path=config_path if config_path.exists() else None,
                save_results=False,  # 테스트용이므로 저장 안 함
            )
            
            print(f"  [OK] {subject} 파이프라인 초기화 성공")
            print(f"     추출기: {type(pipeline.extractor).__name__}")
            print(f"     파서: {pipeline.parser if pipeline.parser else '동적 선택 (HybridRouter)'}")
            print(f"     강의 추출기: {type(pipeline.lecture_extractor).__name__}")
            
        except Exception as e:
            print(f"  [ERROR] {subject} 파이프라인 초기화 실패: {e}")
            import traceback
            traceback.print_exc()


def test_with_pdf():
    """PDF 파일이 있는 경우 실제 파싱 테스트"""
    print("\n" + "=" * 60)
    print("실제 PDF 파싱 테스트")
    print("=" * 60)
    
    subjects = ['literature', 'math1', 'english']
    found_pdf = False
    
    for subject in subjects:
        pdf_dir = project_root / "data" / subject / "pdf"
        if pdf_dir.exists():
            pdf_files = list(pdf_dir.glob("*.pdf"))
            if pdf_files:
                found_pdf = True
                pdf_path = pdf_files[0]
                print(f"\n[{subject}] PDF 파일 발견: {pdf_path}")
                print(f"  파일 크기: {pdf_path.stat().st_size / 1024 / 1024:.2f} MB")
                
                try:
                    # config.json 경로
                    config_path = settings.API_DIR / "data" / subject / "config.json"
                    
                    # 파이프라인 초기화
                    print(f"  파이프라인 초기화 중...")
                    pipeline = UnifiedPipeline(
                        subject=subject,
                        use_ocr=False,  # pdfplumber 사용 (빠름)
                        config_path=config_path if config_path.exists() else None,
                        save_results=True,
                        max_pages=5,  # 테스트용으로 5페이지만
                    )
                    
                    print(f"  파싱 시작 (최대 5페이지)...")
                    result = pipeline.process(pdf_path)
                    
                    # 결과 출력
                    lectures = result.get('lectures', [])
                    problems = result.get('problems', [])
                    lecture_contents = result.get('lecture_contents', [])
                    
                    print(f"  [OK] 파싱 완료!")
                    print(f"     강의: {len(lectures)}개")
                    print(f"     문제: {len(problems)}개")
                    print(f"     강의 콘텐츠: {len(lecture_contents)}개")
                    
                    # 메타데이터 출력
                    metadata = result.get('metadata', {})
                    if metadata:
                        print(f"     전략: {metadata.get('parsing_strategy', 'N/A')}")
                        if metadata.get('template_name'):
                            print(f"     템플릿: {metadata.get('template_name')} (신뢰도: {metadata.get('confidence', 0):.2f})")
                    
                    return True  # 성공하면 종료
                    
                except Exception as e:
                    print(f"  [ERROR] 파싱 실패: {e}")
                    import traceback
                    traceback.print_exc()
    
    if not found_pdf:
        print("\n[WARNING] PDF 파일을 찾을 수 없습니다.")
        print("   다음 경로에 PDF 파일을 넣어주세요:")
        for subject in subjects:
            pdf_dir = project_root / "data" / subject / "pdf"
            print(f"   - {pdf_dir}")
    
    return found_pdf


if __name__ == "__main__":
    try:
        # 1. 파이프라인 초기화 테스트
        test_pipeline_initialization()
        
        # 2. PDF 파일이 있으면 실제 파싱 테스트
        test_with_pdf()
        
        print("\n" + "=" * 60)
        print("[OK] 테스트 완료!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n[ERROR] 테스트 실패: {e}")
        import traceback
        traceback.print_exc()
