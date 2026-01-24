"""
통합 파싱 모듈
"""
from .base import BaseParser
from .unified_parser import UnifiedTemplateParser
from .config_manager import ParserConfigManager
from .template import ParsingTemplate
from .template_manager import TemplateManager
from .hybrid_router import HybridRouter

# 하위 호환성을 위해 과목별 파서도 export (deprecated)
from .literature import LiteratureParser  # deprecated
from .math1 import Math1Parser  # deprecated
from .english import EnglishParser  # deprecated

__all__ = [
    'BaseParser',
    'UnifiedTemplateParser',  # 권장: 통합 파서
    'ParserConfigManager',
    'ParsingTemplate',
    'TemplateManager',
    'HybridRouter',
    # Deprecated (하위 호환성 유지)
    'LiteratureParser',
    'Math1Parser',
    'EnglishParser',
]