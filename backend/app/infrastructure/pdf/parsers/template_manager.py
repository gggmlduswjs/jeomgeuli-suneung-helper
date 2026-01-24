"""
템플릿 관리 및 매칭
교재 텍스트에 가장 적합한 파싱 템플릿을 찾아 반환
"""
import re
import logging
from pathlib import Path
from typing import List, Optional, Dict, Tuple
from collections import Counter

from .template import ParsingTemplate
from app.core.config import settings
from app.infrastructure.pdf.types import OCRPageData

logger = logging.getLogger(__name__)


class TemplateManager:
    """템플릿 관리 및 매칭
    
    기능:
    - 템플릿 로드/저장
    - PDF 텍스트에 적합한 템플릿 매칭
    - 신뢰도 계산
    """
    
    def __init__(self, template_dir: Optional[Path] = None, enable_cache: bool = True):
        """
        Args:
            template_dir: 템플릿 저장 디렉토리 (None이면 기본 경로 사용)
            enable_cache: 템플릿 매칭 결과 캐싱 활성화
        """
        if template_dir is None:
            template_dir = settings.API_DIR / "data" / "templates"
        
        # 절대 경로로 변환
        self.template_dir = Path(template_dir).resolve()
        self.templates: Dict[str, ParsingTemplate] = {}
        self.enable_cache = enable_cache
        self._match_cache: Dict[str, Tuple[ParsingTemplate, float]] = {}  # (subject_text_hash) -> (template, confidence)
        
        logger.info(f"[TemplateManager] 초기화 - 템플릿 디렉토리: {self.template_dir}")
        logger.info(f"[TemplateManager] API_DIR: {settings.API_DIR}")
        logger.info(f"[TemplateManager] 디렉토리 존재 여부: {self.template_dir.exists()}")
        
        self._load_templates()
    
    def _load_templates(self):
        """템플릿 디렉토리에서 모든 템플릿 로드"""
        if not self.template_dir.exists():
            logger.warning(
                f"[TemplateManager] 템플릿 디렉토리가 존재하지 않습니다: {self.template_dir}\n"
                f"  절대 경로: {self.template_dir.absolute()}\n"
                f"  API_DIR: {settings.API_DIR}\n"
                f"  API_DIR 절대 경로: {settings.API_DIR.resolve()}"
            )
            # 디렉토리 생성 시도
            try:
                self.template_dir.mkdir(parents=True, exist_ok=True)
                logger.info(f"[TemplateManager] 템플릿 디렉토리 생성 완료: {self.template_dir}")
            except Exception as e:
                logger.error(f"[TemplateManager] 템플릿 디렉토리 생성 실패: {e}")
            return
        
        # 디렉토리 내용 확인
        try:
            all_files = list(self.template_dir.iterdir())
            logger.info(f"[TemplateManager] 디렉토리 내용 ({len(all_files)}개 항목):")
            for item in all_files:
                logger.info(f"  - {item.name} ({'파일' if item.is_file() else '디렉토리'})")
        except Exception as e:
            logger.warning(f"[TemplateManager] 디렉토리 내용 확인 실패: {e}")
        
        template_files = list(self.template_dir.glob("*.json"))
        logger.info(f"[TemplateManager] 발견된 템플릿 파일: {len(template_files)}개")
        
        if len(template_files) == 0:
            logger.warning(
                f"[TemplateManager] 템플릿 파일이 없습니다. 디렉토리: {self.template_dir}\n"
                f"  예상 경로: {settings.API_DIR.resolve() / 'data' / 'templates'}"
            )
        
        for template_file in template_files:
            try:
                logger.debug(f"[TemplateManager] 템플릿 로드 시도: {template_file.name}")
                template = ParsingTemplate.load(template_file)
                # 키: {subject}_{name}
                key = f"{template.subject}_{template.name}"
                self.templates[key] = template
                logger.info(f"[TemplateManager] 템플릿 로드 성공: {key} (파일: {template_file.name})")
            except Exception as e:
                logger.error(f"[TemplateManager] 템플릿 로드 실패 {template_file}: {e}", exc_info=True)
        
        logger.info(f"[TemplateManager] 총 {len(self.templates)}개 템플릿 로드 완료")
    
    def add_template(self, template: ParsingTemplate) -> Path:
        """템플릿 추가 및 저장
        
        Args:
            template: 추가할 템플릿
            
        Returns:
            저장된 파일 경로
        """
        logger.info(f"[TemplateManager] 템플릿 저장 시작: {template.subject}_{template.name}")
        logger.info(f"[TemplateManager] 저장 디렉토리: {self.template_dir}")
        logger.info(f"[TemplateManager] 디렉토리 존재 여부: {self.template_dir.exists()}")
        
        file_path = template.save(self.template_dir)
        
        # 저장 확인
        if not file_path.exists():
            raise FileNotFoundError(f"템플릿 파일이 저장되지 않았습니다: {file_path}")
        
        logger.info(f"[TemplateManager] 템플릿 파일 저장 완료: {file_path}")
        logger.info(f"[TemplateManager] 파일 크기: {file_path.stat().st_size} bytes")
        
        key = f"{template.subject}_{template.name}"
        self.templates[key] = template
        logger.info(f"[TemplateManager] 템플릿 메모리 로드 완료: {key}")
        logger.info(f"[TemplateManager] TOC 강의 목록: {len(template.config.get('toc_lecture_list', []))}개")
        
        return file_path
    
    def reload_templates(self):
        """템플릿 디렉토리에서 모든 템플릿을 다시 로드"""
        logger.info(f"[TemplateManager] 템플릿 재로드 시작")
        # 기존 템플릿은 유지하되, 파일 시스템에서 새로 로드
        self._load_templates()
        logger.info(f"[TemplateManager] 템플릿 재로드 완료: 총 {len(self.templates)}개 템플릿")
    
    def get_templates_by_subject(self, subject: str) -> List[ParsingTemplate]:
        """과목별 템플릿 목록 반환
        
        Args:
            subject: 과목명
            
        Returns:
            해당 과목의 템플릿 리스트
        """
        return [
            template for template in self.templates.values()
            if template.subject == subject
        ]
    
    def match_template(
        self,
        pdf_text: str,
        subject: str,
        threshold: float = 0.85,
        book_id: Optional[str] = None,
        pdf_ocr_data: Optional[List[OCRPageData]] = None
    ) -> Optional[Tuple[ParsingTemplate, float]]:
        """PDF 텍스트에 가장 적합한 템플릿 찾기

        Args:
            pdf_text: PDF에서 추출한 텍스트 (첫 3-5페이지 권장)
            subject: 과목명
            threshold: 최소 신뢰도 임계값 (0.0-1.0)
            book_id: 교재 ID (캐싱용, 선택적)
            pdf_ocr_data: OCR 데이터 (영역 유사도 계산용, 선택적)

        Returns:
            (매칭된 템플릿, 신뢰도) 튜플 또는 None (매칭 실패시)
        """
        # 캐시 확인 (book_id가 제공된 경우)
        if self.enable_cache and book_id:
            cache_key = f"{subject}_{book_id}"
            if cache_key in self._match_cache:
                cached_template, cached_confidence = self._match_cache[cache_key]
                logger.info(f"템플릿 매칭 캐시 히트: {cached_template.name} (신뢰도: {cached_confidence:.2f})")
                return (cached_template, cached_confidence)

        subject_templates = self.get_templates_by_subject(subject)

        if not subject_templates:
            logger.warning(f"No templates found for subject: {subject}")
            return None

        # 영역 마킹이 있는 템플릿과 없는 템플릿 분리
        templates_with_regions = []
        templates_without_regions = []

        for template in subject_templates:
            if (template.config and
                template.config.get('region_text_examples') and
                template.config.get('region_hints')):
                templates_with_regions.append(template)
            else:
                templates_without_regions.append(template)

        if templates_with_regions and pdf_ocr_data:
            logger.info(
                f"[템플릿 매칭] 영역 마킹 있음: {len(templates_with_regions)}개, "
                f"없음: {len(templates_without_regions)}개"
            )

        best_match: Optional[Tuple[ParsingTemplate, float]] = None
        best_confidence = 0.0

        # 1순위: 영역 마킹이 있는 템플릿 (OCR 데이터가 있을 때만)
        if templates_with_regions and pdf_ocr_data:
            for template in templates_with_regions:
                confidence = self._calculate_confidence(pdf_text, template, pdf_ocr_data)

                if confidence > best_confidence:
                    best_confidence = confidence
                    best_match = (template, confidence)

            # 영역 마킹이 있는 템플릿은 임계값을 10% 낮춤
            adjusted_threshold = threshold * 0.9
            if best_match and best_match[1] >= adjusted_threshold:
                logger.info(
                    f"[템플릿 매칭] 영역 기반 매칭 성공: {best_match[0].name} "
                    f"(신뢰도: {best_match[1]:.2f} >= {adjusted_threshold:.2f})"
                )

                # 캐시 저장
                if self.enable_cache and book_id:
                    cache_key = f"{subject}_{book_id}"
                    self._match_cache[cache_key] = best_match

                return best_match

        # 2순위: 일반 템플릿 또는 OCR 데이터 없을 때
        for template in templates_without_regions:
            confidence = self._calculate_confidence(pdf_text, template, pdf_ocr_data)

            if confidence > best_confidence:
                best_confidence = confidence
                best_match = (template, confidence)

        if best_match and best_match[1] >= threshold:
            logger.info(
                f"[템플릿 매칭] 패턴 기반 매칭 성공: {best_match[0].name} "
                f"(confidence: {best_match[1]:.2f})"
            )

            # 캐시 저장
            if self.enable_cache and book_id:
                cache_key = f"{subject}_{book_id}"
                self._match_cache[cache_key] = best_match

            return best_match
        else:
            if best_match:
                logger.info(
                    f"[템플릿 매칭] 매칭 실패 (임계값 미달): {best_match[0].name} "
                    f"(confidence: {best_match[1]:.2f} < {threshold})"
                )
            return None
    
    def clear_cache(self):
        """매칭 캐시 초기화"""
        self._match_cache.clear()
        logger.info("템플릿 매칭 캐시 초기화 완료")
    
    def _calculate_confidence(
        self,
        pdf_text: str,
        template: ParsingTemplate,
        pdf_ocr_data: Optional[List[OCRPageData]] = None
    ) -> float:
        """템플릿과 PDF 텍스트의 매칭 신뢰도 계산

        신뢰도 계산 방법:
        - 영역 마킹이 있을 때:
          1. 강의 제목 패턴 매칭률 (30%)
          2. 문제 번호 패턴 매칭률 (20%)
          3. 개념/섹션 패턴 매칭률 (15%)
          4. 템플릿 기본 신뢰도 (5%)
          5. 영역별 텍스트 유사도 (30%)
        - 영역 마킹이 없을 때:
          1. 강의 제목 패턴 매칭률 (40%)
          2. 문제 번호 패턴 매칭률 (30%)
          3. 개념/섹션 패턴 매칭률 (20%)
          4. 템플릿 기본 신뢰도 (10%)

        Args:
            pdf_text: PDF 텍스트
            template: 비교할 템플릿
            pdf_ocr_data: OCR 데이터 (영역 유사도 계산용, 선택적)

        Returns:
            신뢰도 (0.0-1.0)
        """
        if not pdf_text or not template.patterns:
            return 0.0

        # 텍스트를 줄 단위로 분리
        lines = pdf_text.split('\n')

        # 영역 마킹 정보 확인
        has_region_marking = (
            pdf_ocr_data and
            template.config and
            template.config.get('region_text_examples') and
            template.config.get('region_hints')
        )

        # 1. 강의 제목/목차 패턴 매칭
        lecture_score, lecture_matches = self._match_patterns(
            lines,
            template.patterns.get("lecture_title_patterns", []),
            template.patterns.get("toc_lecture_patterns", [])
        )

        # 2. 문제 번호 패턴 매칭
        problem_pattern = template.patterns.get("problem_number_pattern", "")
        problem_score = 0.0
        problem_matches = 0
        if problem_pattern:
            problem_matches = sum(
                1 for line in lines
                if re.search(problem_pattern, line.strip())
            )
            # 문제가 3개 이상 발견되면 높은 점수
            problem_score = min(problem_matches / 10.0, 1.0)

        # 3. 개념/섹션 패턴 매칭
        concept_score, concept_matches = self._match_patterns(
            lines,
            template.patterns.get("concept_title_patterns", []),
            template.patterns.get("section_title_patterns", [])
        )

        # 4. 템플릿 기본 신뢰도
        base_confidence = template.confidence

        # 매칭 신호가 전혀 없으면 0 (기본 confidence만으로는 매칭 금지)
        signal_matches = lecture_matches + problem_matches + concept_matches
        if signal_matches == 0 and not has_region_marking:
            return 0.0

        # 5. 영역별 텍스트 유사도 (영역 마킹이 있을 때만)
        region_score = 0.0
        if has_region_marking:
            region_score = self._calculate_region_similarity(pdf_ocr_data, template)

        # 가중 평균 계산 (영역 마킹 유무에 따라 가중치 다름)
        if has_region_marking:
            confidence = (
                lecture_score * 0.30 +
                problem_score * 0.20 +
                concept_score * 0.15 +
                base_confidence * 0.05 +
                region_score * 0.30  # 영역 유사도 30%
            )
            logger.info(
                f"[템플릿 매칭] {template.name} 신뢰도 계산 (영역 마킹 포함): "
                f"강의={lecture_score:.2f}(30%), 문제={problem_score:.2f}(20%), "
                f"개념={concept_score:.2f}(15%), 기본={base_confidence:.2f}(5%), "
                f"영역={region_score:.2f}(30%) → 총={confidence:.2f}"
            )
        else:
            confidence = (
                lecture_score * 0.4 +
                problem_score * 0.3 +
                concept_score * 0.2 +
                base_confidence * 0.1
            )
            # 템플릿 기본 신뢰도는 "신호가 있을 때" 최소 바닥값으로 사용
            bonus = min(0.05, signal_matches * 0.01)
            confidence = max(confidence, base_confidence + bonus)
            logger.debug(
                f"[템플릿 매칭] {template.name} 신뢰도 계산 (패턴만): "
                f"강의={lecture_score:.2f}(40%), 문제={problem_score:.2f}(30%), "
                f"개념={concept_score:.2f}(20%), 기본={base_confidence:.2f}(10%) → 총={confidence:.2f}"
            )

        return min(confidence, 1.0)
    
    def _match_patterns(
        self,
        lines: List[str],
        *pattern_lists: List[str]
    ) -> Tuple[float, int]:
        """패턴 리스트와 텍스트 라인 매칭률 계산
        
        Args:
            lines: 텍스트 라인 리스트
            *pattern_lists: 정규식 패턴 리스트들
            
        Returns:
            (매칭률(0.0-1.0), 매칭된 라인 수)
        """
        if not pattern_lists or not any(pattern_lists):
            return 0.0, 0
        
        all_patterns = []
        for pattern_list in pattern_lists:
            all_patterns.extend(pattern_list)
        
        if not all_patterns:
            return 0.0, 0
        
        matches = 0
        total_lines = len(lines)
        
        if total_lines == 0:
            return 0.0, 0
        
        for line in lines:
            line_stripped = line.strip()
            for pattern in all_patterns:
                try:
                    if re.search(pattern, line_stripped):
                        matches += 1
                        break  # 한 라인에서 하나의 패턴만 매칭
                except re.error as e:
                    logger.warning(f"Invalid regex pattern: {pattern}, error: {e}")
        
        # 매칭률: 매칭된 라인 수 / 전체 라인 수
        # 최소 5개 라인에서 매칭되어야 신뢰도 있음
        if matches < 5:
            return matches / max(total_lines, 1) * 0.5, matches  # 패널티 적용
        
        return min(matches / max(total_lines, 1), 1.0), matches
    
    def get_template(self, subject: str, name: str) -> Optional[ParsingTemplate]:
        """특정 템플릿 조회
        
        Args:
            subject: 과목명
            name: 템플릿 이름
            
        Returns:
            ParsingTemplate 또는 None
        """
        key = f"{subject}_{name}"
        return self.templates.get(key)
    
    def list_templates(self, subject: Optional[str] = None) -> List[ParsingTemplate]:
        """템플릿 목록 반환

        Args:
            subject: 과목 필터 (None이면 전체)

        Returns:
            템플릿 리스트
        """
        if subject:
            return self.get_templates_by_subject(subject)
        return list(self.templates.values())

    def _calculate_region_similarity(
        self,
        pdf_ocr_data: List[OCRPageData],
        template: ParsingTemplate
    ) -> float:
        """PDF와 템플릿의 영역별 텍스트 유사도 계산

        영역 마킹 정보를 활용하여:
        1. 템플릿의 region_hints로 PDF에서 각 영역 텍스트 추출
        2. 추출된 텍스트와 template.region_text_examples 비교
        3. 영역별 유사도 평균 계산

        Args:
            pdf_ocr_data: OCR 데이터 (첫 3-5페이지)
            template: 비교할 템플릿

        Returns:
            영역 유사도 점수 (0.0-1.0)
        """
        if not pdf_ocr_data or not template.config:
            return 0.0

        region_hints = template.config.get('region_hints', {})
        region_text_examples = template.config.get('region_text_examples', {})

        if not region_hints or not region_text_examples:
            return 0.0

        # 첫 3-5페이지에서 영역별 텍스트 추출
        sample_pages = pdf_ocr_data[:5]
        region_scores = {}

        for region_type, hint in region_hints.items():
            if region_type not in region_text_examples:
                continue

            # PDF에서 해당 영역 텍스트 추출
            region_texts = self._extract_region_texts(
                sample_pages,
                y_min=hint.get('y_min', 0.0),
                y_max=hint.get('y_max', 1.0)
            )

            if not region_texts:
                continue

            # 템플릿의 예시 텍스트와 유사도 비교
            examples = region_text_examples[region_type]
            max_similarity = 0.0

            # PDF 영역 텍스트와 템플릿 예시를 비교
            for pdf_text in region_texts[:10]:  # 상위 10개만
                for example in examples[:5]:  # 상위 5개만
                    similarity = self._text_similarity(pdf_text, example)
                    max_similarity = max(max_similarity, similarity)

            region_scores[region_type] = max_similarity

        # 평균 계산
        if not region_scores:
            return 0.0

        avg_score = sum(region_scores.values()) / len(region_scores)

        logger.info(
            f"[템플릿 매칭] 영역별 유사도: "
            f"{', '.join(f'{k}={v:.2f}' for k, v in region_scores.items())} "
            f"(평균: {avg_score:.2f})"
        )

        return avg_score

    def _extract_region_texts(
        self,
        pages: List[OCRPageData],
        y_min: float,
        y_max: float,
        max_texts: int = 20
    ) -> List[str]:
        """Y좌표 범위 내의 텍스트 추출

        Args:
            pages: OCR 페이지 데이터 리스트
            y_min: Y좌표 최소값 (0.0-1.0, 정규화된 비율)
            y_max: Y좌표 최대값 (0.0-1.0, 정규화된 비율)
            max_texts: 추출할 최대 텍스트 개수

        Returns:
            추출된 텍스트 리스트
        """
        region_texts = []

        for page in pages:
            page_height = page.get('page_height', 1400.0)
            texts = page.get('text', [])
            tops = page.get('top', [])
            heights = page.get('height', [])

            if not texts or len(texts) != len(tops):
                continue

            for i, text in enumerate(texts):
                if not text or len(str(text).strip()) < 5:
                    continue

                # Y좌표 비율 계산
                top = tops[i]
                height = heights[i] if i < len(heights) else 0
                y_center = (top + height / 2) / page_height

                # 영역 내에 있으면 추가
                if y_min <= y_center <= y_max:
                    region_texts.append(str(text).strip())

                    if len(region_texts) >= max_texts:
                        break

            if len(region_texts) >= max_texts:
                break

        return region_texts

    def _text_similarity(self, text1: str, text2: str) -> float:
        """두 텍스트의 유사도 계산

        여러 방법 중 최고 점수 사용:
        1. 완전 일치 (1.0)
        2. 부분 문자열 포함 (길이 비율)
        3. 단어 중복도 (Jaccard similarity)

        Args:
            text1: 첫 번째 텍스트
            text2: 두 번째 텍스트

        Returns:
            유사도 점수 (0.0-1.0)
        """
        if not text1 or not text2:
            return 0.0

        t1 = text1.lower().strip()
        t2 = text2.lower().strip()

        # 1. 완전 일치
        if t1 == t2:
            return 1.0

        # 2. 부분 문자열 포함 (양방향)
        if t1 in t2 or t2 in t1:
            shorter = min(len(t1), len(t2))
            longer = max(len(t1), len(t2))
            return shorter / longer

        # 3. 단어 중복도 (Jaccard similarity)
        words1 = set(t1.split())
        words2 = set(t2.split())

        if not words1 or not words2:
            return 0.0

        intersection = len(words1 & words2)
        union = len(words1 | words2)

        return intersection / union if union > 0 else 0.0
