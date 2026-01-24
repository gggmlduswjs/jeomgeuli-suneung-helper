"""
ML 기반 섹션 타입 분류 서비스
Hugging Face Transformers를 사용한 섹션 타입 자동 분류
"""
from typing import Dict, Any, Optional, List
import numpy as np

try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False
    print("[MLSectionClassifier] sentence-transformers가 설치되지 않았습니다. pip install sentence-transformers")

try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.linear_model import LogisticRegression
    from sklearn.pipeline import Pipeline
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    print("[MLSectionClassifier] scikit-learn이 설치되지 않았습니다. pip install scikit-learn")

from app.services.ml_content_similarity import MLContentSimilarity


class MLSectionClassifier:
    """
    ML 기반 섹션 타입 분류기
    
    기능:
    - 섹션 타입 자동 분류 (개념/본문/문제/일반)
    - 작품 자동 감지 (작품 텍스트 vs 일반 설명)
    - 문제 자동 감지
    """
    
    # 섹션 타입별 예시 텍스트 (임베딩 기반 유사도 계산용)
    SECTION_TYPE_EXAMPLES = {
        "concept": [
            "개념 설명 형상화는 시의 주제를 형상화하는 표현 기법입니다.",
            "비유와 상징은 문학 작품에서 중요한 표현 수단입니다.",
            "이론과 개념을 설명하는 부분입니다."
        ],
        "content": [
            "작품 본문 시나 소설의 실제 내용입니다.",
            "「해」 - 박두진, 하늘이 맑다.",
            "시나 산문의 실제 작품 내용이 담겨 있습니다."
        ],
        "problem": [
            "다음 중 밑줄 친 부분의 의미를 바르게 해석한 것은?",
            "문제 1번 다음 시의 표현 기법을 설명하시오.",
            "이 문제의 정답을 선택하세요."
        ],
        "example": [
            "예시로 다음을 살펴보겠습니다.",
            "예를 들어 다음과 같은 경우가 있습니다.",
            "실제 사례를 통해 설명하겠습니다."
        ],
        "general": [
            "일반적인 설명과 안내입니다.",
            "추가 정보나 참고 사항입니다."
        ]
    }
    
    def __init__(
        self,
        use_similarity_classifier: bool = True,
        model_name: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    ):
        """
        Args:
            use_similarity_classifier: 유사도 기반 분류기 사용 여부 (True면 임베딩 유사도 사용)
            model_name: Sentence Transformer 모델명
        """
        self.use_similarity_classifier = use_similarity_classifier
        self.model_name = model_name
        self.similarity_service: Optional[MLContentSimilarity] = None
        self.example_embeddings: Dict[str, np.ndarray] = {}
        
        if use_similarity_classifier and SENTENCE_TRANSFORMERS_AVAILABLE:
            self._load_similarity_service()
            self._precompute_example_embeddings()
    
    def _load_similarity_service(self):
        """유사도 계산 서비스 로드"""
        try:
            self.similarity_service = MLContentSimilarity(
                model_name=self.model_name,
                enable_cache=True  # 캐싱 활성화
            )
        except Exception as e:
            print(f"[MLSectionClassifier] 유사도 서비스 로드 실패: {e}")
            self.similarity_service = None
    
    def _precompute_example_embeddings(self):
        """섹션 타입별 예시 텍스트 임베딩 사전 계산"""
        if not self.similarity_service or not self.similarity_service.model:
            return
        
        try:
            for section_type, examples in self.SECTION_TYPE_EXAMPLES.items():
                # 예시 텍스트들의 평균 임베딩 계산
                embeddings = self.similarity_service.encode(examples)
                if len(embeddings) > 0:
                    self.example_embeddings[section_type] = np.mean(embeddings, axis=0)
            
            print(f"[MLSectionClassifier] 예시 임베딩 사전 계산 완료: {len(self.example_embeddings)}개 타입")
        except Exception as e:
            print(f"[MLSectionClassifier] 예시 임베딩 계산 실패: {e}")
    
    def classify_section_type(
        self,
        title: str = "",
        content: str = "",
        threshold: float = 0.5
    ) -> Dict[str, Any]:
        """
        섹션 타입 분류
        
        Args:
            title: 섹션 제목
            content: 섹션 내용
            threshold: 유사도 임계값 (0.0 ~ 1.0)
        
        Returns:
            {
                "section_type": str,  # 예측된 섹션 타입
                "confidence": float,   # 신뢰도 (0.0 ~ 1.0)
                "scores": Dict[str, float]  # 각 타입별 점수
            }
        """
        # 제목과 내용 결합
        combined_text = f"{title}\n{content}".strip()
        
        if not combined_text:
            return {
                "section_type": "general",
                "confidence": 0.0,
                "scores": {}
            }
        
        # 유사도 기반 분류
        if self.use_similarity_classifier and self.similarity_service and len(self.example_embeddings) > 0:
            return self._classify_by_similarity(combined_text, threshold)
        
        # Fallback: 기본 정규식 기반 분류
        return self._classify_by_regex(title, content)
    
    def _classify_by_similarity(
        self,
        text: str,
        threshold: float
    ) -> Dict[str, Any]:
        """임베딩 유사도 기반 분류"""
        if not self.similarity_service or not self.similarity_service.model:
            return self._classify_by_regex("", text)
        
        try:
            # 입력 텍스트 임베딩
            text_embedding = self.similarity_service.encode([text])[0]
            
            # 각 섹션 타입별 유사도 계산
            scores = {}
            for section_type, example_embedding in self.example_embeddings.items():
                # 코사인 유사도 계산
                similarity = np.dot(text_embedding, example_embedding) / (
                    np.linalg.norm(text_embedding) * np.linalg.norm(example_embedding) + 1e-8
                )
                scores[section_type] = float(similarity)
            
            # 가장 유사한 타입 선택
            best_type = max(scores.items(), key=lambda x: x[1])
            
            # 임계값 체크
            if best_type[1] < threshold:
                best_type = ("general", 0.0)
            
            return {
                "section_type": best_type[0],
                "confidence": best_type[1],
                "scores": scores
            }
        except Exception as e:
            print(f"[MLSectionClassifier] 유사도 기반 분류 실패: {e}")
            return self._classify_by_regex("", text)
    
    def _classify_by_regex(self, title: str, content: str) -> Dict[str, Any]:
        """정규식 기반 분류 (Fallback)"""
        import re
        
        title_lower = title.lower()
        content_lower = content.lower()
        
        # 문제 감지
        if re.search(r'문제|problem|다음.*?고른|정답|선택지', title_lower + content_lower):
            return {
                "section_type": "problem",
                "confidence": 0.7,
                "scores": {"problem": 0.7}
            }
        
        # 개념 감지
        if re.search(r'개념|concept|정의|설명', title_lower):
            return {
                "section_type": "concept",
                "confidence": 0.7,
                "scores": {"concept": 0.7}
            }
        
        # 작품 감지 (본문)
        if re.search(r'[-]\s*[가-힣\s]+[,]?\s*「[가-힣\s]+」', content):
            return {
                "section_type": "content",
                "confidence": 0.8,
                "scores": {"content": 0.8}
            }
        
        # 예시 감지
        if re.search(r'예시|example|예를|사례', title_lower + content_lower):
            return {
                "section_type": "example",
                "confidence": 0.6,
                "scores": {"example": 0.6}
            }
        
        return {
            "section_type": "general",
            "confidence": 0.5,
            "scores": {"general": 0.5}
        }
    
    def detect_work_content(
        self,
        content: str,
        threshold: float = 0.6
    ) -> Dict[str, Any]:
        """
        작품 콘텐츠 감지
        
        Args:
            content: 텍스트 내용
            threshold: 작품 감지 임계값
        
        Returns:
            {
                "is_work": bool,       # 작품 여부
                "confidence": float,   # 신뢰도
                "work_start_index": Optional[int]  # 작품 시작 줄 인덱스
            }
        """
        if not content:
            return {
                "is_work": False,
                "confidence": 0.0,
                "work_start_index": None
            }
        
        # 정규식 기반 작품 패턴 감지
        import re
        work_pattern = r'[-]\s*[가-힣\s]+,?\s*「[가-힣\s]+」'
        if re.search(work_pattern, content):
            # 작품 시작 위치 찾기
            lines = content.split('\n')
            work_start_index = None
            for i, line in enumerate(lines):
                if re.search(work_pattern, line):
                    work_start_index = i
                    break
            
            return {
                "is_work": True,
                "confidence": 0.9,
                "work_start_index": work_start_index
            }
        
        # 유사도 기반 작품 감지
        if self.use_similarity_classifier and self.similarity_service:
            # 작품 예시와의 유사도 계산
            work_examples = self.SECTION_TYPE_EXAMPLES.get("content", [])
            if work_examples:
                try:
                    # 본문 예시와 유사도 계산
                    results = self.similarity_service.compute_similarity(
                        query_text=content[:500],  # 처음 500자만 사용
                        candidate_texts=work_examples
                    )
                    
                    if results and len(results) > 0:
                        max_similarity = results[0]["similarity"]
                        if max_similarity >= threshold:
                            return {
                                "is_work": True,
                                "confidence": float(max_similarity),
                                "work_start_index": None
                            }
                except Exception as e:
                    print(f"[MLSectionClassifier] 작품 감지 실패: {e}")
        
        return {
            "is_work": False,
            "confidence": 0.0,
            "work_start_index": None
        }
    
    def detect_problem(
        self,
        text: str,
        threshold: float = 0.6
    ) -> Dict[str, Any]:
        """
        문제 섹션 감지
        
        Args:
            text: 텍스트 내용
            threshold: 문제 감지 임계값
        
        Returns:
            {
                "is_problem": bool,    # 문제 여부
                "confidence": float,   # 신뢰도
                "question_text": Optional[str]  # 질문 텍스트 (추출 가능한 경우)
            }
        """
        if not text:
            return {
                "is_problem": False,
                "confidence": 0.0,
                "question_text": None
            }
        
        # 유사도 기반 문제 감지
        if self.use_similarity_classifier and self.similarity_service:
            problem_examples = self.SECTION_TYPE_EXAMPLES.get("problem", [])
            if problem_examples:
                try:
                    results = self.similarity_service.compute_similarity(
                        query_text=text[:500],
                        candidate_texts=problem_examples
                    )
                    
                    if results and len(results) > 0:
                        max_similarity = results[0]["similarity"]
                        if max_similarity >= threshold:
                            # 질문 텍스트 추출 시도
                            import re
                            question_match = re.search(r'다음.*?[?？]|다음.*?고른|설명.*?[하시오시오]', text[:200])
                            question_text = question_match.group(0) if question_match else None
                            
                            return {
                                "is_problem": True,
                                "confidence": float(max_similarity),
                                "question_text": question_text
                            }
                except Exception as e:
                    print(f"[MLSectionClassifier] 문제 감지 실패: {e}")
        
        # Fallback: 정규식 기반
        import re
        if re.search(r'문제|다음.*?고른|정답|선택지', text):
            return {
                "is_problem": True,
                "confidence": 0.7,
                "question_text": None
            }
        
        return {
            "is_problem": False,
            "confidence": 0.0,
            "question_text": None
        }


# 전역 인스턴스 (싱글톤)
_section_classifier_instance: Optional[MLSectionClassifier] = None


def get_section_classifier() -> MLSectionClassifier:
    """전역 섹션 분류기 인스턴스 가져오기 (싱글톤)"""
    global _section_classifier_instance
    if _section_classifier_instance is None:
        _section_classifier_instance = MLSectionClassifier(
            use_similarity_classifier=True  # 유사도 기반 분류 활성화
        )
    return _section_classifier_instance
