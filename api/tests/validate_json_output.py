"""
생성된 JSON 파일 품질 검증
"""
import sys
import json
from pathlib import Path

# 프로젝트 루트를 경로에 추가
sys.path.insert(0, str(Path(__file__).parent))

def validate_json_structure(json_data: dict) -> dict:
    """JSON 구조 검증"""
    issues = []
    warnings = []
    
    # 필수 필드 확인
    required_fields = ['subject', 'lessonId', 'title', 'order', 'sections']
    for field in required_fields:
        if field not in json_data:
            issues.append(f"필수 필드 누락: {field}")
    
    # subject 값 확인
    if 'subject' in json_data:
        valid_subjects = ['korean', 'math', 'english']
        if json_data['subject'] not in valid_subjects:
            warnings.append(f"subject 값이 표준이 아닙니다: {json_data['subject']}")
    
    # sections 확인
    if 'sections' in json_data:
        sections = json_data['sections']
        if not isinstance(sections, list):
            issues.append("sections는 리스트여야 합니다")
        else:
            if len(sections) == 0:
                warnings.append("sections가 비어있습니다")
            
            for i, section in enumerate(sections):
                # 섹션 필수 필드
                if 'sectionId' not in section:
                    issues.append(f"섹션 {i+1}: sectionId 누락")
                if 'title' not in section:
                    warnings.append(f"섹션 {i+1}: title 누락")
                if 'units' not in section:
                    issues.append(f"섹션 {i+1}: units 누락")
                else:
                    units = section['units']
                    if not isinstance(units, list):
                        issues.append(f"섹션 {i+1}: units는 리스트여야 합니다")
                    elif len(units) == 0:
                        warnings.append(f"섹션 {i+1}: units가 비어있습니다")
                    else:
                        # Unit 검증
                        for j, unit in enumerate(units):
                            if 'unitId' not in unit:
                                issues.append(f"섹션 {i+1}, Unit {j+1}: unitId 누락")
                            if 'type' not in unit:
                                issues.append(f"섹션 {i+1}, Unit {j+1}: type 누락")
                            else:
                                valid_types = ['intro', 'concept', 'definition', 'example', 
                                             'notation', 'problem_intro', 'summary', 'outro']
                                if unit['type'] not in valid_types:
                                    warnings.append(f"섹션 {i+1}, Unit {j+1}: type이 표준이 아닙니다: {unit['type']}")
                            if 'content' not in unit:
                                issues.append(f"섹션 {i+1}, Unit {j+1}: content 누락")
                            elif not unit['content'] or len(unit['content'].strip()) == 0:
                                warnings.append(f"섹션 {i+1}, Unit {j+1}: content가 비어있습니다")
                            elif len(unit['content']) < 10:
                                warnings.append(f"섹션 {i+1}, Unit {j+1}: content가 너무 짧습니다 ({len(unit['content'])}자)")
                            elif len(unit['content']) > 2000:
                                warnings.append(f"섹션 {i+1}, Unit {j+1}: content가 너무 깁니다 ({len(unit['content'])}자)")
    
    return {
        'issues': issues,
        'warnings': warnings,
        'is_valid': len(issues) == 0
    }

def analyze_content_quality(json_data: dict) -> dict:
    """내용 품질 분석"""
    stats = {
        'total_sections': len(json_data.get('sections', [])),
        'total_units': 0,
        'unit_types': {},
        'avg_unit_length': 0,
        'min_unit_length': float('inf'),
        'max_unit_length': 0,
        'empty_units': 0,
        'very_short_units': 0,  # 50자 미만
        'very_long_units': 0,   # 1000자 초과
    }
    
    total_length = 0
    for section in json_data.get('sections', []):
        for unit in section.get('units', []):
            stats['total_units'] += 1
            unit_type = unit.get('type', 'unknown')
            stats['unit_types'][unit_type] = stats['unit_types'].get(unit_type, 0) + 1
            
            content = unit.get('content', '')
            content_len = len(content.strip())
            total_length += content_len
            
            if content_len == 0:
                stats['empty_units'] += 1
            elif content_len < 50:
                stats['very_short_units'] += 1
            elif content_len > 1000:
                stats['very_long_units'] += 1
            
            stats['min_unit_length'] = min(stats['min_unit_length'], content_len)
            stats['max_unit_length'] = max(stats['max_unit_length'], content_len)
    
    if stats['total_units'] > 0:
        stats['avg_unit_length'] = total_length / stats['total_units']
    
    if stats['min_unit_length'] == float('inf'):
        stats['min_unit_length'] = 0
    
    return stats

# JSON 파일 찾기
json_dir = Path(__file__).parent.parent.parent / "data" / "parsed" / "literature"
json_files = list(json_dir.glob("*.json")) if json_dir.exists() else []

if not json_files:
    print("[오류] JSON 파일을 찾을 수 없습니다.")
    print(f"[오류] 디렉토리: {json_dir}")
    sys.exit(1)

print("=" * 70)
print("JSON 파일 품질 검증")
print("=" * 70)

for json_file in json_files:
    print(f"\n[파일] {json_file.name}")
    print("-" * 70)
    
    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            json_data = json.load(f)
        
        # 구조 검증
        validation = validate_json_structure(json_data)
        
        if validation['is_valid']:
            print("[OK] 구조 검증: 통과")
        else:
            print("[FAIL] 구조 검증: 실패")
            for issue in validation['issues']:
                print(f"  - {issue}")
        
        if validation['warnings']:
            print("[!] 경고:")
            for warning in validation['warnings']:
                print(f"  - {warning}")
        
        # 내용 품질 분석
        stats = analyze_content_quality(json_data)
        
        print(f"\n[통계]")
        print(f"  레슨: {json_data.get('title', 'N/A')}")
        print(f"  레슨 ID: {json_data.get('lessonId', 'N/A')}")
        print(f"  섹션 수: {stats['total_sections']}")
        print(f"  학습 단위 수: {stats['total_units']}")
        print(f"  평균 단위 길이: {stats['avg_unit_length']:.1f}자")
        print(f"  최소 단위 길이: {stats['min_unit_length']}자")
        print(f"  최대 단위 길이: {stats['max_unit_length']}자")
        print(f"  빈 단위: {stats['empty_units']}개")
        print(f"  매우 짧은 단위 (<50자): {stats['very_short_units']}개")
        print(f"  매우 긴 단위 (>1000자): {stats['very_long_units']}개")
        
        print(f"\n[단위 타입 분포]")
        for unit_type, count in sorted(stats['unit_types'].items()):
            print(f"  - {unit_type}: {count}개")
        
        # 샘플 출력
        if json_data.get('sections'):
            first_section = json_data['sections'][0]
            print(f"\n[샘플] 첫 번째 섹션: {first_section.get('title', 'N/A')}")
            if first_section.get('units'):
                first_unit = first_section['units'][0]
                print(f"  Unit ID: {first_unit.get('unitId', 'N/A')}")
                print(f"  Type: {first_unit.get('type', 'N/A')}")
                content_preview = first_unit.get('content', '')[:150]
                print(f"  Content: {content_preview}...")
        
    except Exception as e:
        print(f"[오류] {e}")
        import traceback
        traceback.print_exc()

print("\n" + "=" * 70)
print("검증 완료")
print("=" * 70)
