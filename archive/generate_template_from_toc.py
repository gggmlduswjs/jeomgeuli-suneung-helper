"""
완전한 템플릿 생성 스크립트

사용법:
1. toc_full.txt에 전체 목차 텍스트 붙여넣기
2. python generate_template_from_toc.py 실행
3. 생성된 template을 확인하고 필요시 수정
"""
import requests
import json

print("=" * 80)
print("EBS 수능특강 문학 템플릿 생성기")
print("=" * 80)

# ========================================
# 1단계: 전체 목차 텍스트 로드
# ========================================
print("\n[1] 목차 텍스트 로드 중...")

try:
    with open('toc_full.txt', 'r', encoding='utf-8') as f:
        toc_raw = f.read()
    print(f"    로드 완료: {len(toc_raw)} 글자")
except FileNotFoundError:
    print("\n[ERROR] toc_full.txt 파일을 찾을 수 없습니다.")
    print("        전체 목차 텍스트를 toc_full.txt 파일에 붙여넣고 다시 실행하세요.")
    exit(1)

# ========================================
# 2단계: OCR 텍스트 정제
# ========================================
print("\n[2] OCR 텍스트 정제 중...")

# 커스텀 정제 규칙 (009 단위 강의 감지)
custom_prompt = """정제 규칙:
1. 특수 문자 제거 (cid:xxx, 유니코드 오류 등)
2. 분리된 단어들을 올바르게 병합

3. 강의 단위 인식:
   - "N강 제목" 형식 인식
   - 3자리 페이지 번호(009, 012, 015 등)로 끝나는 블록을 하나의 강의로 간주
   - 페이지 번호 바로 위의 모든 텍스트를 합쳐서 한 줄로 출력
   
4. 제외할 항목:
   - 두 자리 작품 번호 (01, 02 등) 단독 라인
   - 섹션 구분자 (>>>, 고전 시가, 현대시 등)
   - 페이지 표시 ("페이지 N 끝" 등)

5. 출력 형식:
   - 각 강의는 한 줄로 표현
   - 빈 줄로 강의 구분

예시:
입력:
7강
캐는
노래
(작자
미상)
032

출력:
7강 캐는 노래 (작자 미상) 032
"""

response = requests.post(
    'http://localhost:8000/api/v1/templates/clean-toc-text',
    json={
        'toc_text': toc_raw,
        'custom_prompt': custom_prompt
    }
)

if response.status_code != 200:
    print(f"[ERROR] 정제 실패: {response.status_code}")
    print(response.text)
    exit(1)

result = response.json()
cleaned_text = result['cleaned_text']
print(f"    정제 완료: {result['changes_made']}")

# 정제된 텍스트 저장
with open('toc_cleaned_full.txt', 'w', encoding='utf-8') as f:
    f.write(cleaned_text)
print("    저장: toc_cleaned_full.txt")

# ========================================
# 3단계: 강의 목록 추출
# ========================================
print("\n[3] 강의 목록 추출 중...")

response = requests.post(
    'http://localhost:8000/api/v1/templates/parse-toc-lectures',
    json=cleaned_text,
    headers={'Content-Type': 'application/json'}
)

if response.status_code != 200:
    print(f"[ERROR] 추출 실패: {response.status_code}")
    print(response.text)
    exit(1)

result = response.json()
lectures = result['lectures']
print(f"    추출 완료: 총 {result['total_lectures']}개 강의")
print(f"    페이지 정보: {result['lectures_with_pages']}개 강의")

# 강의 목록 미리보기
print("\n    --- 강의 목록 미리보기 (처음 10개) ---")
for lecture in lectures[:10]:
    lecture_id = lecture['lecture_id']
    title = lecture['title'][:40]  # 제목 40자로 제한
    start = lecture.get('start_page', '?')
    end = lecture.get('end_page', '?')
    print(f"      {lecture_id}강: {title:<40} (p.{start}~{end})")

# 강의 목록 저장
with open('toc_lectures_full.json', 'w', encoding='utf-8') as f:
    json.dump(lectures, f, ensure_ascii=False, indent=2)
print("\n    저장: toc_lectures_full.json")

# ========================================
# 4단계: 강의 예시 생성
# ========================================
print("\n[4] 강의 예시 생성...")

# 강의 라인 예시 (처음 5개)
lecture_examples = []
for line in cleaned_text.split('\n'):
    line = line.strip()
    if line and any(f'{i}강' in line for i in range(1, 100)):
        lecture_examples.append(line)
        if len(lecture_examples) >= 5:
            break

# 비강의 라인 예시
nonlecture_examples = [
    '01',
    '02',
    '고전 시가 >>>',
    '현대시 >>>',
    '--- 페이지 4 끝 ---'
]

print("    강의 라인 예시:")
for i, example in enumerate(lecture_examples, 1):
    print(f"      {i}. {example}")

print("\n    비강의 라인 예시:")
for i, example in enumerate(nonlecture_examples, 1):
    print(f"      {i}. {example}")

# ========================================
# 5단계: 템플릿 생성 요청
# ========================================
print("\n[5] 템플릿 생성 중 (OpenAI API 호출)...")

template_request = {
    'subject': 'literature',
    'name': 'ebs_수능특강_literature_2026',
    'version': '2026',
    'description': 'EBS 수능특강 문학 2026 (자동 생성)',
    'year': 2026,
    'book_name': 'EBS 수능특강 문학',
    'toc_text': cleaned_text,
    'curriculum_survey': {
        'is_lecture_based': True,
        'lecture_units': ['concept', 'passage', 'problem'],
        'unit_order': ['concept', 'passage', 'problem']
    },
    'toc_lecture_line_examples': lecture_examples,
    'toc_nonlecture_line_examples': nonlecture_examples,
    'expected_lecture_count': len(lectures),
    'toc_lecture_list': lectures,  # 이미 추출한 강의 목록 사용
    'save': False,  # 미리보기만 (save=True로 변경하면 즉시 저장)
    'model_name': 'gpt-4o-mini',
    'confidence': 0.85
}

response = requests.post(
    'http://localhost:8000/api/v1/templates/generate-from-toc',
    json=template_request
)

if response.status_code != 200:
    print(f"[ERROR] 템플릿 생성 실패: {response.status_code}")
    print(response.text)
    exit(1)

result = response.json()
template = result['template']
validation = result.get('validation', {})
warnings = result.get('warnings', [])

print(f"    생성 완료!")
print(f"    템플릿 이름: {template['name']}")
print(f"    과목: {template['subject']}")
print(f"    버전: {template.get('version', '없음')}")

# 템플릿 통계
stats = template.get('stats', {})
if stats:
    print(f"\n    --- 템플릿 통계 ---")
    print(f"      총 강의 수: {stats.get('total_lectures', 0)}")
    print(f"      페이지 정보 있는 강의: {stats.get('lectures_with_pages', 0)}")
    print(f"      패턴 수: {stats.get('total_patterns', 0)}")
    print(f"      region_hints: {'있음' if stats.get('has_region_hints') else '없음'}")

# 경고 메시지
if warnings:
    print(f"\n    --- 경고 ---")
    for warning in warnings:
        print(f"      - {warning}")

# 검증 결과
if validation:
    print(f"\n    --- 검증 결과 ---")
    lec_match_rate = validation.get('lecture_examples_match_rate', 0)
    print(f"      강의 예시 매칭률: {lec_match_rate:.1f}%")
    
    direct_count = validation.get('direct_lecture_ids_count', 0)
    expected = validation.get('expected_lecture_count', 0)
    if expected:
        print(f"      강의 수: {direct_count}/{expected}")

# 템플릿 저장
with open('template_generated.json', 'w', encoding='utf-8') as f:
    json.dump(template, f, ensure_ascii=False, indent=2)
print("\n    저장: template_generated.json")

# ========================================
# 6단계: 다음 단계 안내
# ========================================
print("\n" + "=" * 80)
print("완료!")
print("=" * 80)
print("\n생성된 파일:")
print("  1. toc_cleaned_full.txt - 정제된 목차 텍스트")
print("  2. toc_lectures_full.json - 추출된 강의 목록")
print("  3. template_generated.json - 생성된 템플릿")
print("\n다음 단계:")
print("  1. template_generated.json 내용 확인")
print("  2. 필요시 수정 (패턴, config 등)")
print("  3. 템플릿 저장:")
print("     - 웹 UI: 관리자 페이지 → Template Wizard → 업로드")
print("     - API: POST /api/v1/templates (template_generated.json 내용 전송)")
print("  4. 또는 이 스크립트에서 save=True로 변경하고 재실행")
print("")
