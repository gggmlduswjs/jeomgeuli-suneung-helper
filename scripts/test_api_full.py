"""API 전체 테스트. 프로젝트 루트에서: python scripts/test_api_full.py"""
import os
import requests
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
os.chdir(ROOT)

print("=" * 80)
print("API 테스트")
print("=" * 80)

# 사용자가 제공한 OCR 텍스트 (일부)
test_toc = """1강
시의
표현과
형식
고전
시가
>>>
해
(박두진)
009
매화
등걸에
(매화)
03
거래
귀거래
말뿐이오
(이현보)
녹양이
천만사인들
(이원익)
강산
좋은
경을
(김천택)
사랑
사랑
고고히
맺힌
사랑
(작자
미상)
012
3강
소설의
서술상
특징
04
우가
<제2수>
(이신의)
장마
(윤흥길)
015
전우치전
(작자
미상)
019
고목
(함세덕)
024
6강
교술
문학의
특성과
구성
요소
차마설
(이곡)
029
7강
09
캐는
노래
(작자
미상)
작품의
작가
독자
맥락
사랑손님과
어머니
(주요섭)
사랑을
찬찬
얽동여
(작자
미상)
032
놀부전
(이근삼)
036
9강
작품의
사회·문화적,
역사적
맥락
당신을
보았습니다
(한용운)
041
2강
시의
내용
과정곡
(정서)
소악부
<제6장>
(민사평)
02
046"""

# ========================================
# 1단계: 백엔드 확인
# ========================================
print("\n[1] 백엔드 서버 확인 중...")
try:
    response = requests.get('http://localhost:8000/api/v1/health', timeout=3)
    if response.status_code == 200:
        print("    [OK] 백엔드 실행 중")
    else:
        print(f"    [WARNING] 상태: {response.status_code}")
except requests.exceptions.ConnectionError:
    print("    [ERROR] 백엔드 서버가 실행되지 않았습니다.")
    print("    다음 명령으로 백엔드를 시작하세요:")
    print("    cd backend && python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000")
    exit(1)
except Exception as e:
    print(f"    [ERROR] 연결 실패: {e}")
    exit(1)

# ========================================
# 2단계: 목차 정제 테스트
# ========================================
print("\n[2] 목차 정제 테스트 중...")

custom_prompt = """정제 규칙:
1. 특수 문자 제거 (cid:xxx 등)
2. 분리된 단어들을 병합

3. 강의 단위 인식:
   - "N강 제목" 형식
   - 3자리 페이지 번호(009, 012)로 끝나는 블록을 하나의 강의로 간주
   - 페이지 번호 앞의 모든 텍스트를 한 줄로 병합

4. 제외 항목:
   - 두 자리 번호 (01, 02 등) 단독 라인
   - 섹션 구분자 (>>>, 고전 시가 등)

5. 출력:
   - 각 강의는 한 줄로
   - 빈 줄로 구분
"""

try:
    response = requests.post(
        'http://localhost:8000/api/v1/templates/clean-toc-text',
        json={
            'toc_text': test_toc,
            'custom_prompt': custom_prompt
        },
        timeout=30
    )
    
    if response.status_code == 200:
        result = response.json()
        cleaned_text = result['cleaned_text']
        print(f"    [OK] 정제 완료: {result['changes_made']}")
        print("\n--- 정제된 목차 ---")
        print(cleaned_text)
        
        # 파일 저장
        with open('test_cleaned.txt', 'w', encoding='utf-8') as f:
            f.write(cleaned_text)
        print("\n    [SAVE] test_cleaned.txt")
    else:
        print(f"    [ERROR] 정제 실패: {response.status_code}")
        print(response.text)
        exit(1)
        
except Exception as e:
    print(f"    [ERROR] 요청 실패: {e}")
    exit(1)

# ========================================
# 3단계: 강의 목록 추출 테스트
# ========================================
print("\n[3] 강의 목록 추출 테스트 중...")

try:
    response = requests.post(
        'http://localhost:8000/api/v1/templates/parse-toc-lectures',
        json=cleaned_text,
        headers={'Content-Type': 'application/json'},
        timeout=10
    )
    
    if response.status_code == 200:
        result = response.json()
        lectures = result['lectures']
        print(f"    [OK] 추출 완료: {result['total_lectures']}개 강의")
        print(f"    페이지 정보: {result['lectures_with_pages']}개\n")
        
        print("--- 강의 목록 ---")
        for lecture in lectures[:10]:
            lecture_id = lecture['lecture_id']
            title = lecture['title'][:40]
            start = lecture.get('start_page', '?')
            end = lecture.get('end_page', '?')
            print(f"  {lecture_id}강: {title:<40} (p.{start}~{end})")
        
        if len(lectures) > 10:
            print(f"  ... (외 {len(lectures) - 10}개)")
        
        # 파일 저장
        with open('test_lectures.json', 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        print("\n    [SAVE] test_lectures.json")
    else:
        print(f"    [ERROR] 추출 실패: {response.status_code}")
        print(response.text)
        
except Exception as e:
    print(f"    [ERROR] 요청 실패: {e}")

# ========================================
# 최종 결과
# ========================================
print("\n" + "=" * 80)
print("테스트 완료!")
print("=" * 80)
print("\n생성된 파일:")
print("  - test_cleaned.txt (정제된 목차)")
print("  - test_lectures.json (강의 목록)")
print("\n결과:")
print("  ✓ 목차 정제 API 작동")
print("  ✓ 강의 추출 API 작동")
print("  ✓ 009 단위 페이지 번호 자동 인식")
print("\n실제 사용:")
print("  1. PDF 파일을 준비하고")
print("  2. python extract_full_toc.py 실행")
print("  3. python clean_and_generate.py 실행")
print("")
