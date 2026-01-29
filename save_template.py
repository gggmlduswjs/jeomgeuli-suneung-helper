"""템플릿 저장 (API)"""
import requests
import json

print("템플릿 저장 중...")

with open('template_fixed.json', 'r', encoding='utf-8') as f:
    template = json.load(f)

response = requests.post(
    'http://localhost:8000/api/v1/templates',
    json=template,
    timeout=10
)

if response.status_code == 200:
    result = response.json()
    print(f"\n[OK] 템플릿 저장 완료!")
    print(f"파일 경로: {result.get('file_path', '?')}")
    print(f"\n템플릿 정보:")
    print(f"  - 이름: {template['name']}")
    print(f"  - 과목: {template['subject']}")
    print(f"  - 버전: {template.get('version', '없음')}")
    print(f"  - 총 강의: {len(template['config']['toc_lecture_list'])}개")
else:
    print(f"\n[ERROR] 저장 실패: {response.status_code}")
    print(response.text)
