"""
PDF에서 목차 전체 추출 (2단 구성 자동 처리)

사용법:
1. PDF 파일을 이 디렉토리에 복사하고 파일명을 아래에 입력
2. python extract_full_toc.py 실행
"""
import requests

# ========================================
# 설정
# ========================================
PDF_FILE_PATH = "data/pdfs/2026 수능특강_ 문학.pdf"  # PDF 파일 경로
TOC_PAGES = "3,4,5,6,7"  # 목차 페이지 번호 (페이지 3부터 7까지 시도)

print("=" * 80)
print("PDF 목차 전체 추출")
print("=" * 80)
print(f"\nPDF 파일: {PDF_FILE_PATH}")
print(f"목차 페이지: {TOC_PAGES}")

# ========================================
# API 호출
# ========================================
print("\n[1] PDF에서 목차 추출 중...")
print("    (2단 구성 자동 처리 + 페이지 번호 순서 정렬)")

try:
    with open(PDF_FILE_PATH, 'rb') as f:
        files = {
            'pdf_file': (PDF_FILE_PATH, f, 'application/pdf'),
            'toc_pages': (None, TOC_PAGES)
        }
        
        response = requests.post(
            'http://localhost:8000/api/v1/templates/extract-toc-text',
            files=files
        )
except FileNotFoundError:
    print(f"\n[ERROR] PDF 파일을 찾을 수 없습니다: {PDF_FILE_PATH}")
    print("        PDF 파일을 이 디렉토리에 복사하고 파일명을 확인하세요.")
    exit(1)
except Exception as e:
    print(f"\n[ERROR] 요청 실패: {e}")
    exit(1)

if response.status_code != 200:
    print(f"\n[ERROR] 추출 실패: {response.status_code}")
    print(response.text)
    exit(1)

# ========================================
# 결과 저장
# ========================================
result = response.json()
toc_text = result['toc_text']
pages_extracted = result['pages_extracted']
total_lines = result['total_lines']

print(f"\n[OK] 추출 완료!")
print(f"     추출 페이지: {pages_extracted}")
print(f"     전체 줄 수: {total_lines}")

# 파일로 저장
with open('toc_extracted_full.txt', 'w', encoding='utf-8') as f:
    f.write(toc_text)

print(f"\n[SAVE] 저장 완료: toc_extracted_full.txt")
print(f"       크기: {len(toc_text)} 글자")

# 미리보기 (처음 50줄)
print("\n--- 추출된 목차 미리보기 (처음 50줄) ---")
lines = toc_text.split('\n')
for i, line in enumerate(lines[:50], 1):
    print(f"{i:3d}: {line}")

if len(lines) > 50:
    print(f"... (외 {len(lines) - 50}줄)")

# ========================================
# 다음 단계
# ========================================
print("\n" + "=" * 80)
print("완료! 다음 단계:")
print("=" * 80)
print("\n1. toc_extracted_full.txt 내용 확인")
print("   - 강의들이 순서대로 잘 추출되었는지 확인")
print("   - 페이지 번호(009, 012 등)가 제대로 있는지 확인")
print("\n2. 정제가 필요하면:")
print("   python clean_and_generate.py")
print("\n3. 또는 바로 템플릿 생성:")
print("   - toc_extracted_full.txt를 toc_full.txt로 복사")
print("   - python generate_template_from_toc.py 실행")
print("")
