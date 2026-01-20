# 리팩토링 완료

## 새로운 아키텍처

### 핵심 원칙
1. **PDF만 존재, 강의 대본 없음**
2. **교재 원문이 유일한 Source of Truth**
3. **JSON 중심 설계**
4. **단일 파이프라인, config.json으로 과목 분기**
5. **규칙 기반 문서 파싱 (OCR + y좌표)**

### 폴더 구조

```
data/
 ├─ literature/
 │   ├─ pdf/          (PDF 파일)
 │   ├─ pages/        (페이지 이미지)
 │   ├─ lectures/     (강의 JSON)
 │   │   ├─ lectures.json
 │   │   └─ lecture_XX.json
 │   ├─ problems/     (문제 JSON)
 │   │   └─ problem_XX.json
 │   └─ config.json   (과목별 설정)
 ├─ math1/
 └─ english/
```

### 핵심 파일

1. **api/app/services/textbook_pipeline.py**
   - 단일 파이프라인 클래스
   - config.json 기반 과목 분기
   - PDF → OCR → JSON 자동 생성

2. **api/app/services/tts_reader.py**
   - JSON의 content를 그대로 읽기
   - 요약/재작성 금지

3. **api/app/services/ai_lecture_generator.py**
   - LLM 기반 설명 생성
   - 교재 원문 보존 원칙 준수

4. **api/scripts/run_textbook_pipeline.py**
   - 실행 스크립트

### 삭제된 파일

#### 강의 대본 기반 (삭제)
- lecture_script_parser.py
- curriculum_generator.py
- auto_curriculum_pipeline.py
- auto_tagger.py
- hwp_extract.py
- lecture_lesson_splitter.py
- script_editor.py
- pdf_script_matcher.py

#### 기존 파이프라인 (삭제)
- pdf_only_pipeline.py
- pdf_auto_pipeline.py

#### 기타 불필요한 파일 (삭제)
- curriculum_template.py
- pdf_structure_parser.py
- pdf_to_units_converter.py
- ai_lecture_teacher.py
- subject_strategies/ (전체 폴더)
- pdf_parse/ (전체 폴더)

### 사용법

```bash
python api/scripts/run_textbook_pipeline.py
```

과목을 선택하면 자동으로:
1. PDF → 페이지 이미지 변환
2. OCR 수행
3. 강의 목록 생성
4. 강의 콘텐츠 추출
5. 문제 추출
6. JSON 저장

### JSON 출력 규격

1. **lectures.json**: 강의 목록
   ```json
   [
     {"lecture_id": 1, "title": "시의 표현과 형식"}
   ]
   ```

2. **lecture_XX.json**: 강의 콘텐츠
   ```json
   {
     "subject": "literature",
     "lecture_id": 1,
     "title": "시의 표현과 형식",
     "sections": [
       {
         "title": "시적 표현",
         "content": ["문단1", "문단2"]
       }
     ]
   }
   ```

3. **problem_XX.json**: 문제
   ```json
   {
     "problem_id": "01",
     "page": 12,
     "content": ["지문1", "지문2"]
   }
   ```
