"""
템플릿을 지정해서 재파싱 테스트
"""
import requests

# 재파싱 API 호출 (템플릿 명시)
url = "http://localhost:8000/api/v1/books/book_korean_2026_수능특강_문학_0ef2d9/reparse"
data = {
    "template_name": "ebs_수능특강_literature_2026"
}

print(f"재파싱 요청 중...")
print(f"URL: {url}")
print(f"템플릿: {data['template_name']}")

response = requests.post(url, json=data)

print(f"\n응답 상태: {response.status_code}")
print(f"응답 내용: {response.json()}")
