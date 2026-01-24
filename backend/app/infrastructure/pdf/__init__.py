"""
PDF 처리 인프라

통합 PDF 처리 파이프라인 및 관련 모듈
"""

from .pipeline import UnifiedPipeline
from .page_range_calculator import PageRangeCalculator
from .extractor_factory import ExtractorFactory
from .image_saver import ImageSaver
from .image_cache import ImageCache
from .exceptions import (
    ParsingError,
    ExtractionError,
    TemplateNotFoundError,
    TemplateLoadError,
    ParsingStrategyError,
    SectionExtractionError,
    ImageProcessingError,
    ConfigurationError,
    PageRangeError,
    handle_parsing_error
)

__all__ = [
    "UnifiedPipeline",
    "PageRangeCalculator",
    "ExtractorFactory",
    "ImageSaver",
    "ImageCache",
    "ParsingError",
    "ExtractionError",
    "TemplateNotFoundError",
    "TemplateLoadError",
    "ParsingStrategyError",
    "SectionExtractionError",
    "ImageProcessingError",
    "ConfigurationError",
    "PageRangeError",
    "handle_parsing_error",
]
