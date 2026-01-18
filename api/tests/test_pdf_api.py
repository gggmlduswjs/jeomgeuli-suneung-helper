"""
PDF API 빠른 테스트 스크립트
"""
import requests
import json
from pathlib import Path

API_BASE = "http://localhost:8000/api/v1"

def test_health():
    """헬스 체크 테스트"""
    print("=== 헬스 체크 테스트 ===")
    response = requests.get(f"{API_BASE}/health")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}\n")
    return response.status_code == 200

def test_pdf_extract(pdf_path: Path):
    """PDF 구조화 추출 테스트"""
    print("=== PDF 구조화 추출 테스트 ===")
    
    if not pdf_path.exists():
        print(f"❌ 파일을 찾을 수 없습니다: {pdf_path}")
        return False
    
    print(f"파일: {pdf_path.name}")
    
    with open(pdf_path, "rb") as f:
        files = {"file": f}
        response = requests.post(
            f"{API_BASE}/pdf/extract-structured",
            files=files
        )
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ 성공!")
        print(f"  - 문제 수: {len(data.get('questions', []))}")
        print(f"  - 본문 수: {len(data.get('passages', []))}")
        print(f"  - 레슨 수: {len(data.get('lessons', []))}")
        
        # 첫 번째 문제 샘플 출력
        if data.get('questions'):
            q = data['questions'][0]
            print(f"\n  첫 번째 문제 샘플:")
            print(f"    번호: {q.get('number')}")
            print(f"    문제: {q.get('stem', '')[:50]}...")
            print(f"    선택지 수: {len(q.get('choices', []))}")
        
        return True
    else:
        print(f"❌ 실패: {response.status_code}")
        print(f"  에러: {response.text}")
        return False

def test_pdf_images(pdf_path: Path):
    """PDF 이미지 추출 테스트"""
    print("\n=== PDF 이미지 추출 테스트 ===")
    
    if not pdf_path.exists():
        print(f"❌ 파일을 찾을 수 없습니다: {pdf_path}")
        return False
    
    with open(pdf_path, "rb") as f:
        files = {"file": f}
        data = {"extract_type": "both"}
        response = requests.post(
            f"{API_BASE}/pdf/extract-images",
            files=files,
            data=data
        )
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ 성공!")
        print(f"  - 추출된 이미지 수: {result.get('total_count', 0)}")
        return True
    else:
        print(f"❌ 실패: {response.status_code}")
        print(f"  에러: {response.text}")
        return False

if __name__ == "__main__":
    import sys
    
    print("PDF API 테스트 시작\n")
    
    # 헬스 체크
    if not test_health():
        print("❌ 서버가 실행 중이 아닙니다. 먼저 서버를 시작하세요:")
        print("   cd api && uvicorn app.main:app --reload")
        sys.exit(1)
    
    # PDF 파일 경로
    pdf_path = Path(__file__).parent.parent / "data" / "pdfs"
    
    # PDF 파일 찾기
    pdf_files = list(pdf_path.glob("*.pdf"))
    if not pdf_files:
        print(f"❌ PDF 파일을 찾을 수 없습니다: {pdf_path}")
        print("   data/pdfs/ 폴더에 PDF 파일을 배치하세요.")
        sys.exit(1)
    
    # 첫 번째 PDF 파일로 테스트
    test_pdf = pdf_files[0]
    print(f"테스트 파일: {test_pdf.name}\n")
    
    # 테스트 실행
    success = True
    success &= test_pdf_extract(test_pdf)
    success &= test_pdf_images(test_pdf)
    
    print("\n" + "="*50)
    if success:
        print("✅ 모든 테스트 통과!")
    else:
        print("❌ 일부 테스트 실패")
        sys.exit(1)
