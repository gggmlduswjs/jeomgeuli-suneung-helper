"""
페이지 이미지에서 강의 제목 추출
PDF 텍스트 레이어가 깨진 경우 이미지 기반 OCR 사용
"""
import sys
import re
import json
from pathlib import Path
from PIL import Image
import pytesseract

sys.path.insert(0, 'api')

# Tesseract 경로 설정 (Windows)
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

def extract_top_text(image_path, height_ratio=0.15):
    """페이지 상단 영역만 OCR"""
    img = Image.open(image_path)
    width, height = img.size

    # 상단 15% 영역만 크롭
    top_area = img.crop((0, 0, width, int(height * height_ratio)))

    # OCR 수행 (한글 + 영어)
    text = pytesseract.image_to_string(top_area, lang='kor+eng')
    return text.strip()

def find_lectures(pages_dir):
    """모든 페이지에서 강의 시작점 찾기"""
    pages_dir = Path(pages_dir)
    page_files = sorted(pages_dir.glob('page_*.png'))

    lectures = []

    print(f"총 {len(page_files)}개 페이지 스캔 중...")

    for i, page_file in enumerate(page_files, 1):
        page_num = i

        if i % 50 == 0:
            print(f"  진행: {i}/{len(page_files)} 페이지...")

        # 상단 텍스트 추출
        try:
            top_text = extract_top_text(page_file)

            # "N강" 패턴 찾기
            # 예: "1강", "2강", "73강"
            lecture_match = re.search(r'(\d+)\s*강', top_text, re.MULTILINE)

            if lecture_match:
                lecture_num = int(lecture_match.group(1))

                # 제목 추출 (강의 번호 다음 줄)
                lines = top_text.split('\n')
                title_line = ""
                for line in lines:
                    if f"{lecture_num}강" in line:
                        # 다음 줄이 제목
                        idx = lines.index(line)
                        if idx + 1 < len(lines):
                            title_line = lines[idx + 1].strip()
                        break

                # 제목이 없으면 같은 줄에서 추출
                if not title_line:
                    title_line = lecture_match.string[lecture_match.end():].strip()
                    # 첫 줄만
                    title_line = title_line.split('\n')[0].strip()

                full_title = f"{lecture_num}강 {title_line}" if title_line else f"{lecture_num}강"

                lectures.append({
                    "lecture_id": lecture_num,
                    "title": full_title,
                    "page": page_num,
                })

                print(f"  [발견] 페이지 {page_num}: {full_title}")

        except Exception as e:
            # OCR 실패는 무시
            pass

    return lectures

if __name__ == '__main__':
    pages_dir = 'api/data/literature/pages'
    lectures = find_lectures(pages_dir)

    print(f"\n총 {len(lectures)}개 강의 발견!")

    # 강의 번호로 정렬
    lectures.sort(key=lambda x: x['lecture_id'])

    # 결과 저장
    output_file = 'api/data/literature/lectures/lectures.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(lectures, f, ensure_ascii=False, indent=2)

    print(f"\n강의 목록 저장: {output_file}")
    print(f"\n처음 10개:")
    for lec in lectures[:10]:
        print(f"  {lec['lecture_id']}. {lec['title']}")
