"""
AI Structure Classifier: BERT 기반 블록 타입 분류

PDF 블록을 문제/지문/보기/헤더/푸터로 자동 분류
"""
from typing import Dict, Any, List, Optional
import re

try:
    from transformers import AutoTokenizer, AutoModelForSequenceClassification
    import torch
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False


class AIStructureClassifier:
    """
    BERT 기반 블록 타입 분류기
    
    분류 타입:
    - passage: 지문
    - question: 문제
    - choice: 보기
    - header: 헤더/제목
    - footer: 푸터/페이지 번호
    - other: 기타
    """
    
    def __init__(
        self,
        model_name: str = "skt/kobert-base-v1",
        use_finetuned: bool = False,
        model_path: Optional[str] = None
    ):
        """
        Args:
            model_name: 기본 BERT 모델명
            use_finetuned: Fine-tuned 모델 사용 여부
            model_path: Fine-tuned 모델 경로 (use_finetuned=True일 때)
        """
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.label_map = {
            0: "passage",
            1: "question",
            2: "choice",
            3: "header",
            4: "footer",
            5: "other"
        }
        
        if not TRANSFORMERS_AVAILABLE:
            raise ImportError(
                "transformers가 설치되지 않았습니다. "
                "pip install transformers torch"
            )
        
        try:
            if use_finetuned and model_path:
                # Fine-tuned 모델 로드
                self.tokenizer = AutoTokenizer.from_pretrained(model_path)
                self.model = AutoModelForSequenceClassification.from_pretrained(
                    model_path,
                    num_labels=len(self.label_map)
                )
            else:
                # 기본 모델 로드 (실제로는 Fine-tuned 필요)
                self.tokenizer = AutoTokenizer.from_pretrained(model_name)
                # 여기서는 기본 구조만 제공 (실제 Fine-tuning 필요)
                print("⚠️ Fine-tuned 모델이 없어 규칙 기반 분류만 사용합니다.")
                self.model = None
        except Exception as e:
            print(f"⚠️ 모델 로드 실패, 규칙 기반 분류 사용: {e}")
            self.model = None
            self.tokenizer = None
    
    def classify_block(
        self,
        text: str,
        context: str = "",
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        텍스트 블록의 타입 분류
        
        Args:
            text: 블록 텍스트
            context: 주변 맥락 (선택)
            metadata: 추가 메타데이터 (bbox, page 등)
        
        Returns:
            Dict with keys: type, confidence, probabilities
        """
        if self.model and self.tokenizer:
            return self._classify_with_bert(text, context)
        else:
            return self._classify_with_rules(text, metadata)
    
    def _classify_with_bert(self, text: str, context: str) -> Dict[str, Any]:
        """BERT 모델로 분류"""
        # 입력 구성: [CLS] context [SEP] text [SEP]
        if context:
            input_text = f"{context} [SEP] {text}"
        else:
            input_text = text
        
        # 토큰화
        inputs = self.tokenizer(
            input_text,
            return_tensors="pt",
            truncation=True,
            max_length=512,
            padding=True
        ).to(self.device)
        
        # 추론
        self.model.eval()
        with torch.no_grad():
            outputs = self.model(**inputs)
            probabilities = torch.softmax(outputs.logits, dim=-1)
        
        # 예측
        predicted_class = torch.argmax(probabilities, dim=-1).item()
        confidence = probabilities[0][predicted_class].item()
        
        # 확률 분포
        prob_dict = {
            self.label_map[i]: probabilities[0][i].item()
            for i in range(len(self.label_map))
        }
        
        return {
            "type": self.label_map[predicted_class],
            "confidence": confidence,
            "probabilities": prob_dict
        }
    
    def _classify_with_rules(
        self,
        text: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """규칙 기반 분류 (Fallback)"""
        if not text or not text.strip():
            return {
                "type": "other",
                "confidence": 0.5,
                "probabilities": {"other": 0.5}
            }
        
        text_lower = text.lower().strip()
        text_upper = text.upper()
        
        # 문제 패턴
        question_patterns = [
            r'^\d+[\.\)]\s*',  # "1.", "2)"
            r'^문제\s*\d+',
            r'^question\s*\d+',
            r'다음\s+중',
            r'다음\s+[가-힣]*\s*의\s*값',
        ]
        
        # 보기 패턴
        choice_patterns = [
            r'^[①-⑤]\s*',  # ①②③④⑤
            r'^\([1-5]\)\s*',  # (1), (2)
            r'^[A-E]\)\s*',  # A), B)
        ]
        
        # 헤더 패턴
        header_patterns = [
            r'^\d+\s*강\s*[:：]',
            r'^단원\s*\d+',
            r'^chapter\s*\d+',
            r'^제\s*\d+\s*장',
        ]
        
        # 푸터 패턴
        footer_patterns = [
            r'^\d+$',  # 페이지 번호만
            r'^페이지\s*\d+',
            r'^page\s*\d+',
        ]
        
        # 지문 패턴 (긴 텍스트 + 문제 패턴 없음)
        is_passage = (
            len(text) > 100 and
            not any(re.match(p, text) for p in question_patterns) and
            not any(re.match(p, text) for p in choice_patterns)
        )
        
        # 분류
        if any(re.match(p, text) for p in question_patterns):
            return {
                "type": "question",
                "confidence": 0.85,
                "probabilities": {"question": 0.85, "other": 0.15}
            }
        elif any(re.match(p, text) for p in choice_patterns):
            return {
                "type": "choice",
                "confidence": 0.90,
                "probabilities": {"choice": 0.90, "other": 0.10}
            }
        elif any(re.match(p, text) for p in header_patterns):
            return {
                "type": "header",
                "confidence": 0.80,
                "probabilities": {"header": 0.80, "other": 0.20}
            }
        elif any(re.match(p, text) for p in footer_patterns):
            return {
                "type": "footer",
                "confidence": 0.75,
                "probabilities": {"footer": 0.75, "other": 0.25}
            }
        elif is_passage:
            return {
                "type": "passage",
                "confidence": 0.70,
                "probabilities": {"passage": 0.70, "other": 0.30}
            }
        else:
            return {
                "type": "other",
                "confidence": 0.60,
                "probabilities": {"other": 0.60, "passage": 0.20, "question": 0.20}
            }
    
    def classify_batch(self, blocks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        여러 블록을 한 번에 분류
        
        Args:
            blocks: 블록 리스트 (각 블록은 text, context, metadata 포함)
        
        Returns:
            분류 결과가 추가된 블록 리스트
        """
        results = []
        for block in blocks:
            text = block.get("text", "") or block.get("content", "")
            context = block.get("context", "")
            metadata = block.get("metadata", {})
            
            classification = self.classify_block(text, context, metadata)
            
            # 블록에 분류 결과 추가
            block_with_class = block.copy()
            block_with_class["classified_type"] = classification["type"]
            block_with_class["classification_confidence"] = classification["confidence"]
            block_with_class["classification_probabilities"] = classification["probabilities"]
            
            results.append(block_with_class)
        
        return results


# Fallback: 모델 없이 사용할 수 있는 규칙 기반 분류기
class RuleBasedStructureClassifier:
    """규칙 기반 블록 분류기 (AI 없이)"""
    
    def classify_block(
        self,
        text: str,
        context: str = "",
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """규칙 기반 분류"""
        classifier = AIStructureClassifier()
        return classifier._classify_with_rules(text, metadata)
    
    def classify_batch(self, blocks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """배치 분류"""
        classifier = AIStructureClassifier()
        return classifier.classify_batch(blocks)


def get_structure_classifier(use_ai: bool = True, **kwargs) -> Any:
    """
    구조 분류기 인스턴스 반환
    
    Args:
        use_ai: AI 사용 여부 (False면 RuleBasedStructureClassifier 반환)
        **kwargs: AIStructureClassifier 생성자 인자
    
    Returns:
        AIStructureClassifier 또는 RuleBasedStructureClassifier 인스턴스
    """
    if use_ai:
        try:
            return AIStructureClassifier(**kwargs)
        except (ImportError, Exception) as e:
            print(f"⚠️ AI 구조 분류기 사용 불가, 규칙 기반 분류기 사용: {e}")
            return RuleBasedStructureClassifier()
    else:
        return RuleBasedStructureClassifier()
