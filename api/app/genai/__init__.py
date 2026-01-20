"""
Generative AI Module (Level 3)

Level 3 LLM/Generative AI Features - 생성형 AI 도입

이 모듈은 파이프라인의 **최종 Enrichment 단계**에서 실행되는 생성형 AI 기능들을 제공합니다.

구성:
- metadata_enricher.py: LLM 기반 메타데이터 자동 생성
- explanation_generator.py: 개념 설명 자동 생성 (수준별)
- rag_recommender.py: RAG 기반 유사 콘텐츠 추천

AI 역량 증명:
- LLM 활용 (GPT-3.5/GPT-4, Claude)
- Prompt Engineering (Zero-shot, Few-shot)
- LangChain 프레임워크
- RAG 아키텍처
- Vector DB (FAISS, Chroma)
"""
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
import time

# Conditional imports
try:
    from .metadata_enricher import LLMMetadataEnricher, EnrichmentResult
    from .explanation_generator import ConceptExplanationGenerator, EducationLevel, Explanation
    from .rag_recommender import RAGContentRecommender, RecommendationResult, build_recommendation_system
    GENAI_AVAILABLE = True
except ImportError as e:
    GENAI_AVAILABLE = False
    print(f"[GenAI] Some features not available: {e}")
    print("[GenAI] Install with: pip install langchain openai sentence-transformers")


@dataclass
class GenAIStats:
    """GenAI 처리 통계"""
    enriched_metadata_count: int = 0
    generated_explanations_count: int = 0
    recommendations_built: bool = False
    processing_time_ms: float = 0.0
    api_calls: int = 0
    cache_hits: int = 0


class GenAIProcessor:
    """
    Level 3 Generative AI Processor

    통합 생성형 AI 파이프라인:
    1. LLM Metadata Enrichment: 자동 태깅, 키워드, 난이도 추출
    2. Concept Explanation: 수준별 개념 설명 생성
    3. RAG Recommendation: 유사 콘텐츠 추천 시스템 구축

    특징:
    - OpenAI API 기반 (GPT-3.5/GPT-4)
    - LangChain으로 프롬프트 체인 구성
    - Zero-shot / Few-shot Learning
    - Vector DB 기반 Semantic Search
    - 캐싱으로 API 비용 최적화

    사용 예시:
        processor = GenAIProcessor(
            api_key="sk-...",
            enable_metadata_enrichment=True,
            enable_explanations=True,
            enable_recommendations=True
        )

        enriched, stats = processor.process(lecture_data)
        print(f"API calls: {stats.api_calls}")
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model_name: str = "gpt-3.5-turbo",
        enable_metadata_enrichment: bool = True,
        enable_explanations: bool = False,
        enable_recommendations: bool = False,
        education_level: str = "high",
        vector_db_path: Optional[str] = None
    ):
        """
        Args:
            api_key: OpenAI API 키 (None이면 환경변수 OPENAI_API_KEY 사용)
            model_name: LLM 모델 이름
            enable_metadata_enrichment: 메타데이터 enrichment 활성화
            enable_explanations: 개념 설명 생성 활성화
            enable_recommendations: 추천 시스템 구축 활성화
            education_level: 교육 수준 (elementary/middle/high/university)
            vector_db_path: Vector DB 저장 경로 (추천 시스템용)
        """
        if not GENAI_AVAILABLE:
            raise RuntimeError(
                "GenAI features not available. "
                "Install with: pip install langchain openai sentence-transformers"
            )

        self.api_key = api_key
        self.model_name = model_name
        self.education_level = education_level
        self.vector_db_path = vector_db_path

        # Feature flags
        self.enable_metadata_enrichment = enable_metadata_enrichment
        self.enable_explanations = enable_explanations
        self.enable_recommendations = enable_recommendations

        # Components (lazy initialization)
        self._metadata_enricher: Optional[LLMMetadataEnricher] = None
        self._explanation_generator: Optional[ConceptExplanationGenerator] = None
        self._rag_recommender: Optional[RAGContentRecommender] = None

        print(f"[GenAIProcessor] Initialized with model: {model_name}")
        print(f"[GenAIProcessor] Features: metadata={enable_metadata_enrichment}, "
              f"explanations={enable_explanations}, recommendations={enable_recommendations}")

    @property
    def metadata_enricher(self) -> LLMMetadataEnricher:
        """Lazy load metadata enricher"""
        if self._metadata_enricher is None:
            self._metadata_enricher = LLMMetadataEnricher(
                model_name=self.model_name,
                api_key=self.api_key,
                enable_cache=True
            )
        return self._metadata_enricher

    @property
    def explanation_generator(self) -> ConceptExplanationGenerator:
        """Lazy load explanation generator"""
        if self._explanation_generator is None:
            self._explanation_generator = ConceptExplanationGenerator(
                model_name=self.model_name,
                api_key=self.api_key
            )
        return self._explanation_generator

    @property
    def rag_recommender(self) -> RAGContentRecommender:
        """Lazy load RAG recommender"""
        if self._rag_recommender is None:
            self._rag_recommender = RAGContentRecommender(
                vector_db_type="faiss",
                embedding_type="sentence_transformers"
            )
        return self._rag_recommender

    def process(
        self,
        lecture_data: Dict[str, Any],
        verbose: bool = True
    ) -> tuple[Dict[str, Any], GenAIStats]:
        """
        강의 데이터에 GenAI 적용

        Args:
            lecture_data: 강의 데이터 (Assembly 결과)
            verbose: 진행 상황 출력

        Returns:
            (enriched_data, stats)
        """
        start_time = time.time()
        stats = GenAIStats()

        if verbose:
            print("\n" + "="*60)
            print("Level 3: Generative AI Processing")
            print("="*60)

        # 1. Metadata Enrichment
        if self.enable_metadata_enrichment:
            lecture_data, metadata_stats = self._enrich_metadata(lecture_data, verbose)
            stats.enriched_metadata_count = metadata_stats
            stats.api_calls += metadata_stats

        # 2. Concept Explanations
        if self.enable_explanations:
            lecture_data, explanation_stats = self._generate_explanations(lecture_data, verbose)
            stats.generated_explanations_count = explanation_stats
            stats.api_calls += explanation_stats

        # 3. Build Recommendation System
        if self.enable_recommendations:
            self._build_recommendations(lecture_data, verbose)
            stats.recommendations_built = True

        stats.processing_time_ms = (time.time() - start_time) * 1000

        if verbose:
            print("\n" + "="*60)
            print("GenAI Processing Complete")
            print(f"  Metadata enriched: {stats.enriched_metadata_count}")
            print(f"  Explanations generated: {stats.generated_explanations_count}")
            print(f"  Recommendations built: {stats.recommendations_built}")
            print(f"  Total API calls: {stats.api_calls}")
            print(f"  Processing time: {stats.processing_time_ms:.2f}ms")
            print("="*60)

        return lecture_data, stats

    def _enrich_metadata(
        self,
        lecture_data: Dict[str, Any],
        verbose: bool
    ) -> tuple[Dict[str, Any], int]:
        """메타데이터 enrichment"""
        if verbose:
            print("\n[1/3] LLM Metadata Enrichment")

        enriched_count = 0

        # Lectures
        if "lectures" in lecture_data and isinstance(lecture_data["lectures"], list):
            for lecture in lecture_data["lectures"]:
                content = lecture.get("content", "")
                if content and len(content) > 10:
                    result = self.metadata_enricher.enrich(content)

                    if "llm_metadata" not in lecture:
                        lecture["llm_metadata"] = {}

                    lecture["llm_metadata"].update(result.metadata)
                    lecture["llm_metadata"]["enrichment_confidence"] = result.confidence

                    enriched_count += 1

                    if verbose and enriched_count % 5 == 0:
                        print(f"  Enriched {enriched_count} lectures...")

        # Problems
        if "problems" in lecture_data and isinstance(lecture_data["problems"], list):
            for problem in lecture_data["problems"]:
                question = problem.get("question_text", "")
                if question and len(question) > 10:
                    result = self.metadata_enricher.enrich(question)

                    if "llm_metadata" not in problem:
                        problem["llm_metadata"] = {}

                    problem["llm_metadata"].update(result.metadata)
                    problem["llm_metadata"]["enrichment_confidence"] = result.confidence

                    enriched_count += 1

        if verbose:
            print(f"  ✓ Enriched {enriched_count} items")

        return lecture_data, enriched_count

    def _generate_explanations(
        self,
        lecture_data: Dict[str, Any],
        verbose: bool
    ) -> tuple[Dict[str, Any], int]:
        """개념 설명 생성"""
        if verbose:
            print("\n[2/3] Concept Explanation Generation")

        level = EducationLevel[self.education_level.upper()]
        generated_count = 0

        if "lectures" in lecture_data and isinstance(lecture_data["lectures"], list):
            for lecture in lecture_data["lectures"]:
                # 개념 블록만 처리
                if lecture.get("type") != "concept" and lecture.get("block_type") != "concept":
                    continue

                concept = lecture.get("title", "") or lecture.get("concept_name", "")
                if not concept:
                    continue

                explanation = self.explanation_generator.generate(concept, level)

                if "llm_explanation" not in lecture:
                    lecture["llm_explanation"] = {}

                lecture["llm_explanation"][level.value] = {
                    "explanation": explanation.explanation,
                    "examples": explanation.examples,
                    "key_points": explanation.key_points
                }

                generated_count += 1

                if verbose and generated_count % 3 == 0:
                    print(f"  Generated {generated_count} explanations...")

        if verbose:
            print(f"  ✓ Generated {generated_count} explanations")

        return lecture_data, generated_count

    def _build_recommendations(
        self,
        lecture_data: Dict[str, Any],
        verbose: bool
    ) -> None:
        """추천 시스템 구축"""
        if verbose:
            print("\n[3/3] RAG Recommendation System")

        # Problems 추가
        if "problems" in lecture_data:
            problems = lecture_data["problems"]
            self.rag_recommender.add_problems(problems, text_field="question_text")
            if verbose:
                print(f"  Added {len(problems)} problems to vector DB")

        # Concepts 추가
        if "lectures" in lecture_data:
            concepts = [
                lec for lec in lecture_data["lectures"]
                if lec.get("type") == "concept" or lec.get("block_type") == "concept"
            ]
            self.rag_recommender.add_concepts(concepts, text_field="content")
            if verbose:
                print(f"  Added {len(concepts)} concepts to vector DB")

        # 저장
        if self.vector_db_path:
            self.rag_recommender.save(self.vector_db_path)
            if verbose:
                print(f"  Saved vector DB to {self.vector_db_path}")

        if verbose:
            print("  ✓ Recommendation system built")

    def find_similar_problems(
        self,
        problem_text: str,
        top_k: int = 5
    ) -> RecommendationResult:
        """유사 문제 찾기"""
        if not self.enable_recommendations:
            raise RuntimeError("Recommendations not enabled")

        return self.rag_recommender.find_similar_problems(problem_text, top_k)

    def find_similar_concepts(
        self,
        concept_text: str,
        top_k: int = 5
    ) -> RecommendationResult:
        """유사 개념 찾기"""
        if not self.enable_recommendations:
            raise RuntimeError("Recommendations not enabled")

        return self.rag_recommender.find_similar_concepts(concept_text, top_k)


# Export public API
__all__ = [
    "GenAIProcessor",
    "GenAIStats",
    "LLMMetadataEnricher",
    "ConceptExplanationGenerator",
    "RAGContentRecommender",
    "EducationLevel",
    "EnrichmentResult",
    "Explanation",
    "RecommendationResult",
    "build_recommendation_system",
    "GENAI_AVAILABLE"
]
