"""
간단한 API 테스트 스크립트 (Python)
"""
import requests
import json
from pathlib import Path

BASE_URL = "http://localhost:8000/api/v1"

def test_health():
    """헬스 체크"""
    print("1. 헬스 체크...")
    try:
        response = requests.get(f"{BASE_URL}/health")
        print(f"✅ 서버 정상: {response.json()}")
        return True
    except Exception as e:
        print(f"❌ 서버 연결 실패: {e}")
        return False

def test_curriculum_list():
    """커리큘럼 목록 조회"""
    print("\n2. 커리큘럼 목록 조회...")
    try:
        response = requests.get(f"{BASE_URL}/curriculum")
        curricula = response.json()
        print(f"✅ 총 {len(curricula)}개의 커리큘럼이 있습니다.")
        for curriculum in curricula:
            print(f"   - {curriculum['title']} ({curriculum['curriculum_id']})")
            print(f"     상태: {curriculum['status']}, 레슨: {curriculum['lesson_count']}개")
        return True
    except Exception as e:
        print(f"❌ 목록 조회 실패: {e}")
        return False

def test_content_validate():
    """콘텐츠 검증"""
    print("\n3. 콘텐츠 검증 API 테스트...")
    try:
        data = {
            "content": "자, 그다음에 문제1번을 살펴보겠습니다. ①②③④⑤ 중에서 정답을 찾아보세요.",
            "section_type": "explanation"
        }
        response = requests.post(f"{BASE_URL}/content/validate", json=data)
        result = response.json()
        print(f"✅ 검증 완료!")
        print(f"   준수 여부: {result['is_compliant']}")
        print(f"   점수: {result['score']}")
        print(f"   이슈 수: {len(result['issues'])}")
        if result.get('improvements'):
            print(f"   개선 사항: {len(result['improvements'])}개")
        return True
    except Exception as e:
        print(f"❌ 검증 실패: {e}")
        return False

def test_hwp_upload():
    """HWP 파일 업로드 테스트"""
    print("\n4. HWP 파일 업로드 테스트...")
    
    # HWP 파일 찾기
    hwp_dir = Path("../data/lecture_scripts/수능특강_문학_2026")
    hwp_files = list(hwp_dir.glob("*.hwp"))
    
    if not hwp_files:
        print("❌ HWP 파일을 찾을 수 없습니다.")
        return False
    
    hwp_file = hwp_files[0]
    print(f"   테스트 파일: {hwp_file.name}")
    
    try:
        with open(hwp_file, 'rb') as f:
            files = {'file': (hwp_file.name, f, 'application/x-hwp')}
            data = {
                'title': '2026 수능특강 문학 테스트',
                'subject': 'KOREAN',
                'year': 2026
            }
            response = requests.post(f"{BASE_URL}/books/upload-hwp", files=files, data=data)
            result = response.json()
            print(f"✅ 업로드 성공!")
            print(f"   Book ID: {result['book_id']}")
            print(f"   Title: {result['title']}")
            print(f"   Status: {result['parse_status']}")
            print(f"   Lesson Count: {result['lesson_count']}")
            return True
    except Exception as e:
        print(f"❌ 업로드 실패: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"   응답: {e.response.text}")
        return False

if __name__ == "__main__":
    print("=" * 50)
    print("API 테스트 시작")
    print("=" * 50)
    
    results = []
    results.append(("헬스 체크", test_health()))
    results.append(("커리큘럼 목록", test_curriculum_list()))
    results.append(("콘텐츠 검증", test_content_validate()))
    results.append(("HWP 업로드", test_hwp_upload()))
    
    print("\n" + "=" * 50)
    print("테스트 결과:")
    for name, result in results:
        status = "✅ 통과" if result else "❌ 실패"
        print(f"  {name}: {status}")
