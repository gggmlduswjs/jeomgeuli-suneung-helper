"""
템플릿 초기화 스크립트
기존 config.json 파일들을 템플릿으로 변환하여 저장
"""
import sys
from pathlib import Path
from datetime import datetime

# 프로젝트 루트를 경로에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.infrastructure.pdf.parsers.template import ParsingTemplate
from app.infrastructure.pdf.parsers.template_manager import TemplateManager
from app.core.config import settings


def init_templates_from_configs():
    """기존 config.json 파일들을 템플릿으로 변환"""
    
    print("=" * 60)
    print("템플릿 초기화: config.json → 템플릿 변환")
    print("=" * 60)
    
    # 데이터 디렉토리
    data_dir = settings.API_DIR / "data"
    
    # 과목별 config.json 찾기
    subjects = ['literature', 'math1', 'english']
    templates_created = []
    
    for subject in subjects:
        config_path = data_dir / subject / "config.json"
        
        if not config_path.exists():
            print(f"\n[⚠️] {subject}: config.json 파일이 없습니다. 건너뜁니다.")
            print(f"    경로: {config_path}")
            continue
        
        print(f"\n[{subject}] config.json 발견: {config_path}")
        
        try:
            # 템플릿 이름 생성 (예: "ebs_수능특강_문학_2026")
            template_name = f"ebs_수능특강_{subject}_2026"
            
            # 템플릿 생성
            template = ParsingTemplate.from_config_json(
                name=template_name,
                subject=subject,
                config_path=config_path,
                version="2026",
                description=f"EBS 수능특강 {subject} 교재 파싱 템플릿 (config.json에서 변환)"
            )
            
            # 템플릿 매니저로 저장
            template_manager = TemplateManager()
            saved_path = template_manager.add_template(template)
            
            templates_created.append({
                'subject': subject,
                'name': template_name,
                'path': saved_path
            })
            
            print(f"  ✅ 템플릿 생성 완료: {template_name}")
            print(f"     저장 경로: {saved_path}")
            print(f"     신뢰도: {template.confidence:.2f}")
            print(f"     강의 패턴: {len(template.patterns.get('lecture_title_patterns', []))}개")
            
        except Exception as e:
            print(f"  ❌ 템플릿 생성 실패: {e}")
            import traceback
            traceback.print_exc()
            continue
    
    # 결과 요약
    print("\n" + "=" * 60)
    print("템플릿 초기화 완료")
    print("=" * 60)
    print(f"생성된 템플릿: {len(templates_created)}개")
    
    for template_info in templates_created:
        print(f"  - {template_info['subject']}: {template_info['name']}")
    
    if templates_created:
        print(f"\n템플릿 저장 위치: {settings.API_DIR / 'data' / 'templates'}")
        print("\n다음 실행 시 하이브리드 라우터가 이 템플릿들을 자동으로 사용합니다.")
    else:
        print("\n⚠️ 생성된 템플릿이 없습니다. config.json 파일을 확인해주세요.")
    
    print("=" * 60)


if __name__ == "__main__":
    init_templates_from_configs()
