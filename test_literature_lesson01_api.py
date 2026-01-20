"""
문학 1강 API 테스트
"""
import requests
import json

BASE_URL = "http://localhost:8000/api/v1"

# 1강 유닛 목록 조회
response = requests.get(f"{BASE_URL}/lessons/lesson_literature_01/units")

if response.status_code == 200:
    units = response.json()
    print(f"문학 1강 유닛 수: {len(units)}")
    print()

    for unit in units:
        print(f"[{unit['type']}] {unit['title']}")

        # 이미지 경로
        if unit.get('content_image_paths'):
            print(f"  이미지: {unit['content_image_paths']}")
        elif unit.get('image_path'):
            print(f"  이미지: {unit['image_path']}")

        # AI 설명
        if unit.get('ai_explanation'):
            print(f"  AI 설명: {unit['ai_explanation'][:50]}...")

        # 점자 키워드
        if unit.get('braille_keywords'):
            print(f"  점자키워드: {', '.join(unit['braille_keywords'])}")

        # 문제
        if unit.get('question'):
            q = unit['question']
            print(f"  문제: {q['stem'][:50]}...")
            print(f"  선택지: {q['choices']}")
            print(f"  정답: {q.get('answer')}")

        print()
else:
    print(f"API 오류: {response.status_code}")
    print(response.text)
