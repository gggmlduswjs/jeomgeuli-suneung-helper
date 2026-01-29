# AI 파싱 활성화 가이드

## 개요
하이브리드 라우터의 AI 파싱 기능을 활성화하여 신규 교재를 자동으로 분석할 수 있습니다.

## 설치 방법

### 1. 필수 패키지 설치

```bash
pip install langchain openai pydantic
```

또는 requirements 파일에 추가:

```bash
pip install -r requirements-ai.txt
```

### 2. 환경 변수 설정

`.env` 파일에 OpenAI API 키 추가:

```env
OPENAI_API_KEY=sk-...
```

### 3. 테스트

템플릿 초기화 스크립트 실행:

```bash
python backend/scripts/init_templates.py
```

PDF 파이프라인 실행 (AI 파싱 자동 활성화):

```bash
python backend/scripts/pipeline/run_textbook_pipeline.py
```

## 작동 방식

1. **템플릿 매칭 시도** (2-5초)
   - 기존 템플릿과 매칭 시도
   - 신뢰도 ≥ 0.85면 템플릿 사용

2. **AI 파싱 시도** (60-120초)
   - 템플릿 매칭 실패 시 자동으로 AI 파싱 시도
   - LLM이 PDF 구조를 분석하여 파싱 규칙 생성
   - 생성된 규칙으로 파싱 실행

3. **폴백** (config.json)
   - AI 파싱도 실패하면 기존 config.json 사용

## 비용

- 모델: `gpt-4o-mini` (기본값, 빠르고 저렴)
- 예상 비용: 교재당 약 $0.01-0.05 (텍스트 샘플 분석)
- 캐싱: 같은 교재는 한 번만 분석 (book_id 기반)

## 주의사항

- API 키가 없으면 AI 파싱은 자동으로 건너뜁니다
- langchain이 설치되지 않으면 폴백으로 전환됩니다
- 첫 실행 시 느릴 수 있지만, 템플릿으로 저장되면 다음부터는 빠릅니다
