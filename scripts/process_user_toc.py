"""
사용자가 제공한 전체 목차 텍스트 처리

사용법:
1. 원본 텍스트를 data/toc_raw_input.txt에 저장
2. 프로젝트 루트에서: python scripts/process_user_toc.py
"""
import os
import requests
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
os.chdir(ROOT)

print("=" * 80)
print("사용자 제공 목차 처리 (전체)")
print("=" * 80)

# ========================================
# 1단계: 원본 텍스트 로드
# ========================================
print("\n[1] 원본 목차 로드 중...")

try:
    with open(ROOT / 'data' / 'toc_raw_input.txt', 'r', encoding='utf-8') as f:
        toc_raw = f.read()
    print(f"    로드 완료: {len(toc_raw)} 글자, {len(toc_raw.splitlines())} 줄")
except FileNotFoundError:
    print("\n[ERROR] data/toc_raw_input.txt 파일을 찾을 수 없습니다.")
    exit(1)

# ========================================
# 2단계: 목차 정제
# ========================================
print("\n[2] 목차 정제 중 (OpenAI API)...")

custom_prompt = """정제 규칙:
1. 특수 문자 제거 (cid:xxx, 유니코드 오류 등)
2. 분리된 단어들을 올바르게 병합

3. 강의 단위 인식:
   [1부 개념 학습 - N강 형식]
   - "N강 | 제목" 또는 "N강 제목" 형식
   - 작품들이 나열되고 3자리 페이지 번호(009, 012, 015 등)로 끝남
   - 페이지 번호 바로 앞의 모든 텍스트를 한 줄로 병합
   
   [2부 적용 학습 - NN 번호 형식]
   - ">>> 고전 시가", ">>> 현대시", ">>> 현대 소설", ">>> 고전 산문", ">>> 극·수필" 등 섹션 헤더
   - "01 작품명(작가) 페이지번호" 형식
   - 여러 작품이 한 번호에 있을 수 있음 (/ 로 구분)
   
   [3부 실전 학습]
   - "N회 [NN~NN] 작품명(작가) 페이지번호" 형식

4. 페이지 번호로 블록 구분:
   - 3자리 페이지 번호(009, 012, 077 등)가 나오면 해당 블록/강의 종료
   - 페이지 번호 앞의 모든 텍스트를 한 줄로 병합

5. 제외할 항목:
   - "페이지 N 끝", "오후 6:00", "25. 1. 6." 등 메타 정보
   - "2026학년도수능특강..." 파일명
   - "(cid:xxx)" 형태의 모든 특수 문자

6. 출력 형식:
   - 각 강의/작품 블록은 한 줄로
   - 섹션 구분자는 유지
   - 빈 줄로 구분

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
    },
    timeout=60
)

if response.status_code != 200:
    print(f"[ERROR] 정제 실패: {response.status_code}")
    print(response.text)
    exit(1)

result = response.json()
cleaned_text = result['cleaned_text']
print(f"    정제 완료: {result['changes_made']}")

with open('toc_final_cleaned.txt', 'w', encoding='utf-8') as f:
    f.write(cleaned_text)
print("    저장: toc_final_cleaned.txt")

# 미리보기 (강의 라인만)
print("\n--- 정제된 목차 미리보기 (강의 라인) ---")
lines = cleaned_text.split('\n')
lecture_lines = []
for line in lines:
    if '강' in line and any(f'{i}강' in line for i in range(1, 100)):
        lecture_lines.append(line.strip())
        print(f"  {line.strip()[:80]}")
        if len(lecture_lines) >= 20:
            break

print(f"\n  총 {len([l for l in lines if '강' in l])}개 강의 관련 라인")

# ========================================
# 3단계: 강의 목록 추출
# ========================================
print("\n[3] 강의 목록 추출 중...")

response = requests.post(
    'http://localhost:8000/api/v1/templates/parse-toc-lectures',
    json=cleaned_text,
    headers={'Content-Type': 'application/json'},
    timeout=30
)

if response.status_code != 200:
    print(f"[ERROR] 추출 실패: {response.status_code}")
    lectures = []
else:
    result = response.json()
    lectures = result['lectures']
    print(f"    추출 완료: 총 {result['total_lectures']}개 강의")
    print(f"    페이지 정보: {result['lectures_with_pages']}개 강의\n")
    
    print("--- 강의 목록 (전체) ---")
    for lecture in lectures:
        lecture_id = lecture['lecture_id']
        title = lecture['title'][:50]
        start = lecture.get('start_page', '?')
        end = lecture.get('end_page', '?')
        print(f"  {lecture_id:2d}강: {title:<50} (p.{start}~{end})")
    
    with open('toc_final_lectures.json', 'w', encoding='utf-8') as f:
        json.dump(lectures, f, ensure_ascii=False, indent=2)
    print("\n    저장: toc_final_lectures.json")

# ========================================
# 4단계: 템플릿 생성 준비
# ========================================
print("\n[4] 템플릿 생성 준비...")

# 강의 라인 예시
lecture_examples = []
for line in cleaned_text.split('\n'):
    line = line.strip()
    if line and any(f'{i}강' in line for i in range(1, 100)):
        lecture_examples.append(line)
        if len(lecture_examples) >= 10:
            break

print(f"    강의 예시: {len(lecture_examples)}개")
for i, ex in enumerate(lecture_examples[:5], 1):
    print(f"      {i}. {ex[:70]}...")

# ========================================
# 5단계: 템플릿 생성 (자동)
# ========================================
print("\n[5] 템플릿 생성 중 (OpenAI API)...")

if lectures:
    template_request = {
        'subject': 'literature',
        'name': 'ebs_수능특강_literature_2026',
        'version': '2026',
        'description': 'EBS 수능특강 문학 2026 (전체 목차 기반)',
        'year': 2026,
        'book_name': 'EBS 수능특강 문학',
        'toc_text': cleaned_text,
        'curriculum_survey': {
            'is_lecture_based': True,
            'lecture_units': ['concept', 'passage', 'problem'],
            'unit_order': ['concept', 'passage', 'problem']
        },
        'toc_lecture_line_examples': lecture_examples,
        'toc_nonlecture_line_examples': [
            '01', '02', '03',
            '>>> 고전 시가', '>>> 현대시',
            '--- 페이지 4 끝 ---'
        ],
        'expected_lecture_count': len(lectures),
        'toc_lecture_list': lectures,
        'save': False,  # preview만 (True로 변경하면 즉시 저장)
        'model_name': 'gpt-4o-mini',
        'confidence': 0.85
    }
    
    response = requests.post(
        'http://localhost:8000/api/v1/templates/generate-from-toc',
        json=template_request,
        timeout=120
    )
    
    if response.status_code == 200:
        result = response.json()
        template = result['template']
        stats = template.get('stats', {})
        
        print(f"    생성 완료!")
        print(f"    총 강의: {stats.get('total_lectures', 0)}개")
        print(f"    페이지 정보: {stats.get('lectures_with_pages', 0)}개")
        print(f"    패턴 수: {stats.get('total_patterns', 0)}개")
        
        with open('template_final.json', 'w', encoding='utf-8') as f:
            json.dump(template, f, ensure_ascii=False, indent=2)
        print("\n    저장: template_final.json")
        
        warnings = result.get('warnings', [])
        if warnings:
            print("\n    [경고]")
            for w in warnings[:5]:
                print(f"      - {w}")
    else:
        print(f"    [ERROR] 템플릿 생성 실패: {response.status_code}")
else:
    print("    [SKIP] 강의 목록이 없어서 템플릿 생성 건너뜀")

# ========================================
# 최종 결과
# ========================================
print("\n" + "=" * 80)
print("완료!")
print("=" * 80)
print("\n생성된 파일:")
print("  1. toc_final_cleaned.txt - 정제된 전체 목차")
print("  2. toc_final_lectures.json - 강의 목록")
if lectures:
    print("  3. template_final.json - 생성된 템플릿")
print("\n통계:")
print(f"  - 추출된 강의 수: {len(lectures)}개")
print(f"  - 페이지 정보 있는 강의: {len([l for l in lectures if l.get('start_page')])}개")
print("\n다음 단계:")
print("  1. toc_final_cleaned.txt 확인 (누락된 강의 있는지)")
print("  2. 필요시 수동 수정")
print("  3. template_final.json 확인 및 저장")
print("     - save=True로 변경 후 재실행")
print("     - 또는 웹 UI에서 업로드")
print("")
