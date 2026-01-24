"""
파싱 템플릿 데이터 구조
EBS 교재 파싱 패턴을 재사용 가능한 템플릿으로 정의
"""
from dataclasses import dataclass, field
from typing import List, Optional
from pathlib import Path
import json

from app.infrastructure.pdf.types import JSONDict


@dataclass
class ParsingTemplate:
    """교재 파싱 템플릿
    
    EBS 교재의 파싱 패턴을 템플릿으로 저장하여 재사용
    
    Attributes:
        name: 템플릿 이름 (예: "ebs_수능특강_문학_2026")
        subject: 과목명 ('literature', 'math1', 'english')
        version: 템플릿 버전 (예: "2026", "2025")
        description: 템플릿 설명
        patterns: 파싱 패턴 딕셔너리
            - lecture_title_patterns: 강의 제목 정규식 리스트
            - toc_lecture_patterns: 목차 강의 패턴 리스트
            - concept_title_patterns: 개념 제목 패턴 리스트
            - content_header_patterns: 본문 헤더 패턴 리스트
            - section_title_patterns: 섹션 제목 패턴 리스트
            - problem_number_pattern: 문제 번호 정규식
        config: 추가 설정
            - toc_end_page: 목차 종료 페이지
            - start_content_page: 본문 시작 페이지
            - paragraph_y_threshold: 문단 Y 좌표 임계값
            - toc_text: 관리자가 입력한 TOC 텍스트 (선택, 파싱 시 우선 사용)
            - toc_lecture_list: TOC 텍스트에서 추출한 강의 목록 (선택, 파싱 시 우선 사용)
            - region_hints: 영역 힌트 (y 좌표 기반)
            - region_text_examples: 영역 내 텍스트 예시 (패턴 학습용)
            - region_image_examples: 영역 이미지 예시 (시각적 참고용)
            - font_info: 폰트 정보 (제목/본문 구분, 섹션 타입 판별)
            - layout_info: 레이아웃 정보 (헤더/푸터, 여백, 컬럼 구조)
            - problem_patterns: 문제 번호 패턴 상세 (형식, 위치, 답안 형식)
            - section_spacing: 섹션 간 간격 정보 (경계 판별용)
        confidence: 기본 신뢰도 (0.0-1.0, 템플릿 매칭 시 초기값)
        sample_texts: 샘플 텍스트 (매칭용, 첫 3-5페이지)
        stats: 템플릿 통계 정보 (선택)
        created_at: 템플릿 생성 시각
        updated_at: 템플릿 업데이트 시각
    """
    name: str
    subject: str
    version: str = ""
    description: str = ""
    patterns: JSONDict = field(default_factory=dict)
    config: JSONDict = field(default_factory=dict)
    confidence: float = 0.0
    sample_texts: List[str] = field(default_factory=list)
    stats: Optional[JSONDict] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    def to_dict(self) -> JSONDict:
        """딕셔너리로 변환 (JSON 저장용)"""
        result = {
            "name": self.name,
            "subject": self.subject,
            "version": self.version,
            "description": self.description,
            "patterns": self.patterns,
            "config": self.config,
            "confidence": self.confidence,
            "sample_texts": self.sample_texts,
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }
        # 통계 정보가 있으면 추가
        if self.stats:
            result["stats"] = self.stats
        return result

    @classmethod
    def from_dict(cls, data: JSONDict) -> "ParsingTemplate":
        """딕셔너리에서 생성"""
        return cls(
            name=data.get("name", ""),
            subject=data.get("subject", ""),
            version=data.get("version", ""),
            description=data.get("description", ""),
            patterns=data.get("patterns", {}),
            config=data.get("config", {}),
            confidence=data.get("confidence", 0.0),
            sample_texts=data.get("sample_texts", []),
            stats=data.get("stats"),
            created_at=data.get("created_at"),
            updated_at=data.get("updated_at")
        )

    @classmethod
    def from_config_json(
        cls,
        name: str,
        subject: str,
        config_path: Path,
        version: str = "",
        description: str = ""
    ) -> "ParsingTemplate":
        """기존 config.json 파일에서 템플릿 생성
        
        Args:
            name: 템플릿 이름
            subject: 과목명
            config_path: config.json 파일 경로
            version: 버전 (예: "2026")
            description: 설명
            
        Returns:
            ParsingTemplate 인스턴스
        """
        if not config_path.exists():
            raise FileNotFoundError(f"Config file not found: {config_path}")
        
        with open(config_path, 'r', encoding='utf-8') as f:
            config_data = json.load(f)
        
        # config.json 구조를 템플릿 구조로 변환
        patterns = {
            "lecture_title_patterns": config_data.get("lecture_title_patterns", []),
            "toc_lecture_patterns": config_data.get("toc_lecture_patterns", []),
            "concept_title_patterns": config_data.get("concept_title_patterns", []),
            "content_header_patterns": config_data.get("content_header_patterns", []),
            "section_title_patterns": config_data.get("section_title_patterns", []),
            "problem_number_pattern": config_data.get("problem_number_pattern", "")
        }
        
        config = {
            "toc_end_page": config_data.get("toc_end_page", 7),
            "start_content_page": config_data.get("start_content_page", 8),
            "paragraph_y_threshold": config_data.get("paragraph_y_threshold", 25)
        }
        
        return cls(
            name=name,
            subject=subject,
            version=version,
            description=description,
            patterns=patterns,
            config=config,
            confidence=0.85  # config.json 기반 템플릿은 기본 신뢰도 85%
        )

    def save(self, template_dir: Path) -> Path:
        """템플릿을 JSON 파일로 저장
        
        Args:
            template_dir: 템플릿 저장 디렉토리
            
        Returns:
            저장된 파일 경로
        """
        template_dir.mkdir(parents=True, exist_ok=True)
        
        # 파일명: {subject}_{name}.json
        filename = f"{self.subject}_{self.name}.json"
        file_path = template_dir / filename
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(self.to_dict(), f, ensure_ascii=False, indent=2)
        
        return file_path

    @classmethod
    def load(cls, template_path: Path) -> "ParsingTemplate":
        """JSON 파일에서 템플릿 로드
        
        Args:
            template_path: 템플릿 파일 경로
            
        Returns:
            ParsingTemplate 인스턴스
        """
        if not template_path.exists():
            raise FileNotFoundError(f"Template file not found: {template_path}")
        
        with open(template_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        return cls.from_dict(data)
