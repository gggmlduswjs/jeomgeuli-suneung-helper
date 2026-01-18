# AI/ML 기능 구현 아이디어 가이드

점글이 수능 헬퍼 프로젝트에 AI/ML 전문가가 구현할 수 있는 기능 아이디어와 구현 방안을 정리한 문서입니다.

## 📋 목차

1. [개요](#개요)
2. [즉시 시작 가능한 기능](#즉시-시작-가능한-기능)
3. [중기 구현 기능](#중기-구현-기능)
4. [장기 구현 기능](#장기-구현-기능)
5. [기술 스택 요약](#기술-스택-요약)
6. [구현 우선순위](#구현-우선순위)

---

## 개요

### 현재 프로젝트 상태

- **Phase 0**: 약 60% 완료 (데이터 인프라 구축)
- **Phase 1 (AI/ML)**: 약 10% 완료
  - ✅ 기본 구조만 존재
  - ❌ 실제 ML 모델 미구현
  - ❌ 생성형 AI 미구현

### AI/ML 전문가가 필요한 이유

1. **전통적인 머신러닝 이론과 알고리즘** 이해
2. **CNN, RNN, Transformer** 기반 모델 구조 이해
3. **LLM을 포함한 생성형 AI** 기술 활용
4. **Scikit-learn, PyTorch, LangChain, Hugging Face** 능숙한 활용
5. **실제 동작하는 AI 애플리케이션** 설계 및 구현

---

## 즉시 시작 가능한 기능

### 1. 강의 음성-텍스트 자동 동기화 ⭐⭐⭐⭐⭐

**현재 상태**: 기본 구조만 있음 (10%)

**왜 필요한가?**
- 사용자 피드백에서 **가장 큰 불편사항**
- 알림음 기반 수동 동기화를 자동화로 개선
- 학습 효율성 30% 향상 예상

**구현 아이디어**:

```python
# api/app/services/audio_sync_ml.py
import whisper
from sentence_transformers import SentenceTransformer
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

class AudioTextSyncML:
    """Whisper 기반 실시간 STT + 텍스트 매칭"""
    
    def __init__(self):
        # Whisper 모델 로드 (한국어 최적화)
        self.whisper = whisper.load_model("large-v2")
        # 텍스트 임베딩 (sentence-transformers)
        self.text_encoder = SentenceTransformer('jhgan/ko-sroberta-multitask')
        
    def sync_audio_to_text(self, audio_chunk, lesson_texts):
        """
        음성 청크를 텍스트와 동기화
        
        Args:
            audio_chunk: 오디오 데이터 (numpy array)
            lesson_texts: 강의 텍스트 리스트 (청크 단위)
            
        Returns:
            matched_index: 매칭된 텍스트 인덱스
            matched_text: 매칭된 텍스트
            confidence: 신뢰도 (0-1)
        """
        # 1. STT로 음성 → 텍스트 변환
        transcript = self.whisper.transcribe(
            audio_chunk,
            language='ko',
            task='transcribe'
        )
        
        # 2. 텍스트 임베딩으로 유사도 계산
        audio_embedding = self.text_encoder.encode(transcript['text'])
        text_embeddings = self.text_encoder.encode(lesson_texts)
        
        # 3. 코사인 유사도로 매칭
        similarities = cosine_similarity([audio_embedding], text_embeddings)
        matched_index = np.argmax(similarities[0])
        confidence = similarities[0][matched_index]
        
        return matched_index, lesson_texts[matched_index], confidence
    
    def real_time_sync(self, audio_stream, lesson_texts, callback):
        """
        실시간 동기화 (스트리밍)
        
        Args:
            audio_stream: 오디오 스트림
            lesson_texts: 강의 텍스트 리스트
            callback: 매칭 결과를 받을 콜백 함수
        """
        for audio_chunk in audio_stream:
            matched_index, matched_text, confidence = self.sync_audio_to_text(
                audio_chunk, lesson_texts
            )
            
            if confidence > 0.7:  # 신뢰도 임계값
                callback(matched_index, matched_text)
```

**기술 스택**:
- **Whisper** (OpenAI) - 한국어 fine-tuning 가능
- **Sentence Transformers** - 텍스트 유사도 계산
- **NumPy, Scikit-learn** - 수치 계산

**구현 단계**:
1. Whisper 모델 통합 (1주)
2. 텍스트 임베딩 시스템 구축 (1주)
3. 실시간 스트리밍 처리 (1주)
4. 프론트엔드 통합 (1주)

**예상 기간**: 3-4주

**예상 효과**:
- 학습 효율성 30% 향상
- 사용자 만족도 대폭 증가
- 동기화 정확도 90% 이상

---

### 2. 생성형 AI 콘텐츠 생성 (LLM 활용) ⭐⭐⭐⭐

**현재 상태**: 미구현

**왜 필요한가?**
- 문제 해설 자동 생성으로 제작 시간 단축
- 학습자 맞춤형 해설 제공
- 강의 핵심 포인트 자동 요약

**구현 아이디어**:

```python
# api/app/services/content_generator.py
from langchain.chat_models import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.chains import LLMChain

class ContentGenerator:
    """LangChain + OpenAI 기반 콘텐츠 생성"""
    
    def __init__(self):
        self.llm = ChatOpenAI(
            model="gpt-4-turbo",
            temperature=0.3,  # 일관성 있는 출력
            max_tokens=1000
        )
        self.explanation_chain = self._create_explanation_chain()
        self.summary_chain = self._create_summary_chain()
        
    def _create_explanation_chain(self):
        """문제 해설 생성 체인"""
        prompt = ChatPromptTemplate.from_template("""
        당신은 시각장애 학생을 위한 수능 문제 해설 전문가입니다.
        
        다음 조건을 만족하는 해설을 생성하세요:
        1. 점자로 읽기 쉬운 구조 (말하는 단위로 끊기)
        2. 핵심 포인트를 명확히 제시
        3. 오답 이유를 구체적으로 설명
        4. 관련 개념을 간단히 언급
        
        문제: {question}
        학생 답: {user_answer}
        정답: {correct_answer}
        문제 유형: {question_type}
        
        해설:
        """)
        
        return LLMChain(llm=self.llm, prompt=prompt)
    
    def generate_explanation(self, question, user_answer, correct_answer, question_type):
        """
        문제 해설 자동 생성
        
        Args:
            question: 문제 내용
            user_answer: 학생이 선택한 답
            correct_answer: 정답
            question_type: 문제 유형 (문학, 수학 등)
            
        Returns:
            explanation: 생성된 해설
        """
        explanation = self.explanation_chain.run(
            question=question,
            user_answer=user_answer,
            correct_answer=correct_answer,
            question_type=question_type
        )
        
        return explanation
    
    def generate_summary(self, lesson_content):
        """
        강의 핵심 포인트 요약
        
        Args:
            lesson_content: 강의 전체 내용
            
        Returns:
            summary: 3줄 요약
        """
        prompt = ChatPromptTemplate.from_template("""
        다음 강의 내용을 시각장애 학생이 이해하기 쉽게 3줄로 요약하세요.
        각 줄은 점자로 읽기 쉬운 길이로 작성하세요.
        
        강의 내용:
        {lesson_content}
        
        요약:
        """)
        
        chain = LLMChain(llm=self.llm, prompt=prompt)
        summary = chain.run(lesson_content=lesson_content)
        
        return summary
    
    def generate_lecture_script_draft(self, topic, outline):
        """
        제작자용: 강의 대본 초안 생성
        
        Args:
            topic: 강의 주제
            outline: 강의 개요
            
        Returns:
            draft: 강의 대본 초안
        """
        prompt = ChatPromptTemplate.from_template("""
        수능 강의 대본 초안을 작성하세요.
        
        주제: {topic}
        개요: {outline}
        
        다음 구조를 따르세요:
        1. 오리엔테이션 (OT)
        2. 개요 (Overview)
        3. 개념 설명 (Concept)
        4. 예제 (Example)
        5. 핵심 포인트 (Key Points)
        
        대본:
        """)
        
        chain = LLMChain(llm=self.llm, prompt=prompt)
        draft = chain.run(topic=topic, outline=outline)
        
        return draft
```

**기술 스택**:
- **LangChain** - 프롬프트 체인 관리
- **OpenAI GPT-4** / **Claude** - 생성형 AI 모델
- **프롬프트 엔지니어링** - Few-shot learning

**구현 단계**:
1. LangChain 기본 구조 구축 (3일)
2. 프롬프트 템플릿 작성 (3일)
3. API 엔드포인트 구현 (3일)
4. 비용 모니터링 시스템 (3일)
5. 프론트엔드 통합 (1주)

**예상 기간**: 2-3주

**예상 효과**:
- 문제 해설 생성 시간 90% 단축
- 제작자 작업 효율 향상
- 학습자 맞춤형 콘텐츠 제공

---

## 중기 구현 기능

### 3. 문맥 인식 점자 변환 ML 모델 ⭐⭐⭐

**현재 상태**: 규칙 기반만 있음

**왜 필요한가?**
- 규칙 기반 변환의 한계 극복
- 문맥을 이해하는 정확한 점자 변환
- 동음이의어 처리 개선

**구현 아이디어**:

```python
# api/app/services/braille_ml.py
import torch
from transformers import (
    AutoTokenizer,
    AutoModelForSeq2Seq,
    TrainingArguments,
    Trainer
)
from datasets import Dataset

class ContextualBrailleConverter:
    """Seq2Seq Transformer 기반 점자 변환"""
    
    def __init__(self, model_path='./models/braille-converter'):
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        
        # KoBERT 기반 Encoder-Decoder 모델
        self.tokenizer = AutoTokenizer.from_pretrained('monologg/kobert-base-v1')
        self.model = AutoModelForSeq2Seq.from_pretrained(model_path)
        self.model.to(self.device)
        self.model.eval()
        
        # 문맥 윈도우 (앞뒤 3문장)
        self.context_window = 3
        
    def convert_with_context(self, text, context_before="", context_after=""):
        """
        문맥을 고려한 점자 변환
        
        Args:
            text: 변환할 텍스트
            context_before: 앞 문맥
            context_after: 뒤 문맥
            
        Returns:
            braille_text: 점자 변환 결과
        """
        # 문맥 정보를 포함한 입력
        input_text = f"{context_before} [SEP] {text} [SEP] {context_after}"
        
        # 토크나이징
        inputs = self.tokenizer(
            input_text,
            return_tensors='pt',
            padding=True,
            truncation=True,
            max_length=512
        ).to(self.device)
        
        # 모델 추론
        with torch.no_grad():
            outputs = self.model.generate(
                **inputs,
                max_length=512,
                num_beams=5,
                early_stopping=True
            )
        
        # 디코딩
        braille_text = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
        
        return braille_text
    
    def train(self, train_dataset, val_dataset):
        """
        모델 학습
        
        Args:
            train_dataset: 학습 데이터셋
            val_dataset: 검증 데이터셋
        """
        training_args = TrainingArguments(
            output_dir='./models/braille-converter',
            num_train_epochs=10,
            per_device_train_batch_size=16,
            per_device_eval_batch_size=16,
            warmup_steps=500,
            weight_decay=0.01,
            logging_dir='./logs',
            logging_steps=100,
            evaluation_strategy="epoch",
            save_strategy="epoch",
            load_best_model_at_end=True,
        )
        
        trainer = Trainer(
            model=self.model,
            args=training_args,
            train_dataset=train_dataset,
            eval_dataset=val_dataset,
        )
        
        trainer.train()
```

**데이터셋 구축**:
- 현재 프로젝트에 약 585,000자 데이터 있음
- 한글-점자 병렬 코퍼스 자동 생성
- 데이터 증강 (동의어, 문장 순서 변경)

**기술 스택**:
- **PyTorch** - 딥러닝 프레임워크
- **Transformers (Hugging Face)** - 사전 학습 모델
- **KoBERT/KoGPT** - 한국어 사전 학습 모델
- **Datasets** - 데이터셋 관리

**구현 단계**:
1. 데이터셋 구축 및 전처리 (2주)
2. 모델 아키텍처 설계 (1주)
3. 모델 학습 및 튜닝 (3주)
4. 모델 서빙 인프라 (1주)
5. 기존 규칙 기반과 병행 (Fallback) (1주)
6. 프론트엔드 통합 (1주)

**예상 기간**: 8-10주

**예상 효과**:
- 동음이의어 처리 개선
- 문맥에 따른 약자 선택 최적화
- 정확도 향상 (현재 85% → 목표 95%+)
- BLEU Score 0.85 이상

---

### 4. 학습자 맞춤형 추천 시스템 ⭐⭐⭐

**현재 상태**: 미구현

**왜 필요한가?**
- 소규모 사용자(9명) 최적화
- 개인화된 학습 경험 제공
- 학습 완료율 20% 증가 예상

**구현 아이디어**:

```python
# api/app/services/recommendation_engine.py
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
from typing import List, Dict

class PersonalizedRecommender:
    """콘텐츠 기반 + 협업 필터링 하이브리드"""
    
    def __init__(self):
        # 콘텐츠 임베딩 (BERT 기반)
        self.content_encoder = SentenceTransformer('jhgan/ko-sroberta-multitask')
        self.user_profiler = UserBehaviorProfiler()
        
    def recommend_next_lesson(self, user_id: str, current_progress: Dict) -> List[Dict]:
        """
        다음 강의 추천
        
        Args:
            user_id: 사용자 ID
            current_progress: 현재 진행 상황
            
        Returns:
            recommended_lessons: 추천 강의 리스트
        """
        # 1. 사용자 프로필 생성
        user_profile = self.user_profiler.get_profile(user_id)
        # - 학습 패턴 (시간대, 속도, 선호 과목)
        # - 오답 패턴 (약점 주제)
        # - 학습 스타일 (빠른 진행 vs 꼼꼼한 복습)
        
        # 2. 콘텐츠 기반 필터링
        candidate_lessons = self.get_candidate_lessons(current_progress)
        lesson_embeddings = self.content_encoder.encode(
            [lesson['content'] for lesson in candidate_lessons]
        )
        
        # 3. 사용자 선호도와 매칭
        user_preference = self._calculate_user_preference(user_profile)
        scores = cosine_similarity([user_preference], lesson_embeddings)[0]
        
        # 4. 강의 순서 규칙 적용 (00강→01강→...)
        recommended = self._apply_lesson_order_rules(
            candidate_lessons, scores, current_progress
        )
        
        return recommended
    
    def recommend_review(self, user_id: str) -> List[Dict]:
        """
        복습 추천 (오답 패턴 기반)
        
        Args:
            user_id: 사용자 ID
            
        Returns:
            review_items: 복습 항목 리스트
        """
        # 1. 오답 이력 분석
        wrong_answers = self.user_profiler.get_wrong_answers(user_id)
        
        # 2. 약점 주제 추출
        weak_topics = self._identify_weak_topics(wrong_answers)
        
        # 3. 관련 강의 추천
        related_lessons = self._find_related_lessons(weak_topics)
        
        # 4. 간격 반복 학습 알고리즘 적용
        review_schedule = self._apply_spaced_repetition(related_lessons, wrong_answers)
        
        return review_schedule
    
    def _calculate_user_preference(self, user_profile: Dict) -> np.ndarray:
        """사용자 선호도 벡터 계산"""
        # 학습 시간대, 속도, 선호 과목 등을 벡터로 변환
        preference_vector = np.zeros(768)  # BERT embedding dimension
        
        # 예시: 선호 과목 가중치
        if user_profile.get('preferred_subject') == 'korean':
            preference_vector[:256] += 0.3
        elif user_profile.get('preferred_subject') == 'math':
            preference_vector[256:512] += 0.3
        else:
            preference_vector[512:] += 0.3
        
        return preference_vector
    
    def _apply_lesson_order_rules(self, lessons: List[Dict], scores: np.ndarray, 
                                   current_progress: Dict) -> List[Dict]:
        """강의 순서 규칙 적용"""
        # 00강 → 01강 → ... 순서 유지
        sorted_lessons = sorted(
            zip(lessons, scores),
            key=lambda x: (x[0]['lesson_number'], -x[1])
        )
        
        return [lesson for lesson, score in sorted_lessons[:5]]  # 상위 5개
```

**특징**:
- 소규모 사용자(9명) 대응: 개인화 중심
- 오답 패턴 기반 복습 추천
- 학습 시간대 분석

**기술 스택**:
- **Scikit-learn** - 콘텐츠 기반 필터링
- **Sentence Transformers** - 텍스트 임베딩
- **NumPy** - 수치 계산
- 사용자 행동 로깅 시스템

**구현 단계**:
1. 사용자 행동 데이터 수집 시스템 (1주)
2. 사용자 프로파일링 시스템 (1주)
3. 추천 엔진 구현 (1주)
4. API 엔드포인트 구현 (3일)
5. 프론트엔드 통합 (3일)

**예상 기간**: 4주

**예상 효과**:
- 학습 완료율 20% 증가
- 학습 효율성 향상
- 추천 정확도 60% 이상 (사용자가 추천 콘텐츠를 학습하는 비율)

---

## 장기 구현 기능

### 5. PDF 구조 자동 분류 (Vision Transformer) ⭐⭐

**현재 상태**: 정규식 기반만 있음

**구현 아이디어**:

```python
# api/app/services/pdf_structure_classifier.py
from transformers import LayoutLMv3Processor, LayoutLMv3ForSequenceClassification
from PIL import Image
import torch

class PDFStructureClassifier:
    """Vision Transformer 기반 레이아웃 분석"""
    
    def __init__(self):
        # LayoutLMv3 모델 (이미지 + 텍스트 통합 분석)
        self.processor = LayoutLMv3Processor.from_pretrained(
            'microsoft/layoutlmv3-base'
        )
        self.model = LayoutLMv3ForSequenceClassification.from_pretrained(
            './models/pdf-structure-classifier'
        )
        self.model.eval()
        
    def classify_blocks(self, pdf_page_image: Image, text_blocks: List[Dict]) -> List[Dict]:
        """
        PDF 블록 구조 분류
        
        Args:
            pdf_page_image: PDF 페이지 이미지
            text_blocks: 텍스트 블록 리스트 (bbox 포함)
            
        Returns:
            classified_blocks: 분류된 블록 리스트
        """
        # 1. 이미지 + 텍스트 통합 분석
        inputs = self.processor(
            pdf_page_image,
            text_blocks,
            return_tensors="pt",
            padding=True
        )
        
        # 2. 구조 분류 (문제/지문/선택지/그림/표)
        with torch.no_grad():
            outputs = self.model(**inputs)
            predictions = torch.nn.functional.softmax(outputs.logits, dim=-1)
        
        # 3. 분류 결과 매핑
        class_labels = ['문제', '지문', '선택지', '그림', '표', '기타']
        classified_blocks = []
        
        for i, block in enumerate(text_blocks):
            predicted_class = class_labels[predictions[i].argmax().item()]
            confidence = predictions[i].max().item()
            
            classified_blocks.append({
                'text': block['text'],
                'bbox': block['bbox'],
                'class': predicted_class,
                'confidence': confidence
            })
        
        return classified_blocks
```

**기술 스택**:
- **LayoutLMv3** (Microsoft) - 이미지 + 텍스트 멀티모달
- **Vision Transformer** - 이미지 분석
- **PyTorch** - 딥러닝 프레임워크

**예상 기간**: 6-8주

---

### 6. 제작 프로세스 AI 자동화 완성 ⭐⭐⭐⭐

**현재 상태**: 기본 구조만 있음 (50%)

**구현 아이디어**:

```python
# api/app/services/content_auto_generator_ml.py
from langchain.chat_models import ChatOpenAI
from langchain.chains import LLMChain
from langchain.prompts import ChatPromptTemplate

class ContentAutoGeneratorML:
    """LangChain 기반 제작 자동화"""
    
    def __init__(self):
        self.llm = ChatOpenAI(model="gpt-4-turbo", temperature=0.2)
        self.rule_validator = ManualRuleValidator()
        
    def auto_generate_content(self, raw_text: str) -> Dict:
        """
        원본 텍스트를 자동으로 학습 자료로 변환
        
        Args:
            raw_text: 원본 텍스트 (한글 파일 등)
            
        Returns:
            structured_content: 구조화된 학습 자료
        """
        # 1. 매뉴얼 규칙 자동 적용
        structured = self.apply_manual_rules(raw_text)
        
        # 2. 말하는 단위 자동 분할 (문맥 고려)
        chunks = self.split_into_speaking_units(structured)
        
        # 3. 기호 사용 규칙 검증
        validated = self.rule_validator.validate(chunks)
        
        # 4. 정보 순서 최적화
        optimized = self.optimize_information_order(validated)
        
        # 5. 품질 점수 계산
        quality_score = self.calculate_quality_score(optimized)
        
        return {
            'content': optimized,
            'quality_score': quality_score,
            'suggestions': self.generate_improvement_suggestions(optimized)
        }
    
    def apply_manual_rules(self, text: str) -> str:
        """매뉴얼 규칙 자동 적용"""
        prompt = ChatPromptTemplate.from_template("""
        다음 텍스트에 수능 학습 자료 제작 매뉴얼 규칙을 적용하세요:
        
        1. 원숫자(①②③)는 문제 선지용이므로 설명에는 다른 기호 사용
        2. 유형 정보를 앞에, 시간 정보는 뒤로 배치
        3. 말하는 단위로 끊기 (너무 길지 않게)
        
        원본 텍스트:
        {text}
        
        변환된 텍스트:
        """)
        
        chain = LLMChain(llm=self.llm, prompt=prompt)
        return chain.run(text=text)
```

**예상 기간**: 4-6주

**예상 효과**:
- 제작 시간 80% 단축
- 품질 점수 90점 이상 달성
- 제작자 검수 시간 80% 단축

---

## 기술 스택 요약

### 딥러닝
- **PyTorch** - 딥러닝 프레임워크
- **Transformers (Hugging Face)** - 사전 학습 모델
- **KoBERT/KoGPT** - 한국어 사전 학습 모델

### 생성형 AI
- **LangChain** - 프롬프트 체인 관리
- **OpenAI GPT-4** / **Claude** - LLM 모델
- **프롬프트 엔지니어링** - Few-shot learning

### 음성 처리
- **Whisper (OpenAI)** - STT (Speech-to-Text)
- **Sentence Transformers** - 텍스트 임베딩

### 추천 시스템
- **Scikit-learn** - 전통적인 ML 알고리즘
- **Sentence Transformers** - 콘텐츠 기반 필터링
- **NumPy** - 수치 계산

### Vision
- **LayoutLMv3** - 이미지 + 텍스트 멀티모달
- **Vision Transformer** - 이미지 분석

---

## 구현 우선순위

### 즉시 시작 (High Impact, Medium Effort)

1. **강의 음성-텍스트 자동 동기화** (3-4주) ⭐⭐⭐⭐⭐
   - 사용자 피드백에서 가장 큰 불편사항
   - Whisper + Sentence Transformers 조합
   - 예상 효과: 학습 효율성 30% 향상

2. **생성형 AI 콘텐츠 생성** (2-3주) ⭐⭐⭐⭐
   - 문제 해설 자동 생성
   - LangChain + GPT-4 활용
   - 예상 효과: 제작 시간 90% 단축

### 중기 구현 (High Impact, High Effort)

3. **문맥 인식 점자 변환 ML 모델** (8-10주) ⭐⭐⭐
   - 데이터셋 구축부터 모델 학습까지
   - KoBERT 기반 Seq2Seq
   - 예상 효과: 정확도 85% → 95%+

4. **학습자 맞춤형 추천 시스템** (4주) ⭐⭐⭐
   - 콘텐츠 기반 필터링
   - 사용자 행동 분석
   - 예상 효과: 학습 완료율 20% 증가

### 장기 구현 (Nice to Have)

5. **PDF 구조 자동 분류** (6-8주) ⭐⭐
   - Vision Transformer 활용
   - 레이아웃 분석

6. **제작 프로세스 완전 자동화** (4-6주) ⭐⭐⭐⭐
   - LangChain 기반 자동화
   - 품질 점수 자동 계산

---

## 즉시 시작 가능한 프로젝트

### 추천: 강의 음성-텍스트 자동 동기화

**이유**:
1. ✅ 사용자 피드백에서 **가장 큰 불편사항**
2. ✅ 구현 난이도: **중간** (Whisper 활용)
3. ✅ 예상 효과: **학습 효율성 30% 향상**
4. ✅ 기존 코드베이스와 통합 용이

**시작 방법**:
1. `api/app/services/audio_sync_ml.py` 파일 생성
2. Whisper 모델 통합
3. Sentence Transformers로 텍스트 임베딩
4. 실시간 동기화 로직 구현
5. 프론트엔드 통합

---

## 참고 자료

- [Whisper 공식 문서](https://github.com/openai/whisper)
- [LangChain 공식 문서](https://python.langchain.com/)
- [Hugging Face Transformers](https://huggingface.co/docs/transformers)
- [Sentence Transformers](https://www.sbert.net/)
- [KoBERT GitHub](https://github.com/SKTBrain/KoBERT)

---

*작성일: 2024년*  
*마지막 업데이트: 2024년*
