"""목차 텍스트 정제 및 강의 추출 테스트. 프로젝트 루트에서: python scripts/test_clean_toc.py"""
import os
import requests
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
os.chdir(ROOT)

# 원본 OCR 텍스트
toc_raw = """1강
시의
표현과
형식
고전
시가
>>>
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
죽지랑가
(득오)
화왕가
(이익)
01
044
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

print("=" * 80)
print("1단계: OCR 텍스트 정제")
print("=" * 80)

# 1. 텍스트 정제
response = requests.post(
    'http://localhost:8000/api/v1/templates/clean-toc-text',
    json={
        'toc_text': toc_raw,
        'custom_prompt': None  # 기본 정제 규칙 사용
    }
)

if response.status_code == 200:
    result = response.json()
    cleaned_text = result['cleaned_text']
    print(f"\n[OK] 정제 완료: {result['changes_made']}")
    print("\n--- 정제된 목차 ---")
    print(cleaned_text)
    
    # 정제된 텍스트를 파일로 저장
    with open('toc_cleaned.txt', 'w', encoding='utf-8') as f:
        f.write(cleaned_text)
    print("\n[SAVE] 저장: toc_cleaned.txt")
else:
    print(f"\n[ERROR] 정제 실패: {response.status_code}")
    print(response.text)
    cleaned_text = toc_raw

print("\n" + "=" * 80)
print("2단계: 강의 목록 추출")
print("=" * 80)

# 2. 강의 목록 추출
response = requests.post(
    'http://localhost:8000/api/v1/templates/parse-toc-lectures',
    json=cleaned_text,
    headers={'Content-Type': 'application/json'}
)

if response.status_code == 200:
    result = response.json()
    lectures = result['lectures']
    print(f"\n[OK] 강의 추출 완료: 총 {result['total_lectures']}개")
    print(f"     페이지 정보 있는 강의: {result['lectures_with_pages']}개\n")
    
    print("--- 강의 목록 ---")
    for lecture in lectures[:15]:  # 처음 15개만 출력
        lecture_id = lecture['lecture_id']
        title = lecture['title']
        start = lecture.get('start_page', '?')
        end = lecture.get('end_page', '?')
        print(f"  {lecture_id}강: {title:<30} (페이지 {start} ~ {end})")
    
    if len(lectures) > 15:
        print(f"  ... (외 {len(lectures) - 15}개)")
    
    # 강의 목록을 JSON으로 저장
    with open('toc_lectures.json', 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print("\n[SAVE] 저장: toc_lectures.json")
else:
    print(f"\n[ERROR] 추출 실패: {response.status_code}")
    print(response.text)

print("\n" + "=" * 80)
print("3단계: 강의 예시 생성 (템플릿 생성에 사용)")
print("=" * 80)

if response.status_code == 200:
    # 강의 라인 예시 추출 (처음 5개)
    lecture_examples = []
    for line in cleaned_text.split('\n'):
        line = line.strip()
        if line and any(f'{i}강' in line for i in range(1, 100)):
            lecture_examples.append(line)
            if len(lecture_examples) >= 5:
                break
    
    print("\n강의 라인 예시 (toc_lecture_line_examples):")
    for i, example in enumerate(lecture_examples, 1):
        print(f"  {i}. {example}")
    
    # 비강의 라인 예시
    nonlecture_examples = ['01', '02', '03', '고전 시가 >>>', '현대시 >>>']
    print("\n비강의 라인 예시 (toc_nonlecture_line_examples):")
    for i, example in enumerate(nonlecture_examples, 1):
        print(f"  {i}. {example}")
    
    print(f"\n기대 강의 수 (expected_lecture_count): {result['total_lectures']}")
