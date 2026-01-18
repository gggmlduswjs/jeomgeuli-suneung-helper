# AI/ML 기능 구현 제안서

이 문서는 점글이 수능 헬퍼 프로젝트에 머신러닝, 딥러닝, 생성형 AI 기능을 추가하기 위한 구체적인 제안을 담고 있습니다.

## 📊 현재 상태 분석

### 사용자 분석 (인터뷰 기반)

#### 사용자 규모
- **전체 고3 시각장애 학생**: 약 63명
- **수능 준비 학생**: 9명 (올해), 5명 (작년)
- **인강 활용 학생**: 4명 (인터뷰 참여)
- **타겟 사용자**: 예비고 학생들 (학습 방법 탐색 단계)

#### 사용자 유형

**유형 1: 음성 중심 학습자**
- 목적: 학교에서 배운 내용 복습
- 학습 방식: 강의를 한 번에 쭉 들으며 음성 설명 위주로 보충
- 특징: 인강의 음성만을 학습 수단으로 인식

**유형 2: 전체 활용 학습자**
- 목적: 수능 대비 새로운 내용 학습
- 학습 방식: 
  - PC로 강의 재생
  - 놓친 내용이나 모르는 내용이 있을 때 앞뒤로 돌려가며 반복
  - 강의를 멈춰 놓고 교재를 보면서 수업
- 특징: 인강 전체를 학습 수단으로 인식
- **타겟**: 이 유형의 학생들을 위한 솔루션 개발

#### 학습 패턴 분석
1. **강의 탐색**: 앞뒤로 왔다 갔다 하며 필요한 내용 탐색
2. **교재 활용 시점**:
   - 점역된 교재가 있는 경우: 미리 확인하거나 끝나고 복습용
   - 강의 중 필요시: 실시간으로 자료 참고
3. **텍스트 자료 활용**: 강의 중에 실시간으로 들으면서 정보 보충

#### 사용자 피드백 (개발 과정)

**텍스트 작성 분량**:
- ❌ 처음: 전체 지문을 한 번에 제공
- ✅ 개선: 말하는 단위로 끊어서 제공
- 이유: 점자 읽는 속도 고려, 검색 및 위치 찾기 어려움

**정보 제공 순서**:
- ❌ 처음: 시간 정보를 앞에 배치
- ✅ 개선: 유형 정보를 앞에, 시간 정보는 뒤로
- 이유: 시간 정보 확인 시 화면 검색 기능 사용으로 강의가 끊김

**기존 규칙과의 충돌**:
- ❌ 처음: 원숫자(①②③)를 그대로 사용
- ✅ 개선: 원숫자는 문제 선지용으로 인식되므로 다른 기호 사용
- 이유: 시각장애 학생들에게 원숫자는 문제 선지로 인식됨

**동기화 문제**:
- 문제: 강의 진행 위치와 텍스트 읽는 위치가 다름
- 해결: 알림음(띵동)으로 동기화
- 효과: 시간 정보보다 훨씬 낮고 찾기가 편함

#### 사용자 확대를 위한 고려사항

**고3 학생들의 한계**:
- 수능 준비로 시간 부족
- 새로운 방법 학습에 대한 부담 (학습 효과가 떨어지는 적응 기간)
- 기존 방법 대체의 어려움

**예비고 학생들의 특성**:
- 학습 방법 탐색 단계
- 새로운 방법 시도에 대한 부담이 적음
- 보호자와 함께 강의 화면 보충 설명을 듣는 경우 많음

**학습자 유형 (3가지)**:
1. 주도적 탐색형: 스스로 학습 자료를 찾고 사용법 터득
2. 제공 시도형: 자료가 주어지면 사용해 보려고 시도
3. 외부 도움 필요형: 자료가 주어져도 사용하기까지 외부 도움이 적극적으로 필요

#### 제작 프로세스 현황
- **초기**: 1인 제작 (매뉴얼 개발)
- **현재**: 다수 제작자 + 검수자 시스템
- **운영 방식**: 자원봉사 프로그램
- **제작자 모집**: 사회봉사 관심자, 대체자료 경험자
- **과제**: 제작 시간 단축, 품질 관리, 교육 효율화

---

### 앱 구조 및 기능
- **메인 화면**: 오늘 학습 이어하기, 과목 선택, 교재 관리(PDF 업로드), 점자 디바이스 연결
- **학습 화면**: 교재 목록 → 단원 목록 → 강의 내용
- **강의 구조**: 
  - 00강 오리엔테이션
  - 01강~43강: 교과서 개념, 고전 시가, 현대시, 고전 산문, 현대 소설, 극/수필, 갈래 복합, 실전 문제
- **강의 내용**: 개념 설명 → 핵심 포인트 → 문제 풀이 → 복습
- **데이터 소스**: 한글 파일(강의 대본) + PDF 파일(수능특강 교재)

### 현재 구현 방식
- **점자 변환**: 규칙 기반 매핑 테이블 (`ko_braille.json`)
- **음성 인식**: Google Streaming Provider (외부 API)
- **음성 합성**: Web Speech API (브라우저 내장)
- **PDF 파싱**: 정규표현식 기반 규칙 파싱
- **한글 파일 처리**: 미구현 (추가 필요)

### 개선 필요 영역

#### 사용자 관점
1. **한글 파일 처리**: 강의 대본을 직접 처리하여 학습 콘텐츠로 활용
2. **점자 변환 개선**: 문맥을 이해하는 점자 변환 (개념 설명, 문제 해설 등)
3. **학습자 맞춤형 추천**: 강의 순서(00강→01강→...) 및 오답 패턴 기반 추천
4. **생성형 AI 콘텐츠**: 문제 해설 자동 생성, 핵심 포인트 요약
5. **복습 시스템 개선**: 틀린 문제 분석 및 맞춤형 복습 추천
6. **동기화 개선**: 강의 음성과 텍스트 동기화 (알림음 기반 → AI 기반 자동 동기화)

#### 제작자 관점 (중요)
7. **제작 프로세스 자동화**: 
   - 한글 파일 → 구조화된 텍스트 자동 변환
   - 매뉴얼 기반 자동 검수
   - 제작 시간 단축 (현재 수동 제작 → AI 보조 제작)
8. **품질 관리 자동화**:
   - 텍스트 분량 자동 조절 (말하는 단위로 끊기)
   - 기호 사용 규칙 자동 검증
   - 정보 제공 순서 자동 최적화
9. **교육 효율화**:
   - 제작자 온보딩 자동화
   - 실시간 피드백 시스템

---

## 👥 사용자 연구 결과 요약

### 연구 개요
- **인터뷰 대상**: 시각장애 고3 학생 4명 (인강 활용 학생)
- **전체 규모**: 고3 시각장애 학생 63명 중 수능 준비생 9명
- **연구 목적**: 실제 사용 패턴 파악 및 솔루션 설계

### 핵심 발견사항

#### 1. 사용자 유형
- **유형 1 (음성 중심)**: 학교 복습용, 강의를 쭉 들으며 음성만 활용
- **유형 2 (전체 활용)**: 수능 대비, PC로 강의 재생하며 앞뒤로 탐색, 교재 참고
- **타겟**: 유형 2 학생들을 위한 솔루션 개발

#### 2. 학습 패턴
- 강의 앞뒤로 탐색하며 필요한 내용 찾기
- 점역된 교재는 미리 확인하거나 복습용
- 강의 중 필요시 실시간으로 자료 참고

#### 3. 개발 과정에서의 개선사항
- **텍스트 분량**: 말하는 단위로 끊어서 제공 (너무 길면 점자 읽는 속도 문제)
- **정보 순서**: 유형 정보 먼저, 시간 정보는 뒤로 (시간 확인 시 강의 끊김)
- **기호 사용**: 원숫자(①②③)는 문제 선지용으로 인식 → 설명에는 다른 기호 사용
- **동기화**: 알림음(띵동)으로 강의 위치와 텍스트 동기화

#### 4. 사용자 확대 과제
- **고3 학생**: 수능 준비로 시간 부족, 새로운 방법 학습 부담
- **예비고 학생**: 학습 방법 탐색 단계 → 타겟으로 적합
- **학습자 유형**: 주도적 탐색형, 제공 시도형, 외부 도움 필요형

#### 5. 제작 프로세스 현황
- **초기**: 1인 수동 제작 (시간 소요)
- **현재**: 다수 제작자 + 검수자 시스템
- **운영**: 자원봉사 프로그램
- **과제**: 제작 시간 단축, 품질 관리, 교육 효율화

### AI/ML 적용 전략

#### 사용자 관점
- 소규모 사용자(9명) → 개인화 중심 접근
- 동기화 문제 해결 → AI 기반 자동 동기화
- 맞춤형 추천 → 규칙 기반 + 콘텐츠 기반 (협업 필터링 부적합)

#### 제작자 관점
- 제작 시간 단축 → AI 보조 자동화
- 품질 관리 → 매뉴얼 규칙 자동 검증
- 교육 효율화 → 온보딩 자동화

---

## 🎯 제안 기능 및 구현 방안

### Phase 1: 기초 AI/ML 인프라 구축 (우선순위: 높음)

#### 1.1 점자 변환 개선 - 문맥 인식 모델

**목표**: 규칙 기반 변환의 한계를 극복하여 문맥을 이해하는 점자 변환

**기술 스택**:
- **모델**: KoBERT 또는 KoGPT 기반 fine-tuning
- **프레임워크**: PyTorch, Transformers (Hugging Face)
- **데이터**: 한국어-점자 병렬 코퍼스 구축
  - **데이터 소스**: 한글 파일(강의 대본) + PDF 파일(수능특강 교재)
  - **예상 데이터 규모**: 약 585,000자 (한글 파일 85,000자 + PDF 500,000자)

**구현 방안**:
```python
# api/app/services/braille_ml.py
from transformers import AutoTokenizer, AutoModelForSeq2Seq
import torch

class BrailleMLConverter:
    def __init__(self):
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.tokenizer = AutoTokenizer.from_pretrained('skt/kobert-base-v1')
        self.model = AutoModelForSeq2Seq.from_pretrained('./models/braille-converter')
        self.model.to(self.device)
        self.model.eval()
    
    def convert_with_context(self, text: str, context: str = None) -> str:
        """문맥을 고려한 점자 변환"""
        # 문맥 정보를 포함한 입력 생성
        input_text = f"{context} [SEP] {text}" if context else text
        # 모델 추론
        # ...
```

**예상 효과**:
- 동음이의어 처리 개선 (예: "시험" vs "시험")
- 문맥에 따른 약자 선택 최적화
- 정확도 향상 (현재 85% → 목표 95%+)

**구현 난이도**: ⭐⭐⭐ (중간)
**예상 기간**: 2-3개월

---

#### 1.2 학습자 맞춤형 추천 시스템

**목표**: 사용자의 학습 패턴을 분석하여 맞춤형 학습 콘텐츠 추천

**앱 통합 시나리오**:
- **메인 화면 "오늘 학습 이어하기"**: 마지막 학습 위치 + 추천 다음 강의
- **단원 목록**: 사용자 수준에 맞는 강의 순서 추천
- **복습 추천**: 틀린 문제 기반 복습 강의 추천

**기술 스택**:
- **알고리즘**: 협업 필터링 + 콘텐츠 기반 필터링 + 강의 순서 기반 추천
- **프레임워크**: scikit-learn, pandas
- **추가**: 사용자 행동 데이터 수집 및 분석

**구현 방안**:
```python
# api/app/services/recommendation.py
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import pandas as pd

class LearningRecommendationEngine:
    def __init__(self):
        self.vectorizer = TfidfVectorizer()
        self.user_profiles = {}  # 사용자별 학습 프로필
        # 강의 순서 정보 (한글 파일에서 추출)
        self.lesson_sequence = {
            "문학": [
                "00강 오리엔테이션",
                "01강_[교과서_개념]_1_2_(고3_기본)",
                "02강_[교과서_개념]_3_4_(고3_기본)",
                # ... 43강까지
            ]
        }
    
    def build_user_profile(self, user_id: str, learning_history: List[dict]):
        """사용자 학습 프로필 구축"""
        # 오답 패턴 분석 (문제 1번, 2번, 3번 등)
        # 학습 시간대 분석
        # 선호 과목/단원 분석
        # 강의 완료 순서 분석
        # ...
    
    def recommend_next_lesson(self, user_id: str, current_lesson: str) -> str:
        """다음 강의 추천 (강의 순서 기반)"""
        # 1. 강의 순서에서 다음 강의 찾기
        # 2. 사용자 수준에 맞는 난이도 조정
        # 3. 오답 패턴 기반 보완 강의 추천
        # ...
    
    def recommend_review_lessons(self, user_id: str, wrong_questions: List[dict]) -> List[str]:
        """틀린 문제 기반 복습 강의 추천"""
        # 틀린 문제의 주제 분석
        # 관련 강의 찾기 (예: 고전 시가 문제 틀림 → 고전 시가 강의 추천)
        # ...
    
    def recommend_units(self, user_id: str, n: int = 5) -> List[str]:
        """맞춤형 단원 추천 (소규모 사용자 최적화)"""
        # 소규모 사용자 특성 고려:
        # 1. 콘텐츠 기반 필터링 중심 (사용자 간 유사도 대신 콘텐츠 유사도)
        # 2. 강의 순서 기반 추천 (00강→01강→...)
        # 3. 개인 학습 패턴 분석 (오답 패턴, 학습 시간대 등)
        # 4. 규칙 기반 추천 (매뉴얼 기반)
        
        user_profile = self.user_profiles.get(user_id, {})
        
        # 1. 강의 순서 기반 (가장 기본)
        next_lesson = self.get_next_lesson_by_sequence(user_profile.get("last_lesson"))
        
        # 2. 오답 패턴 기반 보완 강의
        wrong_pattern = user_profile.get("wrong_pattern", {})
        complementary_lessons = self.get_complementary_lessons(wrong_pattern)
        
        # 3. 학습 시간대 고려
        preferred_time = user_profile.get("preferred_time", "any")
        time_optimized = self.filter_by_time(complementary_lessons, preferred_time)
        
        return time_optimized[:n]
```

**데이터 수집 항목**:
- 오답 패턴 및 빈도 (문제 1번, 2번, 3번 등)
- 학습 시간대 및 지속 시간
- 단원별 완료율 (00강~43강)
- 복습 빈도
- 강의 순서 정보 (한글 파일에서 추출: 00강 → 01강 → ... → 43강)
- 주제별 분류 (교과서 개념, 고전 시가, 현대시, 고전 산문, 현대 소설, 극/수필, 갈래 복합, 실전)
- 난이도 정보 (고3_기본)

**앱 통합 예시**:
```typescript
// apps/web/src/services/recommendation.ts
export async function getRecommendedNextLesson(
  userId: string,
  currentLesson: string
): Promise<string> {
  // API 호출하여 다음 강의 추천 받기
  const response = await api.post('/recommendations/next-lesson', {
    user_id: userId,
    current_lesson: currentLesson
  });
  return response.data.recommended_lesson;
}

// 메인 화면에서 사용
// "오늘 학습 이어하기" 버튼 클릭 시
const nextLesson = await getRecommendedNextLesson(userId, lastLesson);
navigate(`/learning/${nextLesson}`);
```

**예상 효과**:
- 학습 효율성 20-30% 향상
- 사용자 만족도 증가
- 학습 이탈률 감소
- 강의 순서 준수율 증가

**구현 난이도**: ⭐⭐ (낮음-중간)
**예상 기간**: 1-2개월

---

### Phase 2: 고급 AI 기능 (우선순위: 중간)

#### 2.1 생성형 AI를 활용한 학습 콘텐츠 생성 및 제작 자동화

**이중 목표**:
1. **학습자용**: 문제 해설, 요약 등 실시간 생성
2. **제작자용**: 강의 대본 자동 제작 보조

**목표**: LLM을 활용하여 문제 해설, 요약, 추가 문제 생성

**기술 스택**:
- **모델**: GPT-4, Claude, 또는 오픈소스 LLM (Llama 2, Mistral)
- **프레임워크**: LangChain, OpenAI API 또는 Ollama (로컬)
- **프롬프트 엔지니어링**: 체인 오브 사고, Few-shot learning

**구현 방안**:
```python
# api/app/services/content_generator.py
from langchain.llms import OpenAI
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain

class LearningContentGenerator:
    def __init__(self):
        self.llm = OpenAI(temperature=0.7)
        self.explanation_prompt = PromptTemplate(
            input_variables=["question", "answer"],
            template="""
            다음 수능 문제에 대한 상세한 해설을 작성해주세요.
            점자 학습자를 위해 명확하고 단계별로 설명해주세요.
            
            문제: {question}
            정답: {answer}
            
            해설:
            """
        )
    
    def generate_explanation(self, question: str, answer: str) -> str:
        """문제 해설 자동 생성"""
        chain = LLMChain(llm=self.llm, prompt=self.explanation_prompt)
        return chain.run(question=question, answer=answer)
    
    def generate_summary(self, passage: str) -> str:
        """지문 요약 생성"""
        # ...
    
    def generate_practice_questions(self, topic: str, difficulty: str) -> List[dict]:
        """추가 연습 문제 생성"""
        # ...
    
    def generate_lecture_script(self, raw_text: str, lesson_info: dict) -> dict:
        """강의 대본 자동 생성 (제작자용)
        
        한글 파일의 원본 텍스트를 매뉴얼 규칙에 맞게 자동 변환
        """
        # 1. 말하는 단위로 분할
        units = self.split_by_speech_unit(raw_text)
        
        # 2. 각 단위를 매뉴얼 규칙에 맞게 변환
        structured_script = []
        for unit in units:
            section_type = self.detect_section_type(unit)
            converted = {
                "type": section_type,
                "content": self.format_by_manual(unit, section_type),
                "symbol": self.get_appropriate_symbol(section_type),
                "braille": text_to_braille(unit)
            }
            structured_script.append(converted)
        
        # 3. 검증 및 피드백
        validation = self.validate_manual_compliance(structured_script)
        
        return {
            "script": structured_script,
            "validation": validation,
            "suggestions": self.generate_improvement_suggestions(validation)
        }
    
    def format_by_manual(self, text: str, section_type: str) -> str:
        """매뉴얼 규칙에 맞게 텍스트 포맷팅"""
        # - 원숫자 제거 (설명 섹션에서)
        # - 적절한 기호 추가
        # - 정보 순서 조정
        # ...
        pass
```

**활용 시나리오** (앱 기능 통합):
1. **문제 해설 생성**: 
   - 문제 1번, 2번, 3번 틀렸을 때 → "기출 탈탈 털어 쏙쏙 뽑아" 섹션에 자동 해설 생성
   - "틀린 문제 복습하기" 화면에서 상세 해설 제공
   
2. **핵심 포인트 요약**:
   - "꼭 집어 핵심 포인트" 섹션에 개념 설명을 요약하여 제공
   - 점자 학습에 적합한 길이로 자동 요약
   
3. **개념 설명 보강**:
   - "개념 설명 -> 시의 표현과 형식" 같은 섹션에 추가 설명 생성
   - 사용자 질문에 대한 답변 생성
   
4. **복습 콘텐츠 생성**:
   - 틀린 문제 유형에 맞는 추가 연습 문제 생성
   - 관련 개념 설명 자동 생성

**앱 통합 예시**:
```typescript
// apps/web/src/pages/Question/Question.tsx
// 문제를 틀렸을 때
const handleWrongAnswer = async (questionId: string, userAnswer: string) => {
  // 생성형 AI로 해설 생성
  const explanation = await generateExplanation(questionId, userAnswer);
  
  // "틀린 문제 복습하기" 화면으로 이동
  navigate('/review', { 
    state: { 
      questionId, 
      explanation,
      wrongAnswer: userAnswer 
    } 
  });
};
```

**비용 고려사항**:
- OpenAI API: 사용량 기반 과금
- 오픈소스 LLM (Ollama): 로컬 실행, 무료이지만 성능 제한

**구현 난이도**: ⭐⭐⭐ (중간)
**예상 기간**: 1-2개월

---

#### 2.2 이미지/그래프 점자 변환 개선 - OCR + ML

**목표**: 그래프, 도표, 수식 이미지를 점자로 정확하게 변환

**기술 스택**:
- **OCR**: Tesseract, EasyOCR, 또는 PaddleOCR
- **이미지 분류**: CNN (ResNet, EfficientNet)
- **수식 인식**: MathPix API 또는 LaTeX 변환
- **프레임워크**: PyTorch, OpenCV

**구현 방안**:
```python
# api/app/services/image_to_braille.py
import cv2
import torch
from transformers import TrOCRProcessor, VisionEncoderDecoderModel
from PIL import Image

class ImageToBrailleConverter:
    def __init__(self):
        # OCR 모델 로드
        self.processor = TrOCRProcessor.from_pretrained('microsoft/trocr-base-printed')
        self.ocr_model = VisionEncoderDecoderModel.from_pretrained('microsoft/trocr-base-printed')
        
        # 그래프 분류 모델
        self.graph_classifier = torch.load('./models/graph_classifier.pth')
    
    def convert_image(self, image_path: str) -> dict:
        """이미지를 점자로 변환"""
        image = Image.open(image_path)
        
        # 1. 이미지 타입 분류 (그래프, 도표, 수식, 텍스트)
        image_type = self.classify_image(image)
        
        # 2. 타입별 처리
        if image_type == 'graph':
            return self.convert_graph(image)
        elif image_type == 'table':
            return self.convert_table(image)
        elif image_type == 'formula':
            return self.convert_formula(image)
        else:
            return self.convert_text_image(image)
    
    def convert_graph(self, image: Image) -> dict:
        """그래프를 점자 패턴으로 변환"""
        # 그래프 요소 추출 (축, 데이터 포인트, 범례)
        # 점자 패턴 생성
        # ...
```

**예상 효과**:
- 그래프/도표 접근성 향상
- 수식 점자 변환 정확도 개선
- 이미지 기반 문제 해결 능력 향상

**구현 난이도**: ⭐⭐⭐⭐ (높음)
**예상 기간**: 3-4개월

---

### Phase 2.5: 동기화 개선 (우선순위: 높음)

#### 2.3 강의 음성-텍스트 자동 동기화

**목표**: 알림음 기반 수동 동기화를 AI 기반 자동 동기화로 개선

**현재 방식**:
- 알림음(띵동)으로 수동 동기화
- 사용자가 직접 위치 찾기

**AI 개선 방안**:
```python
# api/app/services/audio_sync.py
"""
강의 음성과 텍스트 자동 동기화
"""
import speech_recognition as sr
from pydub import AudioSegment

class AudioTextSync:
    def __init__(self):
        self.recognizer = sr.Recognizer()
    
    def sync_audio_to_text(self, audio_path: str, text_sections: List[Dict]) -> List[Dict]:
        """음성 파일과 텍스트 섹션을 자동 동기화"""
        # 1. 음성을 텍스트로 변환 (STT)
        audio_text = self.transcribe_audio(audio_path)
        
        # 2. 텍스트 매칭 (원본 텍스트와 STT 결과 매칭)
        synced_sections = []
        for section in text_sections:
            # 원본 텍스트와 음성 텍스트를 비교하여 시간 위치 찾기
            timestamp = self.find_timestamp(section["content"], audio_text)
            section["timestamp"] = timestamp
            synced_sections.append(section)
        
        return synced_sections
    
    def find_timestamp(self, text: str, audio_transcript: List[Dict]) -> float:
        """텍스트가 음성의 어느 시점에 나오는지 찾기"""
        # 문자열 유사도 기반 매칭
        # 또는 키워드 기반 매칭
        # ...
        pass
```

**앱 통합**:
```typescript
// apps/web/src/hooks/useAudioSync.ts
export function useAudioSync(lessonId: string) {
  const [currentSection, setCurrentSection] = useState(0);
  
  useEffect(() => {
    // 강의 재생 위치 감지
    const audio = document.querySelector('audio');
    if (!audio) return;
    
    // 재생 시간에 따라 해당 텍스트 섹션으로 자동 스크롤
    const handleTimeUpdate = () => {
      const currentTime = audio.currentTime;
      const section = findSectionByTime(currentTime);
      setCurrentSection(section);
      // 점자 디바이스에 해당 섹션 전송
    };
    
    audio.addEventListener('timeupdate', handleTimeUpdate);
    return () => audio.removeEventListener('timeupdate', handleTimeUpdate);
  }, [lessonId]);
}
```

**예상 효과**:
- 수동 동기화 불편 해소
- 실시간 자동 동기화
- 학습 집중도 향상

**구현 난이도**: ⭐⭐⭐⭐ (높음)
**예상 기간**: 3-4주

---

### Phase 3: 고급 딥러닝 기능 (우선순위: 낮음-중간)

#### 3.1 한국어 음성 인식 개선 - 자체 모델

**목표**: 오프라인 지원 및 한국어 특화 음성 인식

**기술 스택**:
- **모델**: Whisper (OpenAI) fine-tuning 또는 Wav2Vec 2.0
- **프레임워크**: PyTorch, Transformers
- **데이터**: 한국어 음성 데이터셋 (KsponSpeech, AI Hub)

**구현 방안**:
```python
# api/app/services/korean_stt.py
import whisper
import torch

class KoreanSTTModel:
    def __init__(self):
        # Whisper 모델 로드 (한국어 fine-tuned)
        self.model = whisper.load_model("base", device="cuda" if torch.cuda.is_available() else "cpu")
    
    def transcribe(self, audio_path: str) -> str:
        """음성을 텍스트로 변환"""
        result = self.model.transcribe(
            audio_path,
            language="ko",
            task="transcribe"
        )
        return result["text"]
```

**장점**:
- 오프라인 지원
- 개인정보 보호 (로컬 처리)
- 커스터마이징 가능

**단점**:
- 초기 구축 비용 높음
- 서버 리소스 필요

**구현 난이도**: ⭐⭐⭐⭐ (높음)
**예상 기간**: 3-4개월

---

#### 3.2 학습 패턴 예측 및 적응형 학습

**목표**: 사용자의 학습 패턴을 예측하여 최적의 학습 경로 제시

**기술 스택**:
- **모델**: LSTM, Transformer 기반 시계열 예측
- **프레임워크**: PyTorch, scikit-learn
- **알고리즘**: 강화학습 (선택적)

**구현 방안**:
```python
# api/app/services/adaptive_learning.py
import torch
import torch.nn as nn

class LearningPatternPredictor(nn.Module):
    """학습 패턴 예측 모델"""
    def __init__(self, input_size, hidden_size, num_layers):
        super().__init__()
        self.lstm = nn.LSTM(input_size, hidden_size, num_layers, batch_first=True)
        self.fc = nn.Linear(hidden_size, 1)  # 다음 단원 난이도 예측
    
    def forward(self, x):
        # 학습 이력 시계열 데이터 입력
        lstm_out, _ = self.lstm(x)
        prediction = self.fc(lstm_out[:, -1, :])
        return prediction

class AdaptiveLearningEngine:
    def __init__(self):
        self.predictor = LearningPatternPredictor(...)
        self.predictor.load_state_dict(torch.load('./models/learning_predictor.pth'))
    
    def recommend_next_unit(self, user_id: str, current_progress: dict) -> dict:
        """적응형 학습 경로 추천"""
        # 사용자 학습 패턴 분석
        # 다음 단원 난이도 예측
        # 최적 학습 경로 계산
        # ...
```

**예상 효과**:
- 학습 효율성 30-40% 향상
- 개인화된 학습 경험
- 학습 목표 달성률 증가

**구현 난이도**: ⭐⭐⭐⭐⭐ (매우 높음)
**예상 기간**: 4-6개월

---

## 📋 구현 로드맵

### 단기 (3-6개월)
1. ✅ **기초 인프라 구축**
   - ML 모델 서빙 환경 구축 (Docker, GPU 지원)
   - 데이터 수집 파이프라인 구축
   - 모델 버전 관리 시스템

2. ✅ **Phase 1 기능 구현**
   - 점자 변환 ML 모델 (문맥 인식)
   - 학습자 맞춤형 추천 시스템

### 중기 (6-12개월)
3. ✅ **Phase 2 기능 구현**
   - 생성형 AI 콘텐츠 생성
   - 이미지/그래프 점자 변환 개선

4. ✅ **성능 최적화**
   - 모델 경량화 및 추론 속도 개선
   - 캐싱 전략 수립

### 장기 (12개월+)
5. ✅ **Phase 3 기능 구현**
   - 한국어 음성 인식 자체 모델
   - 적응형 학습 시스템

6. ✅ **고급 기능**
   - 멀티모달 학습 (텍스트 + 음성 + 점자)
   - 실시간 학습 피드백 시스템

---

## 🛠 기술 스택 요약

### 필수 라이브러리
```txt
# api/requirements.txt (추가)

# Phase 0: 데이터 처리
pyhwp>=0.1.0  # 한글 파일 파싱 (또는 olefile)
python-docx>=1.0.0  # Word 파일 지원 (선택)

# Phase 0.5: PDF 이미지 캡처
pdf2image>=1.16.0  # PDF를 이미지로 변환
Pillow>=10.0.0  # 이미지 처리
pymupdf>=1.23.0  # PDF 처리 (선택, pdfplumber 대안)

# Phase 1: ML/DL
torch>=2.0.0
transformers>=4.30.0
scikit-learn>=1.3.0
pandas>=2.0.0
numpy>=1.24.0
datasets>=2.14.0  # Hugging Face datasets

# Phase 2: 생성형 AI
langchain>=0.0.200
openai>=1.0.0  # 또는 ollama
tiktoken>=0.5.0  # 토큰 카운팅

# Phase 2: 이미지 처리 (선택)
pillow>=10.0.0
opencv-python>=4.8.0
easyocr>=1.7.0  # OCR

# 인프라
redis>=5.0.0  # 캐싱
celery>=5.3.0  # 비동기 작업 (선택)
```

### 인프라 요구사항
- **GPU**: NVIDIA GPU (CUDA 지원) - 모델 학습 및 추론
- **메모리**: 최소 16GB RAM (모델에 따라 더 필요)
- **스토리지**: 모델 저장용 충분한 디스크 공간
- **컨테이너**: Docker, Kubernetes (선택)

---

## 💰 비용 추정

### 개발 비용
- **Phase 1**: 약 2-3개월 (1명 기준)
- **Phase 2**: 약 1-2개월 (1명 기준)
- **Phase 3**: 약 3-4개월 (1명 기준)

### 운영 비용 (월간)
- **GPU 서버**: $200-500 (AWS/GCP)
- **API 사용량**: $50-200 (OpenAI API 등)
- **스토리지**: $20-50

### 오픈소스 대안
- **LLM**: Ollama (로컬 실행, 무료)
- **STT**: Whisper (오픈소스)
- **모델 호스팅**: Hugging Face Inference API

---

## 🎯 우선순위 추천 (사용자 연구 기반)

### 즉시 시작 추천 (High ROI)

1. **PDF 구조화 추출 및 UI/UX 개선** ⭐⭐⭐⭐ (즉시 필요)
   - **이유**: 사용자가 PDF 콘텐츠를 효과적으로 활용하기 위해 필수
   - **사용자 영향**: 문제/본문을 명확히 구분하여 학습 효율 향상
   - **구현 난이도**: 중간
   - **예상 기간**: 2-3주

2. **제작 프로세스 자동화** ⭐⭐⭐⭐⭐ (최우선)
   - **이유**: 제작 시간 80% 단축, 제작자 확대 가능
   - **사용자 영향**: 더 많은 강의 제공 가능 → 사용자 확대
   - **구현 난이도**: 중간
   - **예상 기간**: 2주

2. **강의 음성-텍스트 자동 동기화** ⭐⭐⭐⭐
   - **이유**: 사용자 피드백에서 가장 큰 불편사항
   - **사용자 영향**: 학습 효율성 대폭 향상
   - **구현 난이도**: 높음
   - **예상 기간**: 3-4주

3. **학습자 맞춤형 추천 시스템** ⭐⭐⭐
   - **특수 고려**: 소규모 사용자 (9명) → 개인화 중심
   - 구현 난이도 낮음
   - 즉시 사용자 경험 개선
   - 데이터 수집과 동시에 진행 가능

4. **생성형 AI 콘텐츠 생성** ⭐⭐⭐
   - **이중 목표**: 학습자용 + 제작자용
   - 구현 난이도 중간
   - 사용자 가치 높음
   - API 기반으로 빠른 프로토타입 가능

### 단계적 구현 추천

5. **점자 변환 ML 모델** ⭐⭐⭐
   - 장기적 가치 높음
   - 데이터 구축 필요
   - **제작자 관점**: 자동 점자 변환으로 제작 시간 단축

6. **이미지/그래프 변환** ⭐⭐⭐⭐
   - 접근성 향상에 중요
   - 구현 복잡도 높음
   - **현재**: 국어 과목은 도표/그래프가 적어 우선순위 낮음

### 사용자 확대를 위한 기능

7. **온보딩 자동화** ⭐⭐⭐
   - **학습자 유형별 맞춤 온보딩**
     - 주도적 탐색형: 자가 학습 가이드 제공
     - 제공 시도형: 단계별 튜토리얼
     - 외부 도움 필요형: 상세 가이드 + 지원 연락처
   - **제작자 교육 자동화**
     - 매뉴얼 기반 자동 교육
     - 실습 과제 자동 검증
   - **웹 접근성 교육 통합**
     - PC/모바일 사용법 통합 교육

8. **실시간 피드백 시스템** ⭐⭐
   - 제작자 피드백 자동화
   - 품질 점수 실시간 표시
   - 개선 제안 자동 생성
   - **정량화된 피드백**: 매주 제작자에게 피드백 제공

---

## 📝 구체적인 구현 계획 (사용자 연구 반영)

### 사용자 특성 반영

#### 소규모 사용자 최적화
- **협업 필터링 대신**: 콘텐츠 기반 + 규칙 기반 추천
- **개인화 중심**: 사용자별 학습 패턴 심층 분석
- **수동 피드백 중요**: 사용자 피드백을 빠르게 반영

#### 제작 프로세스 개선
- **자동화 우선**: 제작 시간 단축이 사용자 확대의 핵심
- **품질 관리**: 매뉴얼 규칙 자동 검증
- **교육 효율화**: 제작자 온보딩 자동화

### Phase 0.5: PDF 구조화 추출 및 UI/UX 개선 (우선순위: 높음) ⭐⭐⭐⭐

#### 0.5.1 PDF 문제/본문 구조화 추출

**목표**: PDF에서 문제, 본문, 선택지를 구조화하여 추출하고 UI/UX로 표시

**현재 문제점**:
- PDF 텍스트만 추출 (구조 정보 손실)
- 문제와 본문 구분 어려움
- 선택지 추출 정확도 낮음
- UI에서 구조화된 표시 어려움

**AI/ML 솔루션**:
```python
# api/app/services/pdf_structure_extract.py
"""
PDF 구조화 추출 서비스
문제, 본문, 선택지 등을 구조화하여 추출
"""
import pdfplumber
import re
from typing import List, Dict, Optional
from pathlib import Path

class PDFStructureExtractor:
    def __init__(self):
        # 문제 패턴 (다양한 형식 지원)
        self.question_patterns = [
            r'문제\s*(\d+)\s*번',  # "문제 1번"
            r'(\d+)\s*번\s*문제',  # "1번 문제"
            r'(\d+)[\.\)]\s*',     # "1.", "1)"
            r'[①-⑤]',              # 원숫자
        ]
        
        # 선택지 패턴
        self.choice_patterns = [
            r'[①-⑤]\s*(.+?)(?=[①-⑤]|$)',  # 원숫자 선택지
            r'\(\d+\)\s*(.+?)(?=\(\d+\)|$)',  # (1), (2) 형식
            r'\d+[\.\)]\s*(.+?)(?=\d+[\.\)]|$)',  # 1., 2) 형식
        ]
        
        # 본문 패턴
        self.passage_patterns = [
            r'\[([^\]]+)\]',  # [작품명]
            r'작품\s*[:：]',
            r'지문\s*[:：]',
        ]
    
    def extract_structured_content(self, pdf_path: Path) -> Dict:
        """PDF에서 구조화된 콘텐츠 추출"""
        structured_content = {
            "lessons": [],
            "passages": [],
            "questions": []
        }
        
        with pdfplumber.open(pdf_path) as pdf:
            for page_num, page in enumerate(pdf.pages, 1):
                # 텍스트 추출
                text = page.extract_text()
                
                # 테이블 추출 (문제/선택지가 표 형식인 경우)
                tables = page.extract_tables()
                
                # 페이지별 구조 분석
                page_structure = self._analyze_page_structure(
                    text, tables, page_num
                )
                
                structured_content["lessons"].extend(
                    page_structure.get("lessons", [])
                )
                structured_content["passages"].extend(
                    page_structure.get("passages", [])
                )
                structured_content["questions"].extend(
                    page_structure.get("questions", [])
                )
        
        return structured_content
    
    def _analyze_page_structure(
        self, 
        text: str, 
        tables: List, 
        page_num: int
    ) -> Dict:
        """페이지 구조 분석"""
        structure = {
            "lessons": [],
            "passages": [],
            "questions": []
        }
        
        # 1. 문제 추출
        questions = self._extract_questions(text, page_num)
        structure["questions"].extend(questions)
        
        # 2. 본문 추출
        passages = self._extract_passages(text, page_num)
        structure["passages"].extend(passages)
        
        # 3. 테이블에서 문제/선택지 추출
        if tables:
            table_questions = self._extract_from_tables(tables, page_num)
            structure["questions"].extend(table_questions)
        
        return structure
    
    def _extract_questions(self, text: str, page_num: int) -> List[Dict]:
        """문제 추출"""
        questions = []
        
        # 문제 번호 찾기
        for pattern in self.question_patterns:
            matches = re.finditer(pattern, text)
            for match in matches:
                question_num = match.group(1) if match.groups() else None
                start_pos = match.end()
                
                # 다음 문제까지 또는 선택지까지 추출
                next_question = re.search(
                    r'문제\s*\d+\s*번|(\d+)[\.\)]\s*', 
                    text[start_pos:]
                )
                end_pos = start_pos + (next_question.start() if next_question else len(text))
                
                question_text = text[start_pos:end_pos].strip()
                
                # 선택지 추출
                choices = self._extract_choices(question_text)
                
                questions.append({
                    "number": question_num,
                    "stem": question_text,
                    "choices": choices,
                    "page": page_num,
                    "position": match.start()
                })
        
        return questions
    
    def _extract_choices(self, text: str) -> List[Dict]:
        """선택지 추출"""
        choices = []
        
        # 원숫자 선택지
        choice_pattern = r'([①-⑤])\s*(.+?)(?=[①-⑤]|정답|해설|$)'
        matches = re.finditer(choice_pattern, text, re.DOTALL)
        
        for match in matches:
            choice_num = match.group(1)
            choice_text = match.group(2).strip()
            choices.append({
                "number": choice_num,
                "text": choice_text
            })
        
        return choices
    
    def _extract_passages(self, text: str, page_num: int) -> List[Dict]:
        """본문 추출"""
        passages = []
        
        for pattern in self.passage_patterns:
            matches = re.finditer(pattern, text)
            for match in matches:
                passage_title = match.group(1) if match.groups() else None
                start_pos = match.end()
                
                # 다음 섹션까지 추출
                next_section = re.search(
                    r'\[|작품|지문|문제', 
                    text[start_pos:]
                )
                end_pos = start_pos + (next_section.start() if next_section else len(text))
                
                passage_text = text[start_pos:end_pos].strip()
                
                passages.append({
                    "title": passage_title,
                    "content": passage_text,
                    "page": page_num,
                    "position": match.start()
                })
        
        return passages
```

**ML 기반 개선 (선택적)**:
```python
# api/app/services/pdf_ml_extract.py
"""
ML 기반 PDF 구조 추출 (향후 개선)
"""
from transformers import AutoTokenizer, AutoModelForTokenClassification
import torch

class MLPDFExtractor:
    def __init__(self):
        # NER 모델로 문제/본문/선택지 자동 인식
        self.model = AutoModelForTokenClassification.from_pretrained(
            'klue/bert-base'
        )
        self.tokenizer = AutoTokenizer.from_pretrained('klue/bert-base')
    
    def extract_with_ml(self, pdf_text: str) -> Dict:
        """ML 모델로 구조 추출"""
        # 토큰화
        tokens = self.tokenizer(pdf_text, return_tensors='pt')
        
        # NER 예측
        outputs = self.model(**tokens)
        predictions = torch.argmax(outputs.logits, dim=-1)
        
        # 라벨 매핑
        labels = ['O', 'B-QUESTION', 'I-QUESTION', 
                  'B-PASSAGE', 'I-PASSAGE',
                  'B-CHOICE', 'I-CHOICE']
        
        # 구조화된 결과 반환
        return self._format_results(tokens, predictions, labels)
```

---

#### 0.5.1.1 PDF 이미지 캡처 기능

**목표**: PDF에서 문제/본문 영역을 이미지로 캡처하여 원본 그대로 표시

**구현 방안**:
```python
# api/app/services/pdf_image_extract.py
"""
PDF 이미지 캡처 서비스
문제/본문 영역을 이미지로 추출
"""
import pdfplumber
from PIL import Image
import io
from pathlib import Path
from typing import List, Dict, Tuple, Optional
import base64

class PDFImageExtractor:
    def __init__(self):
        self.dpi = 150  # 이미지 해상도
        
    def extract_question_images(
        self, 
        pdf_path: Path, 
        question_positions: List[Dict]
    ) -> List[Dict]:
        """문제 영역을 이미지로 추출"""
        images = []
        
        with pdfplumber.open(pdf_path) as pdf:
            for q_pos in question_positions:
                page_num = q_pos["page"]
                bbox = q_pos.get("bbox")  # (x0, y0, x1, y1)
                
                if page_num > len(pdf.pages):
                    continue
                
                page = pdf.pages[page_num - 1]
                
                # PDF 페이지를 이미지로 변환
                page_image = page.to_image(resolution=self.dpi)
                
                # 영역 자르기
                if bbox:
                    cropped = page_image.crop(bbox)
                else:
                    # bbox가 없으면 전체 페이지 또는 자동 감지
                    cropped = self._auto_crop_question(page_image, q_pos)
                
                # 이미지를 base64로 인코딩
                img_bytes = io.BytesIO()
                cropped.save(img_bytes, format='PNG')
                img_base64 = base64.b64encode(img_bytes.getvalue()).decode()
                
                images.append({
                    "question_number": q_pos.get("number"),
                    "image": f"data:image/png;base64,{img_base64}",
                    "page": page_num,
                    "bbox": bbox
                })
        
        return images
    
    def extract_passage_images(
        self,
        pdf_path: Path,
        passage_positions: List[Dict]
    ) -> List[Dict]:
        """본문 영역을 이미지로 추출"""
        images = []
        
        with pdfplumber.open(pdf_path) as pdf:
            for p_pos in passage_positions:
                page_num = p_pos["page"]
                bbox = p_pos.get("bbox")
                
                if page_num > len(pdf.pages):
                    continue
                
                page = pdf.pages[page_num - 1]
                page_image = page.to_image(resolution=self.dpi)
                
                if bbox:
                    cropped = page_image.crop(bbox)
                else:
                    cropped = self._auto_crop_passage(page_image, p_pos)
                
                img_bytes = io.BytesIO()
                cropped.save(img_bytes, format='PNG')
                img_base64 = base64.b64encode(img_bytes.getvalue()).decode()
                
                images.append({
                    "passage_title": p_pos.get("title"),
                    "image": f"data:image/png;base64,{img_base64}",
                    "page": page_num,
                    "bbox": bbox
                })
        
        return images
    
    def _auto_crop_question(self, page_image, question_pos: Dict) -> Image:
        """문제 영역 자동 감지 및 자르기"""
        # OCR 또는 레이아웃 분석으로 문제 영역 감지
        # 또는 텍스트 위치 기반으로 영역 추정
        # 현재는 전체 페이지 반환 (향후 ML 모델로 개선)
        return page_image.original
    
    def _auto_crop_passage(self, page_image, passage_pos: Dict) -> Image:
        """본문 영역 자동 감지 및 자르기"""
        return page_image.original
```

**ML 기반 영역 감지 (향후 개선)**:
```python
# api/app/services/pdf_region_detector.py
"""
ML 기반 PDF 영역 감지
문제/본문 영역을 자동으로 감지
"""
import torch
from transformers import LayoutLMv3Processor, LayoutLMv3ForTokenClassification
from PIL import Image

class PDFRegionDetector:
    def __init__(self):
        self.processor = LayoutLMv3Processor.from_pretrained(
            'microsoft/layoutlmv3-base'
        )
        self.model = LayoutLMv3ForTokenClassification.from_pretrained(
            './models/pdf-region-detector'
        )
    
    def detect_regions(self, pdf_image: Image) -> Dict:
        """PDF 이미지에서 문제/본문 영역 감지"""
        # 이미지 전처리
        encoding = self.processor(
            pdf_image, 
            return_tensors="pt",
            padding="max_length",
            truncation=True
        )
        
        # 모델 예측
        with torch.no_grad():
            outputs = self.model(**encoding)
            predictions = torch.argmax(outputs.logits, dim=-1)
        
        # 영역 추출
        regions = self._extract_regions(encoding, predictions)
        
        return {
            "questions": regions.get("question", []),
            "passages": regions.get("passage", []),
            "choices": regions.get("choice", [])
        }
```

**API 엔드포인트**:
```python
# api/app/routers/pdf.py
@router.post("/pdf/extract-images")
async def extract_pdf_images(
    file: UploadFile = File(...),
    extract_type: str = "both",  # "questions", "passages", "both"
    db: Session = Depends(get_db),
):
    """PDF에서 문제/본문 이미지 추출"""
    extractor = PDFImageExtractor()
    structure_extractor = PDFStructureExtractor()
    
    # 임시 파일 저장
    temp_path = save_temp_file(file)
    
    # 구조화된 콘텐츠 추출 (위치 정보 포함)
    structured = structure_extractor.extract_structured_content(temp_path)
    
    images = []
    
    if extract_type in ["questions", "both"]:
        question_images = extractor.extract_question_images(
            temp_path,
            structured["questions"]
        )
        images.extend(question_images)
    
    if extract_type in ["passages", "both"]:
        passage_images = extractor.extract_passage_images(
            temp_path,
            structured["passages"]
        )
        images.extend(passage_images)
    
    return {
        "images": images,
        "total_count": len(images)
    }
```

---

#### 0.5.2 UI/UX 컴포넌트 설계

**프론트엔드 구조**:
```typescript
// apps/web/src/components/pdf/PDFContentViewer.tsx
import React from 'react';
import { QuestionViewer } from './QuestionViewer';
import { PassageViewer } from './PassageViewer';
import { BrailleDisplay } from '../braille/BrailleDisplay';

interface PDFContent {
  questions: Question[];
  passages: Passage[];
  lessons: Lesson[];
}

interface Question {
  number: number;
  stem: string;
  choices: Choice[];
  answer?: string;
  explanation?: string;
}

interface Passage {
  title: string;
  content: string;
  page: number;
}

export function PDFContentViewer({ content }: { content: PDFContent }) {
  return (
    <div className="pdf-content-viewer">
      {/* 본문 표시 */}
      {content.passages.map((passage, idx) => (
        <PassageViewer 
          key={idx} 
          passage={passage}
          showBraille={true}
        />
      ))}
      
      {/* 문제 표시 */}
      {content.questions.map((question) => (
        <QuestionViewer 
          key={question.number}
          question={question}
          showBraille={true}
        />
      ))}
    </div>
  );
}

// apps/web/src/components/pdf/QuestionViewer.tsx
interface Question {
  number: number;
  stem: string;
  choices: Choice[];
  answer?: string;
  explanation?: string;
  // 이미지 캡처 추가
  image?: string;  // base64 이미지 또는 URL
  page?: number;
}

export function QuestionViewer({ 
  question, 
  showBraille,
  showImage = true  // 이미지 표시 여부
}: { 
  question: Question;
  showBraille: boolean;
  showImage?: boolean;
}) {
  const { convertToBraille } = useBraille();
  const [viewMode, setViewMode] = useState<'text' | 'image' | 'both'>('both');
  
  return (
    <div className="question-viewer">
      <h3>문제 {question.number}번</h3>
      
      {/* 뷰 모드 선택 */}
      <div className="view-mode-selector">
        <button 
          onClick={() => setViewMode('text')}
          className={viewMode === 'text' ? 'active' : ''}
        >
          텍스트
        </button>
        <button 
          onClick={() => setViewMode('image')}
          className={viewMode === 'image' ? 'active' : ''}
        >
          원본 이미지
        </button>
        <button 
          onClick={() => setViewMode('both')}
          className={viewMode === 'both' ? 'active' : ''}
        >
          둘 다
        </button>
      </div>
      
      {/* 원본 이미지 표시 */}
      {showImage && question.image && viewMode !== 'text' && (
        <div className="question-image">
          <img 
            src={question.image} 
            alt={`문제 ${question.number}번 원본`}
            className="pdf-capture-image"
            style={{ maxWidth: '100%', height: 'auto' }}
          />
          {question.page && (
            <p className="image-meta">페이지: {question.page}</p>
          )}
        </div>
      )}
      
      {/* 텍스트 표시 */}
      {viewMode !== 'image' && (
        <>
          {/* 문제 지문 */}
          <div className="question-stem">
            <p>{question.stem}</p>
            {showBraille && (
              <BrailleDisplay 
                text={question.stem}
                braille={convertToBraille(question.stem)}
              />
            )}
          </div>
          
          {/* 선택지 */}
          <div className="question-choices">
            {question.choices.map((choice, idx) => (
              <div key={idx} className="choice-item">
                <span className="choice-number">{choice.number}</span>
                <span className="choice-text">{choice.text}</span>
                {showBraille && (
                  <BrailleDisplay 
                    text={choice.text}
                    braille={convertToBraille(choice.text)}
                  />
                )}
              </div>
            ))}
          </div>
        </>
      )}
      
      {/* 정답 및 해설 (학습 모드) */}
      {question.answer && (
        <div className="question-answer">
          <p>정답: {question.answer}</p>
          {question.explanation && (
            <p>해설: {question.explanation}</p>
          )}
        </div>
      )}
    </div>
  );
}

// apps/web/src/components/pdf/PassageViewer.tsx
interface Passage {
  title: string;
  content: string;
  page: number;
  // 이미지 캡처 추가
  image?: string;  // base64 이미지 또는 URL
}

export function PassageViewer({ 
  passage, 
  showBraille,
  showImage = true
}: { 
  passage: Passage;
  showBraille: boolean;
  showImage?: boolean;
}) {
  const { convertToBraille } = useBraille();
  const [viewMode, setViewMode] = useState<'text' | 'image' | 'both'>('both');
  
  return (
    <div className="passage-viewer">
      <h3>{passage.title || '본문'}</h3>
      
      {/* 뷰 모드 선택 */}
      <div className="view-mode-selector">
        <button 
          onClick={() => setViewMode('text')}
          className={viewMode === 'text' ? 'active' : ''}
        >
          텍스트
        </button>
        <button 
          onClick={() => setViewMode('image')}
          className={viewMode === 'image' ? 'active' : ''}
        >
          원본 이미지
        </button>
        <button 
          onClick={() => setViewMode('both')}
          className={viewMode === 'both' ? 'active' : ''}
        >
          둘 다
        </button>
      </div>
      
      {/* 원본 이미지 표시 */}
      {showImage && passage.image && viewMode !== 'text' && (
        <div className="passage-image">
          <img 
            src={passage.image} 
            alt={passage.title || '본문 원본'}
            className="pdf-capture-image"
            style={{ maxWidth: '100%', height: 'auto' }}
          />
          <p className="image-meta">페이지: {passage.page}</p>
        </div>
      )}
      
      {/* 텍스트 표시 */}
      {viewMode !== 'image' && (
        <div className="passage-content">
          <p>{passage.content}</p>
          {showBraille && (
            <BrailleDisplay 
              text={passage.content}
              braille={convertToBraille(passage.content)}
            />
          )}
        </div>
      )}
      
      <div className="passage-meta">
        <span>페이지: {passage.page}</span>
      </div>
    </div>
  );
}
```

**API 엔드포인트**:
```python
# api/app/routers/pdf.py
@router.post("/pdf/extract-structured")
async def extract_structured_pdf(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """PDF에서 구조화된 콘텐츠 추출"""
    extractor = PDFStructureExtractor()
    
    # 임시 파일 저장
    temp_path = save_temp_file(file)
    
    # 구조화된 콘텐츠 추출
    structured_content = extractor.extract_structured_content(temp_path)
    
    # 점자 변환
    for question in structured_content["questions"]:
        question["stem_braille"] = text_to_braille(question["stem"])
        for choice in question["choices"]:
            choice["text_braille"] = text_to_braille(choice["text"])
    
    for passage in structured_content["passages"]:
        passage["content_braille"] = text_to_braille(passage["content"])
    
    return structured_content
```

**UI/UX 개선 사항**:
1. **원본 이미지 표시** (새로 추가)
   - PDF에서 캡처한 원본 이미지 표시
   - 텍스트/이미지/둘 다 보기 모드 선택
   - 이미지 확대/축소 기능
   - 보호자용 시각 UI로 활용

2. **구조화된 표시**
   - 문제와 본문을 명확히 구분
   - 선택지를 리스트로 표시
   - 페이지 번호 표시

3. **점자 통합**
   - 문제/본문/선택지 모두 점자 변환
   - 점자 디바이스 연동
   - 점자/텍스트 토글
   - 이미지와 텍스트 동시 제공

4. **접근성**
   - 스크린 리더 지원 (이미지에 alt 텍스트)
   - 키보드 네비게이션
   - 음성 읽기 기능
   - 이미지 확대 기능 (시각 장애인 보호자용)

5. **학습 기능**
   - 문제 풀이 모드
   - 정답 확인
   - 해설 표시 (AI 생성)
   - 원본 이미지와 텍스트 비교 학습

**예상 효과**:
- **원본 이미지 제공**: PDF 원본 그대로 확인 가능 (보호자용 시각 UI)
- **이중 학습**: 이미지와 텍스트 동시 제공으로 학습 효과 향상
- PDF 콘텐츠 활용도 향상
- 학습 효율성 증가
- 사용자 경험 개선
- **보호자 협력**: 보호자가 원본 이미지를 보고 도움 제공 가능

**현재 코드베이스 통합**:
```typescript
// apps/web/src/pages/Textbook/components/PDFStructuredViewer.tsx
// 기존 UnitContent.tsx를 확장하여 구조화된 PDF 콘텐츠 표시

import { QuestionViewer } from '../../../components/pdf/QuestionViewer';
import { PassageViewer } from '../../../components/pdf/PassageViewer';
import UnitContent from './UnitContent';

interface PDFStructuredViewerProps {
  unit: Unit;
  structuredContent?: {
    questions?: Question[];
    passages?: Passage[];
  };
}

export function PDFStructuredViewer({ unit, structuredContent }: PDFStructuredViewerProps) {
  // 구조화된 콘텐츠가 있으면 구조화된 뷰어 사용
  if (structuredContent) {
    return (
      <div className="pdf-structured-viewer">
        {/* 본문 먼저 표시 */}
        {structuredContent.passages?.map((passage, idx) => (
          <PassageViewer key={idx} passage={passage} />
        ))}
        
        {/* 문제 표시 */}
        {structuredContent.questions?.map((question) => (
          <QuestionViewer key={question.number} question={question} />
        ))}
      </div>
    );
  }
  
  // 기존 UnitContent 사용 (fallback)
  return <UnitContent unit={unit} />;
}
```

**백엔드 API 통합**:
```python
# api/app/routers/books.py에 추가
@router.get("/books/{book_id}/structured-content")
async def get_structured_content(
    book_id: str,
    lesson_id: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """구조화된 PDF 콘텐츠 조회"""
    book = db.query(Book).filter(Book.book_id == book_id).first()
    if not book:
        raise HTTPException(404, "Book not found")
    
    # 구조화된 콘텐츠 추출 (캐시 확인)
    cache_key = f"structured_{book_id}"
    structured = cache.get(cache_key)
    
    if not structured:
        extractor = PDFStructureExtractor()
        pdf_path = Path(book.file_path)
        structured = extractor.extract_structured_content(pdf_path)
        
        # 점자 변환
        for question in structured["questions"]:
            question["stem_braille"] = text_to_braille(question["stem"])
            for choice in question["choices"]:
                choice["text_braille"] = text_to_braille(choice["text"])
        
        for passage in structured["passages"]:
            passage["content_braille"] = text_to_braille(passage["content"])
        
        # 캐시 저장
        cache.set(cache_key, structured, timeout=3600)
    
    # 특정 강의만 필터링
    if lesson_id:
        # lesson_id에 해당하는 문제/본문만 필터링
        pass
    
    return structured
```

**구현 단계**:

**Week 1: 백엔드 구조화 추출 및 이미지 캡처**
- [ ] `PDFStructureExtractor` 클래스 구현
- [ ] 문제/본문/선택지 추출 로직
- [ ] **`PDFImageExtractor` 클래스 구현** (새로 추가)
  - [ ] PDF 페이지를 이미지로 변환
  - [ ] 문제/본문 영역 이미지 캡처
  - [ ] 이미지 base64 인코딩
- [ ] API 엔드포인트 추가 (`/pdf/extract-structured`, `/pdf/extract-images`)
- [ ] 점자 변환 통합

**Week 2: 프론트엔드 UI 컴포넌트**
- [ ] `QuestionViewer` 컴포넌트
  - [ ] 원본 이미지 표시 기능 추가
  - [ ] 텍스트/이미지/둘 다 보기 모드
- [ ] `PassageViewer` 컴포넌트
  - [ ] 원본 이미지 표시 기능 추가
  - [ ] 텍스트/이미지/둘 다 보기 모드
- [ ] `PDFStructuredViewer` 통합 컴포넌트
- [ ] 이미지 확대/축소 기능
- [ ] 기존 `UnitContent`와 통합

**Week 3: UI/UX 개선 및 테스트**
- [ ] 접근성 개선 (스크린 리더, 키보드 네비게이션)
- [ ] 점자 디바이스 연동
- [ ] 사용자 테스트 및 피드백 반영

**구현 난이도**: ⭐⭐⭐ (중간)
**예상 기간**: 2-3주

---

### Phase 0: 데이터 인프라 구축 및 제작 자동화 (2-3주)

#### 0.0 제작 프로세스 자동화 (우선순위: 매우 높음) ⭐⭐⭐⭐⭐

**배경**: 사용자 연구 결과, 제작 시간 단축이 사용자 확대의 핵심

**목표**: 수동 제작 프로세스를 AI로 보조하여 제작 시간 단축 및 품질 향상

**현재 문제점**:
- 1인 제작 시 시간이 오래 걸림
- 다수 제작자 모집 및 교육 필요
- 검수 시간이 오래 걸림
- 매뉴얼 기반 수동 제작

**AI 솔루션**:
```python
# api/app/services/content_auto_generator.py
"""
강의 대본 자동 제작 시스템
한글 파일 → 구조화된 텍스트 → 매뉴얼 준수 검증 → 최종 자료
"""
from app.services.hwp_extract import extract_text_from_hwp, extract_structure_from_hwp
from app.services.braille_convert import text_to_braille
import re

class ContentAutoGenerator:
    def __init__(self):
        self.manual_rules = {
            "text_length": "말하는 단위로 끊기",
            "symbol_rules": {
                "problem_choices": "①②③④⑤",  # 문제 선지용
                "explanation": "→",  # 설명용 (원숫자 사용 금지)
                "key_point": "★",
                "section_break": "---"
            },
            "info_order": ["type", "time"],  # 유형 정보 먼저, 시간 정보 나중
        }
    
    def generate_structured_content(self, hwp_path: Path) -> Dict:
        """한글 파일에서 구조화된 학습 자료 자동 생성"""
        # 1. 텍스트 추출
        text = extract_text_from_hwp(hwp_path)
        structure = extract_structure_from_hwp(hwp_path)
        
        # 2. 말하는 단위로 자동 분할
        speech_units = self.split_by_speech_unit(text)
        
        # 3. 섹션별 처리
        sections = []
        for unit in speech_units:
            section = {
                "type": self.detect_section_type(unit),  # concept, key_point, problem
                "content": unit,
                "braille": text_to_braille(unit),
                "timestamp": self.extract_timestamp(unit),  # 있으면 추출
                "symbol": self.assign_symbol(unit)  # 매뉴얼 규칙에 맞는 기호
            }
            sections.append(section)
        
        # 4. 매뉴얼 규칙 검증
        validation_result = self.validate_manual_compliance(sections)
        
        return {
            "sections": sections,
            "validation": validation_result,
            "needs_review": not validation_result["is_compliant"]
        }
    
    def split_by_speech_unit(self, text: str) -> List[str]:
        """말하는 단위로 텍스트 분할
        - 문장 단위
        - 강사가 설명하는 구간 단위
        - 자연스러운 끊김 지점
        """
        # 문장 단위 분할
        sentences = re.split(r'[.!?]\s+', text)
        
        # 너무 짧은 문장은 합치기
        units = []
        current_unit = ""
        for sentence in sentences:
            if len(current_unit) + len(sentence) < 100:  # 적절한 길이
                current_unit += sentence + ". "
            else:
                if current_unit:
                    units.append(current_unit.strip())
                current_unit = sentence + ". "
        if current_unit:
            units.append(current_unit.strip())
        
        return units
    
    def validate_manual_compliance(self, sections: List[Dict]) -> Dict:
        """매뉴얼 규칙 준수 여부 검증"""
        issues = []
        
        for i, section in enumerate(sections):
            # 1. 텍스트 길이 검증 (말하는 단위로 적절히 끊겼는지)
            if len(section["content"]) > 200:
                issues.append({
                    "section": i,
                    "type": "text_too_long",
                    "message": f"섹션 {i}: 텍스트가 너무 깁니다 ({len(section['content'])}자)"
                })
            
            # 2. 기호 사용 규칙 검증
            if section["type"] == "explanation" and "①" in section["content"]:
                issues.append({
                    "section": i,
                    "type": "symbol_conflict",
                    "message": "설명 섹션에 원숫자 사용 (문제 선지와 혼동 가능)"
                })
            
            # 3. 정보 순서 검증
            if section.get("timestamp") and section.get("type"):
                # 시간 정보가 유형 정보보다 앞에 있으면 경고
                pass  # 구현 필요
        
        return {
            "is_compliant": len(issues) == 0,
            "issues": issues,
            "score": max(0, 100 - len(issues) * 10)  # 품질 점수
        }
```

**매뉴얼 규칙 (사용자 피드백 기반)**:

1. **텍스트 분량 규칙**
   - 말하는 단위로 끊기 (문장 단위, 자연스러운 끊김)
   - 한 섹션당 최대 200자 (점자 읽는 속도 고려)
   - 너무 짧은 문장은 합치기 (최소 50자)

2. **기호 사용 규칙**
   ```python
   SYMBOL_RULES = {
       "problem_choices": "①②③④⑤",  # 문제 선지용 (설명 섹션에서 사용 금지)
       "explanation": "→",              # 설명용
       "key_point": "★",                # 핵심 포인트
       "section_break": "---",          # 섹션 구분
       "emphasis": "【】"                # 강조
   }
   ```

3. **정보 제공 순서 규칙**
   - 유형 정보 먼저 (예: "해설", "개념", "문제")
   - 시간 정보는 뒤로 (시간 확인 시 강의가 끊김)
   - 예: `[해설] 내용... (8분 14초)` ❌
   - 예: `[해설] 내용...` ✅ (시간 정보는 메타데이터로만)

4. **텍스트 작성 규칙**
   - 원숫자(①②③)는 문제 선지에만 사용
   - 설명 섹션에서는 다른 기호 사용
   - 구체적인 행동 설명은 간결하게 (예: "이것도 뭐야?" → "단어를 가르쳤습니다")

**실제 대본 분석 예시** (수능특강 문학 1강):

```python
# 실제 강의 대본 구조 분석
lecture_script = {
    "lesson_number": 1,
    "title": "01강_[교과서_개념]_1_2_(고3_기본)",
    "sections": [
        {
            "type": "intro",
            "content": "여러분, 안녕하세요? 국어 영역 최선의 선택 최서희입니다.",
            "speech_unit": True  # 말하는 단위로 분할
        },
        {
            "type": "concept",
            "title": "개념 설명 – 시의 표현/형식",
            "content": "오늘 1강에서는요. 시의 표현과 형식, 그리고 시의 내용에 대해서 배울 거거든...",
            "key_points": [
                "형상화: 정서나 교훈을 구체적이고 실감나게 그려내는 것",
                "독백체 vs 대화체: 청자 설정 유무로 구분",
                "시의 형식: 내용을 고려해서 선택됨"
            ]
        },
        {
            "type": "work_analysis",
            "title": "작품 분석 – 박두진 <해>",
            "content": "이제 넘어가겠습니다. 구체적인 작품 들어간다...",
            "analysis_framework": "화자가 무엇을 어떻게",
            "key_elements": {
                "subject": "해",
                "emotion": "솟기를 바란다, 소망한다",
                "symbols": ["해 (밝음)", "달밤 (어둠)", "청산 (이상향)"],
                "expression_features": [
                    "반복과 변주 (AABA 구조)",
                    "음성 상징어 (훨훨훨, 이글이글)",
                    "이미지의 대립 (밝음 vs 어둠)",
                    "명령형 어미, 감탄형 어미"
                ]
            }
        },
        {
            "type": "problem",
            "number": 1,
            "content": "시구의 반복과 변주를 통해서 정서의 고조를 드러내고 있다...",
            "explanation": "해야 솟아라. 해야 솟아라. 말갛게 씻은 얼굴 고운 해야 솟아라...",
            "key_learning": "반성적 태도: 잘못한 것만이 아니라 돌이켜 보는 것 전부"
        },
        {
            "type": "practice",
            "title": "기출 탈탈 털어 쏙쏙 뽑아",
            "content": "기출 탈탈 털어서요. 쏙쏙 뽑아 왔습니다...",
            "problems": [
                "명령형 어미를 구사해서 소망의 간절함 드러낸 거 맞죠?",
                "음성 상징어를 활용하여 분위기를 생동감 있게..."
            ]
        },
        {
            "type": "summary",
            "title": "한 판에 담판",
            "content": "박두진의 '해'는요. 이런 주제를 담고 있고..."
        }
    ]
}
```

**말하는 단위 분할 예시**:
```
원본: "오늘 1강에서는요. 시의 표현과 형식, 그리고 시의 내용에 대해서 배울 거거든. 그런데 사실은 구구절절 세세한 개념들은 수능개념에서 이미 공부를 했어야 돼요."

분할 후:
[
  "오늘 1강에서는요. 시의 표현과 형식, 그리고 시의 내용에 대해서 배울 거거든.",
  "그런데 사실은 구구절절 세세한 개념들은 수능개념에서 이미 공부를 했어야 돼요."
]
```

**매뉴얼 규칙 적용 예시**:
```python
# 원본 텍스트
original = "①번부터 한번 같이 읽어 보자."

# 매뉴얼 규칙 적용 (설명 섹션에서는 원숫자 사용 금지)
formatted = "첫 번째부터 한번 같이 읽어 보자."  # 또는 "1번부터..."

# 기호 사용 규칙
symbols = {
    "concept": "→",  # 개념 설명
    "key_point": "★",  # 핵심 포인트
    "problem": "【문제】",  # 문제
    "explanation": "→",  # 해설 (원숫자 사용 금지)
    "summary": "---"  # 섹션 구분
}
```

**예상 효과**:
- 제작 시간: 80% 단축 (수동 4시간 → AI 보조 1시간)
- 품질 일관성: 매뉴얼 규칙 자동 검증
- 제작자 교육 시간: 50% 단축
- 검수 시간: 60% 단축 (자동 검증으로 주요 이슈 사전 발견)
- **실제 대본 기반 검증**: 제공된 대본으로 시스템 테스트 가능

**구현 난이도**: ⭐⭐⭐ (중간)
**예상 기간**: 2주

---

### Phase 0: 데이터 인프라 구축 (1-2주)

#### 0.1 한글 파일 처리 기능 추가

**목표**: 강의 대본(한글 파일)을 처리하여 텍스트 추출 및 구조화

**앱 통합 시나리오**:
- **교재 관리**: 한글 파일 업로드 → 자동으로 강의 구조 파싱 (00강~43강)
- **학습 화면**: 한글 파일의 내용을 점자로 변환하여 표시
- **단원 목록**: 한글 파일명에서 강 번호, 주제, 난이도 정보 추출

**구현 단계**:

1. **한글 파일 파싱 라이브러리 통합**
   ```python
   # api/app/services/hwp_extract.py
   """
   한글 파일 텍스트 추출 서비스
   """
   import olefile
   import struct
   import re
   from pathlib import Path
   from typing import Optional, Dict, List
   
   def extract_text_from_hwp(hwp_path: Path) -> Optional[str]:
       """한글 파일에서 텍스트 추출"""
       # pyhwp 또는 olefile을 사용한 파싱
       pass
   
   def extract_lesson_info_from_filename(filename: str) -> Dict:
       """파일명에서 강의 정보 추출
       
       예: "01강_[교과서_개념]_1_2_(고3_기본).hwp"
       -> {
           "lesson_number": 1,
           "category": "교과서_개념",
           "subcategory": "1_2",
           "difficulty": "고3_기본"
       }
       """
       pattern = r'(\d+)강_\[([^\]]+)\]_([^_]+)_\(([^)]+)\)'
       match = re.match(pattern, filename)
       if match:
           return {
               "lesson_number": int(match.group(1)),
               "category": match.group(2),
               "subcategory": match.group(3),
               "difficulty": match.group(4)
           }
       return {}
   
   def extract_structure_from_hwp(hwp_path: Path) -> Dict:
       """한글 파일에서 강 구조 추출
       
       구조:
       - 개념 설명
       - 꼭 집어 핵심 포인트
       - 문제 1번, 2번, 3번
       - 기출 탈탈 털어 쏙쏙 뽑아
       """
       text = extract_text_from_hwp(hwp_path)
       if not text:
           return {}
       
       structure = {
           "concept_explanations": [],
           "key_points": [],
           "problems": [],
           "practice_section": ""
       }
       
       # 패턴 매칭으로 구조 추출
       # "개념 설명" 섹션 찾기
       concept_pattern = r'개념\s*설명[:\-]?\s*(.+?)(?=꼭|문제|기출|$)'
       # "꼭 집어 핵심 포인트" 섹션 찾기
       keypoint_pattern = r'꼭\s*집어\s*핵심\s*포인트[:\-]?\s*(.+?)(?=문제|기출|$)'
       # "문제 N번" 찾기
       problem_pattern = r'문제\s*(\d+)\s*번[:\-]?\s*(.+?)(?=문제\s*\d+|기출|$)'
       
       # ... 패턴 매칭 및 추출 로직
       
       return structure
   ```

2. **API 엔드포인트 추가**
   ```python
   # api/app/routers/books.py
   @router.post("/books/upload-hwp", response_model=BookResponse)
   async def upload_hwp_book(
       file: UploadFile = File(...),
       title: str = Form(...),
       subject: str = Form(...),
       db: Session = Depends(get_db),
   ):
       """한글 파일 업로드 및 파싱
       
       - 파일명에서 강의 정보 추출
       - 텍스트 추출 및 구조화
       - 데이터베이스에 저장
       """
       # 파일 저장
       # 텍스트 추출
       # 구조 파싱
       # DB 저장
       pass
   
   @router.get("/books/{book_id}/lessons-from-hwp")
   async def get_lessons_from_hwp(book_id: str, db: Session = Depends(get_db)):
       """한글 파일에서 추출한 강의 목록 조회"""
       # 한글 파일에서 파싱한 강의 구조 반환
       pass
   ```

3. **프론트엔드 통합**
   ```typescript
   // apps/web/src/pages/Textbook/components/PDFUpload.tsx
   // 한글 파일 업로드 추가
   const handleHwpUpload = async (file: File) => {
     const formData = new FormData();
     formData.append('file', file);
     formData.append('title', '수능특강 2026 문학');
     formData.append('subject', 'korean');
     
     const response = await booksAPI.uploadHwp(formData);
     // 업로드 후 자동으로 강의 구조 파싱
     // 단원 목록 화면에 반영
   };
   ```

4. **필요 라이브러리 추가**
   ```txt
   # api/requirements.txt
   pyhwp>=0.1.0  # 또는 olefile
   ```

**예상 기간**: 1주
**난이도**: ⭐⭐

---

#### 0.2 학습 데이터셋 구축 파이프라인

**목표**: 한글 파일과 PDF를 활용하여 AI 모델 학습용 데이터셋 자동 구축

**실제 대본 활용**:
- 제공된 강의 대본(텍스트)을 학습 데이터로 활용
- 말하는 단위로 자동 분할
- 섹션별 분류 (인트로, 개념, 작품 분석, 문제, 기출, 요약)

**데이터 구조** (앱 구조 반영):
```json
{
  "dataset_version": "1.0",
  "created_at": "2024-01-16",
  "book": {
    "title": "수능특강 2026 문학",
    "subject": "문학",
    "year": 2026,
    "lessons": [
      {
        "lesson_number": 0,
        "title": "오리엔테이션",
        "category": "오리엔테이션"
      },
      {
        "lesson_number": 1,
        "title": "01강_[교과서_개념]_1_2_(고3_기본)",
        "category": "교과서_개념",
        "subcategory": "1_2",
        "difficulty": "고3_기본",
        "sections": [
          {
            "type": "concept",
            "title": "개념 설명",
            "content": "시의 표현과 형식...",
            "braille": "점자 변환 결과"
          },
          {
            "type": "key_point",
            "title": "꼭 집어 핵심 포인트",
            "content": "핵심 내용...",
            "braille": "점자 변환 결과"
          },
          {
            "type": "problem",
            "number": 1,
            "content": "문제 지문...",
            "choices": ["① 선택지1", "② 선택지2", ...],
            "braille": "점자 변환 결과"
          }
        ]
      }
    ]
  },
  "items": [
    {
      "id": "item_001",
      "source": "hwp",
      "source_file": "01강_[교과서_개념]_1_2_(고3_기본).hwp",
      "lesson_number": 1,
      "category": "교과서_개념",
      "section_type": "concept",
      "text": "원본 텍스트",
      "braille": "점자 변환 결과",
      "context": {
        "subject": "문학",
        "year": 2026,
        "difficulty": "고3_기본",
        "topic": "교과서_개념",
        "lesson_sequence": 1
      },
      "metadata": {
        "char_count": 1500,
        "braille_cell_count": 3000,
        "extracted_at": "2024-01-16T20:31:00"
      }
    }
  ]
}
```

**구축 스크립트** (실제 대본 통합):
```python
# scripts/build_training_dataset.py
"""
학습 데이터셋 자동 구축 스크립트
실제 강의 대본(텍스트)도 활용 가능
"""
from pathlib import Path
import json
import re
from datetime import datetime
from app.services.hwp_extract import extract_text_from_hwp, extract_structure_from_hwp
from app.services.pdf_extract import extract_text_from_pdf
from app.services.braille_convert import text_to_braille

def parse_lecture_script(script_text: str) -> Dict:
    """실제 강의 대본 파싱
    
    예시: 수능특강 문학 1강 대본
    """
    sections = []
    
    # 섹션별 패턴 매칭
    patterns = {
        "intro": r"\[인트로\]",
        "concept": r"\[개념 설명",
        "work_analysis": r"\[작품 분석",
        "problem": r"\[문제 풀이",
        "practice": r"\[기출 탈탈",
        "summary": r"\[한 판에 담판\]"
    }
    
    # 말하는 단위로 분할
    speech_units = split_by_speech_unit(script_text)
    
    for unit in speech_units:
        section_type = detect_section_type(unit, patterns)
        sections.append({
            "type": section_type,
            "content": unit,
            "braille": text_to_braille(unit),
            "length": len(unit)
        })
    
    return {
        "sections": sections,
        "total_length": len(script_text),
        "speech_units_count": len(speech_units)
    }

def split_by_speech_unit(text: str) -> List[str]:
    """말하는 단위로 분할 (실제 대본 기반)
    
    - 문장 단위 (마침표, 물음표, 느낌표)
    - 자연스러운 끊김 지점
    - 적절한 길이 (50-200자)
    """
    # 문장 단위 분할
    sentences = re.split(r'[.!?]\s+', text)
    
    units = []
    current_unit = ""
    
    for sentence in sentences:
        if len(current_unit) + len(sentence) < 150:  # 적절한 길이
            current_unit += sentence + ". "
        else:
            if current_unit:
                units.append(current_unit.strip())
            current_unit = sentence + ". "
    
    if current_unit:
        units.append(current_unit.strip())
    
    return units

def build_braille_dataset(
    hwp_dir: Path = Path("data/lecture_scripts"),
    pdf_dir: Path = Path("data/pdfs"),
    output_path: Path = Path("data/datasets/braille_dataset.json")
):
    """점자 변환 학습 데이터셋 구축"""
    dataset = {
        "dataset_version": "1.0",
        "created_at": datetime.now().isoformat(),
        "items": []
    }
    
    # 한글 파일 처리
    for hwp_file in hwp_dir.glob("*.hwp"):
        print(f"Processing HWP: {hwp_file.name}")
        text = extract_text_from_hwp(hwp_file)
        if not text:
            continue
        
        structure = extract_structure_from_hwp(hwp_file)
        braille = text_to_braille(text)
        
        # 강 번호 추출 (파일명에서)
        lesson_num = extract_lesson_number(hwp_file.name)
        category = extract_category(hwp_file.name)
        
        dataset["items"].append({
            "id": f"item_{len(dataset['items']):03d}",
            "source": "hwp",
            "source_file": hwp_file.name,
            "lesson_number": lesson_num,
            "category": category,
            "text": text,
            "braille": braille,
            "context": {
                "subject": "문학",  # 파일명에서 추출
                "year": 2026,
                "difficulty": "고3_기본",
                "topic": category
            },
            "metadata": {
                "char_count": len(text),
                "braille_cell_count": len(braille.split()),
                "extracted_at": datetime.now().isoformat()
            }
        })
    
    # PDF 파일 처리
    for pdf_file in pdf_dir.glob("*.pdf"):
        print(f"Processing PDF: {pdf_file.name}")
        text = extract_text_from_pdf(pdf_file)
        if not text:
            continue
        
        braille = text_to_braille(text)
        
        dataset["items"].append({
            "id": f"item_{len(dataset['items']):03d}",
            "source": "pdf",
            "source_file": pdf_file.name,
            "text": text,
            "braille": braille,
            "context": {
                "subject": extract_subject_from_filename(pdf_file.name),
                "year": 2026
            },
            "metadata": {
                "char_count": len(text),
                "braille_cell_count": len(braille.split()),
                "extracted_at": datetime.now().isoformat()
            }
        })
    
    # JSON으로 저장
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(dataset, f, ensure_ascii=False, indent=2)
    
    print(f"Dataset built: {len(dataset['items'])} items saved to {output_path}")
    return dataset
```

**예상 데이터 규모**:
- 한글 파일: 44개 강 × 평균 4,500자 = 약 200,000자
- PDF 파일: 10개 교재 × 평균 50,000자 = 약 500,000자
- **실제 강의 대본**: 1강 기준 약 15,000자 (전체 44강 = 약 660,000자)
- **총 약 1,360,000자의 한국어-점자 병렬 데이터**

**실제 대본 활용 장점**:
- 이미 구조화된 텍스트 (한글 파일 파싱 불필요)
- 말하는 단위가 명확함
- 섹션 구분이 명확함 (인트로, 개념, 작품 분석, 문제, 기출, 요약)
- 매뉴얼 규칙 검증에 바로 활용 가능

**예상 기간**: 1주
**난이도**: ⭐⭐

---

### Phase 1: 기초 AI/ML 구현 (상세 계획)

#### 1.1 점자 변환 ML 모델 - 단계별 구현

**Week 1-2: 데이터 전처리 및 준비**
- [ ] 학습 데이터셋 검증 및 정제
- [ ] Train/Validation/Test 세트 분할 (8:1:1)
- [ ] 데이터 증강 (augmentation) 전략 수립
- [ ] 토크나이저 준비 (한국어 특화)

**Week 3-4: 모델 아키텍처 설계**
- [ ] Seq2Seq 모델 선택 (T5, BART, 또는 커스텀)
- [ ] KoBERT/KoGPT 기반 인코더 설계
- [ ] 점자 토크나이저 개발
- [ ] 모델 초기화 및 기본 학습 루프 구현

**Week 5-8: 모델 학습**
- [ ] 하이퍼파라미터 튜닝
- [ ] 학습 진행 및 모니터링
- [ ] 검증 세트로 성능 평가
- [ ] 모델 체크포인트 저장

**Week 9-10: 모델 통합 및 배포**
- [ ] 학습된 모델을 서비스에 통합
- [ ] 추론 API 엔드포인트 구현
- [ ] 성능 벤치마크 테스트
- [ ] 프로덕션 배포

**구현 파일 구조**:
```
api/
├── app/
│   ├── services/
│   │   ├── braille_ml.py          # ML 모델 래퍼
│   │   └── braille_convert.py    # 기존 규칙 기반 (fallback)
│   ├── models/
│   │   └── braille_converter/    # 학습된 모델 저장
│   └── routers/
│       └── braille.py             # 점자 변환 API
└── training/
    ├── train_braille_model.py     # 학습 스크립트
    ├── dataset.py                  # 데이터셋 클래스
    └── evaluate.py                 # 평가 스크립트
```

**성공 지표**:
- BLEU Score: 0.85 이상
- 정확도: 95% 이상
- 추론 속도: 100자당 1초 이내

---

#### 1.2 학습자 맞춤형 추천 시스템 - 단계별 구현

**Week 1: 데이터 수집 인프라**
- [ ] 사용자 행동 로깅 시스템 구축
- [ ] 데이터베이스 스키마 설계 (학습 이력, 오답 패턴)
- [ ] 실시간 데이터 수집 파이프라인

**Week 2: 사용자 프로필 구축**
- [ ] TF-IDF 기반 콘텐츠 벡터화
- [ ] 사용자별 학습 패턴 분석
- [ ] 오답 패턴 클러스터링

**Week 3: 추천 알고리즘 구현**
- [ ] 협업 필터링 구현
- [ ] 콘텐츠 기반 필터링 구현
- [ ] 하이브리드 추천 시스템

**Week 4: API 통합 및 테스트**
- [ ] 추천 API 엔드포인트 구현
- [ ] A/B 테스트 프레임워크 구축
- [ ] 성능 모니터링

**구현 파일 구조**:
```
api/
├── app/
│   ├── services/
│   │   ├── recommendation.py      # 추천 엔진
│   │   └── user_profiling.py      # 사용자 프로필 구축
│   └── routers/
│       └── recommendations.py     # 추천 API
└── data/
    └── user_profiles/              # 사용자 프로필 캐시
```

**성공 지표**:
- 추천 정확도: 70% 이상 (사용자가 추천 콘텐츠를 학습하는 비율)
- 클릭률(CTR): 30% 이상
- 학습 완료율 증가: 20% 이상

---

### Phase 2: 고급 AI 기능 - 단계별 구현

#### 2.1 생성형 AI 콘텐츠 생성 - 단계별 구현

**Week 1: LLM 통합 및 프롬프트 설계**
- [ ] LangChain 설정 및 LLM 초기화
- [ ] 문제 해설 프롬프트 템플릿 작성
- [ ] 지문 요약 프롬프트 템플릿 작성
- [ ] Few-shot 예제 수집

**Week 2: 콘텐츠 생성 모듈 구현**
- [ ] `generate_explanation()` 구현
- [ ] `generate_summary()` 구현
- [ ] `generate_practice_questions()` 구현
- [ ] 출력 품질 검증 로직

**Week 3: API 통합 및 캐싱**
- [ ] 콘텐츠 생성 API 엔드포인트
- [ ] Redis 캐싱 전략 (동일 문제 해설 재사용)
- [ ] 비용 최적화 (토큰 사용량 모니터링)

**Week 4: 품질 개선 및 최적화**
- [ ] 프롬프트 엔지니어링 개선
- [ ] 출력 후처리 (포맷팅, 검증)
- [ ] 사용자 피드백 수집 시스템

**구현 파일 구조**:
```
api/
├── app/
│   ├── services/
│   │   ├── content_generator.py   # LLM 기반 콘텐츠 생성
│   │   └── prompt_templates.py    # 프롬프트 템플릿
│   └── routers/
│       └── content.py              # 콘텐츠 생성 API
└── prompts/
    ├── explanation.txt             # 해설 프롬프트
    ├── summary.txt                 # 요약 프롬프트
    └── practice_questions.txt      # 문제 생성 프롬프트
```

**비용 최적화 전략**:
- 동일 문제 해설 캐싱 (Redis)
- 배치 처리로 API 호출 최소화
- 오픈소스 LLM (Ollama) 옵션 제공

---

## 📅 상세 타임라인

### Month 1: 데이터 인프라 및 제작 자동화 (우선순위)
- **Week 1**: 한글 파일 처리 기능 추가
- **Week 2**: **PDF 구조화 추출 및 UI/UX 개선** (우선)
- **Week 3**: 제작 프로세스 자동화 (AI 보조 제작)
- **Week 4**: 매뉴얼 규칙 검증 시스템 + 학습 데이터셋 구축 파이프라인

### Month 2-3: Phase 1 구현 + 동기화
- **Week 5-6**: 강의 음성-텍스트 자동 동기화 (우선)
- **Week 7-10**: 점자 변환 ML 모델 학습
- **Week 11-12**: 점자 변환 모델 통합 및 배포
- **Week 13-14**: 추천 시스템 구현 (소규모 사용자 최적화)
- **Week 15-16**: 추천 시스템 통합 및 테스트

### Month 4-5: Phase 2 구현
- **Week 15-18**: 생성형 AI 콘텐츠 생성 구현
- **Week 19-22**: 이미지/그래프 변환 (선택적)

---

## ✅ 체크리스트

### 📍 현재 진행 상태 (2024년 기준)

#### Phase 0: 데이터 인프라 및 제작 자동화 (약 60% 완료)
- [x] 한글 파일 처리 라이브러리 통합 ✅
  - `api/app/services/hwp_extract.py` - HWP 파일 텍스트 추출 완료
  - 파일명에서 강의 정보 추출 기능 완료
- [ ] 한글 파일 업로드 API 구현 (미완료)
- [x] **PDF 구조화 추출 시스템** (부분 완료) ⚠️
  - [x] 문제/본문/선택지 추출 (기본 파싱 완료)
  - [x] 구조화된 데이터 반환 (JSON 저장 완료)
  - [x] 과목별 파서 구현 (Math1, Literature, English)
  - [ ] UI/UX 컴포넌트 구현 (미완료)
  - [x] 점자 변환 통합 (규칙 기반 완료)
- [x] **강의 대본 파서** ✅ (새로 완료)
  - `api/app/services/lecture_script_parser.py` - 대본 파싱 기능 완료
  - 섹션 분류 (OT, Overview, Concept, Example 등) 완료
  - 핵심 포인트 및 수학 표현식 추출 완료
  - API 엔드포인트 추가 완료 (`/api/lecture-scripts/parse`)
- [x] **제작 프로세스 자동화 시스템** (기본 구조 완료) ⚠️
  - [x] 말하는 단위 자동 분할 (기본 구현 완료)
  - [x] 매뉴얼 규칙 자동 검증 (기본 검증 로직 완료)
  - [ ] 기호 사용 규칙 자동 적용 (부분 완료)
  - [ ] 정보 순서 자동 최적화 (미완료)
- [x] 데이터셋 구축 스크립트 작성 ✅
  - `api/scripts/build_training_dataset.py` - 기본 구조 완료
- [ ] 데이터 검증 및 품질 관리 시스템 (미완료)

**완료된 주요 파일들:**
- `api/app/services/pdf_extract/` - PDF 추출 모듈 (완료)
- `api/app/services/pdf_parse/` - PDF 파싱 파이프라인 (완료)
- `api/app/services/subject_strategies/` - 과목별 파서 (완료)
- `api/app/services/braille_convert.py` - 점자 변환 (규칙 기반 완료)
- `api/app/services/lecture_script_parser.py` - 강의 대본 파서 (완료)
- `api/app/services/content_auto_generator.py` - 제작 자동화 (기본 구조 완료)

### Phase 1: 기초 AI/ML (약 10% 완료)
- [x] **강의 음성-텍스트 자동 동기화** (기본 구조 완료) ⚠️
  - [x] 기본 클래스 구조 (`api/app/services/audio_sync.py`)
  - [ ] STT 기반 음성-텍스트 매칭 (미완료)
  - [ ] 실시간 동기화 기능 (미완료)
  - [ ] 점자 디바이스 자동 업데이트 (미완료)
- [ ] 점자 변환 ML 모델 학습 완료 (규칙 기반만 완료)
- [ ] 모델 서빙 인프라 구축 (미완료)
- [ ] 추천 시스템 MVP 완성 (미완료)
- [ ] 개인화 추천 시스템 (미완료)

### Phase 2: 고급 AI (0% 완료)
- [ ] 생성형 AI 콘텐츠 생성 기능 완성 (미완료)
  - [ ] 학습자용: 문제 해설, 요약
  - [ ] 제작자용: 강의 대본 자동 생성
- [ ] 프롬프트 최적화 완료 (미완료)
- [ ] 비용 모니터링 시스템 구축 (미완료)
- [ ] 제작자 온보딩 자동화 (미완료)
- [ ] 실시간 피드백 시스템 (미완료)

---

## 📊 현재 완료 상태 요약

### ✅ 완료된 기능 (Phase 0 - 60%)
1. **PDF 추출 및 파싱 인프라** (100%)
   - PDF 블록 추출 (pdfplumber 기반)
   - 과목별 파서 (Math1, Literature, English)
   - JSON 저장 및 파싱 파이프라인
   
2. **점자 변환** (100% - 규칙 기반)
   - 규칙 기반 한글→점자 변환
   - 약자 처리
   
3. **한글 파일 처리** (100%)
   - HWP 파일 텍스트 추출
   - 파일명에서 강의 정보 추출
   
4. **강의 대본 파서** (100%) ⭐ 새로 완료
   - 대본 섹션 분류 (OT, Overview, Concept 등)
   - 핵심 포인트 추출
   - 수학 표현식 추출
   - API 엔드포인트 제공
   
5. **제작 자동화 기본 구조** (50%)
   - 기본 클래스 구조 완료
   - 말하는 단위 분할 로직 완료
   - 매뉴얼 규칙 검증 기본 로직 완료

### ⚠️ 부분 완료 (추가 작업 필요)
- PDF 구조화 추출 (백엔드 완료, 프론트엔드 미완료)
- 제작 프로세스 자동화 (기본 구조만, 완전 자동화 미완료)
- 음성-텍스트 동기화 (기본 구조만, 실제 STT 통합 미완료)

### ❌ 미완료
- 한글 파일 업로드 API
- PDF 이미지 캡처 기능
- 점자 변환 ML 모델 (규칙 기반만 존재)
- 추천 시스템
- 생성형 AI 콘텐츠 생성

---

## 📝 다음 단계

### 즉시 시작 가능한 작업 (우선순위 순)

1. **한글 파일 업로드 API 구현** (1주)
   - 현재: 텍스트 추출 기능만 완료
   - 필요: 파일 업로드 엔드포인트 추가
   - 우선순위: ⭐⭐⭐ (높음)

2. **강의 대본 파서 완성** ⭐ (방금 완료)
   - ✅ 대본 파싱 기능 완료
   - ✅ API 엔드포인트 추가 완료
   - 다음: 프론트엔드 통합 및 테스트

3. **제작 프로세스 자동화 완성** (1-2주)
   - 현재: 기본 구조 50% 완료
   - 필요: 매뉴얼 규칙 완전 자동 적용
   - 우선순위: ⭐⭐⭐⭐⭐ (최우선)

4. **PDF 구조화 추출 UI/UX 구현** (2-3주)
   - 현재: 백엔드 완료
   - 필요: 프론트엔드 컴포넌트 구현
   - 우선순위: ⭐⭐⭐⭐ (높음)

5. **학습 데이터셋 구축 스크립트 완성** (1주)
   - 현재: 기본 구조 완료
   - 필요: 강의 대본 파서 통합 및 테스트

2. **데이터 수집 시작**
   - 사용자 학습 행동 데이터 수집 (지속적)
   - 점자 변환 학습 데이터 구축 (완료 시점: 2주 후)

3. **인프라 준비**
   - GPU 서버 환경 구축 (2주)
   - 모델 서빙 파이프라인 설계 (1주)

---

## 🎮 앱 통합 시나리오

### 시나리오 1: 메인 화면 "오늘 학습 이어하기"

**현재**: 마지막 학습 위치 표시
**AI 개선 후**:
```typescript
// apps/web/src/pages/Home.tsx
const ContinueLearningCard = () => {
  const { lastLesson, recommendedNext } = useRecommendation();
  
  return (
    <Card onClick={() => navigate(`/learning/${recommendedNext}`)}>
      <h3>오늘 학습 이어하기</h3>
      <p>마지막: {lastLesson}</p>
      <p>추천: {recommendedNext} (AI 추천)</p>
      {/* AI가 추천한 이유 표시 */}
      <Badge>틀린 문제 보완</Badge>
    </Card>
  );
};
```

**AI 기능**:
- 마지막 학습 위치 분석
- 오답 패턴 기반 다음 강의 추천
- 학습 시간대 고려 (예: 아침에는 개념 강의, 저녁에는 실전 문제)

---

### 시나리오 2: 단원 목록 화면

**현재**: 00강~43강 목록 표시
**AI 개선 후**:
```typescript
// apps/web/src/pages/Textbook/Textbook.tsx
const UnitList = ({ units }) => {
  const { recommendedOrder, difficulty } = useRecommendation();
  
  return (
    <div>
      {units.map(unit => (
        <UnitCard 
          unit={unit}
          isRecommended={recommendedOrder.includes(unit.id)}
          difficulty={difficulty[unit.id]}
          // AI 추천 이유 표시
          recommendationReason={getRecommendationReason(unit.id)}
        />
      ))}
    </div>
  );
};
```

**AI 기능**:
- 사용자 수준에 맞는 강의 순서 재정렬
- 난이도 표시 (쉬움/보통/어려움)
- 추천 이유 표시 ("고전 시가 보완 필요", "이전 강의 완료 후 권장" 등)

---

### 시나리오 3: 강의 학습 화면

**현재 구조**:
```
01강_[교과서_개념]_1_2_(고3_기본)
├── 개념 설명 -> 시의 표현과 형식
├── 개념 설명 -> 시의 내용
├── 꼭 집어 핵심 포인트
├── 박두진 [해]
├── 문제 1번
├── 문제 2번
├── 문제 3번
└── 기출 탈탈 털어 쏙쏙 뽑아
```

**AI 개선 후**:
```typescript
// apps/web/src/pages/Learning/LearningScreen.tsx
const LearningScreen = ({ lessonId }) => {
  const { 
    conceptExplanation,      // 개념 설명 (한글 파일에서)
    keyPoints,               // 핵심 포인트 (AI 요약)
    problems,                // 문제들
    explanations             // 문제 해설 (AI 생성)
  } = useLessonContent(lessonId);
  
  // 점자 변환 (ML 모델 사용)
  const brailleContent = useBrailleML(conceptExplanation);
  
  return (
    <div>
      {/* 개념 설명 - 점자로 표시 */}
      <BrailleDisplay content={brailleContent} />
      
      {/* 핵심 포인트 - AI 요약 */}
      <KeyPointsSection points={keyPoints} />
      
      {/* 문제 풀이 */}
      {problems.map(problem => (
        <ProblemCard 
          problem={problem}
          explanation={explanations[problem.id]} // AI 생성 해설
        />
      ))}
    </div>
  );
};
```

**AI 기능**:
1. **점자 변환**: ML 모델로 문맥을 고려한 점자 변환
2. **핵심 포인트 요약**: 생성형 AI로 개념 설명을 요약
3. **문제 해설 생성**: 틀린 문제에 대해 자동 해설 생성

---

### 시나리오 4: 틀린 문제 복습하기

**현재**: 틀린 문제 목록 표시
**AI 개선 후**:
```typescript
// apps/web/src/pages/Review.tsx
const ReviewScreen = () => {
  const { wrongQuestions } = useReviewStore();
  const { recommendedLessons, explanations } = useAIReview(wrongQuestions);
  
  return (
    <div>
      <h2>틀린 문제 복습하기</h2>
      
      {/* AI 추천 복습 강의 */}
      <RecommendedLessons lessons={recommendedLessons} />
      
      {/* 틀린 문제별 상세 해설 */}
      {wrongQuestions.map(q => (
        <QuestionReviewCard
          question={q}
          explanation={explanations[q.id]} // AI 생성 해설
          relatedLessons={getRelatedLessons(q)} // 관련 강의 추천
        />
      ))}
    </div>
  );
};
```

**AI 기능**:
- 틀린 문제 패턴 분석
- 관련 강의 추천 (예: 고전 시가 문제 틀림 → 고전 시가 강의 추천)
- 맞춤형 해설 생성
- 추가 연습 문제 생성

---

### 시나리오 5: 한글 파일 → 점자 변환

**사용자 플로우**:
1. 교재 관리에서 한글 파일 업로드
2. 자동으로 강의 구조 파싱 (00강~43강)
3. 각 섹션을 점자로 변환하여 학습 화면에 표시

**AI 통합**:
```typescript
// apps/web/src/services/braille.ts
export async function convertHwpToBraille(hwpFile: File) {
  // 1. 한글 파일 업로드
  const uploadResult = await uploadHwpFile(hwpFile);
  
  // 2. 텍스트 추출 및 구조 파싱
  const structure = await parseHwpStructure(uploadResult.fileId);
  
  // 3. 각 섹션을 점자로 변환 (ML 모델 사용)
  const brailleStructure = await Promise.all(
    structure.sections.map(async (section) => ({
      ...section,
      braille: await convertToBrailleML(section.text, {
        context: section.type, // "concept", "key_point", "problem"
        lesson: structure.lessonNumber,
        category: structure.category
      })
    }))
  );
  
  return brailleStructure;
}
```

---

## 📱 사용자 여정 (User Journey) 개선

### Before (현재)
1. 메인 → 교재 선택 → 단원 선택 → 학습
2. 문제 틀림 → 수동으로 복습

### After (AI 통합 후)
1. 메인 → **AI 추천 다음 강의** → 학습
2. 문제 틀림 → **AI 해설 자동 생성** → **관련 강의 추천** → 복습
3. 학습 중 → **핵심 포인트 AI 요약** → 효율적 학습
4. 한글 파일 업로드 → **자동 구조 파싱** → **점자 변환** → 즉시 학습 가능

---

## 🔗 참고 자료

- [Hugging Face Transformers](https://huggingface.co/docs/transformers)
- [LangChain Documentation](https://python.langchain.com/)
- [PyTorch Tutorials](https://pytorch.org/tutorials/)
- [scikit-learn User Guide](https://scikit-learn.org/stable/user_guide.html)

---

## 🗂 데이터 활용 전략

### 보유 데이터 분석

#### 한글 파일 (강의 대본)
- **파일 수**: 44개 강 (00강 오리엔테이션 + 01강~43강)
- **파일명 패턴**: `[번호]강_[카테고리]_[세부]_[난이도].hwp`
- **카테고리**: 
  - 교과서 개념 (01강~05강)
  - 고전 시가 (05강~10강)
  - 현대시 (10강~15강)
  - 고전 산문 (16강~21강)
  - 현대 소설 (21강~26강)
  - 극/수필 (27강~29강)
  - 갈래 복합 (30강~39강)
  - 실전 문제 (40강~43강)
- **예상 텍스트량**: 약 200,000자 (44개 강 × 평균 4,500자)
- **구조화 정보**: 
  - 강 번호 (00~43)
  - 주제 카테고리
  - 난이도 (고3_기본)
  - 섹션 구조 (개념 설명, 핵심 포인트, 문제, 기출)

#### PDF 파일 (수능특강 교재)
- **파일 수**: 10개 이상 (문학, 독서, 수학, 영어 등)
- **파일 크기**: 3MB ~ 45MB
- **예상 텍스트량**: 약 500,000자
- **구조**: 강별로 구성, 문제 및 해설 포함

### 데이터 활용 계획

#### 1. 점자 변환 모델 학습
```
입력: 한글 텍스트 (강의 대본 + PDF)
출력: 점자 변환 결과
문맥: 강 번호, 주제, 난이도
```

**학습 데이터 예시**:
```json
{
  "input": "수능특강 문학 2026 01강 교과서 개념",
  "text": "문학 작품을 이해하기 위해서는...",
  "braille": "⠍⠝⠤⠞⠤⠃⠤⠃ ⠍⠝⠤⠤ ⠃⠃⠃⠃ ⠃⠃⠛ ⠛⠛⠛⠛⠛⠛⠛⠛⠛⠛",
  "context": {
    "lesson": 1,
    "category": "교과서_개념",
    "difficulty": "고3_기본"
  }
}
```

#### 2. 추천 시스템 학습
- **강의 순서 정보**: 한글 파일명에서 강 번호 추출 → 학습 경로 추천
- **주제별 분류**: 카테고리 정보 활용 → 주제 기반 추천
- **난이도 정보**: "고3_기본" 등 → 난이도별 추천

#### 3. 생성형 AI Few-shot 학습
- **문제 해설 생성**: PDF의 문제와 해설을 Few-shot 예제로 활용
- **지문 요약**: 긴 지문을 요약하는 예제 수집

---

## 🎯 마일스톤 및 성공 지표

### Milestone 1: 데이터 인프라 및 제작 자동화 완성 (3주)
- ✅ 한글 파일 처리 기능 완성
- ✅ **제작 프로세스 자동화 시스템 완성** (우선)
  - ✅ 말하는 단위 자동 분할
  - ✅ 매뉴얼 규칙 자동 검증
  - ✅ 기호 사용 규칙 자동 적용
- ✅ 데이터셋 구축 스크립트 실행 성공
- ✅ 최소 200,000자 이상의 학습 데이터 확보 (44개 강)
- ✅ 강의 구조 파싱 완료 (00강~43강)
- ✅ 섹션별 데이터 분리 (개념, 핵심 포인트, 문제, 기출)

### Milestone 2: 동기화 및 점자 변환 ML 모델 MVP (10주)
- ✅ **강의 음성-텍스트 자동 동기화 완성** (우선)
  - ✅ STT 기반 음성-텍스트 매칭
  - ✅ 실시간 동기화 기능
  - ✅ 알림음 기반 수동 동기화 개선
- ✅ 점자 변환 ML 모델 학습 완료 (BLEU Score 0.80 이상)
- ✅ 프로덕션 환경 배포
- ✅ 기존 규칙 기반 대비 정확도 10% 이상 향상

### Milestone 3: 추천 시스템 MVP (4주)
- ✅ 추천 API 정상 작동
- ✅ "오늘 학습 이어하기" 기능에 통합
- ✅ 강의 순서 기반 추천 (00강→01강→...→43강)
- ✅ 틀린 문제 기반 복습 강의 추천
- ✅ **소규모 사용자 최적화** (개인화 중심, 협업 필터링 대신)
- ✅ 추천 정확도 60% 이상
- ✅ 사용자 학습 완료율 15% 이상 증가

### Milestone 4: 생성형 AI 콘텐츠 생성 (4주)
- ✅ 문제 해설 자동 생성 기능 완성
  - "기출 탈탈 털어 쏙쏙 뽑아" 섹션에 통합
  - "틀린 문제 복습하기" 화면에 상세 해설 제공
- ✅ 핵심 포인트 자동 요약 기능
  - "꼭 집어 핵심 포인트" 섹션에 통합
  - 점자 학습에 적합한 길이로 자동 요약 (200자 이내)
- ✅ 개념 설명 보강 기능
- ✅ **제작자용 강의 대본 자동 생성** (이중 목표)
- ✅ 사용자 만족도 70% 이상

---

## 🔧 개발 환경 설정

### 로컬 개발 환경
```bash
# 1. Python 가상환경 생성
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 2. 의존성 설치
cd api
pip install -r requirements.txt

# 3. 데이터 디렉토리 구조 생성
mkdir -p data/{lecture_scripts,pdfs,datasets,models}

# 4. 한글 파일 및 PDF 파일 배치
# data/lecture_scripts/ 에 한글 파일 복사
# data/pdfs/ 에 PDF 파일 복사
```

### Docker 환경 (ML 모델 서빙)
```dockerfile
# Dockerfile.ml
FROM pytorch/pytorch:2.0.0-cuda11.7-cudnn8-runtime

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
CMD ["python", "app/main.py"]
```

---

## 📊 예상 데이터 통계

### 데이터셋 구축 후 예상 통계
- **총 텍스트량**: 약 1,360,000자
  - 한글 파일: 200,000자
  - PDF 파일: 500,000자
  - 실제 강의 대본: 660,000자 (44강 × 15,000자)
- **점자 변환 쌍**: 약 1,360,000개
- **강의 수**: 44개 (00강~43강)
- **교재 수**: 10개 이상 (PDF 기준)
- **주제 카테고리**: 8개 (교과서 개념, 고전 시가, 현대시, 고전 산문, 현대 소설, 극/수필, 갈래 복합, 실전)
- **섹션 타입**: 6개 이상
  - 인트로
  - 개념 설명
  - 작품 분석
  - 문제 풀이
  - 기출 탈탈 털어 쏙쏙 뽑아
  - 한 판에 담판 (요약)

### 학습 데이터 분할
- **Train**: 1,088,000자 (80%)
- **Validation**: 136,000자 (10%)
- **Test**: 136,000자 (10%)

**실제 대본 기반 검증**:
- 제공된 1강 대본(약 15,000자)을 Test 세트로 활용 가능
- 실제 사용 패턴과 일치하는 데이터로 검증

### 강의별 데이터 분포
- **00강 오리엔테이션**: 약 2,000자
- **01강~05강 (교과서 개념)**: 각 약 4,000자
- **06강~15강 (시가/현대시)**: 각 약 4,500자
- **16강~26강 (산문/소설)**: 각 약 5,000자
- **27강~39강 (극/수필/갈래 복합)**: 각 약 4,500자
- **40강~43강 (실전 문제)**: 각 약 6,000자

---

## 🚀 빠른 시작 가이드

### 1단계: 데이터 준비 (1일)
```bash
# 한글 파일과 PDF 파일을 적절한 디렉토리에 배치
cp /path/to/hwp/files/* data/lecture_scripts/
cp /path/to/pdf/files/* data/pdfs/
```

### 2단계: 데이터셋 구축 (1일)
```bash
# 데이터셋 구축 스크립트 실행
python scripts/build_training_dataset.py

# 결과 확인
cat data/datasets/braille_dataset.json | jq '.items | length'
```

### 3단계: 모델 학습 시작 (선택)
```bash
# 점자 변환 모델 학습
python training/train_braille_model.py \
  --dataset data/datasets/braille_dataset.json \
  --output_dir models/braille_converter \
  --epochs 10
```

---

## 💡 추가 고려사항

### 소규모 사용자 특화 전략

#### 1. 개인화 중심 접근
- **협업 필터링 대신**: 콘텐츠 기반 + 규칙 기반 추천
- **심층 개인 분석**: 각 사용자의 학습 패턴 상세 분석
- **빠른 피드백 반영**: 소규모이므로 피드백을 즉시 반영 가능

#### 2. 사용자 확대 전략

**타겟 사용자 전환**:
- **고3 학생**: 수능 준비로 시간 부족 → 새로운 방법 학습 부담
- **예비고 학생**: 학습 방법 탐색 단계 → **주요 타겟**
- **보호자와 함께 학습**: 보호자가 화면 설명하는 경우 → 텍스트 자료로 대체 가능

**학습자 유형별 접근**:
1. **주도적 탐색형**: 
   - 자가 학습 가이드 제공
   - 자료 탐색 기능 강화
2. **제공 시도형**:
   - 단계별 튜토리얼
   - 사용법 안내 강화
3. **외부 도움 필요형**:
   - 상세 가이드 + 지원 연락처
   - 원격 지원 기능

**온보딩 자동화**:
- 학습자 유형별 맞춤 온보딩
- 접근성 교육 통합: 웹 접근성 교육을 앱 내에 통합
- 실시간 도움말: 사용 중 도움말 제공

#### 3. 제작자 확대 전략
- **자동화로 제작 시간 단축**: 더 많은 제작자 참여 유도
- **품질 관리 자동화**: 검수 시간 단축
- **교육 효율화**: 온라인/오프라인 하이브리드 교육

### 데이터 품질 관리
- **검증**: 추출된 텍스트의 품질 검증 (인코딩, 특수문자 처리)
- **중복 제거**: 동일한 콘텐츠의 중복 제거
- **라벨링**: 수동 검수 및 라벨링 (필요 시)

### 확장성 고려
- **증분 학습**: 새로운 데이터 추가 시 모델 재학습
- **버전 관리**: 데이터셋 버전 관리 (Git LFS 또는 별도 스토리지)
- **자동화**: 데이터셋 구축 파이프라인 자동화 (Cron 또는 CI/CD)

### 법적/윤리적 고려사항
- **저작권**: 교재 데이터 사용 시 저작권 확인
- **개인정보**: 사용자 데이터 수집 시 개인정보 보호
- **데이터 보관**: 학습 데이터 보관 정책 수립

---

*작성일: 2024년*
*마지막 업데이트: 2024년*
