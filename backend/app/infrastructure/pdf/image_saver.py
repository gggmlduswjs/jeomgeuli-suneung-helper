"""
이미지 저장 유틸리티
문제/개념/본문 이미지 저장 로직 통합
"""
import json
import logging
from pathlib import Path
from typing import List, Optional, Callable
from PIL import Image

from app.core.config import settings
from app.infrastructure.pdf.exceptions import ImageProcessingError
from app.infrastructure.pdf.image_cache import ImageCache
from app.infrastructure.pdf.types import OCRPageData, SectionData, JSONDict

logger = logging.getLogger(__name__)


class ImageSaver:
    """이미지 저장 유틸리티 클래스
    
    문제, 개념, 본문 이미지 저장 로직을 통합하여 중복 제거
    """
    
    def __init__(
        self,
        pdf_path: Path,
        subject: str,
        book_id: Optional[str] = None,
        render_page_fn: Optional[Callable[[Path, int], Optional[Image.Image]]] = None,
        image_cache: Optional[ImageCache] = None
    ):
        """
        Args:
            pdf_path: PDF 파일 경로
            subject: 과목명
            book_id: 교재 ID (None이면 과목별)
            render_page_fn: PDF 페이지 렌더링 함수 (pdf_path, page_num) -> Image
            image_cache: 이미지 캐시 인스턴스 (None이면 자동 생성)
        """
        self.pdf_path = pdf_path
        self.subject = subject
        self.book_id = book_id
        self.render_page_fn = render_page_fn
        
        # 이미지 캐시 설정
        if image_cache:
            self.image_cache = image_cache
        else:
            self.image_cache = ImageCache(render_page_fn=render_page_fn)
        
        # 데이터 디렉토리 설정
        if self.book_id:
            self.data_dir = settings.API_DIR / "data" / self.subject / self.book_id
        else:
            self.data_dir = settings.API_DIR / "data" / self.subject
    
    def save_images(
        self,
        items: List[JSONDict],
        item_type: str,
        ocr_data: List[OCRPageData],
        filename_generator: Optional[Callable[[JSONDict, int, int], str]] = None,
        save_metadata: bool = False
    ) -> int:
        """
        이미지 저장 (공통 로직)
        
        Args:
            items: 저장할 아이템 리스트 (각 아이템은 page, bbox 필수)
            item_type: 아이템 타입 ('problem', 'concept', 'content')
            ocr_data: OCR 데이터 (페이지 경로 정보 포함)
            filename_generator: 파일명 생성 함수 (item, page_num, idx) -> filename
            save_metadata: JSON 메타데이터 저장 여부 (문제만 True)
            
        Returns:
            저장된 이미지 수
        """
        if not items:
            logger.debug(f"   저장할 {item_type} 섹션이 없습니다.")
            return 0
        
        # 저장 디렉토리 설정
        images_dir = self.data_dir / f"{item_type}s_images"
        images_dir.mkdir(parents=True, exist_ok=True)
        
        # 페이지별로 그룹화
        items_by_page = {}
        for item in items:
            page = item.get('page', 0)
            if page not in items_by_page:
                items_by_page[page] = []
            items_by_page[page].append(item)
        
        saved_count = 0
        
        # 각 페이지에서 이미지 크롭 및 저장
        for page_num, page_items in items_by_page.items():
            try:
                if not page_num or int(page_num) < 1:
                    logger.warning(f"   유효하지 않은 페이지 번호로 {item_type} 이미지 저장 건너뜀: {page_num}")
                    continue
                
                # 페이지 이미지 가져오기
                page_image = self._get_page_image(page_num, ocr_data)
                if page_image is None:
                    logger.warning(f"   페이지 {page_num} 이미지를 가져올 수 없음")
                    continue
                
                # 각 아이템 이미지 크롭 및 저장
                for idx, item in enumerate(page_items):
                    try:
                        # bbox 검증
                        bbox = item.get('bbox', [])
                        if not bbox or len(bbox) < 4:
                            item_id = item.get('problem_id') or item.get('title', '') or str(idx)
                            logger.warning(f"   {item_type} {item_id}의 bbox가 유효하지 않음: {bbox}")
                            continue
                        
                        # bbox 정규화
                        left, top, right, bottom = self._normalize_bbox(bbox, page_image.size)
                        
                        # 이미지 크롭
                        cropped_image = page_image.crop((left, top, right, bottom))
                        
                        # 파일명 생성
                        if filename_generator:
                            filename = filename_generator(item, page_num, idx)
                        else:
                            filename = self._default_filename_generator(item_type, item, page_num, idx)
                        
                        output_path = images_dir / filename
                        
                        # 이미지 저장
                        cropped_image.save(output_path, 'PNG')
                        logger.debug(
                            f"   {item_type} 이미지 저장: {filename} "
                            f"(bbox: [{left}, {top}, {right}, {bottom}])"
                        )
                        saved_count += 1
                        
                        # 섹션 데이터에 이미지 파일명 추가 (원본 item이 섹션인 경우)
                        if 'section_ref' in item:
                            section_ref = item['section_ref']
                            if section_ref:
                                section_ref['image_filename'] = filename
                                section_ref['image_path'] = str(output_path.relative_to(self.data_dir))
                                logger.debug(f"   섹션 데이터에 이미지 경로 추가: {filename}")
                        
                        # 메타데이터 저장 (문제만)
                        if save_metadata:
                            self._save_metadata(item, page_num, bbox, images_dir, filename)
                            
                    except ImageProcessingError:
                        raise  # 이미지 처리 예외는 그대로 전파
                    except Exception as e:
                        item_id = item.get('problem_id') or item.get('title', '') or str(idx)
                        logger.error(f"   {item_type} {item_id} 이미지 크롭 실패: {e}")
                        # 개별 아이템 실패는 전체 프로세스를 중단하지 않음
                        continue
                        
            except ImageProcessingError:
                raise  # 이미지 처리 예외는 그대로 전파
            except Exception as e:
                logger.error(f"   페이지 {page_num} 처리 실패: {e}")
                # 페이지별 실패는 전체 프로세스를 중단하지 않음
                continue
        
        return saved_count
    
    def _get_page_image(self, page_num: int, ocr_data: List[OCRPageData]) -> Optional[Image.Image]:
        """페이지 이미지 가져오기 (캐싱 지원)
        
        Args:
            page_num: 페이지 번호
            ocr_data: OCR 데이터
            
        Returns:
            PIL.Image 또는 None
        """
        return self.image_cache.get_page_image(
            pdf_path=self.pdf_path,
            page_num=page_num,
            ocr_data=ocr_data,
            fallback_to_ocr=True
        )
    
    def _normalize_bbox(
        self,
        bbox: List[float],
        image_size: tuple
    ) -> tuple:
        """bbox를 이미지 크기에 맞게 정규화
        
        Args:
            bbox: [left, top, right, bottom]
            image_size: (width, height)
            
        Returns:
            (left, top, right, bottom) 정규화된 좌표
            
        Raises:
            ImageProcessingError: bbox가 유효하지 않을 때
        """
        if len(bbox) < 4:
            raise ImageProcessingError(
                f"bbox는 4개 요소가 필요합니다: {bbox}",
                details={"bbox": bbox, "image_size": image_size}
            )
        
        left, top, right, bottom = bbox[:4]
        img_width, img_height = image_size
        
        # 이미지 크기를 넘지 않도록 제한
        left = max(0, min(int(left), img_width - 1))
        top = max(0, min(int(top), img_height - 1))
        right = max(left + 1, min(int(right), img_width))
        bottom = max(top + 1, min(int(bottom), img_height))
        
        return (left, top, right, bottom)
    
    def _default_filename_generator(
        self,
        item_type: str,
        item: JSONDict,
        page_num: int,
        idx: int
    ) -> str:
        """기본 파일명 생성기
        
        Args:
            item_type: 아이템 타입
            item: 아이템 딕셔너리
            page_num: 페이지 번호
            idx: 페이지 내 인덱스
            
        Returns:
            파일명
        """
        if item_type == 'problem':
            problem_id = item.get('problem_id', f'unknown_{idx}')
            return f"problem_p{page_num:02d}_{problem_id}.png"
        elif item_type == 'concept':
            return f"concept_p{page_num:02d}_{idx+1:02d}.png"
        elif item_type == 'content':
            return f"content_p{page_num:02d}_{idx+1:02d}.png"
        else:
            return f"{item_type}_p{page_num:02d}_{idx+1:02d}.png"
    
    def _save_metadata(
        self,
        item: JSONDict,
        page_num: int,
        bbox: List[float],
        images_dir: Path,
        image_filename: str
    ):
        """메타데이터 JSON 파일 저장 (문제만)
        
        Args:
            item: 아이템 딕셔너리
            page_num: 페이지 번호
            bbox: bbox 좌표
            images_dir: 이미지 디렉토리
            image_filename: 이미지 파일명
        """
        try:
            problem_id = item.get('problem_id', '')
            json_filename = image_filename.replace('.png', '.json')
            json_path = images_dir / json_filename
            
            metadata = {
                "problem_id": problem_id,
                "page": page_num,
                "bbox": bbox[:4] if len(bbox) >= 4 else bbox
            }
            
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, ensure_ascii=False, indent=2)
                
        except Exception as e:
            logger.warning(f"   메타데이터 저장 실패: {e}")
    
    def save_problem_images(
        self,
        problems: List[JSONDict],
        ocr_data: List[OCRPageData]
    ) -> int:
        """문제 이미지 저장
        
        Args:
            problems: 문제 리스트
            ocr_data: OCR 데이터
            
        Returns:
            저장된 이미지 수
        """
        def filename_gen(item, page_num, idx):
            problem_id = item.get('problem_id', f'unknown_{idx}')
            return f"problem_p{page_num:02d}_{problem_id}.png"
        
        return self.save_images(
            items=problems,
            item_type='problem',
            ocr_data=ocr_data,
            filename_generator=filename_gen,
            save_metadata=True
        )
    
    def save_concept_images(
        self,
        lecture_contents: List[JSONDict],
        ocr_data: List[OCRPageData]
    ) -> int:
        """개념 이미지 저장
        
        Args:
            lecture_contents: 강의 콘텐츠 리스트
            ocr_data: OCR 데이터
            
        Returns:
            저장된 이미지 수
        """
        # 강의 콘텐츠에서 개념 섹션 추출
        concepts = []
        for lecture_content in lecture_contents:
            sections = lecture_content.get('sections', [])
            for section in sections:
                if section.get('type') == 'concept':
                    concepts.append({
                        'lecture_id': lecture_content.get('lecture_id', ''),
                        'title': section.get('title', ''),
                        'page': section.get('page', 0),
                        'bbox': section.get('bbox', []),
                        'section_ref': section  # 원본 섹션 참조 추가
                    })
        
        return self.save_images(
            items=concepts,
            item_type='concept',
            ocr_data=ocr_data
        )
    
    def save_content_images(
        self,
        lecture_contents: List[JSONDict],
        ocr_data: List[OCRPageData]
    ) -> int:
        """본문 이미지 저장
        
        Args:
            lecture_contents: 강의 콘텐츠 리스트
            ocr_data: OCR 데이터
            
        Returns:
            저장된 이미지 수
        """
        # 강의 콘텐츠에서 본문 섹션 추출
        contents = []
        for lecture_content in lecture_contents:
            sections = lecture_content.get('sections', [])
            for section in sections:
                if section.get('type') in ['content', 'passage']:
                    contents.append({
                        'lecture_id': lecture_content.get('lecture_id', ''),
                        'title': section.get('title', ''),
                        'page': section.get('page', 0),
                        'bbox': section.get('bbox', []),
                        'section_ref': section  # 원본 섹션 참조 추가
                    })
        
        return self.save_images(
            items=contents,
            item_type='content',
            ocr_data=ocr_data
        )
