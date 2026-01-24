# YOLO 사용 가이드

YOLO 기반 PDF 파싱 기능 사용 방법입니다.

## 기본 설정

YOLO는 **기본적으로 활성화**되어 있습니다. PDF를 업로드하면 자동으로 YOLO 감지가 실행됩니다.

## 사용 방법

### 1. 프론트엔드에서 사용 (자동)

프론트엔드에서 PDF를 업로드하면 자동으로 YOLO가 실행됩니다:

```typescript
// apps/web/src/components/textbook/PDFUpload.tsx
// YOLO는 기본적으로 활성화되어 있음
const formData = new FormData();
formData.append('file', pdfFile);
formData.append('title', '2026 수능특강 문학');
formData.append('subject', 'KOREAN');
formData.append('year', '2026');
// enable_yolo_detection은 기본값이 true이므로 생략 가능
// formData.append('enable_yolo_detection', 'true');
```

### 2. API 직접 호출

#### curl 예시

```bash
curl -X POST "http://localhost:8000/api/v1/books/upload" \
  -F "file=@/path/to/your/file.pdf" \
  -F "title=2026 수능특강 문학" \
  -F "subject=KOREAN" \
  -F "year=2026" \
  -F "enable_yolo_detection=true" \
  -F "roboflow_api_key=ohDbNa6uGc3Aozm81aci"
```

#### Python 예시

```python
import requests

url = "http://localhost:8000/api/v1/books/upload"

files = {
    'file': ('literature.pdf', open('literature.pdf', 'rb'), 'application/pdf')
}

data = {
    'title': '2026 수능특강 문학',
    'subject': 'KOREAN',
    'year': 2026,
    'enable_yolo_detection': True,  # 기본값이 True이므로 생략 가능
    'roboflow_api_key': 'ohDbNa6uGc3Aozm81aci'  # 선택사항 (기본값 있음)
}

response = requests.post(url, files=files, data=data)
print(response.json())
```

### 3. YOLO 비활성화 (필요시)

YOLO를 사용하지 않으려면:

```bash
curl -X POST "http://localhost:8000/api/v1/books/upload" \
  -F "file=@/path/to/your/file.pdf" \
  -F "title=2026 수능특강 문학" \
  -F "subject=KOREAN" \
  -F "year=2026" \
  -F "enable_yolo_detection=false"
```

## 동작 과정

1. **PDF 업로드**: `/api/v1/books/upload` 엔드포인트로 PDF 업로드
2. **YOLO 감지 자동 실행**: 
   - Roboflow API를 사용하여 페이지별로 영역 감지
   - 감지되는 클래스:
     - `header`: 강의 제목
     - `section`: 개념 제목
     - `concept_box`: 개념 내용
     - `sidebar`: 세부 개념
     - `passage`: 본문
     - `question`: 문제
3. **Unit 변환**: 감지된 영역이 자동으로 Unit으로 변환
4. **데이터베이스 저장**: Lesson과 Unit이 DB에 저장됨

## 결과 확인

### 파싱 상태 확인

```bash
curl "http://localhost:8000/api/v1/books/{book_id}/parse-status"
```

### 강의 목록 확인

```bash
curl "http://localhost:8000/api/v1/books/{book_id}/lessons"
```

### Unit 목록 확인

```bash
curl "http://localhost:8000/api/v1/lessons/{lesson_id}/units"
```

## 클래스 매핑

YOLO가 감지한 영역은 다음과 같이 변환됩니다:

| YOLO 클래스 | Unit 타입 | 설명 |
|------------|-----------|------|
| `header` | Lesson | 강의 제목 (예: "1강") |
| `section` | Unit (concept, title) | 개념 제목 |
| `concept_box` | Unit (concept, content) | 개념 내용 |
| `sidebar` | Unit (concept_detail) | 세부 개념 |
| `passage` | Unit (passage) | 본문/지문 |
| `question` | Unit (question) | 문제 |

## 로그 확인

파이프라인 실행 중 다음 로그를 확인할 수 있습니다:

```
[2.5/5] YOLO 레이아웃 감지 중... (Level 2.2 AI 기능)
[2.5/5] YOLO 감지 완료: 150개 영역 감지 (12.3초)
     - 강의: 10개, 문제: 30개
[2.6/5] YOLO 감지 결과를 unit으로 변환 중...
[2.6/5] YOLO 기반 파싱 완료: 10개 강의, 30개 문제
```

## 문제 해결

### YOLO 감지가 실행되지 않음

1. **과목 확인**: 현재 YOLO는 `literature` (문학) 과목에서만 작동합니다
2. **API 키 확인**: Roboflow API 키가 올바른지 확인
3. **로그 확인**: 서버 로그에서 오류 메시지 확인

### 감지 결과가 부정확함

1. **신뢰도 임계값 조정**: `confidence_threshold` 값 조정 (기본값: 0.25)
2. **모델 재학습**: 더 많은 데이터로 YOLO 모델 재학습
3. **OCR 결과 확인**: YOLO 감지 후 OCR로 텍스트 추출이 정확한지 확인

### 성능 최적화

- **배치 처리**: 여러 페이지를 한 번에 처리
- **캐싱**: 동일한 PDF는 캐시된 결과 사용
- **병렬 처리**: 여러 페이지를 병렬로 감지

## 참고

- Roboflow API 엔드포인트: `https://detect.roboflow.com/-wshlq/2`
- 기본 API 키: `ohDbNa6uGc3Aozm81aci` (환경변수 `ROBOFLOW_API_KEY`로 오버라이드 가능)
- YOLO 모델 학습 가이드: `api/docs/YOLO_TRAINING_GUIDE.md`
