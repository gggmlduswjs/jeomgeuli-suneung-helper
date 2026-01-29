# 전체 파싱 모드 (Full Parsing Mode)

이 폴더에는 전체 파싱 모드에서 사용하는 파일들이 있습니다.

## 구조

- `pipeline.py`: UnifiedPipeline 클래스 (메인 파이프라인)
- `parsers/`: 과목별 파서 (literature, math1, english 등)
- `postprocessors/`: 후처리 (중복 제거, 분류 등)
- `lecture_contents_extractor.py`: 강의 콘텐츠 추출
- `result_saver.py`: 결과 저장
- `image_saver.py`: 이미지 저장
- `extractor_factory.py`: 추출기 팩토리
- `page_range_calculator.py`: 페이지 범위 계산

## 사용 방법

전체 파싱 모드는 `_process_pdf_background()` 함수에서 사용됩니다.

```python
from app.infrastructure.pdf.full_parsing.pipeline import UnifiedPipeline
```

## 간단 모드와의 차이

- **간단 모드**: OCR 데이터만 생성 (텍스트 추출)
- **전체 파싱 모드**: 구조화된 데이터 생성 (개념/지문/문제 분류, 이미지 크롭 등)

## 참고

간단 모드에서 사용하는 파일들은 `backend/app/infrastructure/pdf/` 루트에 있습니다:
- `extractors/`: 텍스트 추출기
- `constants.py`, `exceptions.py`, `types.py`: 공통 유틸리티
