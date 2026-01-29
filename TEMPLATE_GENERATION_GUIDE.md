# 📖 템플릿 생성 가이드 (009 단위 강의)

EBS 수능특강 문학 교재의 목차에서 자동으로 템플릿을 생성하는 방법

---

## 🎯 목차 구조 이해

수능특강 문학 교재는 다음과 같은 구조입니다:

```
1강 시의 표현과 형식
해 (박두진) 009           ← 3자리 페이지 번호로 강의 구분
매화 등걸에 (매화) 03
거래 귀거래 말뿐이오 (이현보)
...
사랑 사랑 고고히 맺힌 사랑 (작자 미상) 012  ← 다음 강의 시작 전

2강 시의 내용
과정곡 (정서)
소악부 <제6장> (민사평) 046  ← 페이지 번호
```

**핵심 규칙:**
- `N강 제목` 형식으로 강의 시작
- **3자리 페이지 번호(009, 012, 015 등)**가 나오면 해당 강의 종료
- 페이지 번호로 강의 범위 자동 계산

---

## 🚀 사용 방법 (3단계)

### 1단계: 목차 텍스트 준비

1. PDF에서 목차 페이지 복사 (Ctrl+C)
2. `toc_full.txt` 파일 생성
3. 복사한 텍스트 붙여넣기 (Ctrl+V)

**예시 (toc_full.txt):**
```
1강
시의
표현과
형식
고전
시가
>>>
해
(박두진)
009
매화
등걸에
...
```

> 💡 **Tip:** OCR 오류가 있어도 괜찮습니다. 시스템이 자동으로 정제합니다.

---

### 2단계: 스크립트 실행

```bash
# 프로젝트 디렉토리로 이동
cd c:\Users\user\Desktop\jeomgeuli-suneung-helper

# 가상환경 활성화 (이미 활성화되어 있으면 생략)
.venv\Scripts\activate

# 백엔드 서버 실행 (별도 터미널)
cd backend
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 템플릿 생성 스크립트 실행 (메인 터미널)
python generate_template_from_toc.py
```

---

### 3단계: 결과 확인

스크립트가 다음 파일들을 생성합니다:

```
✅ toc_cleaned_full.txt        - 정제된 목차 텍스트
✅ toc_lectures_full.json      - 추출된 강의 목록 (페이지 범위 포함)
✅ template_generated.json     - 생성된 템플릿 (바로 사용 가능)
```

**강의 목록 예시 (toc_lectures_full.json):**
```json
[
  {
    "lecture_id": 1,
    "title": "시의 표현과 형식",
    "start_page": 9,
    "end_page": 11
  },
  {
    "lecture_id": 2,
    "title": "시의 내용",
    "start_page": 12,
    "end_page": 14
  },
  ...
]
```

---

## 📋 생성된 템플릿 구조

`template_generated.json`은 다음 정보를 포함합니다:

### 1. 메타데이터
```json
{
  "name": "ebs_수능특강_literature_2026",
  "subject": "literature",
  "version": "2026",
  "description": "EBS 수능특강 문학 2026"
}
```

### 2. 패턴 (자동 생성)
```json
{
  "patterns": {
    "toc_lecture_patterns": [
      "^\\d+강",
      "^\\d+강\\s*[|:]",
      "^\\d+강\\s+[가-힣]"
    ],
    "problem_number_pattern": "^\\d{2}$",
    ...
  }
}
```

### 3. 설정 (강의별 페이지 범위 포함)
```json
{
  "config": {
    "unit_order": ["concept", "passage", "problem"],
    "toc_lecture_list": [
      {
        "lecture_id": 1,
        "title": "시의 표현과 형식",
        "start_page": 9,
        "end_page": 11
      },
      ...
    ],
    "lecture_page_ranges": {
      "1": {"start": 9, "end": 11},
      "2": {"start": 12, "end": 14},
      ...
    }
  }
}
```

---

## 🔧 템플릿 저장 방법

### 방법 1: 스크립트 자동 저장 (권장)

`generate_template_from_toc.py` 수정:
```python
template_request = {
    ...
    'save': True,  # False → True로 변경
    ...
}
```

다시 실행:
```bash
python generate_template_from_toc.py
```

### 방법 2: 웹 UI 사용

1. 브라우저에서 `http://localhost:3000` 접속
2. **관리자 페이지** → **Template Wizard** 이동
3. `template_generated.json` 파일 업로드
4. 검토 후 **"저장"** 버튼 클릭

### 방법 3: API 직접 호출

```python
import requests

with open('template_generated.json', 'r', encoding='utf-8') as f:
    template = json.load(f)

response = requests.post(
    'http://localhost:8000/api/v1/templates',
    json=template
)

print(response.json())
```

---

## 📊 프롬프트 커스터마이징

`generate_template_from_toc.py`의 `custom_prompt` 수정:

```python
custom_prompt = """정제 규칙:
1. 특수 문자 제거
2. 단어 병합

3. 강의 단위 인식:
   - "N강 제목" 형식
   - 3자리 페이지 번호(009, 012, 015)로 구분
   
4. 추가 규칙:
   - 작품명은 괄호로 감싸기
   - 작가명은 작품명 뒤에 배치
   - ...
"""
```

---

## ❓ FAQ

### Q1: OCR 텍스트가 너무 지저분한데 괜찮나요?
A: 네! 시스템이 자동으로 정제합니다. `(cid:xxx)` 같은 오류도 제거됩니다.

### Q2: 페이지 번호가 일부만 추출되면 어떻게 하나요?
A: `toc_lectures_full.json`을 열어서 수동으로 `start_page`, `end_page`를 추가하면 됩니다.

### Q3: 강의 제목이 이상하게 병합되면?
A: `toc_cleaned_full.txt`를 수동으로 수정하고, 3단계(강의 목록 추출)부터 다시 실행하세요.

### Q4: 템플릿 생성 시 OpenAI API 오류가 나면?
A: `backend/.env` 파일에 `OPENAI_API_KEY`가 설정되어 있는지 확인하세요.

---

## 🎓 완전 자동화 예시

전체 프로세스를 한 번에:

```bash
# 1. 목차 텍스트 준비 (수동)
# toc_full.txt에 붙여넣기

# 2. 템플릿 생성 및 저장 (자동)
python generate_template_from_toc.py

# 3. 결과 확인
cat template_generated.json

# 4. 템플릿 사용 (PDF 파싱)
# 웹 UI에서 PDF 업로드 → 템플릿 선택 → 파싱 시작
```

---

## 📚 관련 문서

- `docs/root/MASTER_PROMPT_generate_parsing_template_from_toc_v1.md` - 마스터 프롬프트
- `docs/root/PARSING_TEMPLATE_SCHEMA_V1.md` - 템플릿 스키마
- `backend/app/routers/templates.py` - 템플릿 API 소스코드

---

## 🙋 도움이 필요하신가요?

1. **목차 정제 테스트**: `test_clean_toc.py` 실행
2. **강의 추출 테스트**: `POST /api/v1/templates/parse-toc-lectures`
3. **템플릿 검증**: `POST /api/v1/templates/{subject}/{name}/test`

문의사항이 있으시면 이슈를 등록해주세요!
