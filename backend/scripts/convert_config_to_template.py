"""
기존 config.json 파일을 템플릿으로 변환하는 스크립트

사용법:
    python convert_config_to_template.py
    python convert_config_to_template.py --subject literature
    python convert_config_to_template.py --all
"""
import sys
import argparse
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.infrastructure.pdf.parsers.template import ParsingTemplate
from app.core.config import settings


def convert_config_to_template(
    subject: str,
    config_path: Path,
    template_name: str = None,
    version: str = ""
) -> ParsingTemplate:
    """config.json을 템플릿으로 변환
    
    Args:
        subject: 과목명 ('literature', 'math1', 'english')
        config_path: config.json 파일 경로
        template_name: 템플릿 이름 (None이면 자동 생성)
        version: 버전 (예: "2026")
        
    Returns:
        생성된 ParsingTemplate
    """
    if template_name is None:
        # 파일명에서 템플릿 이름 추출
        template_name = f"ebs_수능특강_{subject}"
        if version:
            template_name += f"_{version}"
    
    description = f"EBS 수능특강 {subject} 교재 파싱 템플릿"
    if version:
        description += f" ({version}년)"
    
    template = ParsingTemplate.from_config_json(
        name=template_name,
        subject=subject,
        config_path=config_path,
        version=version,
        description=description
    )
    
    return template


def main():
    parser = argparse.ArgumentParser(
        description="기존 config.json을 템플릿으로 변환"
    )
    parser.add_argument(
        "--subject",
        choices=["literature", "math1", "english"],
        help="변환할 과목 (지정하지 않으면 모든 과목)"
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="모든 과목의 config.json 변환"
    )
    parser.add_argument(
        "--version",
        default="2026",
        help="템플릿 버전 (기본값: 2026)"
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        help="템플릿 출력 디렉토리 (기본값: backend/data/templates)"
    )
    
    args = parser.parse_args()
    
    # 출력 디렉토리 설정
    if args.output_dir:
        output_dir = args.output_dir
    else:
        output_dir = settings.API_DIR / "data" / "templates"
    
    output_dir.mkdir(parents=True, exist_ok=True)
    print(f"템플릿 출력 디렉토리: {output_dir}")
    
    # 변환할 과목 목록
    subjects = []
    if args.all:
        subjects = ["literature", "math1", "english"]
    elif args.subject:
        subjects = [args.subject]
    else:
        # 기본값: 모든 과목
        subjects = ["literature", "math1", "english"]
    
    converted_count = 0
    failed_count = 0
    
    for subject in subjects:
        config_path = settings.API_DIR / "data" / subject / "config.json"
        
        if not config_path.exists():
            print(f"⚠️  Config 파일이 없습니다: {config_path}")
            failed_count += 1
            continue
        
        try:
            print(f"\n📄 변환 중: {subject}")
            print(f"   Config: {config_path}")
            
            template = convert_config_to_template(
                subject=subject,
                config_path=config_path,
                version=args.version
            )
            
            # 템플릿 저장
            saved_path = template.save(output_dir)
            print(f"   ✅ 템플릿 저장 완료: {saved_path}")
            print(f"   템플릿 이름: {template.name}")
            print(f"   신뢰도: {template.confidence}")
            
            converted_count += 1
            
        except Exception as e:
            print(f"   ❌ 변환 실패: {e}")
            import traceback
            traceback.print_exc()
            failed_count += 1
    
    print(f"\n{'='*50}")
    print(f"변환 완료: {converted_count}개 성공, {failed_count}개 실패")
    print(f"템플릿 저장 위치: {output_dir}")
    print(f"{'='*50}")


if __name__ == "__main__":
    main()
