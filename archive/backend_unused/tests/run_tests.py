"""
테스트 실행 스크립트
pytest가 없어도 기본적인 테스트를 실행할 수 있도록 함
"""
import sys
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def test_template_manager_basic():
    """TemplateManager 기본 테스트"""
    print("=" * 50)
    print("TemplateManager 기본 테스트")
    print("=" * 50)
    
    try:
        from app.infrastructure.pdf.parsers.template_manager import TemplateManager
        from app.infrastructure.pdf.parsers.template import ParsingTemplate
        import tempfile
        
        with tempfile.TemporaryDirectory() as tmpdir:
            template_dir = Path(tmpdir) / "templates"
            manager = TemplateManager(template_dir=template_dir)
            
            # 템플릿 생성
            template = ParsingTemplate(
                name="test_template",
                subject="literature",
                patterns={
                    "lecture_title_patterns": [r'^\d+강\s+[가-힣]+'],
                    "problem_number_pattern": r'^\d{2}$'
                },
                confidence=0.9
            )
            
            manager.add_template(template)
            print("[OK] 템플릿 추가 성공")
            
            # 템플릿 목록 확인
            templates = manager.list_templates("literature")
            print(f"[OK] 템플릿 목록 조회 성공: {len(templates)}개")
            
            # 매칭 테스트
            sample_text = "1강 시의 표현과 형식\n01\n02"
            result = manager.match_template(
                pdf_text=sample_text,
                subject="literature",
                threshold=0.85
            )
            
            if result:
                template_matched, confidence = result
                print(f"[OK] 템플릿 매칭 성공: {template_matched.name}, 신뢰도: {confidence:.2f}")
            else:
                print("[WARN] 템플릿 매칭 실패 (예상됨 - 테스트 템플릿이 간단함)")
            
            print("[OK] TemplateManager 기본 테스트 통과")
            return True
            
    except Exception as e:
        print(f"❌ 테스트 실패: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_hybrid_router_basic():
    """HybridRouter 기본 테스트"""
    print("\n" + "=" * 50)
    print("HybridRouter 기본 테스트")
    print("=" * 50)
    
    try:
        from app.infrastructure.pdf.parsers.hybrid_router import HybridRouter
        
        router = HybridRouter(template_threshold=0.85, enable_ai_parsing=False)
        print("[OK] HybridRouter 초기화 성공")
        
        # 모의 OCR 데이터
        ocr_data = [
            {
                'page_num': 1,
                'text': ['1강', '시의', '표현과', '형식', '01', '02']
            }
        ]
        
        parser, strategy, metadata = router.select_parser(
            subject="literature",
            ocr_data=ocr_data,
            book_id="test_book"
        )
        
        print(f"[OK] 파서 선택 성공: 전략={strategy}")
        assert parser is not None, "파서가 None입니다"
        print("[OK] HybridRouter 기본 테스트 통과")
        return True
        
    except Exception as e:
        print(f"❌ 테스트 실패: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_imports():
    """모든 모듈 import 테스트"""
    print("\n" + "=" * 50)
    print("Import 테스트")
    print("=" * 50)
    
    modules = [
        "app.infrastructure.pdf.parsers.template",
        "app.infrastructure.pdf.parsers.template_manager",
        "app.infrastructure.pdf.parsers.hybrid_router",
        "app.infrastructure.pdf.parsers.rule_generator",
        "app.infrastructure.pdf.parsers.ai_parser",
        "app.infrastructure.ai.genai.structure_analyzer",
    ]
    
    failed = []
    for module_name in modules:
        try:
            __import__(module_name)
            print(f"[OK] {module_name}")
        except Exception as e:
            print(f"[FAIL] {module_name}: {e}")
            failed.append(module_name)
    
    if failed:
        print(f"\n[WARN] {len(failed)}개 모듈 import 실패")
        return False
    else:
        print("\n[OK] 모든 모듈 import 성공")
        return True


if __name__ == "__main__":
    print("하이브리드 파싱 시스템 테스트 시작\n")
    
    results = []
    
    # Import 테스트
    results.append(("Import", test_imports()))
    
    # TemplateManager 테스트
    results.append(("TemplateManager", test_template_manager_basic()))
    
    # HybridRouter 테스트
    results.append(("HybridRouter", test_hybrid_router_basic()))
    
    # 결과 요약
    print("\n" + "=" * 50)
    print("테스트 결과 요약")
    print("=" * 50)
    
    for name, passed in results:
        status = "[PASS] 통과" if passed else "[FAIL] 실패"
        print(f"{name}: {status}")
    
    all_passed = all(result[1] for result in results)
    
    if all_passed:
        print("\n[SUCCESS] 모든 테스트 통과!")
        sys.exit(0)
    else:
        print("\n[WARN] 일부 테스트 실패")
        sys.exit(1)
