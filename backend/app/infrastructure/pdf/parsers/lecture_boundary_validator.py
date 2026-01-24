"""
강의 경계 검증기
TOC 강의 목록을 활용한 강의 경계 검증 및 보정
"""
import logging
from typing import List, Dict, Any, Optional
from difflib import SequenceMatcher
import re

logger = logging.getLogger(__name__)


class LectureBoundaryValidator:
    """강의 목록을 활용한 경계 검증"""
    
    def __init__(self, toc_lecture_list: List[Dict[str, Any]]):
        """
        Args:
            toc_lecture_list: TOC 강의 목록
        """
        self.toc_lecture_list = toc_lecture_list
        
        # 강의 ID별 정보 맵
        self.lecture_map = {
            l.get('lecture_id'): l
            for l in toc_lecture_list
            if l.get('lecture_id') is not None
        }
    
    def validate_lecture_boundaries(
        self,
        extracted_lectures: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """추출된 강의 목록을 TOC와 비교하여 검증
        
        Args:
            extracted_lectures: 추출된 강의 목록
            
        Returns:
            {
                'validated_lectures': 검증된 강의 목록,
                'missing_lectures': 누락된 강의 목록,
                'extra_lectures': 추가로 발견된 강의 목록,
                'validation_summary': 검증 요약
            }
        """
        validated_lectures = []
        missing_lectures = []
        extra_lectures = []
        
        # TOC 강의 ID 집합
        toc_lecture_ids = set(self.lecture_map.keys())
        extracted_lecture_ids = set(l.get('lecture_id') for l in extracted_lectures if l.get('lecture_id'))
        
        # 누락된 강의 찾기
        missing_ids = toc_lecture_ids - extracted_lecture_ids
        for lecture_id in missing_ids:
            toc_lecture = self.lecture_map[lecture_id]
            missing_lectures.append({
                **toc_lecture,
                'reason': 'not_extracted',
                'suggested_page': toc_lecture.get('start_page')
            })
        
        # 추가로 발견된 강의 찾기
        extra_ids = extracted_lecture_ids - toc_lecture_ids
        for lecture in extracted_lectures:
            if lecture.get('lecture_id') in extra_ids:
                extra_lectures.append({
                    **lecture,
                    'reason': 'not_in_toc'
                })
        
        # 추출된 강의 검증 및 보정
        for extracted in extracted_lectures:
            lecture_id = extracted.get('lecture_id')
            
            if lecture_id in self.lecture_map:
                toc_lecture = self.lecture_map[lecture_id]
                
                # 제목 유사도 확인
                extracted_title = extracted.get('title', '')
                toc_title = toc_lecture.get('title', '')
                title_similarity = self._calculate_title_similarity(extracted_title, toc_title)
                
                # 페이지 범위 검증
                extracted_page = extracted.get('page')
                toc_start_page = toc_lecture.get('start_page')
                toc_end_page = toc_lecture.get('end_page')
                
                page_valid = True
                if toc_start_page is not None:
                    if extracted_page is None:
                        page_valid = False
                    else:
                        # 페이지가 범위 내에 있는지 확인 (여유 있게 ±3페이지)
                        if toc_end_page:
                            page_valid = (toc_start_page - 3) <= extracted_page <= (toc_end_page + 3)
                        else:
                            page_valid = extracted_page >= (toc_start_page - 3)
                
                # 보정 적용
                if not page_valid and toc_start_page:
                    logger.info(
                        f"[강의 경계 보정] 강의 {lecture_id}: "
                        f"페이지 {extracted_page} -> {toc_start_page} (TOC 기준)"
                    )
                    extracted['page'] = toc_start_page
                    extracted['start_page'] = toc_start_page
                    extracted['end_page'] = toc_end_page
                
                if title_similarity < 0.7 and toc_title:
                    logger.info(
                        f"[강의 제목 보정] 강의 {lecture_id}: "
                        f"'{extracted_title}' -> '{toc_title}' (유사도: {title_similarity:.2f})"
                    )
                    extracted['title'] = toc_title
                    extracted['original_title'] = extracted_title  # 원본 보존
                
                extracted['validated'] = True
                extracted['validation_confidence'] = title_similarity
                extracted['toc_title'] = toc_title
            else:
                extracted['validated'] = False
                extracted['validation_confidence'] = 0.0
            
            validated_lectures.append(extracted)
        
        # 누락된 강의를 적절한 위치에 삽입
        for missing in missing_lectures:
            # 적절한 위치 찾기 (lecture_id 순서대로)
            insert_idx = len(validated_lectures)
            for i, lecture in enumerate(validated_lectures):
                if lecture.get('lecture_id', 0) > missing.get('lecture_id', 0):
                    insert_idx = i
                    break
            
            validated_lectures.insert(insert_idx, {
                'lecture_id': missing.get('lecture_id'),
                'title': missing.get('title'),
                'page': missing.get('start_page'),
                'start_page': missing.get('start_page'),
                'end_page': missing.get('end_page'),
                'validated': True,
                'validation_confidence': 1.0,
                'source': 'toc_only',
                'toc_title': missing.get('title')
            })
        
        # lecture_id 순서대로 정렬
        validated_lectures.sort(key=lambda x: x.get('lecture_id', 0))
        
        validation_summary = {
            'total_toc_lectures': len(self.toc_lecture_list),
            'total_extracted_lectures': len(extracted_lectures),
            'validated_count': len([l for l in validated_lectures if l.get('validated', False)]),
            'missing_count': len(missing_lectures),
            'extra_count': len(extra_lectures),
            'final_count': len(validated_lectures)
        }
        
        if missing_lectures:
            logger.warning(
                f"[강의 경계 검증] {len(missing_lectures)}개 강의 누락: "
                f"{[l.get('lecture_id') for l in missing_lectures]}"
            )
        
        if extra_lectures:
            logger.info(
                f"[강의 경계 검증] {len(extra_lectures)}개 추가 강의 발견: "
                f"{[l.get('lecture_id') for l in extra_lectures]}"
            )
        
        return {
            'validated_lectures': validated_lectures,
            'missing_lectures': missing_lectures,
            'extra_lectures': extra_lectures,
            'validation_summary': validation_summary
        }
    
    def _calculate_title_similarity(
        self,
        title1: str,
        title2: str
    ) -> float:
        """두 강의 제목의 유사도 계산"""
        if not title1 or not title2:
            return 0.0
        
        # 정규화: 강의 번호, 특수문자 제거
        def normalize(title: str) -> str:
            title = re.sub(r'^\d+강\s*[|]?\s*', '', title)
            title = re.sub(r'[^\w\s가-힣]', '', title)
            return title.strip()
        
        norm1 = normalize(title1)
        norm2 = normalize(title2)
        
        if not norm1 or not norm2:
            return 0.0
        
        # SequenceMatcher로 유사도 계산
        similarity = SequenceMatcher(None, norm1, norm2).ratio()
        
        # 키워드 기반 보정
        words1 = set(re.findall(r'[가-힣]{2,}', norm1))
        words2 = set(re.findall(r'[가-힣]{2,}', norm2))
        
        if words1 and words2:
            common_words = words1 & words2
            word_similarity = len(common_words) / max(len(words1), len(words2))
            similarity = (similarity + word_similarity) / 2.0
        
        return similarity
