"""
추출된 목차 정제 + 템플릿 생성 (한 번에)

사용법:
1. extract_full_toc.py로 toc_extracted_full.txt 생성
2. python clean_and_generate.py 실행
"""
import requests
import json

print("=" * 80)
print("목차 정제 + 템플릿 자동 생성")
print("=" * 80)

# ========================================
# 1단계: 추출된 목차 로드
# ========================================
print("\n[1] 추출된 목차 로드 중...")

try:
    with open('toc_extracted_full.txt', 'r', encoding='utf-8') as f:
        toc_raw = f.read()
    print(f"    로드 완료: {len(toc_raw)} 글자")
except FileNotFoundError:
    print("\n[ERROR] toc_extracted_full.txt 파일을 찾을 수 없습니다.")
    print("        먼저 extract_full_toc.py를 실행하세요.")
    exit(1)

# ========================================
# 2단계: 목차 정제
# ========================================
print("\n[2] 목차 정제 중...")

custom_prompt = """정제 규칙:
1. 특수 문자 제거 (cid:xxx, 유니코드 오류 등)
2. 분리된 단어들을 올바르게 병합

3. 강의 단위 인식:
   [1부 개념 학습]
   - "N강 | 제목" 또는 "N강 제목" 형식
   - 작품들이 나열되고 3자리 페이지 번호(009, 012)로 끝남
   
   [2부 적용 학습] 
   - ">>> 고전 시가", ">>> 현대시" 등 섹션 헤더
   - "01 작품명(작가) 페이지번호" 형식
   - 여러 작품이 한 줄에 있을 수 있음 (/ 로 구분)
   
   [3부 실전 학습]
   - "N회 [NN~NN] 작품명(작가) 페이지번호" 형식

4. 페이지 번호로 단위 구분:
   - 3자리 페이지 번호가 나오면 해당 블록 종료
   - 페이지 번호 앞의 모든 텍스트를 한 줄로 병합

5. 제외할 항목:
   - "페이지 N 끝", "오후 6:00" 등
   - "1부", "2부", "3부" 단독 라인 (섹션 구분은 유지)

6. 출력 형식:
   - 각 강의/작품 단위는 한 줄로
   - 빈 줄로 구분
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

with open('toc_cleaned_auto.txt', 'w', encoding='utf-8') as f:
    f.write(cleaned_text)
print("    저장: toc_cleaned_auto.txt")

# 미리보기
print("\n--- 정제된 목차 미리보기 (처음 30줄) ---")
lines = cleaned_text.split('\n')
for i, line in enumerate(lines[:30], 1):
    if line.strip():
        print(f"{i:3d}: {line}")

if len(lines) > 30:
    print(f"... (외 {len(lines) - 30}줄)")

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
    # 실패해도 계속 진행 (수동 수정 가능)
    lectures = []
else:
    result = response.json()
    lectures = result['lectures']
    print(f"    추출 완료: 총 {result['total_lectures']}개 강의")
    print(f"    페이지 정보: {result['lectures_with_pages']}개 강의")
    
    # 미리보기
    print("\n--- 강의 목록 미리보기 (처음 15개) ---")
    for lecture in lectures[:15]:
        lecture_id = lecture['lecture_id']
        title = lecture['title'][:40]
        start = lecture.get('start_page', '?')
        end = lecture.get('end_page', '?')
        print(f"  {lecture_id}강: {title:<40} (p.{start}~{end})")
    
    if len(lectures) > 15:
        print(f"  ... (외 {len(lectures) - 15}개)")
    
    with open('toc_lectures_auto.json', 'w', encoding='utf-8') as f:
        json.dump(lectures, f, ensure_ascii=False, indent=2)
    print("\n    저장: toc_lectures_auto.json")

# ========================================
# 4단계: 강의 예시 생성
# ========================================
print("\n[4] 강의 예시 생성...")

lecture_examples = []
for line in cleaned_text.split('\n'):
    line = line.strip()
    if line and any(f'{i}강' in line for i in range(1, 100)):
        lecture_examples.append(line)
        if len(lecture_examples) >= 10:
            break

print(f"    강의 라인 예시: {len(lecture_examples)}개")
for i, example in enumerate(lecture_examples[:5], 1):
    print(f"      {i}. {example[:60]}...")

# ========================================
# 최종 결과
# ========================================
print("\n" + "=" * 80)
print("완료!")
print("=" * 80)
print("\n생성된 파일:")
print("  1. toc_cleaned_auto.txt - 정제된 목차")
print("  2. toc_lectures_auto.json - 추출된 강의 목록")
print("\n다음 단계:")
print("  1. toc_cleaned_auto.txt 내용 확인")
print("     - 강의 제목과 페이지 번호가 잘 정제되었는지 확인")
print("     - 필요시 수동 수정")
print("\n  2. 템플릿 생성:")
print("     - toc_cleaned_auto.txt를 toc_full.txt로 복사")
print("     - python generate_template_from_toc.py 실행")
print("\n  또는 웹 UI 사용:")
print("     - 관리자 페이지 → Template Wizard")
print("     - PDF 업로드 + 목차 붙여넣기")
print("")
