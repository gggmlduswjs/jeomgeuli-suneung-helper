"""
Test script for improved multi-line lecture title extraction
"""
import re

# Mock OCR data simulating the actual textbook format
mock_ocr_lines = [
    # Page 8 - 1강
    {"text": "1강", "top": 50, "left": 100, "width": 50, "height": 30},
    {"text": "시의 표현과 형식 - 해(박도진)", "top": 90, "left": 100, "width": 200, "height": 25},

    # Page 16 - 2강
    {"text": "2강", "top": 50, "left": 100, "width": 50, "height": 30},
    {"text": "시의 표현과 형식 - 현대시", "top": 90, "left": 100, "width": 180, "height": 25},

    # Page 23 - 3강
    {"text": "3강", "top": 50, "left": 100, "width": 50, "height": 30},
    {"text": "소설의 서술상 특징", "top": 90, "left": 100, "width": 160, "height": 25},

    # False positive - problem number (should be filtered)
    {"text": "01 간을 옮긴 이유도 겉으로는", "top": 200, "left": 100, "width": 300, "height": 20},
]

# Simulate the improved extraction logic
def extract_lectures_test(lines):
    """Test version of the improved lecture extraction"""
    lectures = []
    lecture_id = 1

    for idx, line in enumerate(lines):
        line_text = line["text"].strip()

        # Check for "N강" standalone
        lecture_num_match = re.match(r'^(\d+)강\s*$', line_text)
        if lecture_num_match:
            lecture_num = lecture_num_match.group(1)
            title_parts = [line_text]

            # Look ahead for next line(s) to get full title
            for next_idx in range(idx + 1, min(idx + 3, len(lines))):
                next_line = lines[next_idx]
                next_line_text = next_line["text"].strip()

                if not next_line_text:
                    break

                # Stop if next line starts with a number (next lecture)
                if re.match(r'^\d+', next_line_text):
                    break

                title_parts.append(next_line_text)

                # Stop if title is long enough
                if len(" ".join(title_parts)) >= 30:
                    break

            full_title = " ".join(title_parts)
            lectures.append({
                "lecture_id": lecture_id,
                "title": full_title,
            })
            lecture_id += 1
            print(f"[OK] 강의 발견: {full_title}")
            continue

        # Filter out problem numbers (2-digit numbers followed by Korean text)
        if re.match(r'^\d{2,}\s+', line_text):
            print(f"[SKIP] 필터링 (문제 번호): {line_text[:50]}")
            continue

    return lectures

# Run test
print("=" * 60)
print("다중 라인 강의 제목 추출 테스트")
print("=" * 60)
lectures = extract_lectures_test(mock_ocr_lines)

print("\n" + "=" * 60)
print(f"총 {len(lectures)}개 강의 추출 완료:")
print("=" * 60)
for lec in lectures:
    print(f"  {lec['lecture_id']}. {lec['title']}")

print("\n예상 결과: 3개 강의 (1강, 2강, 3강)")
print(f"실제 결과: {len(lectures)}개 강의")
print(f"테스트: {'성공' if len(lectures) == 3 else '실패'}")
