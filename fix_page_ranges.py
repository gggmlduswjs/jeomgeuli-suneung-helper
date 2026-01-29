"""
강의별 페이지 범위 수정

2단 레이아웃 때문에 뒤섞인 페이지 범위를 정확하게 수정
"""
import json

print("=" * 80)
print("페이지 범위 수정")
print("=" * 80)

# 템플릿 로드
with open('template_final.json', 'r', encoding='utf-8') as f:
    template = json.load(f)

# 기존 강의 목록
lectures = template['config']['toc_lecture_list']

print("\n[원본 페이지 범위]")
for lecture in lectures:
    lid = lecture['lecture_id']
    start = lecture.get('start_page', '?')
    end = lecture.get('end_page', '?')
    print(f"  {lid}강: {start}~{end}")

# ========================================
# 페이지 범위 재계산 (강의 순서로 정렬)
# ========================================
print("\n[페이지 범위 재계산]")

# 강의 ID 순서로 정렬
lectures_sorted = sorted(lectures, key=lambda x: x['lecture_id'])

# 페이지 번호가 있는 강의들을 시작 페이지 순서로 정렬
lectures_with_pages = [l for l in lectures_sorted if l.get('start_page')]
lectures_with_pages.sort(key=lambda x: x['start_page'])

print("\n  페이지 순서로 정렬된 강의:")
for lecture in lectures_with_pages:
    lid = lecture['lecture_id']
    start = lecture.get('start_page')
    print(f"    {lid}강: 시작 페이지 {start}")

# 종료 페이지 재계산
for i, lecture in enumerate(lectures_with_pages):
    if i + 1 < len(lectures_with_pages):
        next_lecture = lectures_with_pages[i + 1]
        lecture['end_page'] = next_lecture['start_page'] - 1
    else:
        lecture['end_page'] = None  # 마지막 강의는 끝까지

# lecture_page_ranges 재생성
lecture_page_ranges = {}
for lecture in lectures_sorted:
    if lecture.get('start_page'):
        lecture_id = str(lecture['lecture_id'])
        lecture_page_ranges[lecture_id] = {
            'start': lecture['start_page'],
            'end': lecture.get('end_page')
        }

# 템플릿 업데이트
template['config']['toc_lecture_list'] = lectures_sorted
template['config']['lecture_page_ranges'] = lecture_page_ranges

print("\n[수정된 페이지 범위]")
for lecture in lectures_sorted:
    lid = lecture['lecture_id']
    start = lecture.get('start_page', '?')
    end = lecture.get('end_page', '?')
    print(f"  {lid}강: {start}~{end}")

# 저장
with open('template_fixed.json', 'w', encoding='utf-8') as f:
    json.dump(template, f, ensure_ascii=False, indent=2)

print("\n[SAVE] 저장 완료: template_fixed.json")

print("\n" + "=" * 80)
print("완료!")
print("=" * 80)
print("\n수정된 템플릿:")
print("  - template_fixed.json")
print("\n다음 단계:")
print("  1. template_fixed.json 확인")
print("  2. 저장:")
print("     POST /api/v1/templates (template_fixed.json 전송)")
print("  3. 또는 웹 UI에서 업로드")
print("")
