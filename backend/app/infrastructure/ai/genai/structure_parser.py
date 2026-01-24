"""
AI 기반 PDF 구조 자동 파싱 (GPT-4 Vision or Claude)

진짜 자동화:
- PDF 페이지를 이미지로 변환
- AI에게 "강의 제목 찾아줘", "문제 번호 찾아줘" 요청
- 정규식 설정 불필요
"""
from typing import List, Dict, Any, Optional
import json
import re

try:
    from anthropic import Anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False
    print("[StructureParser] anthropic not available. Install with: pip install anthropic")


class AIStructureParser:
    """
    AI 기반 교재 구조 자동 파싱

    특징:
    - GPT-4 Vision 또는 Claude로 PDF 구조 분석
    - 정규식 패턴 없이 자동 추출
    - Few-shot learning으로 정확도 향상

    사용:
        parser = AIStructureParser(api_key="...")
        lectures = parser.extract_lectures_from_toc(toc_pages_ocr_data)
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "claude-3-5-sonnet-20241022",
        use_vision: bool = False
    ):
        """
        Args:
            api_key: Anthropic API 키
            model: 모델 이름
            use_vision: 비전 모델 사용 여부 (PDF 이미지 직접 분석)
        """
        if not ANTHROPIC_AVAILABLE:
            raise RuntimeError(
                "anthropic not available. "
                "Install with: pip install anthropic"
            )

        self.client = Anthropic(api_key=api_key)
        self.model = model
        self.use_vision = use_vision

        print(f"[AIStructureParser] Initialized with model: {model}")

    def extract_lectures_from_toc(
        self,
        ocr_data: List[Dict[str, Any]],
        toc_page_range: tuple = (1, 7)
    ) -> List[Dict[str, Any]]:
        """
        목차에서 강의 목록 자동 추출

        Args:
            ocr_data: OCR 결과 (전체 페이지)
            toc_page_range: 목차 페이지 범위

        Returns:
            강의 리스트 [{"lecture_id": 1, "title": "1강 | ...", "page": 4}, ...]
        """
        # TOC 페이지만 추출
        toc_pages = [
            page for page in ocr_data
            if toc_page_range[0] <= page.get('page_num', 0) <= toc_page_range[1]
        ]

        if not toc_pages:
            print("[AIStructureParser] No TOC pages found")
            return []

        # TOC 텍스트 결합
        toc_text = self._extract_text_from_pages(toc_pages)

        # AI에게 강의 추출 요청
        prompt = self._create_lecture_extraction_prompt(toc_text)

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=4096,
                messages=[{"role": "user", "content": prompt}]
            )

            # JSON 파싱
            result_text = response.content[0].text
            lectures = self._parse_lectures_response(result_text)

            print(f"[AIStructureParser] Extracted {len(lectures)} lectures from TOC")
            return lectures

        except Exception as e:
            print(f"[AIStructureParser] Failed to extract lectures: {e}")
            import traceback
            traceback.print_exc()
            return []

    def _extract_text_from_pages(self, pages: List[Dict[str, Any]]) -> str:
        """페이지들에서 텍스트 추출"""
        all_text = []

        for page in pages:
            page_num = page.get('page_num', 0)
            texts = page.get('text', [])

            page_lines = []
            for text_obj in texts:
                if isinstance(text_obj, dict):
                    page_lines.append(text_obj.get('text', ''))
                elif isinstance(text_obj, str):
                    page_lines.append(text_obj)

            page_text = '\n'.join(page_lines)
            all_text.append(f"=== Page {page_num} ===\n{page_text}")

        return '\n\n'.join(all_text)

    def _create_lecture_extraction_prompt(self, toc_text: str) -> str:
        """강의 추출 프롬프트 생성"""
        return f"""당신은 교재 목차(TOC) 분석 전문가입니다.

다음은 수능 특강 교재의 목차 텍스트입니다. 이 텍스트에서 강의 목록을 추출하세요.

<목차 텍스트>
{toc_text[:8000]}  # 토큰 제한
</목차 텍스트>

**추출 규칙:**
1. "N강 | 제목" 형식의 강의 찾기 (예: "1강 | 시의 표현과 형식")
2. "N강 제목" 형식도 포함 (예: "10강 고전 시가")
3. 강의 번호는 1부터 시작
4. 페이지 번호는 무시
5. 작품 목록이나 부제목은 제외

**출력 형식 (JSON):**
```json
[
  {{"lecture_id": 1, "title": "1강 | 시의 표현과 형식"}},
  {{"lecture_id": 2, "title": "2강 | 시의 내용"}},
  ...
]
```

반드시 JSON 배열로만 답변하세요. 다른 설명 없이 JSON만 출력하세요."""

    def _parse_lectures_response(self, response_text: str) -> List[Dict[str, Any]]:
        """AI 응답에서 강의 리스트 파싱"""
        try:
            # JSON 블록 추출
            json_match = re.search(r'\[.*\]', response_text, re.DOTALL)
            if json_match:
                lectures = json.loads(json_match.group(0))
                return lectures
        except Exception as e:
            print(f"[AIStructureParser] JSON parsing failed: {e}")

        # Fallback: 라인별 파싱 시도
        lectures = []
        for line in response_text.split('\n'):
            # "lecture_id": 1, "title": "..." 형식 찾기
            match = re.search(r'"lecture_id":\s*(\d+).*"title":\s*"([^"]+)"', line)
            if match:
                lectures.append({
                    "lecture_id": int(match.group(1)),
                    "title": match.group(2)
                })

        return lectures

    def extract_problems_from_page(
        self,
        ocr_page: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        페이지에서 문제 번호 자동 추출

        Returns:
            문제 리스트 [{"problem_id": "01", "page": 10}, ...]
        """
        page_text = self._extract_text_from_pages([ocr_page])

        prompt = f"""다음 페이지에서 문제 번호를 모두 찾아주세요.

<페이지 텍스트>
{page_text[:4000]}
</페이지 텍스트>

수능 특강 문제 번호는 보통 "01", "02" 같은 2자리 숫자입니다.
페이지 번호나 강의 번호는 제외하고, 실제 문제 번호만 찾으세요.

**출력 형식 (JSON):**
```json
["01", "02", "03"]
```

JSON 배열로만 답변하세요."""

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=1024,
                messages=[{"role": "user", "content": prompt}]
            )

            result_text = response.content[0].text

            # JSON 파싱
            json_match = re.search(r'\[.*\]', result_text, re.DOTALL)
            if json_match:
                problem_ids = json.loads(json_match.group(0))
                return [
                    {"problem_id": pid, "page": ocr_page.get('page_num', 0)}
                    for pid in problem_ids
                ]

        except Exception as e:
            print(f"[AIStructureParser] Problem extraction failed: {e}")

        return []


class HybridParser:
    """
    하이브리드 파서: AI 우선 + Fallback 정규식

    전략:
    1. 먼저 AI로 시도 (정확하지만 느림, 비용 발생)
    2. 실패하거나 신뢰도 낮으면 정규식 사용
    3. 결과 캐싱으로 반복 작업 방지
    """

    def __init__(
        self,
        ai_parser: Optional[AIStructureParser] = None,
        fallback_config: Optional[Dict[str, Any]] = None,
        use_ai_first: bool = True
    ):
        """
        Args:
            ai_parser: AI 파서 (None이면 AI 사용 안함)
            fallback_config: 정규식 패턴 설정
            use_ai_first: AI 우선 사용 여부
        """
        self.ai_parser = ai_parser
        self.fallback_config = fallback_config or {}
        self.use_ai_first = use_ai_first and ai_parser is not None

        print(f"[HybridParser] AI first: {self.use_ai_first}")

    def extract_lectures(
        self,
        ocr_data: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """강의 추출 (AI + Fallback)"""

        # AI 시도
        if self.use_ai_first:
            try:
                print("[HybridParser] Trying AI extraction...")
                lectures = self.ai_parser.extract_lectures_from_toc(ocr_data)

                # 최소 개수 확인 (신뢰도 체크)
                if len(lectures) >= 5:  # 최소 5개 이상 추출되어야 성공
                    print(f"[HybridParser] AI extraction successful: {len(lectures)} lectures")
                    return lectures
                else:
                    print(f"[HybridParser] AI extraction insufficient: {len(lectures)} lectures")
            except Exception as e:
                print(f"[HybridParser] AI extraction failed: {e}")

        # Fallback: 정규식 파싱
        print("[HybridParser] Using fallback regex parsing...")
        return self._extract_lectures_regex(ocr_data)

    def _extract_lectures_regex(
        self,
        ocr_data: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """정규식 기반 강의 추출 (통합 파서 사용)"""
        from app.infrastructure.pdf.parsers.unified_parser import UnifiedTemplateParser

        parser = UnifiedTemplateParser(
            subject="literature",
            config_path=None,
            template=None,
            enable_ai_parsing=False
        )
        # fallback_config가 있으면 config에 병합
        if self.fallback_config:
            parser.config.update(self.fallback_config)
        return parser.extract_lectures(ocr_data)


# 사용 예시:
"""
# API 키 설정
ai_parser = AIStructureParser(api_key="sk-ant-...")

# 하이브리드 파서 생성
hybrid = HybridParser(
    ai_parser=ai_parser,
    fallback_config=config_dict,
    use_ai_first=True
)

# PDF 파싱
lectures = hybrid.extract_lectures(ocr_data)
"""
